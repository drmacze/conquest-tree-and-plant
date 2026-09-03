#!/usr/bin/env python3
"""Validate and package DLavie Conquest Nature for Bedrock 1.26.45+."""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

from apply_species_visuals import apply as apply_species_visuals
from apply_tree_forms import SPECIES as TREE_FORM_SPECIES, apply as apply_tree_forms
from generate_obj_runtime_assets import generate as generate_obj_runtime_assets

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
DIST = ROOT / "dist"
VERSION = "0.3.3"
PACK_VERSION = [0, 3, 3]
TARGET_ENGINE = [1, 26, 45]
BLOCK_SCHEMA_FLOOR = (1, 26, 0)
REQUIRED_TEXTURES = [
    "dlavie_branch_bark.png",
    "dlavie_branch_end.png",
    "dlavie_leaf_oak.png",
    "dlavie_fern.png",
    "dlavie_meadow_grass.png",
    "dlavie_clover.png",
    "dlavie_heather.png",
    "dlavie_nettle.png",
    "dlavie_obj_bark.png",
    "dlavie_obj_leaf.png",
    "dlavie_wal_bark.png",
    "dlavie_wal_leaf.png",
    "dlavie_mos_bark.png",
    "dlavie_mos_leaf.png",
    "dlavie_sml_bark.png",
    "dlavie_sml_leaf.png",
    "dlavie_oak_bark.png",
    "dlavie_oak_leaf.png",
    "dlavie_gnt_bark.png",
    "dlavie_gnt_leaf.png",
    "dlavie_son_bark.png",
    "dlavie_son_leaf.png",
    "dlavie_tal_bark.png",
    "dlavie_tal_leaf.png",
]
OBJ_STRUCTURE_NAMES = list(TREE_FORM_SPECIES)
REQUIRED_STRUCTURES = [BP / "structures" / "dlavie" / f"{name}.mcstructure" for name in OBJ_STRUCTURE_NAMES]
REQUIRED_FORM_GEOMETRIES = [
    "obj_trunk.geo.json",
    "obj_branch_x.geo.json",
    "obj_branch_z.geo.json",
    "obj_branch_d1.geo.json",
    "obj_branch_d2.geo.json",
    "obj_root.geo.json",
    "obj_leaf_sparse.geo.json",
    "obj_leaf_medium.geo.json",
    "obj_leaf_dense.geo.json",
]


def parse_version(value: object) -> tuple[int, int, int] | None:
    if isinstance(value, str):
        parts = value.split(".")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            return tuple(int(part) for part in parts)  # type: ignore[return-value]
    if isinstance(value, list) and len(value) == 3 and all(isinstance(part, int) for part in value):
        return tuple(value)  # type: ignore[return-value]
    return None


def validate_json() -> None:
    errors: list[str] = []
    json_files = sorted([*BP.rglob("*.json"), *RP.rglob("*.json")])
    parsed: dict[Path, object] = {}
    for path in json_files:
        try:
            with path.open("r", encoding="utf-8") as handle:
                parsed[path] = json.load(handle)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    for manifest in (BP / "manifest.json", RP / "manifest.json"):
        data = parsed.get(manifest)
        if not isinstance(data, dict):
            continue
        header = data.get("header")
        if not isinstance(header, dict):
            errors.append(f"{manifest.relative_to(ROOT)}: missing header")
            continue
        if header.get("min_engine_version") != TARGET_ENGINE:
            errors.append(f"{manifest.relative_to(ROOT)}: min_engine_version must be {TARGET_ENGINE}")
        if header.get("version") != PACK_VERSION:
            errors.append(f"{manifest.relative_to(ROOT)}: header version must be {PACK_VERSION}")

    rp_manifest = parsed.get(RP / "manifest.json")
    if isinstance(rp_manifest, dict) and "pbr" not in rp_manifest.get("capabilities", []):
        errors.append("resource_pack/manifest.json: capabilities must include 'pbr'")

    for path in sorted((BP / "blocks").glob("*.json")):
        data = parsed.get(path)
        if not isinstance(data, dict):
            continue
        format_version = parse_version(data.get("format_version"))
        if format_version is None or format_version < BLOCK_SCHEMA_FLOOR:
            errors.append(f"{path.relative_to(ROOT)}: block format_version must be >= 1.26.0")

    texture_dir = RP / "textures" / "blocks"
    for filename in REQUIRED_TEXTURES:
        if not (texture_dir / filename).is_file():
            errors.append(f"resource_pack/textures/blocks/{filename}: required texture missing")

    geometry_dir = RP / "models" / "blocks"
    for filename in REQUIRED_FORM_GEOMETRIES:
        if not (geometry_dir / filename).is_file():
            errors.append(f"resource_pack/models/blocks/{filename}: required v0.3.3 form geometry missing")

    for structure in REQUIRED_STRUCTURES:
        if not structure.is_file() or structure.stat().st_size < 128:
            errors.append(f"{structure.relative_to(ROOT)}: required OBJ-derived structure missing or invalid")

    for name, meta in TREE_FORM_SPECIES.items():
        path = BP / "structures" / "dlavie" / f"{name}.mcstructure"
        if not path.is_file():
            continue
        data = path.read_bytes()
        code = meta["code"]
        required_ids = [
            f"dlavie:{code}_trunk".encode(),
            f"dlavie:{code}_root".encode(),
            f"dlavie:{code}_leaf_cluster".encode(),
        ]
        for block_id in required_ids:
            if block_id not in data:
                errors.append(f"{path.relative_to(ROOT)}: missing form palette id {block_id.decode()}")

    form_report = ROOT / "docs" / "V033_TREE_FORMS.json"
    if not form_report.is_file():
        errors.append("docs/V033_TREE_FORMS.json: v0.3.3 form report missing")

    for pack in (BP, RP):
        if not (pack / "pack_icon.png").is_file():
            errors.append(f"{pack.name}/pack_icon.png: pack icon missing")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)
    print(
        f"Validated {len(json_files)} JSON files + {len(REQUIRED_STRUCTURES)} directional OBJ structures "
        f"for DLavie Conquest Nature {VERSION} / Bedrock 1.26.45+."
    )


def zip_directory(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))


def build() -> None:
    generate_obj_runtime_assets(ROOT)
    apply_species_visuals(ROOT)
    apply_tree_forms(ROOT)
    validate_json()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    bp_mcpack = DIST / f"DLavie-Conquest-Nature-BP-{VERSION}.mcpack"
    rp_mcpack = DIST / f"DLavie-Conquest-Nature-RP-{VERSION}.mcpack"
    mcaddon = DIST / f"DLavie-Conquest-Nature-{VERSION}.mcaddon"
    zip_directory(BP, bp_mcpack)
    zip_directory(RP, rp_mcpack)
    with zipfile.ZipFile(mcaddon, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for prefix, source in (("DLavie_Conquest_Nature_BP", BP), ("DLavie_Conquest_Nature_RP", RP)):
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, Path(prefix) / path.relative_to(source))
    print("Built:")
    for artifact in (bp_mcpack, rp_mcpack, mcaddon):
        print(f"  - {artifact.relative_to(ROOT)}")


if __name__ == "__main__":
    build()

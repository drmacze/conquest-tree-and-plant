#!/usr/bin/env python3
"""Validate and package DLavie Conquest Nature for Minecraft Bedrock 1.26.45+."""
from __future__ import annotations
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"
DIST = ROOT / "dist"
VERSION = "0.2.0"
TARGET_ENGINE = [1, 26, 45]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate() -> None:
    errors: list[str] = []
    json_files = sorted([*BP.rglob("*.json"), *RP.rglob("*.json")])
    for path in json_files:
        try:
            load_json(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")

    if not errors:
        for manifest in (BP / "manifest.json", RP / "manifest.json"):
            data = load_json(manifest)
            if data["header"].get("min_engine_version") != TARGET_ENGINE:
                errors.append(f"{manifest.relative_to(ROOT)} must target {TARGET_ENGINE}")
            if data["header"].get("version") != [0, 2, 0]:
                errors.append(f"{manifest.relative_to(ROOT)} must use pack version [0, 2, 0]")

        rp_manifest = load_json(RP / "manifest.json")
        if "pbr" not in rp_manifest.get("capabilities", []):
            errors.append("resource_pack/manifest.json must include the pbr capability")

        terrain = load_json(RP / "textures" / "terrain_texture.json")
        for key, entry in terrain.get("texture_data", {}).items():
            ref = entry.get("textures")
            if not isinstance(ref, str) or not ref.startswith("textures/nature/"):
                errors.append(f"{key}: v0.2 texture must be an original textures/nature asset")
                continue
            source = RP / f"{ref}.png"
            if not source.exists():
                errors.append(f"{key}: missing {source.relative_to(ROOT)}")

        for block_path in sorted((BP / "blocks").glob("*.json")):
            data = load_json(block_path)
            if not str(data.get("format_version", "")).startswith("1.26."):
                errors.append(f"{block_path.relative_to(ROOT)} must use 1.26.x block schema")
            comps = data.get("minecraft:block", {}).get("components", {})
            if "minecraft:geometry" in comps and "minecraft:material_instances" not in comps:
                errors.append(f"{block_path.relative_to(ROOT)}: geometry requires material_instances")

        required = [RP / "pack_icon.png", BP / "pack_icon.png", RP / "textures/nature/leaf_oak.texture_set.json", BP / "features/woodland_oak_b_feature.json", BP / "features/woodland_oak_c_feature.json"]
        for path in required:
            if not path.exists():
                errors.append(f"missing required v0.2 file: {path.relative_to(ROOT)}")

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Validated {len(json_files)} JSON files for Bedrock 1.26.45+.")


def zip_directory(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))


def build() -> None:
    validate()
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

#!/usr/bin/env python3
"""Generate species-specific runtime definitions and patch OBJ structure palettes."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

SPECIES = {
    "wal": {"tree": "obj_walnut_01", "roughness": 225, "subsurface": 95},
    "mos": {"tree": "obj_mossy_01", "roughness": 215, "subsurface": 105},
    "sml": {"tree": "obj_bark_small_01", "roughness": 230, "subsurface": 100},
    "oak": {"tree": "obj_oak_01", "roughness": 232, "subsurface": 100},
    "gnt": {"tree": "obj_giant_01", "roughness": 228, "subsurface": 95},
    "son": {"tree": "obj_sonnerat_01", "roughness": 220, "subsurface": 100},
    "tal": {"tree": "obj_bark_tall_01", "roughness": 230, "subsurface": 100},
}
PAIRS = {meta["tree"]: (f"{code}_branch", f"{code}_leaf_cluster") for code, meta in SPECIES.items()}
GENERIC_BRANCH = b"dlavie:obj_branch"
GENERIC_LEAF = b"dlavie:obj_leaf_cluster"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _extract_texture_archive(root: Path) -> None:
    archive = root / "tools" / "assets" / "species_textures.zip"
    destination = root / "resource_pack" / "textures" / "blocks"
    if not archive.is_file():
        raise FileNotFoundError(f"Missing source texture archive: {archive.relative_to(root)}")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = Path(info.filename)
            if info.is_dir():
                continue
            if name.parent != Path(".") or name.suffix.lower() != ".png" or not name.name.startswith("dlavie_"):
                raise ValueError(f"Unsafe or unexpected species texture entry: {info.filename}")
            target = destination / name.name
            target.write_bytes(zf.read(info))
    # Remove temporary payload files from earlier development iterations so they
    # never leak into a packaged Resource Pack.
    for stale in destination.glob("*.png.b64"):
        stale.unlink()


def _generate_blocks(root: Path) -> None:
    blocks = root / "behavior_pack" / "blocks"
    texture_sets = root / "resource_pack" / "textures" / "blocks"
    terrain_path = root / "resource_pack" / "textures" / "terrain_texture.json"
    terrain = json.loads(terrain_path.read_text(encoding="utf-8"))
    texture_data = terrain["texture_data"]

    for code, meta in SPECIES.items():
        branch = {
            "format_version": "1.26.20",
            "minecraft:block": {
                "description": {"identifier": f"dlavie:{code}_branch", "menu_category": {"category": "nature"}},
                "components": {
                    "minecraft:geometry": "geometry.dlavie.obj_branch",
                    "minecraft:material_instances": {
                        "*": {"texture": f"dlavie_{code}_bark", "render_method": "opaque", "ambient_occlusion": 1.0}
                    },
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.8},
                    "minecraft:flammable": {"catch_chance_modifier": 5, "destroy_chance_modifier": 5},
                },
            },
        }
        leaf = {
            "format_version": "1.26.20",
            "minecraft:block": {
                "description": {"identifier": f"dlavie:{code}_leaf_cluster", "menu_category": {"category": "nature"}},
                "components": {
                    "minecraft:geometry": "geometry.dlavie.obj_leaf_cluster",
                    "minecraft:material_instances": {
                        "*": {"texture": f"dlavie_{code}_leaf", "render_method": "alpha_test_single_sided", "ambient_occlusion": 0.0}
                    },
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.15},
                    "minecraft:collision_box": False,
                    "minecraft:light_dampening": 0,
                    "minecraft:flammable": {"catch_chance_modifier": 30, "destroy_chance_modifier": 60},
                },
            },
        }
        bark_set = {
            "format_version": "1.21.30",
            "minecraft:texture_set": {
                "color": f"dlavie_{code}_bark",
                "metalness_emissive_roughness": [0, 0, meta["roughness"]],
            },
        }
        leaf_set = {
            "format_version": "1.21.30",
            "minecraft:texture_set": {
                "color": f"dlavie_{code}_leaf",
                "metalness_emissive_roughness_subsurface": [0, 0, 190, meta["subsurface"]],
            },
        }
        _write_json(blocks / f"{code}_branch.json", branch)
        _write_json(blocks / f"{code}_leaf_cluster.json", leaf)
        _write_json(texture_sets / f"dlavie_{code}_bark.texture_set.json", bark_set)
        _write_json(texture_sets / f"dlavie_{code}_leaf.texture_set.json", leaf_set)
        texture_data[f"dlavie_{code}_bark"] = {"textures": f"textures/blocks/dlavie_{code}_bark"}
        texture_data[f"dlavie_{code}_leaf"] = {"textures": f"textures/blocks/dlavie_{code}_leaf"}

    _write_json(terrain_path, terrain)


def _patch_structures(root: Path) -> None:
    structures = root / "behavior_pack" / "structures" / "dlavie"
    for name, (branch, leaf) in PAIRS.items():
        path = structures / f"{name}.mcstructure"
        data = path.read_bytes()
        branch_id = f"dlavie:{branch}".encode()
        leaf_id = f"dlavie:{leaf}".encode()
        if len(branch_id) != len(GENERIC_BRANCH) or len(leaf_id) != len(GENERIC_LEAF):
            raise ValueError(f"Palette replacement must preserve NBT string length for {name}")
        if GENERIC_BRANCH in data and GENERIC_LEAF in data:
            data = data.replace(GENERIC_BRANCH, branch_id).replace(GENERIC_LEAF, leaf_id)
            path.write_bytes(data)
        elif branch_id not in data or leaf_id not in data:
            raise ValueError(f"{path}: expected OBJ palette entries not found")


def apply(root: Path) -> None:
    _extract_texture_archive(root)
    _generate_blocks(root)
    _patch_structures(root)


if __name__ == "__main__":
    apply(Path(__file__).resolve().parents[1])

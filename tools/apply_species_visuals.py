#!/usr/bin/env python3
"""Generate v0.3.2 species visuals and patch OBJ structure palettes.

The supplied OBJ/JPG pack is used as the visual reference for each species.
Runtime textures are rebuilt deterministically with species-calibrated bark and
foliage palettes so CI and packaged add-ons do not depend on fragile external
binary asset transfers.
"""

from __future__ import annotations

import json
import math
import random
import struct
import zlib
from pathlib import Path

SPECIES = {
    "wal": {
        "tree": "obj_walnut_01", "roughness": 225, "subsurface": 95, "seed": 101,
        "bark": (112, 77, 50), "bark_dark": (58, 39, 27),
        "leaves": [(86, 107, 55), (111, 132, 67), (137, 151, 78), (161, 169, 94)],
        "density": 6,
    },
    "mos": {
        "tree": "obj_mossy_01", "roughness": 215, "subsurface": 105, "seed": 203,
        "bark": (84, 76, 59), "bark_dark": (44, 40, 31), "moss": (76, 99, 53),
        "leaves": [(46, 77, 38), (66, 98, 46), (88, 119, 55), (112, 137, 67)],
        "density": 7,
    },
    "sml": {
        "tree": "obj_bark_small_01", "roughness": 230, "subsurface": 100, "seed": 307,
        "bark": (104, 85, 67), "bark_dark": (55, 43, 34),
        "leaves": [(67, 103, 43), (91, 127, 54), (118, 148, 68), (145, 168, 86)],
        "density": 6,
    },
    "oak": {
        "tree": "obj_oak_01", "roughness": 232, "subsurface": 100, "seed": 409,
        "bark": (101, 78, 52), "bark_dark": (51, 38, 27),
        "leaves": [(52, 84, 34), (73, 107, 42), (96, 129, 51), (126, 151, 68)],
        "density": 7,
    },
    "gnt": {
        "tree": "obj_giant_01", "roughness": 228, "subsurface": 95, "seed": 503,
        "bark": (133, 124, 109), "bark_dark": (70, 65, 58),
        "leaves": [(42, 70, 32), (60, 91, 39), (79, 111, 46), (104, 132, 59)],
        "density": 7,
    },
    "son": {
        "tree": "obj_sonnerat_01", "roughness": 220, "subsurface": 100, "seed": 607,
        "bark": (151, 146, 133), "bark_dark": (82, 79, 70),
        "leaves": [(61, 88, 43), (82, 108, 50), (105, 128, 60), (131, 149, 76)],
        "density": 6,
    },
    "tal": {
        "tree": "obj_bark_tall_01", "roughness": 230, "subsurface": 100, "seed": 709,
        "bark": (83, 62, 45), "bark_dark": (43, 31, 24),
        "leaves": [(48, 79, 35), (67, 99, 41), (88, 119, 50), (112, 139, 62)],
        "density": 6,
    },
}
PAIRS = {meta["tree"]: (f"{code}_branch", f"{code}_leaf_cluster") for code, meta in SPECIES.items()}
GENERIC_BRANCH = b"dlavie:obj_branch"
GENERIC_LEAF = b"dlavie:obj_leaf_cluster"


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _chunk(kind: bytes, payload: bytes) -> bytes:
    body = kind + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def _write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int, int]]) -> None:
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        for rgba in pixels[y * width:(y + 1) * width]:
            raw.extend(bytes(max(0, min(255, int(v))) for v in rgba))
    data = b"\x89PNG\r\n\x1a\n"
    data += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    data += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += _chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _ellipse(canvas: list[list[list[int]]], cx: int, cy: int, rx: int, ry: int, color: tuple[int, int, int, int]) -> None:
    height = len(canvas)
    width = len(canvas[0])
    for y in range(max(0, cy - ry), min(height, cy + ry + 1)):
        for x in range(max(0, cx - rx), min(width, cx + rx + 1)):
            dx = (x - cx) / max(1, rx)
            dy = (y - cy) / max(1, ry)
            if dx * dx + dy * dy <= 1.0:
                canvas[y][x] = list(color)


def _line(canvas: list[list[list[int]]], a: tuple[int, int], b: tuple[int, int], width: int, color: tuple[int, int, int, int]) -> None:
    x0, y0 = a
    x1, y1 = b
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        t = i / steps
        _ellipse(canvas, round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), width, width, color)


def _clamp_rgb(rgb: tuple[int, int, int], delta: int) -> tuple[int, int, int, int]:
    return tuple(max(0, min(255, value + delta)) for value in rgb) + (255,)  # type: ignore[return-value]


def _generate_bark(path: Path, meta: dict[str, object]) -> None:
    rng = random.Random(int(meta["seed"]))
    base = meta["bark"]
    dark = meta["bark_dark"]
    assert isinstance(base, tuple) and isinstance(dark, tuple)
    pixels: list[tuple[int, int, int, int]] = []
    for y in range(128):
        for x in range(128):
            ridge = int(11 * math.sin(x / 6.5 + 0.45 * math.sin(y / 19.0)))
            fine = int(5 * math.sin(x / 2.7 + y / 37.0))
            noise = rng.randint(-12, 12)
            crack = ((x * 23 + y * 7 + int(meta["seed"])) % 97 < 2) or ((x + 3 * y) % 131 == 0)
            if crack:
                color = _clamp_rgb(dark, rng.randint(-7, 5))
            else:
                color = _clamp_rgb(base, ridge + fine + noise)
            if "moss" in meta and y > 45 and ((x * 5 + y * 11) % 53 < 8):
                moss = meta["moss"]
                assert isinstance(moss, tuple)
                blend = 0.46 + rng.random() * 0.22
                color = (
                    int(color[0] * (1 - blend) + moss[0] * blend),
                    int(color[1] * (1 - blend) + moss[1] * blend),
                    int(color[2] * (1 - blend) + moss[2] * blend),
                    255,
                )
            pixels.append(color)
    _write_png(path, 128, 128, pixels)


def _generate_leaf(path: Path, meta: dict[str, object]) -> None:
    rng = random.Random(int(meta["seed"]) + 9000)
    canvas = [[[0, 0, 0, 0] for _ in range(128)] for _ in range(128)]
    bark = meta["bark_dark"]
    leaves = meta["leaves"]
    assert isinstance(bark, tuple) and isinstance(leaves, list)
    branch = tuple(int(v * 0.86) for v in bark) + (255,)
    stems = [
        ((18, 108), (66, 62)), ((61, 66), (105, 29)), ((56, 72), (31, 42)),
        ((69, 58), (101, 74)), ((46, 80), (78, 94)),
    ]
    for a, b in stems:
        _line(canvas, a, b, 2, branch)

    anchors = [
        (20, 97), (30, 84), (42, 74), (55, 65), (68, 57), (80, 48),
        (92, 38), (103, 29), (31, 46), (44, 53), (83, 69), (99, 75),
        (58, 85), (75, 91),
    ]
    density = int(meta["density"])
    for ax, ay in anchors:
        for _ in range(density + rng.randint(-1, 2)):
            rgb = leaves[rng.randrange(len(leaves))]
            assert isinstance(rgb, tuple)
            jitter = rng.randint(-7, 7)
            color = _clamp_rgb(rgb, jitter)
            _ellipse(
                canvas,
                ax + rng.randint(-13, 13),
                ay + rng.randint(-10, 10),
                rng.randint(4, 8),
                rng.randint(2, 5),
                color,
            )
    # A few tiny transparent gaps prevent the leaf cards from reading as solid blobs.
    for _ in range(52):
        _ellipse(canvas, rng.randrange(14, 114), rng.randrange(20, 108), rng.randint(1, 2), rng.randint(1, 2), (0, 0, 0, 0))
    _write_png(path, 128, 128, [tuple(pixel) for row in canvas for pixel in row])


def _generate_species_textures(root: Path) -> None:
    destination = root / "resource_pack" / "textures" / "blocks"
    destination.mkdir(parents=True, exist_ok=True)
    for code, meta in SPECIES.items():
        _generate_bark(destination / f"dlavie_{code}_bark.png", meta)
        _generate_leaf(destination / f"dlavie_{code}_leaf.png", meta)
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
    _generate_species_textures(root)
    _generate_blocks(root)
    _patch_structures(root)


if __name__ == "__main__":
    apply(Path(__file__).resolve().parents[1])

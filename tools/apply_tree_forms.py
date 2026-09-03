#!/usr/bin/env python3
"""v0.3.3 tree-form pass: roots, grounded trunks, directional branches and canopy profiles."""

from __future__ import annotations

import io
import json
import random
import statistics
import struct
from pathlib import Path

PALETTE_VERSION = 18168865

SPECIES = {
    "obj_walnut_01": {"code": "wal", "roots": 6, "root_reach": 1, "canopy": "medium", "leaf_growth": 0.06, "trunk_extra": 2},
    "obj_mossy_01": {"code": "mos", "roots": 8, "root_reach": 2, "canopy": "dense", "leaf_growth": 0.10, "trunk_extra": 3},
    "obj_bark_small_01": {"code": "sml", "roots": 4, "root_reach": 1, "canopy": "sparse", "leaf_growth": 0.02, "trunk_extra": 1},
    "obj_oak_01": {"code": "oak", "roots": 6, "root_reach": 1, "canopy": "medium", "leaf_growth": 0.07, "trunk_extra": 2},
    "obj_giant_01": {"code": "gnt", "roots": 8, "root_reach": 2, "canopy": "dense", "leaf_growth": 0.09, "trunk_extra": 4},
    "obj_sonnerat_01": {"code": "son", "roots": 5, "root_reach": 1, "canopy": "medium", "leaf_growth": 0.05, "trunk_extra": 2},
    "obj_bark_tall_01": {"code": "tal", "roots": 7, "root_reach": 2, "canopy": "sparse", "leaf_growth": 0.04, "trunk_extra": 3},
}

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


class _NBTReader:
    def __init__(self, data: bytes):
        self.stream = io.BytesIO(data)

    def u8(self) -> int:
        raw = self.stream.read(1)
        if not raw:
            raise EOFError("Unexpected end of NBT")
        return raw[0]

    def i8(self) -> int:
        return struct.unpack("<b", self.stream.read(1))[0]

    def i16(self) -> int:
        return struct.unpack("<h", self.stream.read(2))[0]

    def u16(self) -> int:
        return struct.unpack("<H", self.stream.read(2))[0]

    def i32(self) -> int:
        return struct.unpack("<i", self.stream.read(4))[0]

    def i64(self) -> int:
        return struct.unpack("<q", self.stream.read(8))[0]

    def f32(self) -> float:
        return struct.unpack("<f", self.stream.read(4))[0]

    def f64(self) -> float:
        return struct.unpack("<d", self.stream.read(8))[0]

    def string(self) -> str:
        length = self.u16()
        return self.stream.read(length).decode("utf-8")


def _read_payload(reader: _NBTReader, tag: int):
    if tag == TAG_BYTE:
        return reader.i8()
    if tag == TAG_SHORT:
        return reader.i16()
    if tag == TAG_INT:
        return reader.i32()
    if tag == TAG_LONG:
        return reader.i64()
    if tag == TAG_FLOAT:
        return reader.f32()
    if tag == TAG_DOUBLE:
        return reader.f64()
    if tag == TAG_BYTE_ARRAY:
        length = reader.i32()
        return reader.stream.read(length)
    if tag == TAG_STRING:
        return reader.string()
    if tag == TAG_LIST:
        element_tag = reader.u8()
        length = reader.i32()
        return [_read_payload(reader, element_tag) for _ in range(length)]
    if tag == TAG_COMPOUND:
        result = {}
        while True:
            child_tag = reader.u8()
            if child_tag == TAG_END:
                return result
            name = reader.string()
            result[name] = _read_payload(reader, child_tag)
    if tag == TAG_INT_ARRAY:
        return [reader.i32() for _ in range(reader.i32())]
    if tag == TAG_LONG_ARRAY:
        return [reader.i64() for _ in range(reader.i32())]
    raise ValueError(f"Unsupported NBT tag: {tag}")


def _read_structure(path: Path) -> dict:
    reader = _NBTReader(path.read_bytes())
    root_tag = reader.u8()
    if root_tag != TAG_COMPOUND:
        raise ValueError(f"{path}: expected root compound")
    reader.string()
    return _read_payload(reader, TAG_COMPOUND)


def _s16(value: int) -> bytes:
    return struct.pack("<H", value)


def _i32(value: int) -> bytes:
    return struct.pack("<i", int(value))


def _name(value: str) -> bytes:
    raw = value.encode("utf-8")
    return _s16(len(raw)) + raw


def _header(tag: int, name: str) -> bytes:
    return bytes([tag]) + _name(name)


def _string(value: str) -> bytes:
    raw = value.encode("utf-8")
    return _s16(len(raw)) + raw


def _list(tag: int, values: list[bytes]) -> bytes:
    return bytes([tag]) + _i32(len(values)) + b"".join(values)


def _compound(values: list[bytes]) -> bytes:
    return b"".join(values) + bytes([TAG_END])


def _n_int(name: str, value: int) -> bytes:
    return _header(TAG_INT, name) + _i32(value)


def _n_string(name: str, value: str) -> bytes:
    return _header(TAG_STRING, name) + _string(value)


def _n_list(name: str, tag: int, values: list[bytes]) -> bytes:
    return _header(TAG_LIST, name) + _list(tag, values)


def _n_compound(name: str, values: list[bytes]) -> bytes:
    return _header(TAG_COMPOUND, name) + _compound(values)


def _write_structure(path: Path, size: tuple[int, int, int], primary: list[int], palette_names: list[str]) -> None:
    sx, sy, sz = size
    secondary = [-1] * len(primary)
    palette = [
        _compound([
            _n_string("name", block),
            _n_compound("states", []),
            _n_int("version", PALETTE_VERSION),
        ])
        for block in palette_names
    ]
    root_tags = [
        _n_int("format_version", 1),
        _n_list("size", TAG_INT, [_i32(sx), _i32(sy), _i32(sz)]),
        _n_compound("structure", [
            _n_list("block_indices", TAG_LIST, [
                _list(TAG_INT, [_i32(value) for value in primary]),
                _list(TAG_INT, [_i32(value) for value in secondary]),
            ]),
            _n_list("entities", TAG_COMPOUND, []),
            _n_compound("palette", [
                _n_compound("default", [
                    _n_list("block_palette", TAG_COMPOUND, palette),
                    _n_compound("block_position_data", []),
                ])
            ]),
        ]),
        _n_list("structure_world_origin", TAG_INT, [_i32(0), _i32(0), _i32(0)]),
    ]
    path.write_bytes(bytes([TAG_COMPOUND]) + _s16(0) + _compound(root_tags))


def _decode_cells(data: dict) -> tuple[tuple[int, int, int], dict[tuple[int, int, int], int]]:
    size = tuple(int(v) for v in data["size"])
    primary = data["structure"]["block_indices"][0]
    sx, sy, sz = size
    cells: dict[tuple[int, int, int], int] = {}
    index = 0
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                value = int(primary[index])
                index += 1
                if value >= 0:
                    cells[(x, y, z)] = value
    return size, cells


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _geometry_files(root: Path) -> None:
    model_dir = root / "resource_pack" / "models" / "blocks"
    geometries = {
        "obj_trunk.geo.json": ("geometry.dlavie.obj_trunk", [
            {"origin": [-4.5, 0, -4], "size": [8, 16, 8], "uv": [0, 0]},
            {"origin": [1.5, 1, -3], "size": [3, 14, 6], "pivot": [0, 8, 0], "rotation": [0, 7, 0], "uv": [0, 0]},
            {"origin": [-5, 2, -1.5], "size": [3, 11, 4], "pivot": [0, 8, 0], "rotation": [0, -9, 0], "uv": [0, 0]},
        ]),
        "obj_branch_x.geo.json": ("geometry.dlavie.obj_branch_x", [
            {"origin": [-3, 3, -3], "size": [6, 10, 6], "uv": [0, 0]},
            {"origin": [-9, 5.5, -2.5], "size": [18, 5, 5], "pivot": [0, 8, 0], "rotation": [0, 0, 18], "uv": [0, 0]},
            {"origin": [-8, 7, -2], "size": [16, 4, 4], "pivot": [0, 8, 0], "rotation": [0, 0, -9], "uv": [0, 0]},
        ]),
        "obj_branch_z.geo.json": ("geometry.dlavie.obj_branch_z", [
            {"origin": [-3, 3, -3], "size": [6, 10, 6], "uv": [0, 0]},
            {"origin": [-2.5, 5.5, -9], "size": [5, 5, 18], "pivot": [0, 8, 0], "rotation": [-18, 0, 0], "uv": [0, 0]},
            {"origin": [-2, 7, -8], "size": [4, 4, 16], "pivot": [0, 8, 0], "rotation": [9, 0, 0], "uv": [0, 0]},
        ]),
        "obj_branch_d1.geo.json": ("geometry.dlavie.obj_branch_d1", [
            {"origin": [-3, 3, -3], "size": [6, 10, 6], "uv": [0, 0]},
            {"origin": [-9, 5.5, -2.5], "size": [18, 5, 5], "pivot": [0, 8, 0], "rotation": [0, 45, 18], "uv": [0, 0]},
            {"origin": [-8, 7, -2], "size": [16, 4, 4], "pivot": [0, 8, 0], "rotation": [0, 45, -8], "uv": [0, 0]},
        ]),
        "obj_branch_d2.geo.json": ("geometry.dlavie.obj_branch_d2", [
            {"origin": [-3, 3, -3], "size": [6, 10, 6], "uv": [0, 0]},
            {"origin": [-9, 5.5, -2.5], "size": [18, 5, 5], "pivot": [0, 8, 0], "rotation": [0, -45, -18], "uv": [0, 0]},
            {"origin": [-8, 7, -2], "size": [16, 4, 4], "pivot": [0, 8, 0], "rotation": [0, -45, 8], "uv": [0, 0]},
        ]),
        "obj_root.geo.json": ("geometry.dlavie.obj_root", [
            {"origin": [-4, 0, -4], "size": [8, 8, 8], "uv": [0, 0]},
            {"origin": [-10, 0.5, -2.5], "size": [20, 4, 5], "pivot": [0, 3, 0], "rotation": [0, 0, -5], "uv": [0, 0]},
            {"origin": [-2.5, 0.5, -10], "size": [5, 4, 20], "pivot": [0, 3, 0], "rotation": [5, 0, 0], "uv": [0, 0]},
            {"origin": [-9, 1, -2], "size": [18, 3, 4], "pivot": [0, 3, 0], "rotation": [0, 45, 4], "uv": [0, 0]},
        ]),
    }
    for filename, (identifier, cubes) in geometries.items():
        _write_json(model_dir / filename, {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier": identifier,
                    "texture_width": 128,
                    "texture_height": 128,
                    "visible_bounds_width": 3.4,
                    "visible_bounds_height": 2.4,
                    "visible_bounds_offset": [0, 0.6, 0],
                },
                "bones": [{"name": "tree_form", "pivot": [0, 8, 0], "cubes": cubes}],
            }],
        })

    leaf_profiles = {
        "sparse": [[0, 0, 0], [0, 60, 0], [0, 120, 0], [32, 25, 0], [-32, -25, 0], [0, 0, 32]],
        "medium": [[0, 0, 0], [0, 45, 0], [0, 90, 0], [0, 135, 0], [34, 22, 0], [-34, -22, 0], [20, 70, 8], [-20, -70, -8]],
        "dense": [[0, 0, 0], [0, 36, 0], [0, 72, 0], [0, 108, 0], [0, 144, 0], [36, 18, 0], [-36, -18, 0], [24, 62, 8], [-24, -62, -8], [42, 105, 0]],
    }
    for profile, rotations in leaf_profiles.items():
        cubes = [{
            "origin": [-8, 0, -0.4],
            "size": [16, 16, 0.8],
            "pivot": [0, 8, 0],
            "rotation": rotation,
            "uv": [0, 0],
        } for rotation in rotations]
        _write_json(model_dir / f"obj_leaf_{profile}.geo.json", {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier": f"geometry.dlavie.obj_leaf_{profile}",
                    "texture_width": 128,
                    "texture_height": 128,
                    "visible_bounds_width": 3.0,
                    "visible_bounds_height": 3.0,
                    "visible_bounds_offset": [0, 0.75, 0],
                },
                "bones": [{"name": "foliage", "pivot": [0, 8, 0], "cubes": cubes}],
            }],
        })


def _block_files(root: Path) -> None:
    blocks = root / "behavior_pack" / "blocks"
    for meta in SPECIES.values():
        code = meta["code"]
        for suffix, geometry in (
            ("trunk", "geometry.dlavie.obj_trunk"),
            ("branch_x", "geometry.dlavie.obj_branch_x"),
            ("branch_z", "geometry.dlavie.obj_branch_z"),
            ("branch_d1", "geometry.dlavie.obj_branch_d1"),
            ("branch_d2", "geometry.dlavie.obj_branch_d2"),
            ("root", "geometry.dlavie.obj_root"),
        ):
            components = {
                "minecraft:geometry": geometry,
                "minecraft:material_instances": {"*": {"texture": f"dlavie_{code}_bark", "render_method": "opaque", "ambient_occlusion": 1.0}},
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 1.8},
                "minecraft:flammable": {"catch_chance_modifier": 5, "destroy_chance_modifier": 5},
            }
            if suffix == "root":
                components["minecraft:collision_box"] = False
            _write_json(blocks / f"{code}_{suffix}.json", {
                "format_version": "1.26.20",
                "minecraft:block": {
                    "description": {"identifier": f"dlavie:{code}_{suffix}", "menu_category": {"category": "nature"}},
                    "components": components,
                },
            })

        leaf_path = blocks / f"{code}_leaf_cluster.json"
        leaf = json.loads(leaf_path.read_text(encoding="utf-8"))
        leaf["minecraft:block"]["components"]["minecraft:geometry"] = f"geometry.dlavie.obj_leaf_{meta['canopy']}"
        _write_json(leaf_path, leaf)


def _wood_variant(pos: tuple[int, int, int], wood: set[tuple[int, int, int]], height: int) -> str:
    x, y, z = pos
    if y <= max(2, height // 10):
        return "trunk"
    if (x, y - 1, z) in wood or (x, y + 1, z) in wood:
        return "trunk"

    candidates = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                neighbor = (x + dx, y + dy, z + dz)
                if neighbor in wood and (dx or dz):
                    candidates.append((dx, dy, dz))
    if not candidates:
        return "trunk"

    dx, _, dz = max(candidates, key=lambda value: (abs(value[0]) + abs(value[2]), -abs(value[1])))
    if abs(dx) > abs(dz):
        return "branch_x"
    if abs(dz) > abs(dx):
        return "branch_z"
    return "branch_d1" if dx * dz >= 0 else "branch_d2"


def _transform_structure(path: Path, meta: dict) -> dict:
    data = _read_structure(path)
    old_size, cells = _decode_cells(data)

    # The OBJ voxelizer stores woody/trunk cells as palette index 1 and
    # canopy cells as index 0. v0.3.2 retained the labels in the opposite
    # order, so this pass corrects the runtime semantics while rebuilding.
    wood = {pos for pos, value in cells.items() if value == 1}
    leaves = {pos for pos, value in cells.items() if value == 0}
    if not wood or not leaves:
        raise ValueError(f"{path}: expected both OBJ wood and foliage cells")

    margin = 2
    wood = {(x + margin, y, z + margin) for x, y, z in wood}
    leaves = {(x + margin, y, z + margin) for x, y, z in leaves}
    sx, sy, sz = old_size
    sx += margin * 2
    sz += margin * 2

    base_y = min(y for _, y, _ in wood)
    if base_y != 0:
        wood = {(x, y - base_y, z) for x, y, z in wood if y >= base_y}
        leaves = {(x, y - base_y, z) for x, y, z in leaves if y >= base_y}
        sy -= base_y

    lower = [(x, z) for x, y, z in wood if y <= min(2, sy - 1)]
    cx = round(statistics.median([x for x, _ in lower]))
    cz = round(statistics.median([z for _, z in lower]))

    thick_pattern = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for y in range(min(3, sy)):
        for dx, dz in thick_pattern[: 1 + int(meta["trunk_extra"])]:
            position = (cx + dx, y, cz + dz)
            if 0 <= position[0] < sx and 0 <= position[2] < sz:
                wood.add(position)
                leaves.discard(position)

    roots: set[tuple[int, int, int]] = set()
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    for dx, dz in directions[: int(meta["roots"])]:
        placed = 0
        for distance in range(1, int(meta["root_reach"]) + 3):
            position = (cx + dx * distance, 0, cz + dz * distance)
            if not (0 <= position[0] < sx and 0 <= position[2] < sz):
                break
            if position in wood:
                continue
            roots.add(position)
            leaves.discard(position)
            placed += 1
            if placed >= int(meta["root_reach"]):
                break

    rng = random.Random(33045 + sum(ord(char) for char in meta["code"]))
    neighbors = [
        (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1),
        (1, 0, 1), (-1, 0, -1), (1, 0, -1), (-1, 0, 1),
        (0, 1, 0), (0, -1, 0),
    ]
    candidates: list[tuple[int, int, int]] = []
    for x, y, z in tuple(leaves):
        for dx, dy, dz in neighbors:
            position = (x + dx, y + dy, z + dz)
            if not (0 <= position[0] < sx and 1 <= position[1] < sy and 0 <= position[2] < sz):
                continue
            if position in wood or position in leaves or position in roots:
                continue
            if rng.random() < float(meta["leaf_growth"]):
                candidates.append(position)

    rng.shuffle(candidates)
    growth_cap = max(12, int(len(leaves) * float(meta["leaf_growth"])))
    for position in candidates[:growth_cap]:
        leaves.add(position)

    palette_names = [
        f"dlavie:{meta['code']}_trunk",
        f"dlavie:{meta['code']}_branch_x",
        f"dlavie:{meta['code']}_branch_z",
        f"dlavie:{meta['code']}_branch_d1",
        f"dlavie:{meta['code']}_branch_d2",
        f"dlavie:{meta['code']}_root",
        f"dlavie:{meta['code']}_leaf_cluster",
    ]
    palette_index = {"trunk": 0, "branch_x": 1, "branch_z": 2, "branch_d1": 3, "branch_d2": 4, "root": 5, "leaf": 6}

    cells_out: dict[tuple[int, int, int], int] = {}
    for position in wood:
        cells_out[position] = palette_index[_wood_variant(position, wood, sy)]
    for position in roots:
        cells_out.setdefault(position, palette_index["root"])
    for position in leaves:
        cells_out.setdefault(position, palette_index["leaf"])

    primary: list[int] = []
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                primary.append(cells_out.get((x, y, z), -1))

    _write_structure(path, (sx, sy, sz), primary, palette_names)
    return {
        "structure": path.stem,
        "size": [sx, sy, sz],
        "wood_cells": len(wood),
        "root_cells": len(roots),
        "leaf_cells": len(leaves),
        "canopy_profile": meta["canopy"],
    }


def _feature_clearance(root: Path) -> None:
    feature_dir = root / "behavior_pack" / "features"
    for name in SPECIES:
        feature = feature_dir / f"{name}_structure_feature.json"
        data = json.loads(feature.read_text(encoding="utf-8"))
        data["minecraft:structure_template_feature"]["adjustment_radius"] = 2
        _write_json(feature, data)


def apply(root: Path) -> None:
    _geometry_files(root)
    _block_files(root)
    _feature_clearance(root)
    report = []
    structure_dir = root / "behavior_pack" / "structures" / "dlavie"
    for name, meta in SPECIES.items():
        report.append(_transform_structure(structure_dir / f"{name}.mcstructure", meta))
    _write_json(root / "docs" / "V033_TREE_FORMS.json", {"version": "0.3.3", "trees": report})


if __name__ == "__main__":
    apply(Path(__file__).resolve().parents[1])

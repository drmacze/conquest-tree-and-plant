#!/usr/bin/env python3
"""Generate binary runtime assets for the first OBJ-derived tree."""

from __future__ import annotations

import math
import random
import struct
import zlib
from pathlib import Path

WOOD = [(1, 0, 2), (1, 10, 3), (1, 11, 3), (1, 12, 2), (1, 12, 3), (2, 0, 1), (2, 0, 2), (2, 0, 3), (2, 7, 4), (2, 9, 3), (2, 10, 2), (2, 10, 4), (2, 11, 2), (2, 11, 4), (2, 12, 1), (2, 12, 4), (2, 13, 2), (2, 13, 3), (3, 0, 2), (3, 5, 2), (3, 6, 3), (3, 8, 4), (3, 10, 3), (3, 11, 3), (3, 12, 2), (3, 12, 4), (3, 13, 3), (3, 14, 3), (3, 15, 3), (4, 12, 3)]
LEAVES = [(0, 7, 2), (0, 8, 3), (1, 7, 2), (1, 7, 3), (1, 8, 4), (1, 9, 5), (1, 13, 3), (1, 14, 2), (1, 14, 3), (2, 4, 2), (2, 4, 4), (2, 5, 2), (2, 6, 3), (2, 7, 3), (2, 7, 5), (2, 8, 0), (2, 8, 1), (2, 8, 2), (2, 8, 4), (2, 9, 1), (2, 9, 4), (2, 10, 3), (2, 12, 2), (2, 12, 5), (2, 13, 4), (2, 15, 3), (2, 15, 4), (2, 16, 2), (2, 17, 2), (3, 4, 4), (3, 8, 0), (3, 8, 1), (3, 8, 2), (3, 9, 2), (3, 11, 2), (3, 11, 4), (3, 12, 3), (3, 14, 2), (3, 17, 3), (4, 4, 3), (4, 5, 3), (4, 5, 4), (4, 7, 1), (4, 7, 4), (4, 7, 5), (4, 8, 2), (4, 8, 5), (4, 9, 1), (4, 9, 2), (4, 9, 3), (4, 9, 4), (4, 10, 1), (4, 11, 3), (4, 11, 4), (4, 12, 1), (4, 12, 4), (4, 13, 2), (4, 14, 4), (4, 16, 3), (5, 8, 3)]
SIZE = (6, 18, 6)
PALETTE_VERSION = 18168865


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


def _disc(canvas: list[list[list[int]]], cx: int, cy: int, rx: int, ry: int, color: tuple[int, int, int, int]) -> None:
    for y in range(max(0, cy - ry), min(len(canvas), cy + ry + 1)):
        for x in range(max(0, cx - rx), min(len(canvas[0]), cx + rx + 1)):
            dx = (x - cx) / max(1, rx)
            dy = (y - cy) / max(1, ry)
            if dx * dx + dy * dy <= 1:
                canvas[y][x] = list(color)


def _line(canvas: list[list[list[int]]], a: tuple[int, int], b: tuple[int, int], color: tuple[int, int, int, int]) -> None:
    x0, y0 = a
    x1, y1 = b
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        t = i / steps
        _disc(canvas, round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), 2, 2, color)


def generate_textures(root: Path) -> None:
    rng = random.Random(26045)
    bark: list[tuple[int, int, int, int]] = []
    for y in range(128):
        for x in range(128):
            vertical = 10 * math.sin(x / 7.0 + math.sin(y / 23.0))
            grain = rng.randint(-18, 18)
            crevice = -42 if ((x * 17 + y * 5 + 11) % 79 == 0 or (x + y * 3) % 113 == 0) else 0
            bark.append((int(174 + vertical + grain + crevice), int(131 + vertical * 0.45 + grain * 0.7 + crevice), int(112 + grain * 0.55 + crevice), 255))
    _write_png(root / "resource_pack/textures/blocks/dlavie_obj_bark.png", 128, 128, bark)

    canvas = [[[0, 0, 0, 0] for _ in range(128)] for _ in range(128)]
    branch = (92, 67, 41, 255)
    for a, b in [((18, 103), (66, 62)), ((62, 66), (103, 31)), ((52, 73), (30, 46)), ((71, 57), (94, 72))]:
        _line(canvas, a, b, branch)
    leaf_rng = random.Random(903)
    anchors = [(24, 91), (35, 78), (47, 72), (59, 62), (75, 51), (90, 39), (101, 29), (31, 49), (43, 57), (82, 66), (97, 73), (68, 78)]
    palette = [(153, 192, 100, 255), (132, 176, 78, 255), (181, 218, 125, 255), (101, 148, 54, 255), (196, 235, 145, 255)]
    for ax, ay in anchors:
        for _ in range(leaf_rng.randint(4, 7)):
            _disc(canvas, ax + leaf_rng.randint(-12, 12), ay + leaf_rng.randint(-10, 10), leaf_rng.randint(4, 8), leaf_rng.randint(2, 5), palette[leaf_rng.randrange(len(palette))])
    _write_png(root / "resource_pack/textures/blocks/dlavie_obj_leaf.png", 128, 128, [tuple(px) for row in canvas for px in row])


TAG_END = 0
TAG_INT = 3
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10


def _s16(n: int) -> bytes: return struct.pack("<H", n)
def _i32(n: int) -> bytes: return struct.pack("<i", int(n))
def _name(value: str) -> bytes:
    raw = value.encode()
    return _s16(len(raw)) + raw

def _header(tag: int, name: str) -> bytes: return bytes([tag]) + _name(name)
def _string(value: str) -> bytes:
    raw = value.encode()
    return _s16(len(raw)) + raw

def _list(tag: int, values: list[bytes]) -> bytes: return bytes([tag]) + _i32(len(values)) + b"".join(values)
def _compound(values: list[bytes]) -> bytes: return b"".join(values) + bytes([TAG_END])
def _n_int(name: str, value: int) -> bytes: return _header(TAG_INT, name) + _i32(value)
def _n_string(name: str, value: str) -> bytes: return _header(TAG_STRING, name) + _string(value)
def _n_list(name: str, tag: int, values: list[bytes]) -> bytes: return _header(TAG_LIST, name) + _list(tag, values)
def _n_compound(name: str, values: list[bytes]) -> bytes: return _header(TAG_COMPOUND, name) + _compound(values)


def generate_structure(root: Path) -> None:
    sx, sy, sz = SIZE
    wood = set(WOOD)
    leaves = set(LEAVES)
    primary = []
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                pos = (x, y, z)
                primary.append(0 if pos in wood else 1 if pos in leaves else -1)
    secondary = [-1] * len(primary)
    palette = []
    for block in ("dlavie:obj_branch", "dlavie:obj_leaf_cluster"):
        palette.append(_compound([_n_string("name", block), _n_compound("states", []), _n_int("version", PALETTE_VERSION)]))
    root_tags = [
        _n_int("format_version", 1),
        _n_list("size", TAG_INT, [_i32(sx), _i32(sy), _i32(sz)]),
        _n_compound("structure", [
            _n_list("block_indices", TAG_LIST, [_list(TAG_INT, [_i32(v) for v in primary]), _list(TAG_INT, [_i32(v) for v in secondary])]),
            _n_list("entities", TAG_COMPOUND, []),
            _n_compound("palette", [_n_compound("default", [_n_list("block_palette", TAG_COMPOUND, palette), _n_compound("block_position_data", [])])]),
        ]),
        _n_list("structure_world_origin", TAG_INT, [_i32(0), _i32(0), _i32(0)]),
    ]
    data = bytes([TAG_COMPOUND]) + _s16(0) + _compound(root_tags)
    path = root / "behavior_pack/structures/dlavie/obj_oak_01.mcstructure"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def generate(root: Path) -> None:
    generate_textures(root)
    generate_structure(root)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])

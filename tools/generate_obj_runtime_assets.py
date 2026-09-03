#!/usr/bin/env python3
"""Generate compact Bedrock runtime assets reconstructed from the supplied OBJ pack."""

from __future__ import annotations

import base64
import json
import math
import random
import struct
import zlib
from pathlib import Path

PALETTE_VERSION = 18168865
TREE_DATA = {
    "obj_walnut_01": "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",
    "obj_mossy_01": "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",
    "obj_bark_small_01": "eNpFl8GO1jAMhN9lzzk0je1xeJXVHpDYAxLSHlYCCcS70yafy2lKOpMWf27875+Xz++/31++vPaj9dH68dZefn18fLtWXo9mzd/apb60t46eLZaOdqIDdbTua6k1Qx3d95312j/YJ1gXmkvP6/mlvvR8NJZe/wH0RAdqqKPl11LDZ/gMn+EzfI7P8Tk+b7k0eG7gC3yBL9gv2C/ICb/wC7/wC3/iq3okvsSX+CbrF9T7YrTSXcCrPKtQt55orTsaSwe+gW8XdFDQQUEHBR0U9NZcauSNvJE38kbeyBt5e/JzqbcD7ehADXU0UKGJ7n2CXJALckEuyAW5ICfeX+RFXuRFXuQTX+JLfIkvH99+zsQ/8U/8E/8FctSF1YXXBZ6C23vd6nVrc7W2t7k1lu6I8UHdWutCc+nuF6Nfbh1ooELLP5cOcoPcIDfIDXKD3CBn5IyckTNyRs7I7f4w+uPWEx1ooEIrt58X+AN/UJcgF+SCnPALv/AJX7KerOezvvOT+5P7s+pdgPpDqNfKw+qBVBT6Wbc2D4fvVY31nrcO1NB9/2T9fP6tpZubw83h5nBzuDncHG4OL4eXw8vh5fByODmcHE4OJ4eTw+laXXxv7eiJDjRQoTsnfMInfMInfIkv8SW+xJf4Jr6Jb+Kb3IefF791sbfoD4Mqfu916ywsm0PwnQa8gu8z4BZwC87t4NyOVvnNL+AX8AvO7YBjwDHgGPAL+AXndHBOBzwDngHPgGfAM+AZnM8B14BrwDHgGHAMvrvgXA64BlwDrsG5fK2yj9hH7CP2EfuIfcQ+iT/xJ/7En/jz8e/nTnKT3CQ3yU1y/QF4FMGjEB7l6eV5KD+Y+3/PfoFepHuhplfEty16RZzd4qwWvSJ6Ra1yu0dEj4geET0iZrvoFdErokdEj4geET0iekT0iOgF0QtiVoueED0hvnXRC6IHRA+IHhA9IJgL5oK5YC6YC+aCuWAumAvmgrVgK9gKtoKtiq2KrYqtim1y7ia1Ts7VpNZJrZNaJ7VOap3UOql1UuukxkmNkxonNU5qnNQ4qXFS46TGyXeW1DipcVK7pHZJDSb/j8n7Tt538r6T95h8/5P3mTx3wnTy3Mlz53re9RfHj/evP98/77857p8mxk8U56eEoc5PBEOdnwCGOiPdUGdkO6PZUGcUG+qMYEO9JrDVhdfg9Rqzzpg11Bmrzhg11BmPhjpj0FBnzBnqjC9DnTFlqDOODHXGj6FeQ8fqwmvWWF14zRpn1jgzwDmjLyZ//wFPEURP",
    "obj_oak_01": "eNpFlUuOJDcMRO/S61yURFJZ5asMajGAe2FggFkMMAZs+O5Wpt5TryJEUh9SVOjfj19//fP58ce382jP4/k+Pv7++fPPOf72OMbR38fEc2OAeeOT8XOP68bWb0ebCzSwg8t+Yl8LtTmxgR2sG1/YX9hfzH8d48b2wDBJStbU1pgzCa6upRsTWsKY0JWunLpKS92Wucg9u5NlJ8sL68bzeIANTFD/uPFJ3BP7E/sL+8q6k3W/cmySLgkJMc2YZkxj+0nWPrMOTcKs0JLOSmels0x716GZ+CRYTi2nB1vJz4LfnjgCXMW6cNy4ihYULShSUKQLzxtfjMk4zO8mWLokWGwSLMn2pBVXNpB19hlwrzfzZ7xOmpw0OWnSvEnzJidMTpg0cdLEFxa41pkZPCQpWSHcYtqyaSppp6YHz6+DU+uixvOa7ksoGrZo1KLGxbsuGrOoeZFZkVnRoEWDFpkVmRWZFZmVjVo2atmoZa5lruXzLHMtn2eZa3lt5fMs+7O8yPKdlv1ZV1teloGODfId5DXQr0Eegwc3yGdc1xCSFYnC3QTLbOn3VM8fn99/f/669LOxX2O/hl429rtkTNyaFSrUJluY1kMKXpbj3KgoBSIkKjodDESmgR3UnohNAzuovVSalJS6EspJl2xLSkql6ZKQpKSUnFBpQoGJ+5E+eL6PPebtM+5gbFyP22ef2JN5uf1LH4q4Iq6Ic//B+CTuxH5ue6FWDexggAkaN1C1BnYwwARL1WuSLglJSkpBbJIuCUmplU3SJSFJSSmjXRKSlJTCGpJUYbskJLiGLgvcrHCztKhacufJS0ju+EL1OkDHSx+L+MJf+E8UVfk88Z/bX+BA3wNMsMCBrge41bxJuiTU9y7ZlpSU0r//gC4JSfoZdElIcPl9NevS8su1v5AuCQkxQ9fQNXT5bcTG5JtJvhG/jQCT7yFA9Lmp2O3Lsj+FkKR/QUgS9Vat8/3+739RcXor",
    "obj_giant_01": "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",
    "obj_sonnerat_01": "eNo9lsuu1TAMRf/ljjto4+1H+BXEAIk7QEK6AySQQPw7Pc1yRisPp/U+cb3P37ef3/+8v336fNlxXcd1fjnefn98fLtXPp+HHfpyPPSHgs66M49nft1xBgPmQx0XHNCgoMOAfa4eOuecc84555xzzjnnnAvig7ggLogL4pK45LlJfBJfrBfrxfpkfbI+n/Vx6x7QYD5cv8NA/0D3QPdA77jzv+CaB88LzgXxwX6yn+wn+8V85T/Ie9x5GhTs9ZXndbJxD14rhiJDkaHoxXq4lBkK7no5Ttjz+TCIC54XPG9VkHEzhjJDmaHoxbVfrBfn180YCl9ccZP9yfMncZO4uePW+27B3oNXhKhlofiu2EeZqGVRq0K5UC4UC8VCobg7oVQoFUpFDQqlQqlQKpQJZUKZUKC+O/XdPYPXlpO6U25O6k7qTupO+TkSHAmOBEeCI8GR8OKKX1IcKY4UR4pTjo6U+y2sL0nO5TiX4y3J+3a8byeQFEgKJAVSAilBBwk6SFCXgcRAYlCXQV0GkgOpgdR7Bov44v1F3GR98pzJcyb7SIqWFC0p+ZSSAkuaRCIlkZJISSQkqSepJ7eUpJ6kntxScktJ00huK5GWFFwiKZGSSEluKVtKtoIiwyLDoj0XP3qRaZFZkVmRQdF+i7opMioyKn7sIqMio+LjLjKrzqz6R55kNslsYiAT45hkOCmHSaaT9jPJaFLBk7Yz2wDOdrizre1s7zrbvNo9r7bPZ5A9qDWIPoVlne1Z20S3K25b3L64jXE747bCq716m+J2xbalZ6A14BXjefL91+DH+9df7z9ffw4u/hxc/DnoBw/WB+uDBjrIux8++FT7HQMVAxEDDQMJgx9p7PcE+8F6sp6sF+yWb1iA7XlgWQMaFHTYcYmVXXBAg4IOA7alOWwrMyjYFqZ2oNW/u6GvIhZChBDRMIQAIUAIEAJE4iJxkbhIXCQuEheJi6IUNSlKSQgSQoQA8bEIIeIixGcrLkR8pqInqr9SdSO5eziG0P1/t//2A+aDuW06xnbBAQ0KOkY3oEHB3g+YsA1vQIOO4RnseWB4Bh220QkuLzhxjTaJ7RFtGswHc4PCxYT7aK87btcM2K7mMHC3AQ0KOuy4xPUMCjpu11xW0U4h6JttcQETtmUJOhbVDJhYlaDDwKq8HWo5hDAG33TYjmRQ0GHgSIETCS4fEL4i/ME3Az8xKOiw97PtY5vF7v/WA/XA2xGsB3eX/vcfhB80+A==",
    "obj_bark_tall_01": "eNpNl82uJCcMRt/lrnvR/sMmrzK6i5FyF5EizWKkREqUd08V+FCz6oMxYGygvv734+cf/3x9/PZN5KX5Ev18ffz948fvl+Xb+yX1Gp+vG+bLFujFgAKnyzfI6pKX5Bq+IIHaUGuUsMSCBNpnMs/Eeb4CGEACe9QVxhsQIIDtfEX4BgQw4N6F3qEeSKCAuWHvYkEA3TWx7FCVCBdsn45QiXDBABLYozpUJb1KzPrEfEEP12Wxl+zqLGhLruHGBhcEMIAC5oZaqy9QoLtmW3o7xtkwtmMEb8RsxGzEvCCBvfq1CwEUMMCBAAbQ8xijjFHGKMPZcHZ8nAkdn6Ar1nB/7fN4/+62SBtEHktsUCz2wNjg+DiWsTa8QIGeOelK5kmGF13FqH2FnJvjHEfn8DlFcu6tU60F7SM9c585p35O2ZyyLehRum6XUz+nJAvax/AxfEjLBTv4qwAKdFeweqztBOc7yOoFu0hBMoNkBskMkhkkM7jkQTKDZAbJjDt1AihggAMDmGfUe5ES631R2iQ9ZaczSGdwC4K8bucepgxTnBSnndjgZMedvTcggAIB9PJBVxAs+Tw5V/J5wd01yPAgwwvGhp3qwbuzwIDjk0BtKEYVPhPLZJ75S9d7Ub9Ag8O9LW3ab/44aRykcfC+DPI5yOcgn4ODOjiogwwvaGfHx5lwZ3iQ4QU9KnAOnKPzqaSxM5z3qQ5gbDhd47Hkhp3zJOdJzpMDn+Q8yXmS8wUOzA2TrsmEkwknzpMwJjN3XZK6JHVJ7kLy+iSPTp7bkZQsuRTJXUg+BMmHIHn/k8cmef8XBNBdTpdjCSzBhKRcSXmXJZ+yXHD7FNVYcCwDyA27GkURiie8uApFWYpqFO9QITYKsVFIpuKJKspSlKV4+IuyFDqkeKKKGhRfgEJ+FPKjKE/xZBXfhAUBDKCHa8fTn+miTEWZijIVn+niM10UrrhzRQWLChYf7uKqFVeteMOKmhY1LUpZlHJywyYVnFRnUp1JLSa1mNRi8lBNijLJ/ORmTGTe5OGZPDyTvc87eAfaObDsUOW9Z7yU+p9f3//6+nlrdaHiwh0T7phQX3mkY29N2Zpy6ZWNKBtRTpdy+5VjpiyqnC5ldWV1ZXUjacZaRvaMRY1FjUWNtYy1jMQaiTVWN862cbaNMOwJo6tgHHLjkBsn2Th4RjmuV6KVB+qrul2osTdK6/1YjgQMlF8g3RQwFNsBB468G0Ci4RwYwOkqNJwBASRQKDYHAn2mgAEOHJ8j1BQwwIEAEg1ngAOBmNsK431+W9whqhAeKJFuW7et295tVA3zIlxGt0e3syUOIjDbXm2vtlfbEXnzEZ8OtOWETMxC0ELUQthC3ELgQuRy9O141GygVBU4ajZQqgY4cLoGkOjSAI6l0KcKOBDAABI4o45OVcAABwK9qoABDhyfASSaVgAFDHAggIG4NWDrq/f53eJM0LGINXRYt63b1m3mQdyh26Lb6OLRbRRvtj3bXm2vtlfbZ7cn8RGwnIhPyMQsBC1ELYQtxC0ELkQuhC7ELr+I+kCVOxCocgUMcOD4JFDodAMcCCCB4zxR8AY4EMAAEijgDJdH9wMKGOBAAANIoIDJfwQDHAhgAOc/ggIGOHD+Ixjg/CPYijPP7xae1e16/gQEcv7AQMUrYEAAxyeBQrwHcCxHoAcwgAQKoS6AAgY4EMAACg0vgAJHwxvgwEDMG+BAAAMxf1T0QAYf0Xs0qgBHZPrn53//A1vg1N4="
}


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
            vertical = 12 * math.sin(x / 6.5 + math.sin(y / 19.0))
            grain = rng.randint(-20, 20)
            crevice = -48 if ((x * 17 + y * 5 + 11) % 79 == 0 or (x + y * 3) % 113 == 0) else 0
            bark.append((int(160 + vertical + grain + crevice), int(118 + vertical * 0.45 + grain * 0.7 + crevice), int(94 + grain * 0.55 + crevice), 255))
    _write_png(root / "resource_pack/textures/blocks/dlavie_obj_bark.png", 128, 128, bark)

    canvas = [[[0, 0, 0, 0] for _ in range(128)] for _ in range(128)]
    branch = (86, 60, 36, 255)
    for a, b in [((15, 105), (62, 65)), ((58, 68), (108, 27)), ((52, 73), (27, 42)), ((69, 57), (101, 77)), ((58, 69), (76, 101))]:
        _line(canvas, a, b, branch)
    leaf_rng = random.Random(903)
    anchors = [(20, 94), (33, 79), (46, 72), (58, 62), (75, 51), (91, 39), (104, 28), (28, 47), (43, 56), (83, 68), (99, 76), (68, 82)]
    palette = [(116, 151, 62, 255), (92, 132, 46, 255), (145, 178, 83, 255), (73, 112, 36, 255), (168, 198, 103, 255)]
    for ax, ay in anchors:
        for _ in range(leaf_rng.randint(5, 8)):
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


def _decode_tree(encoded: str) -> dict[str, object]:
    return json.loads(zlib.decompress(base64.b64decode(encoded)).decode("utf-8"))


def generate_structure(root: Path, name: str, encoded: str) -> None:
    tree = _decode_tree(encoded)
    sx, sy, sz = (int(v) for v in tree["size"])
    wood = {tuple(p) for p in tree["wood"]}
    leaves = {tuple(p) for p in tree["leaves"]}
    primary: list[int] = []
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
    path = root / f"behavior_pack/structures/dlavie/{name}.mcstructure"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def generate(root: Path) -> None:
    generate_textures(root)
    for name, encoded in TREE_DATA.items():
        generate_structure(root, name, encoded)


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1])

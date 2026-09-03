#!/usr/bin/env python3
"""Split a combined OBJ tree pack into individual source meshes and metadata.

This tool intentionally keeps third-party/user-provided source assets out of git.
It accepts a local .zip containing OBJ/MTL/textures, extracts it to a working
folder, parses the OBJ, and writes one standalone OBJ per `o` object with
re-mapped v/vt/vn indices plus a JSON report.

Usage:
    python tools/import_obj_tree_pack.py /path/to/trees.zip build/source_trees
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FaceRecord:
    tokens: list[str]
    material: str | None


@dataclass
class ObjectRecord:
    name: str
    faces: list[FaceRecord] = field(default_factory=list)
    min_xyz: list[float] = field(default_factory=lambda: [float("inf")] * 3)
    max_xyz: list[float] = field(default_factory=lambda: [float("-inf")] * 3)
    materials: Counter[str] = field(default_factory=Counter)

    def include_vertex(self, xyz: tuple[float, float, float]) -> None:
        for i, value in enumerate(xyz):
            self.min_xyz[i] = min(self.min_xyz[i], value)
            self.max_xyz[i] = max(self.max_xyz[i], value)

    @property
    def size(self) -> list[float]:
        if self.min_xyz[0] == float("inf"):
            return [0.0, 0.0, 0.0]
        return [self.max_xyz[i] - self.min_xyz[i] for i in range(3)]


def safe_extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        root = destination.resolve()
        for member in zf.infolist():
            target = (destination / member.filename).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        zf.extractall(destination)


def parse_index(token: str) -> tuple[int, int | None, int | None]:
    parts = token.split("/")
    v = int(parts[0])
    vt = int(parts[1]) if len(parts) > 1 and parts[1] else None
    vn = int(parts[2]) if len(parts) > 2 and parts[2] else None
    return v, vt, vn


def resolve_index(index: int, count: int) -> int:
    return index if index > 0 else count + index + 1


def find_asset_files(root: Path) -> tuple[Path, Path | None]:
    objs = sorted(root.rglob("*.obj"))
    if not objs:
        raise FileNotFoundError("No .obj file found in archive")
    if len(objs) > 1:
        raise ValueError(f"Expected one combined OBJ, found {len(objs)}")
    obj_path = objs[0]
    mtls = sorted(root.rglob("*.mtl"))
    mtl_path = mtls[0] if mtls else None
    return obj_path, mtl_path


def split_obj(obj_path: Path, output: Path, mtl_path: Path | None) -> dict[str, object]:
    vertices: list[str] = []
    texcoords: list[str] = []
    normals: list[str] = []
    vertex_xyz: list[tuple[float, float, float]] = []
    objects: list[ObjectRecord] = []
    current: ObjectRecord | None = None
    current_material: str | None = None
    mtllib: str | None = mtl_path.name if mtl_path else None

    with obj_path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("mtllib "):
                mtllib = line[7:].strip()
            elif line.startswith("v "):
                vertices.append(line)
                parts = line.split()
                vertex_xyz.append(tuple(map(float, parts[1:4])))
            elif line.startswith("vt "):
                texcoords.append(line)
            elif line.startswith("vn "):
                normals.append(line)
            elif line.startswith("o "):
                current = ObjectRecord(line[2:].strip() or f"object_{len(objects)+1}")
                objects.append(current)
            elif line.startswith("usemtl "):
                current_material = line[7:].strip()
            elif line.startswith("f "):
                if current is None:
                    current = ObjectRecord("default")
                    objects.append(current)
                tokens = line[2:].split()
                current.faces.append(FaceRecord(tokens=tokens, material=current_material))
                if current_material:
                    current.materials[current_material] += 1
                for token in tokens:
                    v, _, _ = parse_index(token)
                    rv = resolve_index(v, len(vertices))
                    current.include_vertex(vertex_xyz[rv - 1])

    meshes_dir = output / "meshes"
    meshes_dir.mkdir(parents=True, exist_ok=True)
    if mtl_path:
        shutil.copy2(mtl_path, output / mtl_path.name)

    report_objects: list[dict[str, object]] = []

    for index, record in enumerate(objects, start=1):
        used_v: set[int] = set()
        used_vt: set[int] = set()
        used_vn: set[int] = set()
        parsed_faces: list[tuple[list[tuple[int, int | None, int | None]], str | None]] = []

        for face in record.faces:
            parsed: list[tuple[int, int | None, int | None]] = []
            for token in face.tokens:
                v, vt, vn = parse_index(token)
                v = resolve_index(v, len(vertices))
                vt = resolve_index(vt, len(texcoords)) if vt is not None else None
                vn = resolve_index(vn, len(normals)) if vn is not None else None
                used_v.add(v)
                if vt is not None:
                    used_vt.add(vt)
                if vn is not None:
                    used_vn.add(vn)
                parsed.append((v, vt, vn))
            parsed_faces.append((parsed, face.material))

        v_map = {old: new for new, old in enumerate(sorted(used_v), start=1)}
        vt_map = {old: new for new, old in enumerate(sorted(used_vt), start=1)}
        vn_map = {old: new for new, old in enumerate(sorted(used_vn), start=1)}

        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in record.name)
        mesh_path = meshes_dir / f"{index:02d}_{safe_name}.obj"
        with mesh_path.open("w", encoding="utf-8") as out:
            out.write(f"# Split from {obj_path.name}\n")
            if mtllib:
                out.write(f"mtllib ../{Path(mtllib).name}\n")
            out.write(f"o {record.name}\n")
            for old in sorted(used_v):
                out.write(vertices[old - 1] + "\n")
            for old in sorted(used_vt):
                out.write(texcoords[old - 1] + "\n")
            for old in sorted(used_vn):
                out.write(normals[old - 1] + "\n")

            last_material: str | None = None
            for face, material in parsed_faces:
                if material != last_material and material:
                    out.write(f"usemtl {material}\n")
                    last_material = material
                tokens: list[str] = []
                for v, vt, vn in face:
                    nv = v_map[v]
                    nvt = vt_map[vt] if vt is not None else None
                    nvn = vn_map[vn] if vn is not None else None
                    if nvt is not None and nvn is not None:
                        tokens.append(f"{nv}/{nvt}/{nvn}")
                    elif nvt is not None:
                        tokens.append(f"{nv}/{nvt}")
                    elif nvn is not None:
                        tokens.append(f"{nv}//{nvn}")
                    else:
                        tokens.append(str(nv))
                out.write("f " + " ".join(tokens) + "\n")

        report_objects.append(
            {
                "name": record.name,
                "mesh": str(mesh_path.relative_to(output)),
                "vertices": len(used_v),
                "uvs": len(used_vt),
                "normals": len(used_vn),
                "faces": len(record.faces),
                "materials": dict(record.materials),
                "bbox_min": record.min_xyz,
                "bbox_max": record.max_xyz,
                "size": record.size,
            }
        )

    return {
        "source_obj": obj_path.name,
        "source_mtl": mtl_path.name if mtl_path else None,
        "vertex_count": len(vertices),
        "uv_count": len(texcoords),
        "normal_count": len(normals),
        "face_count": sum(len(item.faces) for item in objects),
        "object_count": len(objects),
        "objects": report_objects,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.output.exists():
        shutil.rmtree(args.output)
    extracted = args.output / "extracted"
    safe_extract(args.archive, extracted)
    obj_path, mtl_path = find_asset_files(extracted)

    # Keep textures in the local build workspace; source assets are not committed.
    texture_dir = next((p for p in extracted.iterdir() if p.is_dir()), None)
    if texture_dir:
        shutil.copytree(texture_dir, args.output / "textures", dirs_exist_ok=True)

    report = split_obj(obj_path, args.output, mtl_path)
    (args.output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Imported {report['object_count']} OBJ objects")
    print(f"Source faces: {report['face_count']:,}")
    print(f"Report: {args.output / 'report.json'}")


if __name__ == "__main__":
    main()

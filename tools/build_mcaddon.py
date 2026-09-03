#!/usr/bin/env python3
"""Validate the add-on JSON files and package Bedrock importable artifacts."""

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
VERSION = "0.1.0"
TARGET_ENGINE = [1, 26, 45]
BLOCK_SCHEMA_FLOOR = (1, 26, 0)


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
        except Exception as exc:  # noqa: BLE001 - CLI validation should report any parse failure
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    for manifest in (BP / "manifest.json", RP / "manifest.json"):
        data = parsed.get(manifest)
        if not isinstance(data, dict):
            continue
        header = data.get("header")
        min_engine = header.get("min_engine_version") if isinstance(header, dict) else None
        if min_engine != TARGET_ENGINE:
            errors.append(
                f"{manifest.relative_to(ROOT)}: min_engine_version must be {TARGET_ENGINE} "
                "to guarantee Minecraft Bedrock 1.26.45+ targeting"
            )

    for path in sorted((BP / "blocks").glob("*.json")):
        data = parsed.get(path)
        if not isinstance(data, dict):
            continue
        format_version = parse_version(data.get("format_version"))
        if format_version is None or format_version < BLOCK_SCHEMA_FLOOR:
            errors.append(
                f"{path.relative_to(ROOT)}: block format_version must be >= "
                f"{'.'.join(map(str, BLOCK_SCHEMA_FLOOR))} for the 1.26 geometry semantics"
            )

    if errors:
        print("Validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Validated {len(json_files)} JSON files for Minecraft Bedrock 1.26.45+.")


def zip_directory(source: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))


def build() -> None:
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
        for prefix, source in (
            ("DLavie_Conquest_Nature_BP", BP),
            ("DLavie_Conquest_Nature_RP", RP),
        ):
            for path in sorted(source.rglob("*")):
                if path.is_file():
                    archive.write(path, Path(prefix) / path.relative_to(source))

    print("Built:")
    for artifact in (bp_mcpack, rp_mcpack, mcaddon):
        print(f"  - {artifact.relative_to(ROOT)}")


if __name__ == "__main__":
    build()

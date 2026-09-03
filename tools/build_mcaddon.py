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


def validate_json() -> None:
    errors: list[str] = []
    json_files = sorted([*BP.rglob("*.json"), *RP.rglob("*.json")])

    for path in json_files:
        try:
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)
        except Exception as exc:  # noqa: BLE001 - CLI validation should report any parse failure
            errors.append(f"{path.relative_to(ROOT)}: {exc}")

    if errors:
        print("JSON validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Validated {len(json_files)} JSON files.")


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

    # A .mcaddon can contain multiple pack directories. Keeping each pack in a
    # named top-level folder lets Minecraft discover both manifests on import.
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

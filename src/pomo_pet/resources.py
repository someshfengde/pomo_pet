"""Locate assets both in a source checkout and an installed wheel."""
from pathlib import Path


def resource_dir(name: str) -> Path:
    bundled = Path(__file__).resolve().parent / "resources" / name
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[2] / name

"""
Read-only bullet library loader.

Consumes data/bullet_library.json and exposes a small API for UI code to
list bullets and fetch a single preset by id. Falls back to an empty
library if the file is missing or malformed, so the UI never hard-fails.
"""
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "bullet_library.json"


@dataclass
class BulletPreset:
    id: str
    manufacturer: str
    caliber: str
    bullet: str
    mass_grains: float
    diameter_in: float
    length_in: float
    bc_g7: float
    bc_g1: Optional[float]
    default_mv_mps: float
    default_twist_in: float

    @property
    def label(self) -> str:
        return f"{self.caliber} | {self.manufacturer} {self.bullet}"


@lru_cache(maxsize=1)
def load_all() -> List[BulletPreset]:
    """Return every bullet in the library, sorted by caliber then mass."""
    if not _DATA_FILE.exists():
        return []
    try:
        with _DATA_FILE.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    bullets: List[BulletPreset] = []
    for entry in payload.get("bullets", []):
        try:
            bullets.append(BulletPreset(
                id=entry["id"],
                manufacturer=entry["manufacturer"],
                caliber=entry["caliber"],
                bullet=entry["bullet"],
                mass_grains=float(entry["mass_grains"]),
                diameter_in=float(entry["diameter_in"]),
                length_in=float(entry["length_in"]),
                bc_g7=float(entry["bc_g7"]),
                bc_g1=float(entry["bc_g1"]) if entry.get("bc_g1") is not None else None,
                default_mv_mps=float(entry["default_mv_mps"]),
                default_twist_in=float(entry["default_twist_in"]),
            ))
        except (KeyError, TypeError, ValueError):
            continue  # skip malformed entries, keep the rest usable

    bullets.sort(key=lambda b: (b.caliber, b.mass_grains))
    return bullets


def as_label_map() -> Dict[str, BulletPreset]:
    """Return {display_label: preset} for selectbox rendering."""
    return {b.label: b for b in load_all()}


def get(bullet_id: str) -> Optional[BulletPreset]:
    for b in load_all():
        if b.id == bullet_id:
            return b
    return None

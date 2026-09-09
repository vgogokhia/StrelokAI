"""
Chamberings and bullet-diameter compatibility.

A rifle profile carries a *chambering* (what the barrel is chambered for)
and an ammo profile carries a *cartridge*; both are names from this list.
Filtering ammo/bullets for a rifle uses the bore diameter, so an old
profile without a cartridge name still matches by its bullet diameter.
"""
from typing import Optional

# name -> bullet diameter (inches)
CHAMBERINGS = {
    ".22 LR": 0.224,
    ".223 Rem / 5.56": 0.224,
    ".22-250": 0.224,
    ".243 Win": 0.243,
    "6mm Creedmoor": 0.243,
    "6.5 Creedmoor": 0.264,
    "6.5x55": 0.264,
    ".260 Rem": 0.264,
    ".270 Win": 0.277,
    "7mm-08": 0.284,
    "7mm Rem Mag": 0.284,
    ".300 BLK": 0.308,
    ".308 Win / 7.62": 0.308,
    ".30-06": 0.308,
    ".300 Win Mag": 0.308,
    ".300 PRC": 0.308,
    ".338 Lapua": 0.338,
    ".50 BMG": 0.510,
    "Other": None,
}

# Bullet-library caliber labels -> chambering names above.
LIBRARY_CALIBER_TO_CHAMBERING = {
    ".22 LR": ".22 LR",
    ".223 Rem": ".223 Rem / 5.56",
    ".243 Win": ".243 Win",
    "6.5 Creedmoor": "6.5 Creedmoor",
    ".270 Win": ".270 Win",
    "7mm": "7mm Rem Mag",
    "7mm Rem Mag": "7mm Rem Mag",
    ".300 BLK": ".300 BLK",
    ".308 Win": ".308 Win / 7.62",
    ".300 Win Mag": ".300 Win Mag",
    ".338 Lapua": ".338 Lapua",
    ".50 BMG": ".50 BMG",
}

_TOL_IN = 0.003


def chambering_diameter(name: Optional[str]) -> Optional[float]:
    return CHAMBERINGS.get(name or "")


def is_compatible(chambering: Optional[str], bullet_diameter_in: Optional[float],
                  cartridge: Optional[str] = None) -> bool:
    """Does a bullet/ammo fit a rifle chambering?

    Unknown chambering ("Other"/empty) accepts everything. A matching
    cartridge name is accepted outright; otherwise the bullet diameter must
    match the bore.
    """
    bore = chambering_diameter(chambering)
    if bore is None:
        return True
    if cartridge and cartridge == chambering:
        return True
    if bullet_diameter_in is None:
        return False
    return abs(float(bullet_diameter_in) - bore) <= _TOL_IN

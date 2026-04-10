"""
StrelokAI Profile Management Module
Save and load rifle and cartridge profiles via Firestore.
Version: 2.0.0
"""
import json
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from datetime import datetime


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------

def _profiles_col(username: str, profile_type: str):
    """Return a Firestore subcollection: users/{username}/{type}_profiles"""
    from core.firestore_client import get_firestore_client
    db = get_firestore_client()
    return db.collection("users").document(username.lower()).collection(f"{profile_type}_profiles")


# ---------------------------------------------------------------------------
# Dataclass filter helper
# ---------------------------------------------------------------------------

def _filter_known(cls, data: dict) -> dict:
    known = {f.name for f in cls.__dataclass_fields__.values()}
    return {k: v for k, v in data.items() if k in known}


# ---------------------------------------------------------------------------
# Dataclasses (unchanged from v1)
# ---------------------------------------------------------------------------

@dataclass
class RifleProfile:
    name: str
    zero_range: float
    sight_height: float
    twist_rate: float
    twist_direction: str = "right"
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RifleProfile":
        return cls(**_filter_known(cls, data))


@dataclass
class CartridgeProfile:
    name: str
    muzzle_velocity: float
    drag_model: str
    bc_g7: float
    mass_grains: float
    diameter: float
    mv_temp_c: float = 15.0
    temp_sensitivity: float = 0.1
    bullet_length_in: float = 1.0
    description: str = ""
    bc_g1: Optional[float] = None
    bc_segments: Optional[List[List[float]]] = None
    mv_curve: Optional[Dict[str, float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CartridgeProfile":
        return cls(**_filter_known(cls, data))


# ---------------------------------------------------------------------------
# Rifle Profiles
# ---------------------------------------------------------------------------

def save_rifle_profile(username: str, profile: RifleProfile) -> tuple[bool, str]:
    try:
        profile.updated_at = datetime.now().isoformat()
        _profiles_col(username, "rifle").document(profile.name).set(profile.to_dict())
        return True, f"Rifle profile '{profile.name}' saved"
    except Exception as e:
        return False, f"Error saving profile: {e}"


def load_rifle_profile(username: str, profile_name: str) -> Optional[RifleProfile]:
    doc = _profiles_col(username, "rifle").document(profile_name).get()
    if doc.exists:
        return RifleProfile.from_dict(doc.to_dict())
    return None


def list_rifle_profiles(username: str) -> List[str]:
    return [doc.id for doc in _profiles_col(username, "rifle").stream()]


def delete_rifle_profile(username: str, profile_name: str) -> tuple[bool, str]:
    ref = _profiles_col(username, "rifle").document(profile_name)
    if ref.get().exists:
        ref.delete()
        return True, f"Profile '{profile_name}' deleted"
    return False, "Profile not found"


# ---------------------------------------------------------------------------
# Cartridge Profiles
# ---------------------------------------------------------------------------

def save_cartridge_profile(username: str, profile: CartridgeProfile) -> tuple[bool, str]:
    try:
        profile.updated_at = datetime.now().isoformat()
        _profiles_col(username, "cartridge").document(profile.name).set(profile.to_dict())
        return True, f"Cartridge profile '{profile.name}' saved"
    except Exception as e:
        return False, f"Error saving profile: {e}"


def load_cartridge_profile(username: str, profile_name: str) -> Optional[CartridgeProfile]:
    doc = _profiles_col(username, "cartridge").document(profile_name).get()
    if doc.exists:
        return CartridgeProfile.from_dict(doc.to_dict())
    return None


def list_cartridge_profiles(username: str) -> List[str]:
    return [doc.id for doc in _profiles_col(username, "cartridge").stream()]


def delete_cartridge_profile(username: str, profile_name: str) -> tuple[bool, str]:
    ref = _profiles_col(username, "cartridge").document(profile_name)
    if ref.get().exists:
        ref.delete()
        return True, f"Profile '{profile_name}' deleted"
    return False, "Profile not found"


# ---------------------------------------------------------------------------
# Full (Rifle + Cartridge) Profiles
# ---------------------------------------------------------------------------

@dataclass
class FullProfile:
    name: str
    rifle: RifleProfile
    cartridge: CartridgeProfile
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "rifle": self.rifle.to_dict(),
            "cartridge": self.cartridge.to_dict(),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FullProfile":
        rifle_data = data["rifle"]
        cartridge_data = data["cartridge"]
        if "muzzle_velocity" in rifle_data and "muzzle_velocity" not in cartridge_data:
            cartridge_data["muzzle_velocity"] = rifle_data.pop("muzzle_velocity")
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            rifle=RifleProfile.from_dict(rifle_data),
            cartridge=CartridgeProfile.from_dict(cartridge_data),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


def save_full_profile(username: str, profile: FullProfile) -> tuple[bool, str]:
    try:
        _profiles_col(username, "full").document(profile.name).set(profile.to_dict())
        return True, f"Profile '{profile.name}' saved"
    except Exception as e:
        return False, f"Error saving profile: {e}"


def load_full_profile(username: str, profile_name: str) -> Optional[FullProfile]:
    doc = _profiles_col(username, "full").document(profile_name).get()
    if doc.exists:
        return FullProfile.from_dict(doc.to_dict())
    return None


def list_full_profiles(username: str) -> List[str]:
    return [doc.id for doc in _profiles_col(username, "full").stream()]

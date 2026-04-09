"""
StrelokAI Profile Management Module
Save and load rifle and cartridge profiles
Version: 1.1.0
"""
import json
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime

from auth import get_user_data_dir


def _filter_known(cls, data: dict) -> dict:
    """Keep only keys that are fields of the dataclass. Unknown keys are
    ignored for forward-compat, so newer profile files still load in older
    code that doesn't know about every field."""
    known = {f.name for f in cls.__dataclass_fields__.values()}
    return {k: v for k, v in data.items() if k in known}


@dataclass
class RifleProfile:
    """Rifle configuration profile"""
    name: str
    zero_range: float  # meters
    sight_height: float  # mm
    twist_rate: float  # 1:X inches
    twist_direction: str = "right"  # "right" or "left"
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
    """Cartridge/bullet configuration profile"""
    name: str
    muzzle_velocity: float  # m/s
    drag_model: str  # "G1" or "G7"
    bc_g7: float  # G7 Ballistic Coefficient
    mass_grains: float  # Bullet weight in grains
    diameter: float  # inches
    mv_temp_c: float = 15.0  # Temperature at which MV was measured
    temp_sensitivity: float = 0.1  # % change in MV per 1°C
    bullet_length_in: float = 1.0  # Bullet length (inches) for Miller stability
    description: str = ""
    bc_g1: Optional[float] = None  # Optional G1 BC
    bc_segments: Optional[List[List[float]]] = None  # Stepped BC: [[floor_fps, bc], ...]
    # Optional non-linear MV curve: {temp_c: mv_mps}. Overrides temp_sensitivity.
    mv_curve: Optional[Dict[str, float]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CartridgeProfile":
        return cls(**_filter_known(cls, data))


def _get_profiles_file(username: str, profile_type: str) -> Path:
    """Get the path to a user's profiles file"""
    user_dir = get_user_data_dir(username)
    return user_dir / f"{profile_type}_profiles.json"


def _load_profiles(username: str, profile_type: str) -> dict:
    """Load profiles from file"""
    filepath = _get_profiles_file(username, profile_type)
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_profiles(username: str, profile_type: str, profiles: dict):
    """Save profiles to file"""
    filepath = _get_profiles_file(username, profile_type)
    with open(filepath, 'w') as f:
        json.dump(profiles, f, indent=2)


# ============ Rifle Profile Functions ============

def save_rifle_profile(username: str, profile: RifleProfile) -> tuple[bool, str]:
    """Save a rifle profile for a user"""
    try:
        profiles = _load_profiles(username, "rifle")
        profile.updated_at = datetime.now().isoformat()
        profiles[profile.name] = profile.to_dict()
        _save_profiles(username, "rifle", profiles)
        return True, f"Rifle profile '{profile.name}' saved"
    except Exception as e:
        return False, f"Error saving profile: {str(e)}"


def load_rifle_profile(username: str, profile_name: str) -> Optional[RifleProfile]:
    """Load a specific rifle profile"""
    profiles = _load_profiles(username, "rifle")
    if profile_name in profiles:
        return RifleProfile.from_dict(profiles[profile_name])
    return None


def list_rifle_profiles(username: str) -> List[str]:
    """List all rifle profile names for a user"""
    profiles = _load_profiles(username, "rifle")
    return list(profiles.keys())


def delete_rifle_profile(username: str, profile_name: str) -> tuple[bool, str]:
    """Delete a rifle profile"""
    profiles = _load_profiles(username, "rifle")
    if profile_name in profiles:
        del profiles[profile_name]
        _save_profiles(username, "rifle", profiles)
        return True, f"Profile '{profile_name}' deleted"
    return False, "Profile not found"


# ============ Cartridge Profile Functions ============

def save_cartridge_profile(username: str, profile: CartridgeProfile) -> tuple[bool, str]:
    """Save a cartridge profile for a user"""
    try:
        profiles = _load_profiles(username, "cartridge")
        profile.updated_at = datetime.now().isoformat()
        profiles[profile.name] = profile.to_dict()
        _save_profiles(username, "cartridge", profiles)
        return True, f"Cartridge profile '{profile.name}' saved"
    except Exception as e:
        return False, f"Error saving profile: {str(e)}"


def load_cartridge_profile(username: str, profile_name: str) -> Optional[CartridgeProfile]:
    """Load a specific cartridge profile"""
    profiles = _load_profiles(username, "cartridge")
    if profile_name in profiles:
        return CartridgeProfile.from_dict(profiles[profile_name])
    return None


def list_cartridge_profiles(username: str) -> List[str]:
    """List all cartridge profile names for a user"""
    profiles = _load_profiles(username, "cartridge")
    return list(profiles.keys())


def delete_cartridge_profile(username: str, profile_name: str) -> tuple[bool, str]:
    """Delete a cartridge profile"""
    profiles = _load_profiles(username, "cartridge")
    if profile_name in profiles:
        del profiles[profile_name]
        _save_profiles(username, "cartridge", profiles)
        return True, f"Profile '{profile_name}' deleted"
    return False, "Profile not found"


# ============ Combined Profile (Rifle + Cartridge) ============

@dataclass
class FullProfile:
    """Combined rifle and cartridge profile for quick loading"""
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
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "FullProfile":
        # Handle legacy profiles where muzzle_velocity was in Rifle
        rifle_data = data["rifle"]
        cartridge_data = data["cartridge"]
        if "muzzle_velocity" in rifle_data and "muzzle_velocity" not in cartridge_data:
            cartridge_data["muzzle_velocity"] = rifle_data.pop("muzzle_velocity")
            
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            rifle=RifleProfile.from_dict(rifle_data),
            cartridge=CartridgeProfile.from_dict(cartridge_data),
            created_at=data.get("created_at", datetime.now().isoformat())
        )


def save_full_profile(username: str, profile: FullProfile) -> tuple[bool, str]:
    """Save a full (rifle+cartridge) profile"""
    try:
        profiles = _load_profiles(username, "full")
        profiles[profile.name] = profile.to_dict()
        _save_profiles(username, "full", profiles)
        return True, f"Profile '{profile.name}' saved"
    except Exception as e:
        return False, f"Error saving profile: {str(e)}"


def load_full_profile(username: str, profile_name: str) -> Optional[FullProfile]:
    """Load a full profile"""
    profiles = _load_profiles(username, "full")
    if profile_name in profiles:
        return FullProfile.from_dict(profiles[profile_name])
    return None


def list_full_profiles(username: str) -> List[str]:
    """List all full profile names"""
    profiles = _load_profiles(username, "full")
    return list(profiles.keys())

"""
StrelokAI Profile Management Module
Save and load rifle and cartridge profiles
"""
import json
from dataclasses import dataclass, asdict, field
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from auth import get_user_data_dir


@dataclass
class RifleProfile:
    """Rifle configuration profile"""
    name: str
    muzzle_velocity: float  # m/s
    zero_range: float  # meters
    sight_height: float  # mm
    twist_rate: float  # 1:X inches
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "RifleProfile":
        return cls(**data)


@dataclass
class CartridgeProfile:
    """Cartridge/bullet configuration profile"""
    name: str
    bc_g7: float  # G7 Ballistic Coefficient
    mass_grains: float  # Bullet weight in grains
    diameter: float  # inches
    description: str = ""
    bc_g1: Optional[float] = None  # Optional G1 BC
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "CartridgeProfile":
        return cls(**data)


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
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            rifle=RifleProfile.from_dict(data["rifle"]),
            cartridge=CartridgeProfile.from_dict(data["cartridge"]),
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

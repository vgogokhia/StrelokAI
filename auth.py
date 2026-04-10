"""
StrelokAI Authentication Module
User authentication with password hashing, backed by Firestore.
Version: 2.0.0
"""
import hashlib
import secrets as _secrets
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------

def _users_col():
    from core.firestore_client import get_firestore_client
    return get_firestore_client().collection("users")


# ---------------------------------------------------------------------------
# User dataclass (unchanged from v1)
# ---------------------------------------------------------------------------

@dataclass
class User:
    """User account data"""
    username: str
    password_hash: str
    salt: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(**{k: data[k] for k in ("username", "password_hash", "salt", "created_at")})


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if salt is None:
        salt = _secrets.token_hex(16)
    salted = (password + salt).encode("utf-8")
    password_hash = hashlib.sha256(salted).hexdigest()
    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == password_hash


# ---------------------------------------------------------------------------
# Public API (same signatures as v1 file-based auth)
# ---------------------------------------------------------------------------

def create_user(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 4:
        return False, "Password must be at least 4 characters"

    doc_ref = _users_col().document(username.lower())
    if doc_ref.get().exists:
        return False, "Username already exists"

    password_hash, salt = hash_password(password)
    user = User(
        username=username,
        password_hash=password_hash,
        salt=salt,
        created_at=datetime.now().isoformat(),
    )
    doc_ref.set(user.to_dict())
    return True, "Account created successfully"


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password are required"

    doc = _users_col().document(username.lower()).get()
    if not doc.exists:
        return False, "Invalid username or password"

    user = User.from_dict(doc.to_dict())
    if verify_password(password, user.password_hash, user.salt):
        return True, "Login successful"
    return False, "Invalid username or password"


def user_exists(username: str) -> bool:
    return _users_col().document(username.lower()).get().exists


def get_user_data_dir(username: str):
    """Kept for backward-compat imports but no longer used for storage.
    Returns a placeholder string (not a Path) — callers should use
    Firestore via profiles.py instead."""
    return username.lower()

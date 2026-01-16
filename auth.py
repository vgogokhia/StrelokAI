"""
StrelokAI Authentication Module
Simple file-based user authentication with password hashing
"""
import hashlib
import json
import os
import secrets
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


# Data directory for user storage
DATA_DIR = Path.home() / ".strelokai"
USERS_FILE = DATA_DIR / "users.json"


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
        return cls(**data)


def _ensure_data_dir():
    """Create data directory if it doesn't exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_users() -> dict:
    """Load users from JSON file"""
    _ensure_data_dir()
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_users(users: dict):
    """Save users to JSON file"""
    _ensure_data_dir()
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    Hash a password with a salt using SHA-256
    Returns: (hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine password and salt, hash it
    salted = (password + salt).encode('utf-8')
    password_hash = hashlib.sha256(salted).hexdigest()
    
    return password_hash, salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verify a password against stored hash"""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == password_hash


def create_user(username: str, password: str) -> tuple[bool, str]:
    """
    Create a new user account
    Returns: (success, message)
    """
    if not username or not password:
        return False, "Username and password are required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    
    users = _load_users()
    
    if username.lower() in users:
        return False, "Username already exists"
    
    # Create user
    password_hash, salt = hash_password(password)
    from datetime import datetime
    
    user = User(
        username=username,
        password_hash=password_hash,
        salt=salt,
        created_at=datetime.now().isoformat()
    )
    
    users[username.lower()] = user.to_dict()
    _save_users(users)
    
    return True, "Account created successfully"


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """
    Authenticate a user
    Returns: (success, message)
    """
    if not username or not password:
        return False, "Username and password are required"
    
    users = _load_users()
    
    user_data = users.get(username.lower())
    if not user_data:
        return False, "Invalid username or password"
    
    user = User.from_dict(user_data)
    
    if verify_password(password, user.password_hash, user.salt):
        return True, "Login successful"
    else:
        return False, "Invalid username or password"


def user_exists(username: str) -> bool:
    """Check if a user exists"""
    users = _load_users()
    return username.lower() in users


def get_user_data_dir(username: str) -> Path:
    """Get the data directory for a specific user"""
    user_dir = DATA_DIR / "profiles" / username.lower()
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

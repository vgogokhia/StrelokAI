"""
AI Scope Recognition using Gemini Vision API
Takes a photo of a scope and identifies the model to auto-populate settings
"""
import os
from dataclasses import dataclass
from typing import Optional
import base64

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Common scope database with settings
SCOPE_DATABASE = {
    "vortex_razor_hd_gen_iii": {
        "manufacturer": "Vortex",
        "model": "Razor HD Gen III",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 32.5,
        "turret_direction": "cw_up",
        "reticle_options": ["EBR-7C", "EBR-7B"],
    },
    "vortex_viper_pst_gen_ii": {
        "manufacturer": "Vortex", 
        "model": "Viper PST Gen II",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 27.5,
        "turret_direction": "cw_up",
        "reticle_options": ["EBR-7C", "EBR-4"],
    },
    "nightforce_atacr": {
        "manufacturer": "Nightforce",
        "model": "ATACR 5-25x56",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 35.0,
        "turret_direction": "cw_up",
        "reticle_options": ["MIL-R", "MIL-XT", "MOAR-T"],
    },
    "nightforce_nx8": {
        "manufacturer": "Nightforce",
        "model": "NX8 2.5-20x50",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 31.5,
        "turret_direction": "cw_up",
        "reticle_options": ["MIL-C", "MIL-CF2"],
    },
    "leupold_mark5_hd": {
        "manufacturer": "Leupold",
        "model": "Mark 5HD 5-25x56",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 29.0,
        "turret_direction": "cw_up",
        "reticle_options": ["TMR", "Tremor 3", "H59"],
    },
    "schmidt_bender_pm_ii": {
        "manufacturer": "Schmidt & Bender",
        "model": "PM II 5-25x56",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 26.0,
        "turret_direction": "cw_up",
        "reticle_options": ["P4FL", "MRAD", "GR²ID"],
    },
    "kahles_k525i": {
        "manufacturer": "Kahles",
        "model": "K525i 5-25x56",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 26.0,
        "turret_direction": "cw_up",
        "reticle_options": ["SKMR4", "MSR2"],
    },
    "primary_arms_glx": {
        "manufacturer": "Primary Arms",
        "model": "GLx 4-16x50",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 25.0,
        "turret_direction": "cw_up",
        "reticle_options": ["ACSS HUD DMR", "Athena BPR"],
    },
    "athlon_ares_etr": {
        "manufacturer": "Athlon",
        "model": "Ares ETR 4.5-30x56",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 36.0,
        "turret_direction": "cw_up",
        "reticle_options": ["APLR", "APRS"],
    },
    "zeiss_lrp_s5": {
        "manufacturer": "Zeiss",
        "model": "LRP S5 525-56",
        "click_value_mrad": 0.1,
        "max_elevation_mrad": 24.0,
        "turret_direction": "cw_up",
        "reticle_options": ["ZF-MRi", "MRAD"],
    },
}


@dataclass
class ScopeInfo:
    """Identified scope information"""
    manufacturer: str
    model: str
    click_value_mrad: float
    max_elevation_mrad: float
    turret_direction: str  # "cw_up" = clockwise is up
    reticle_options: list
    confidence: float  # 0-1


def identify_scope(
    image_path: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    api_key: Optional[str] = None
) -> Optional[ScopeInfo]:
    """
    Identify scope from image using Gemini Vision API
    
    Args:
        image_path: Path to image file
        image_bytes: Raw image bytes (alternative to path)
        api_key: Gemini API key
        
    Returns:
        ScopeInfo if identified, None otherwise
    """
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    
    if not key or key == "your-gemini-api-key-here":
        # Demo mode - return a sample scope
        return ScopeInfo(
            manufacturer="Demo",
            model="Add Gemini API key for real recognition",
            click_value_mrad=0.1,
            max_elevation_mrad=25.0,
            turret_direction="cw_up",
            reticle_options=["MIL-R"],
            confidence=0.0
        )
    
    if not GEMINI_AVAILABLE:
        print("Gemini API not available. Install google-generativeai package.")
        return None
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Load image
        if image_path:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        
        if not image_bytes:
            return None
        
        # Create prompt for scope identification
        prompt = """Analyze this image of a rifle scope. Identify the manufacturer and model.

Look for:
- Brand name on the scope body or turrets
- Model number or name
- Magnification range on the zoom ring
- Turret style and markings

Known scope brands to look for:
- Vortex (Razor, Viper, Diamondback, Strike Eagle)
- Nightforce (ATACR, NX8, NXS, SHV)
- Leupold (Mark 5HD, VX-5HD, VX-3i)
- Schmidt & Bender (PM II, EXOS)
- Kahles (K525i, K318i)
- Zeiss (LRP S5, Conquest)
- Primary Arms (GLx, SLx)
- Athlon (Ares ETR, Midas TAC)

Respond in this exact format:
MANUFACTURER: [brand name]
MODEL: [full model name]
CONFIDENCE: [high/medium/low]

If you cannot identify the scope, respond with:
MANUFACTURER: Unknown
MODEL: Unknown
CONFIDENCE: low
"""
        
        # Send to Gemini
        response = model.generate_content([
            prompt,
            {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}
        ])
        
        # Parse response
        text = response.text
        lines = text.strip().split("\n")
        
        manufacturer = "Unknown"
        model_name = "Unknown"
        confidence_str = "low"
        
        for line in lines:
            if line.startswith("MANUFACTURER:"):
                manufacturer = line.split(":", 1)[1].strip()
            elif line.startswith("MODEL:"):
                model_name = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                confidence_str = line.split(":", 1)[1].strip().lower()
        
        confidence = {"high": 0.9, "medium": 0.7, "low": 0.4}.get(confidence_str, 0.5)
        
        # Look up in database for exact settings
        for key, info in SCOPE_DATABASE.items():
            if (manufacturer.lower() in info["manufacturer"].lower() and 
                model_name.lower() in info["model"].lower()):
                return ScopeInfo(
                    manufacturer=info["manufacturer"],
                    model=info["model"],
                    click_value_mrad=info["click_value_mrad"],
                    max_elevation_mrad=info["max_elevation_mrad"],
                    turret_direction=info["turret_direction"],
                    reticle_options=info["reticle_options"],
                    confidence=confidence
                )
        
        # Return basic info if not in database
        return ScopeInfo(
            manufacturer=manufacturer,
            model=model_name,
            click_value_mrad=0.1,  # Default
            max_elevation_mrad=25.0,  # Default
            turret_direction="cw_up",
            reticle_options=["Unknown"],
            confidence=confidence * 0.8  # Lower confidence for DB miss
        )
        
    except Exception as e:
        print(f"Scope recognition error: {e}")
        return None


def get_scope_from_database(manufacturer: str, model: str) -> Optional[ScopeInfo]:
    """
    Get scope info directly from database by name
    """
    for key, info in SCOPE_DATABASE.items():
        if (manufacturer.lower() in info["manufacturer"].lower() and 
            model.lower() in info["model"].lower()):
            return ScopeInfo(
                manufacturer=info["manufacturer"],
                model=info["model"],
                click_value_mrad=info["click_value_mrad"],
                max_elevation_mrad=info["max_elevation_mrad"],
                turret_direction=info["turret_direction"],
                reticle_options=info["reticle_options"],
                confidence=1.0
            )
    return None


def list_supported_scopes() -> list:
    """Return list of all supported scopes"""
    return [f"{v['manufacturer']} {v['model']}" for v in SCOPE_DATABASE.values()]

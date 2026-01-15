"""
Atmospheric calculations for ballistics
Includes density altitude, air density, and speed of sound
"""
import math
from dataclasses import dataclass


@dataclass
class AtmosphericConditions:
    """Atmospheric conditions at shooting location"""
    temperature_c: float  # Celsius
    pressure_mbar: float  # Millibars (hPa)
    humidity_pct: float   # 0-100
    altitude_m: float     # Meters above sea level
    
    @property
    def temperature_k(self) -> float:
        """Temperature in Kelvin"""
        return self.temperature_c + 273.15
    
    @property
    def temperature_f(self) -> float:
        """Temperature in Fahrenheit"""
        return self.temperature_c * 9/5 + 32
    
    @property
    def pressure_inhg(self) -> float:
        """Pressure in inches of mercury"""
        return self.pressure_mbar * 0.02953


class Atmosphere:
    """
    Atmospheric model for ballistic calculations
    Uses ICAO Standard Atmosphere as reference
    """
    
    # Standard atmosphere constants (ICAO)
    STD_TEMP_C = 15.0          # Standard temperature at sea level
    STD_PRESSURE_MBAR = 1013.25  # Standard pressure at sea level
    STD_DENSITY = 1.225        # kg/m³ at standard conditions
    LAPSE_RATE = 0.0065        # Temperature lapse rate K/m
    GAS_CONSTANT = 287.05      # J/(kg·K) for dry air
    GRAVITY = 9.80665          # m/s²
    
    def __init__(self, conditions: AtmosphericConditions):
        self.conditions = conditions
    
    @classmethod
    def standard(cls) -> "Atmosphere":
        """Return standard atmosphere conditions"""
        return cls(AtmosphericConditions(
            temperature_c=15.0,
            pressure_mbar=1013.25,
            humidity_pct=0.0,
            altitude_m=0.0
        ))
    
    def air_density(self) -> float:
        """
        Calculate air density in kg/m³
        Uses the ideal gas law with humidity correction
        """
        T = self.conditions.temperature_k
        P = self.conditions.pressure_mbar * 100  # Convert to Pascals
        
        # Saturation vapor pressure (Magnus formula)
        es = 6.1078 * 10 ** (7.5 * self.conditions.temperature_c / 
                              (self.conditions.temperature_c + 237.3))
        
        # Actual vapor pressure
        e = es * (self.conditions.humidity_pct / 100)
        
        # Partial pressure of dry air
        Pd = P - (e * 100)
        
        # Density with humidity correction
        # ρ = (Pd / (Rd * T)) + (e * 100 / (Rv * T))
        Rd = 287.05   # Gas constant for dry air
        Rv = 461.495  # Gas constant for water vapor
        
        rho = (Pd / (Rd * T)) + (e * 100 / (Rv * T))
        return rho
    
    def density_ratio(self) -> float:
        """Ratio of current density to standard density"""
        return self.air_density() / self.STD_DENSITY
    
    def density_altitude_m(self) -> float:
        """
        Calculate density altitude in meters
        The altitude in standard atmosphere that has the same air density
        """
        rho = self.air_density()
        
        # Inverse of barometric formula
        # DA = (T0/L) * (1 - (rho/rho0)^(L*R/g))
        T0 = 288.15  # Standard temp at sea level in K
        L = self.LAPSE_RATE
        
        try:
            da = (T0 / L) * (1 - (rho / self.STD_DENSITY) ** 
                            (L * self.GAS_CONSTANT / self.GRAVITY))
            return da
        except (ValueError, ZeroDivisionError):
            return self.conditions.altitude_m
    
    def density_altitude_ft(self) -> float:
        """Density altitude in feet"""
        return self.density_altitude_m() * 3.28084
    
    def speed_of_sound(self) -> float:
        """
        Speed of sound in m/s
        Varies with temperature only (for ideal gas)
        """
        # c = sqrt(γ * R * T)
        gamma = 1.4  # Heat capacity ratio for air
        return math.sqrt(gamma * self.GAS_CONSTANT * self.conditions.temperature_k)
    
    def mach_number(self, velocity_mps: float) -> float:
        """Calculate Mach number for given velocity"""
        return velocity_mps / self.speed_of_sound()
    
    def pressure_at_altitude(self, altitude_m: float) -> float:
        """
        Calculate pressure at altitude using barometric formula
        Returns pressure in mbar
        """
        P0 = self.STD_PRESSURE_MBAR * 100  # Pascals
        T0 = 288.15  # Standard temp at sea level
        
        # Barometric formula
        P = P0 * (1 - (self.LAPSE_RATE * altitude_m) / T0) ** \
            (self.GRAVITY / (self.LAPSE_RATE * self.GAS_CONSTANT))
        
        return P / 100  # Convert back to mbar
    
    def __repr__(self) -> str:
        return (f"Atmosphere(T={self.conditions.temperature_c:.1f}°C, "
                f"P={self.conditions.pressure_mbar:.1f}mbar, "
                f"RH={self.conditions.humidity_pct:.0f}%, "
                f"ρ={self.air_density():.4f}kg/m³)")

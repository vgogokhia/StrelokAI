"""
Point-mass ballistic solver for StrelokAI.

Physics implemented:
- True 4th-order Runge-Kutta integration (adaptive step)
- Physically correct drag: a = Cd(mach) * rho * v^2 / (2 * BC_si)
- Velocity-dependent (stepped) ballistic coefficients (Berger convention)
- Miller gyroscopic stability factor (+ Litz velocity/atmosphere correction)
- Litz empirical spin drift
- Litz aerodynamic jump (from crosswind)
- Shooting angle (inclination) via rotated gravity
- Rifle cant angle (post-process rotation of scope frame)
- Coriolis effect (horizontal + Eotvos vertical)

Coordinate convention (world frame):
    x = downrange (horizontal projection along line of sight)
    y = vertical (positive up)
    z = horizontal right (perpendicular to x)
Drop is reported as y-offset from line-of-sight (negative = below).
"""
import math
import os
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

from .atmosphere import Atmosphere, AtmosphericConditions
from .drag_models import G1_DRAG, G7_DRAG, get_drag_coefficient
from .cdm import DragCurve, curve_to_drag_table


# BC (lb/in^2) sectional-density conversion to SI (kg/m^2): 1 lb/in^2 = 703.0696 kg/m^2.
#
# Standard G1/G7 drag tables (McCoy, BRL) express coefficients referenced to
# the *diameter-squared* area (d^2), NOT the circular cross-section (pi*d^2/4).
# Since BC = m/d^2 also uses d^2, the pi/4 factors cancel and the retardation
# simplifies to:
#     a = Cd_table(M) * rho * v^2 / (2 * BC_si)
#
# where BC_si = BC_lbin2 * 703.0696.  Validated against JBM Ballistics.
#
# For Custom Drag Models (CDM) the Cd values are true aerodynamic coefficients
# referenced to the circular area A = pi*d^2/4, so the retardation uses:
#     a = Cd_true(M) * rho * v^2 * (pi*d^2/4) / (2*m)
#       = (pi/8) * Cd_true * rho * v^2 * d^2 / m
BC_LBIN2_TO_KGM2 = 703.0696
CDM_SHAPE_FACTOR = math.pi / 8.0  # for CDM (true aero Cd) only

# Legacy drag model can be re-enabled with STRELOKAI_LEGACY_DRAG=1 for A/B comparison.
_LEGACY_DRAG = os.environ.get("STRELOKAI_LEGACY_DRAG") == "1"
_LEGACY_RETARDATION_CONSTANT = 1600.0


@dataclass
class Projectile:
    """Projectile (bullet) parameters."""
    mass_grains: float
    diameter_inches: float
    bc_g1: Optional[float] = None
    bc_g7: Optional[float] = None
    length_inches: float = 1.0
    # Optional velocity-stepped BCs: list of (velocity_fps_floor, bc) pairs,
    # sorted high-to-low. Active segment is the first whose floor <= v_fps.
    bc_segments: Optional[List[Tuple[float, float]]] = None
    # Optional Custom Drag Model. When set, the solver bypasses G1/G7 and
    # uses this curve directly. It is treated as absolute (BC is ignored).
    drag_curve: Optional[DragCurve] = None

    @property
    def mass_kg(self) -> float:
        return self.mass_grains * 0.0000647989

    @property
    def diameter_m(self) -> float:
        return self.diameter_inches * 0.0254

    @property
    def sectional_density(self) -> float:
        """Sectional density in lb/in^2."""
        mass_lbs = self.mass_grains / 7000.0
        return mass_lbs / (self.diameter_inches ** 2)

    @property
    def length_calibers(self) -> float:
        return self.length_inches / self.diameter_inches


@dataclass
class Rifle:
    """Rifle parameters."""
    muzzle_velocity_mps: float
    zero_range_m: float = 100.0
    sight_height_mm: float = 40.0
    twist_rate_inches: float = 10.0
    twist_direction: str = "right"

    @property
    def sight_height_m(self) -> float:
        return self.sight_height_mm / 1000.0


@dataclass
class Wind:
    """Wind conditions.

    direction_deg is the direction the wind is coming FROM, relative to the
    shooter's heading: 0 = headwind, 90 = from right, 180 = tailwind.
    """
    speed_mps: float = 0.0
    direction_deg: float = 0.0

    @property
    def crosswind_component(self) -> float:
        """Crosswind component (positive = from right)."""
        return self.speed_mps * math.sin(math.radians(self.direction_deg))

    @property
    def headwind_component(self) -> float:
        """Headwind component (positive = headwind, slows bullet)."""
        return self.speed_mps * math.cos(math.radians(self.direction_deg))


@dataclass
class ShootingConditions:
    """Complete shooting setup."""
    projectile: Projectile
    rifle: Rifle
    atmosphere: Atmosphere
    wind: Wind = field(default_factory=Wind)
    latitude_deg: float = 41.7
    azimuth_deg: float = 0.0
    elevation_angle_deg: float = 0.0  # Line-of-sight inclination (+ = uphill)
    cant_angle_deg: float = 0.0       # Rifle roll (+ = top tilted right)


@dataclass
class TrajectoryPoint:
    time_s: float
    range_m: float
    drop_m: float
    windage_m: float
    velocity_mps: float
    energy_j: float
    mach: float

    @property
    def drop_mrad(self) -> float:
        if self.range_m == 0:
            return 0.0
        return (self.drop_m / self.range_m) * 1000

    @property
    def drop_moa(self) -> float:
        return self.drop_mrad * 3.43775

    @property
    def windage_mrad(self) -> float:
        if self.range_m == 0:
            return 0.0
        return (self.windage_m / self.range_m) * 1000

    @property
    def windage_moa(self) -> float:
        return self.windage_mrad * 3.43775


@dataclass
class BallisticSolution:
    trajectory: List[TrajectoryPoint]
    zero_angle_mrad: float
    spin_drift_m: float
    coriolis_vertical_m: float
    coriolis_horizontal_m: float
    stability_factor: float = 0.0
    aero_jump_mrad: float = 0.0

    def at_range(self, range_m: float) -> Optional[TrajectoryPoint]:
        """Get trajectory point at a specific range (linear interpolation)."""
        if not self.trajectory:
            return None
        if range_m <= self.trajectory[0].range_m:
            return self.trajectory[0]
        for i in range(len(self.trajectory) - 1):
            pt = self.trajectory[i]
            nxt = self.trajectory[i + 1]
            if pt.range_m <= range_m <= nxt.range_m:
                span = nxt.range_m - pt.range_m
                t = 0.0 if span == 0 else (range_m - pt.range_m) / span
                return TrajectoryPoint(
                    time_s=pt.time_s + t * (nxt.time_s - pt.time_s),
                    range_m=range_m,
                    drop_m=pt.drop_m + t * (nxt.drop_m - pt.drop_m),
                    windage_m=pt.windage_m + t * (nxt.windage_m - pt.windage_m),
                    velocity_mps=pt.velocity_mps + t * (nxt.velocity_mps - pt.velocity_mps),
                    energy_j=pt.energy_j + t * (nxt.energy_j - pt.energy_j),
                    mach=pt.mach + t * (nxt.mach - pt.mach),
                )
        return self.trajectory[-1]


class BallisticSolver:
    """RK4 point-mass ballistic solver."""

    EARTH_ROTATION_RAD_S = 7.2921159e-5
    GRAVITY = 9.80665

    def __init__(self, conditions: ShootingConditions):
        self.conditions = conditions
        self._select_drag_model()
        self._rho = self.conditions.atmosphere.air_density()
        self._sos = self.conditions.atmosphere.speed_of_sound()
        self._sg_cache: Optional[float] = None

    def _select_drag_model(self):
        proj = self.conditions.projectile
        # Precedence: drag_curve (CDM) > bc_g7 > bc_g1
        if proj.drag_curve is not None:
            self.drag_table = curve_to_drag_table(proj.drag_curve)
            self.bc = 1.0  # unused when _use_cdm is True
            self.drag_model = "CDM"
            self._use_cdm = True
        elif proj.bc_g7:
            self.drag_table = G7_DRAG
            self.bc = proj.bc_g7
            self.drag_model = "G7"
            self._use_cdm = False
        elif proj.bc_g1:
            self.drag_table = G1_DRAG
            self.bc = proj.bc_g1
            self.drag_model = "G1"
            self._use_cdm = False
        else:
            raise ValueError("Projectile must have either a drag_curve, G7 BC, or G1 BC")

    # --- Physics primitives ------------------------------------------------

    def _active_bc(self, v_mps: float) -> float:
        """Return the BC to use at a given air-relative velocity."""
        segments = self.conditions.projectile.bc_segments
        if not segments:
            return self.bc
        v_fps = v_mps * 3.28084
        # Segments are ordered (velocity_floor_fps, bc) high-to-low.
        # Pick the first segment whose floor is <= v_fps.
        ordered = sorted(segments, key=lambda s: -s[0])
        for floor_fps, bc in ordered:
            if v_fps >= floor_fps:
                return bc
        return ordered[-1][1]

    def _drag_accel(self, v_rel: float, mach: float) -> float:
        """Drag deceleration magnitude (m/s^2) for speed v_rel relative to air."""
        if v_rel <= 0:
            return 0.0
        cd = get_drag_coefficient(mach, self.drag_table)
        if self._use_cdm:
            # Custom Drag Model: Cd is a true aerodynamic coefficient
            # referenced to circular area A = pi*d^2/4:
            #     a = (pi/8) * Cd * rho * v^2 * d^2 / m
            proj = self.conditions.projectile
            d_m = proj.diameter_m
            m_kg = proj.mass_kg
            if m_kg <= 0:
                return 0.0
            return CDM_SHAPE_FACTOR * cd * self._rho * v_rel * v_rel * (d_m * d_m) / m_kg
        if _LEGACY_DRAG:
            # Legacy path for A/B comparison only. Scales by density ratio
            # and uses the old hand-tuned retardation constant.
            rho_ratio = self._rho / Atmosphere.STD_DENSITY
            return (rho_ratio * cd * v_rel ** 2) / (self.bc * _LEGACY_RETARDATION_CONSTANT)
        # G1/G7 standard drag: Cd_table values are d^2-referenced (include pi/4).
        #     a = Cd_table * rho * v^2 / (2 * BC_si)
        bc = self._active_bc(v_rel)
        bc_si = bc * BC_LBIN2_TO_KGM2
        return 0.5 * cd * self._rho * v_rel * v_rel / bc_si

    def _miller_stability(self) -> float:
        """
        Miller gyroscopic stability factor with Litz velocity/atmosphere
        correction. Cached per solver instance (depends only on conditions).
        """
        if self._sg_cache is not None:
            return self._sg_cache
        proj = self.conditions.projectile
        rifle = self.conditions.rifle
        atm = self.conditions.atmosphere

        d = proj.diameter_inches
        if d <= 0:
            self._sg_cache = 0.0
            return 0.0
        t = rifle.twist_rate_inches / d  # twist in calibers per turn
        L = proj.length_inches / d       # length in calibers
        m = proj.mass_grains
        denom = (t * t) * (d ** 3) * L * (1.0 + L * L)
        if denom <= 0:
            self._sg_cache = 0.0
            return 0.0
        sg = 30.0 * m / denom

        # Velocity correction (ref: 2800 fps)
        v_fps = rifle.muzzle_velocity_mps * 3.28084
        if v_fps > 0:
            sg *= (v_fps / 2800.0) ** (1.0 / 3.0)

        # Atmosphere correction: ref T = 59 F (519 R), P = 29.92 inHg
        T_R = (atm.conditions.temperature_c + 273.15) * 1.8
        P_inHg = atm.conditions.pressure_mbar * 0.02953
        if T_R > 0 and P_inHg > 0:
            sg *= (T_R / 519.0) * (29.92 / P_inHg)

        self._sg_cache = sg
        return sg

    def _spin_drift_m(self, tof_s: float) -> float:
        """Litz empirical spin drift in meters at time-of-flight tof_s."""
        if tof_s <= 0:
            return 0.0
        sg = self._miller_stability()
        sd_inches = 1.25 * (sg + 1.2) * (tof_s ** 1.83)
        sd_m = sd_inches * 0.0254
        if self.conditions.rifle.twist_direction == "left":
            sd_m = -sd_m
        return sd_m

    def _aero_jump_mrad(self) -> float:
        """
        Litz aerodynamic jump from crosswind:
            AJ_moa = 0.01 * SG * crosswind_mph (signed)
        Positive crosswind from 3 o'clock -> positive (upward) jump in RH twist.
        """
        sg = self._miller_stability()
        cross_mph = self.conditions.wind.crosswind_component * 2.23694
        aj_moa = 0.01 * sg * cross_mph
        aj_mrad = aj_moa / 3.43775
        if self.conditions.rifle.twist_direction == "left":
            aj_mrad = -aj_mrad
        return aj_mrad

    def _coriolis_effect(self, tof_s: float, range_m: float) -> Tuple[float, float]:
        """
        Coriolis deflection (vertical_m, horizontal_m) at target.

        Derivation (point-mass approximation):
          * Horizontal Coriolis deflects the bullet to the right of its
            path in the N hemisphere and to the left in the S hemisphere,
            independent of azimuth:
                d_horiz = omega * sin(lat) * v * tof^2
                        = omega * sin(lat) * range * tof
          * Eotvos vertical effect: a bullet fired with an eastward
            component is effectively lifted (apparent gravity reduced);
            westward is heavier. The acceleration magnitude is
                a_vert = 2 * omega * cos(lat) * v_east
            with v_east = v * sin(az), az measured clockwise from true
            north. Integrating twice gives the deflection:
                d_vert = omega * cos(lat) * sin(az) * v * tof^2
                       = omega * cos(lat) * sin(az) * range * tof
            Positive d_vert means the bullet lands higher than it would
            in a non-rotating frame; it is added to the drop field with
            the same sign convention as other vertical corrections.
        """
        lat = math.radians(self.conditions.latitude_deg)
        az = math.radians(self.conditions.azimuth_deg)
        omega = self.EARTH_ROTATION_RAD_S
        horiz = omega * range_m * math.sin(lat) * tof_s
        vert = omega * range_m * math.cos(lat) * math.sin(az) * tof_s
        return vert, horiz

    # --- Integrator --------------------------------------------------------

    def _derivatives(self, state: Tuple[float, float, float, float, float, float],
                     wind_x: float, wind_z: float,
                     g_x: float, g_y: float) -> Tuple[float, float, float, float, float, float]:
        """Return dstate/dt for 6-state (x, y, z, vx, vy, vz)."""
        _, _, _, vx, vy, vz = state
        v_rel_x = vx - wind_x
        v_rel_z = vz - wind_z
        v_rel = math.sqrt(v_rel_x * v_rel_x + vy * vy + v_rel_z * v_rel_z)
        mach = v_rel / self._sos if self._sos > 0 else 0.0
        if v_rel > 0:
            a_drag = self._drag_accel(v_rel, mach)
            ax = -a_drag * v_rel_x / v_rel + g_x
            ay = -a_drag * vy / v_rel + g_y
            az = -a_drag * v_rel_z / v_rel
        else:
            ax, ay, az = g_x, g_y, 0.0
        return (vx, vy, vz, ax, ay, az)

    def _rk4_step(self, state, dt, wind_x, wind_z, g_x, g_y):
        k1 = self._derivatives(state, wind_x, wind_z, g_x, g_y)
        s2 = tuple(state[i] + 0.5 * dt * k1[i] for i in range(6))
        k2 = self._derivatives(s2, wind_x, wind_z, g_x, g_y)
        s3 = tuple(state[i] + 0.5 * dt * k2[i] for i in range(6))
        k3 = self._derivatives(s3, wind_x, wind_z, g_x, g_y)
        s4 = tuple(state[i] + dt * k3[i] for i in range(6))
        k4 = self._derivatives(s4, wind_x, wind_z, g_x, g_y)
        return tuple(
            state[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
            for i in range(6)
        )

    def _integrate_trajectory(self, bore_angle: float, max_range_m: float,
                              step_m: float = 10.0) -> List[TrajectoryPoint]:
        """
        Integrate the trajectory with adaptive-step RK4.
        Records points at exact multiples of step_m via linear interpolation
        between the two straddling integrator states.
        """
        rifle = self.conditions.rifle
        proj = self.conditions.projectile
        wind = self.conditions.wind

        v0 = rifle.muzzle_velocity_mps

        # Inclination: rotate gravity into the bore reference frame so
        # integration runs along the canted line-of-sight axis.
        theta = math.radians(self.conditions.elevation_angle_deg)
        g_x = -self.GRAVITY * math.sin(theta)
        g_y = -self.GRAVITY * math.cos(theta)

        vx = v0 * math.cos(bore_angle)
        vy = v0 * math.sin(bore_angle)
        vz = 0.0
        x, y, z = 0.0, -rifle.sight_height_m, 0.0
        t = 0.0

        wind_x = -wind.headwind_component
        wind_z = wind.crosswind_component

        state = (x, y, z, vx, vy, vz)
        trajectory: List[TrajectoryPoint] = []
        next_record_x = step_m  # First recorded point at x = step_m
        prev_state = state
        prev_t = 0.0

        max_time = 10.0
        while state[0] < max_range_m and t < max_time:
            v_rel_x = state[3] - wind_x
            v_rel_z = state[5] - wind_z
            v_rel = math.sqrt(v_rel_x * v_rel_x + state[4] * state[4] + v_rel_z * v_rel_z)
            mach = v_rel / self._sos if self._sos > 0 else 0.0

            # Adaptive step: finer near transonic and in the early high-speed
            # region, coarser in flat subsonic flight.
            if abs(mach - 1.0) < 0.2:
                dt = 0.00015
            elif mach > 1.5:
                dt = 0.0003
            else:
                dt = 0.0005

            prev_state = state
            prev_t = t
            state = self._rk4_step(state, dt, wind_x, wind_z, g_x, g_y)
            t += dt

            # Record points at exact step_m multiples via linear interpolation.
            while state[0] >= next_record_x and next_record_x <= max_range_m:
                dx = state[0] - prev_state[0]
                if dx <= 0:
                    break
                u = (next_record_x - prev_state[0]) / dx
                rec = tuple(prev_state[i] + u * (state[i] - prev_state[i]) for i in range(6))
                rec_t = prev_t + u * (t - prev_t)
                v_total = math.sqrt(rec[3] ** 2 + rec[4] ** 2 + rec[5] ** 2)
                # Mach at record point (use v_rel for consistency with drag)
                rv_rel_x = rec[3] - wind_x
                rv_rel_z = rec[5] - wind_z
                rv_rel = math.sqrt(rv_rel_x ** 2 + rec[4] ** 2 + rv_rel_z ** 2)
                rec_mach = rv_rel / self._sos if self._sos > 0 else 0.0
                energy = 0.5 * proj.mass_kg * v_total * v_total
                trajectory.append(TrajectoryPoint(
                    time_s=rec_t,
                    range_m=next_record_x,
                    drop_m=rec[1],
                    windage_m=rec[2],
                    velocity_mps=v_total,
                    energy_j=energy,
                    mach=rec_mach,
                ))
                next_record_x += step_m

        return trajectory

    # --- Zero finding ------------------------------------------------------

    def _find_zero_angle(self, zero_range_m: float) -> float:
        """Iteratively find the bore elevation angle that zeros at zero_range_m."""
        sight_height = self.conditions.rifle.sight_height_m
        v0 = self.conditions.rifle.muzzle_velocity_mps

        t_flight = zero_range_m / v0
        drop_simple = 0.5 * self.GRAVITY * t_flight ** 2
        angle = math.atan((drop_simple + sight_height) / zero_range_m)

        for _ in range(12):
            trajectory = self._integrate_trajectory(
                angle, zero_range_m + 20.0, step_m=5.0
            )
            drop_at_zero = None
            for pt in trajectory:
                if pt.range_m >= zero_range_m:
                    drop_at_zero = pt.drop_m
                    break
            if drop_at_zero is None:
                if trajectory:
                    drop_at_zero = trajectory[-1].drop_m
                else:
                    break
            # We want drop_at_zero == 0 (bullet crosses the sight line).
            error = -drop_at_zero
            correction = math.atan(error / zero_range_m)
            angle += correction * 0.7
            if abs(error) < 0.0001:
                break

        return angle

    # --- Top-level solve ---------------------------------------------------

    def solve(self, target_range_m: float, step_m: float = 10.0) -> BallisticSolution:
        zero_range = self.conditions.rifle.zero_range_m
        zero_angle = self._find_zero_angle(zero_range)

        max_range = max(target_range_m + 50.0, zero_range + 50.0)
        trajectory = self._integrate_trajectory(zero_angle, max_range, step_m)

        # Target-range corrections
        target_pt = None
        for pt in trajectory:
            if pt.range_m >= target_range_m:
                target_pt = pt
                break
        if target_pt is not None:
            tof = target_pt.time_s
            spin_drift = self._spin_drift_m(tof)
            coriolis_v, coriolis_h = self._coriolis_effect(tof, target_range_m)
        else:
            spin_drift = 0.0
            coriolis_v = coriolis_h = 0.0

        sg = self._miller_stability()
        aj_mrad = self._aero_jump_mrad()

        # Apply per-point corrections: spin drift + Coriolis + aerodynamic jump.
        # Aerodynamic jump is a muzzle-born angle, so it integrates linearly
        # with range (offset = aj_mrad * range / 1000).
        for pt in trajectory:
            sd = self._spin_drift_m(pt.time_s)
            cv, ch = self._coriolis_effect(pt.time_s, pt.range_m)
            pt.windage_m += sd + ch
            pt.drop_m += cv + (aj_mrad / 1000.0) * pt.range_m

        # Cant: post-process 2D rotation of (drop, windage) into the canted
        # scope frame. phi positive = rifle rolled right (scope top tilts right).
        phi = math.radians(self.conditions.cant_angle_deg)
        if phi != 0.0:
            cos_p = math.cos(phi)
            sin_p = math.sin(phi)
            for pt in trajectory:
                d = pt.drop_m
                w = pt.windage_m
                pt.drop_m = d * cos_p - w * sin_p
                pt.windage_m = d * sin_p + w * cos_p

        return BallisticSolution(
            trajectory=trajectory,
            zero_angle_mrad=zero_angle * 1000.0,
            spin_drift_m=spin_drift,
            coriolis_vertical_m=coriolis_v,
            coriolis_horizontal_m=coriolis_h,
            stability_factor=sg,
            aero_jump_mrad=aj_mrad,
        )


# Convenience wrapper --------------------------------------------------------

def calculate_solution(
    muzzle_velocity_mps: float,
    bc_g7: Optional[float],
    mass_grains: float,
    diameter_inches: float,
    zero_range_m: float,
    target_range_m: float,
    temperature_c: float = 15.0,
    pressure_mbar: float = 1013.25,
    humidity_pct: float = 50.0,
    altitude_m: float = 0.0,
    wind_speed_mps: float = 0.0,
    wind_direction_deg: float = 90.0,
    latitude_deg: float = 41.7,
    azimuth_deg: float = 0.0,
    bc_g1: Optional[float] = None,
    bullet_length_in: float = 1.0,
    twist_rate_inches: float = 10.0,
    twist_direction: str = "right",
    sight_height_mm: float = 40.0,
    elevation_angle_deg: float = 0.0,
    cant_angle_deg: float = 0.0,
    bc_segments: Optional[List[Tuple[float, float]]] = None,
    drag_curve: Optional[DragCurve] = None,
) -> BallisticSolution:
    """Quick calculation with minimal setup (kwargs-first for cache keying)."""
    projectile = Projectile(
        mass_grains=mass_grains,
        diameter_inches=diameter_inches,
        bc_g1=bc_g1,
        bc_g7=bc_g7,
        length_inches=bullet_length_in,
        bc_segments=bc_segments,
        drag_curve=drag_curve,
    )
    rifle = Rifle(
        muzzle_velocity_mps=muzzle_velocity_mps,
        zero_range_m=zero_range_m,
        sight_height_mm=sight_height_mm,
        twist_rate_inches=twist_rate_inches,
        twist_direction=twist_direction,
    )
    atmosphere = Atmosphere(AtmosphericConditions(
        temperature_c=temperature_c,
        pressure_mbar=pressure_mbar,
        humidity_pct=humidity_pct,
        altitude_m=altitude_m,
    ))
    wind = Wind(speed_mps=wind_speed_mps, direction_deg=wind_direction_deg)

    conditions = ShootingConditions(
        projectile=projectile,
        rifle=rifle,
        atmosphere=atmosphere,
        wind=wind,
        latitude_deg=latitude_deg,
        azimuth_deg=azimuth_deg,
        elevation_angle_deg=elevation_angle_deg,
        cant_angle_deg=cant_angle_deg,
    )
    return BallisticSolver(conditions).solve(target_range_m)


if __name__ == "__main__":
    solution = calculate_solution(
        muzzle_velocity_mps=792,  # ~2600 fps (.308 175 SMK reference)
        bc_g7=0.243,
        mass_grains=175,
        diameter_inches=0.308,
        zero_range_m=100,
        target_range_m=800,
        wind_speed_mps=4.47,  # 10 mph
        wind_direction_deg=90,
        bullet_length_in=1.24,
        twist_rate_inches=11.25,
    )
    print(f"SG={solution.stability_factor:.2f}  AJ={solution.aero_jump_mrad:.3f} mrad")
    print(f"{'Range':>6} {'Drop(m)':>8} {'Drop(MRAD)':>10} {'Wind(MRAD)':>10} "
          f"{'Vel':>6} {'ToF':>6}")
    for pt in solution.trajectory:
        if int(pt.range_m) % 100 == 0:
            print(f"{pt.range_m:>6.0f} {pt.drop_m:>8.3f} {pt.drop_mrad:>10.2f} "
                  f"{pt.windage_mrad:>10.2f} {pt.velocity_mps:>6.0f} {pt.time_s:>6.3f}")

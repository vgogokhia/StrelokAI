"""
Muzzle-velocity truing.

"Truing" is the standard long-range technique of adjusting the muzzle
velocity used by the ballistic model until the predicted drop at a
known range matches the *observed* drop (the elevation dialed or
held to get an actual impact). Published chronograph numbers are
usually off by 5-30 fps and that error grows non-linearly with range,
so truing is how serious shooters get sub-MRAD predictions past 600m.

The back-solver uses a secant (bounded) search on MV because drop(MV)
is smooth and monotonic over any reasonable MV window. Convergence is
typically 4-6 solver calls.
"""
from typing import Optional

from ballistics.solver import calculate_solution


def true_muzzle_velocity(
    *,
    observed_drop_mrad: float,
    observed_range_m: float,
    # All the usual solver inputs — mirrors calculate_solution for clarity:
    initial_mv_guess_mps: float,
    bc_g7: Optional[float],
    mass_grains: float,
    diameter_inches: float,
    zero_range_m: float,
    temperature_c: float = 15.0,
    pressure_mbar: float = 1013.25,
    humidity_pct: float = 50.0,
    wind_speed_mps: float = 0.0,
    wind_direction_deg: float = 90.0,
    bc_g1: Optional[float] = None,
    bullet_length_in: float = 1.0,
    twist_rate_inches: float = 10.0,
    twist_direction: str = "right",
    sight_height_mm: float = 40.0,
    # Tolerances
    tolerance_mrad: float = 0.01,
    max_iterations: int = 20,
) -> dict:
    """
    Back-solve the muzzle velocity that produces ``observed_drop_mrad``
    at ``observed_range_m``.

    Returns
    -------
    dict with keys:
        trued_mv_mps   — solved muzzle velocity (m/s)
        iterations     — number of solver calls
        residual_mrad  — drop error at convergence
        converged      — bool
    """
    def _drop_at(mv: float) -> float:
        sol = calculate_solution(
            muzzle_velocity_mps=mv,
            bc_g7=bc_g7,
            bc_g1=bc_g1,
            mass_grains=mass_grains,
            diameter_inches=diameter_inches,
            zero_range_m=zero_range_m,
            target_range_m=observed_range_m,
            temperature_c=temperature_c,
            pressure_mbar=pressure_mbar,
            humidity_pct=humidity_pct,
            wind_speed_mps=wind_speed_mps,
            wind_direction_deg=wind_direction_deg,
            bullet_length_in=bullet_length_in,
            twist_rate_inches=twist_rate_inches,
            twist_direction=twist_direction,
            sight_height_mm=sight_height_mm,
        )
        pt = sol.at_range(observed_range_m)
        if pt is None:
            raise RuntimeError("Solver returned no point at observed range")
        return pt.drop_mrad

    # Secant search. Bracket with two initial guesses ±3% from the user's
    # published MV — truing corrections are almost never larger than this.
    mv_lo = initial_mv_guess_mps * 0.97
    mv_hi = initial_mv_guess_mps * 1.03
    drop_lo = _drop_at(mv_lo)
    drop_hi = _drop_at(mv_hi)

    iterations = 2
    mv = initial_mv_guess_mps
    residual = 0.0
    converged = False

    for _ in range(max_iterations):
        # If the bracket collapsed (should not happen with sane inputs),
        # bail out with whichever side is closer.
        if abs(drop_hi - drop_lo) < 1e-9:
            mv = (mv_lo + mv_hi) / 2.0
            break

        # Secant step toward the observed drop.
        slope = (drop_hi - drop_lo) / (mv_hi - mv_lo)
        mv = mv_hi + (observed_drop_mrad - drop_hi) / slope

        # Clamp to a sane window (±10% of initial guess) to avoid
        # runaway if the user enters nonsense.
        mv = max(initial_mv_guess_mps * 0.90, min(mv, initial_mv_guess_mps * 1.10))

        drop = _drop_at(mv)
        iterations += 1
        residual = drop - observed_drop_mrad

        if abs(residual) < tolerance_mrad:
            converged = True
            break

        # Shift the bracket: drop the older endpoint.
        mv_lo, drop_lo = mv_hi, drop_hi
        mv_hi, drop_hi = mv, drop

    return {
        "trued_mv_mps": mv,
        "iterations": iterations,
        "residual_mrad": residual,
        "converged": converged,
    }

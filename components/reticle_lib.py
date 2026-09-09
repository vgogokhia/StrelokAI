"""
ballistics.ge - Parametric reticle library.

Each reticle is a spec (unit, hash spacing, tree layout...) rendered to an
SVG by one generic routine, with the holdover dot placed in *reticle units*.
The drawings are schematic approximations of the real reticles — spacing
and subtension are correct, cosmetics are simplified.

SFP scaling: on a second-focal-plane scope the reticle only subtends its
nominal value at the calibrated magnification. At another magnification
each mark subtends nominal * (calibrated / current), so a hold of H mrad
lands at H * current / calibrated marks from centre.
Version: 1.0.0
"""
from dataclasses import dataclass, field
from typing import List, Optional

MRAD_TO_MOA = 3.43775


@dataclass
class ReticleSpec:
    name: str
    unit: str                      # "MRAD" | "MOA"
    view: float                    # half-span shown, in reticle units
    major: float                   # major hash spacing (units)
    minor: float = 0.0             # minor hash spacing (0 = none)
    dots: bool = False             # dots instead of hashes on major marks (Mil-Dot)
    labels_every: float = 0.0      # label major marks every N units (0 = none)
    tree_rows: float = 0.0         # christmas-tree rows every N units below centre (0 = none)
    tree_cols: float = 0.0         # hash spacing along each tree row
    tree_width_per_unit: float = 0.0   # half-width growth per unit of drop (0 = full grid)
    grid_full: bool = False        # Horus-style full grid in the lower half
    note: str = ""


RETICLES: List[ReticleSpec] = [
    ReticleSpec("MIL-Dot", "MRAD", 10, 1.0, 0.0, dots=True, labels_every=5,
                note="Classic 1-mil dots (Leupold, Bushnell, many others)."),
    ReticleSpec("TMR / Mil hash", "MRAD", 10, 1.0, 0.5, labels_every=5,
                note="Leupold TMR, Vortex EBR-1, Athlon APMR — 0.5 mil hashes."),
    ReticleSpec("Vortex EBR-7C (MRAD)", "MRAD", 10, 1.0, 0.2, labels_every=2,
                tree_rows=1.0, tree_cols=0.2, tree_width_per_unit=0.5,
                note="Razor Gen II/III, Viper PST Gen II. 0.2 mil detail, tree below."),
    ReticleSpec("Mil-C / Mil-R", "MRAD", 10, 1.0, 0.5, labels_every=2,
                tree_rows=1.0, tree_cols=0.5, tree_width_per_unit=0.4,
                note="Nightforce Mil-C / Mil-R, Bushnell G3 style tree."),
    ReticleSpec("Horus-style grid (H59/TREMOR)", "MRAD", 10, 1.0, 0.2, labels_every=1,
                tree_rows=1.0, tree_cols=1.0, grid_full=True,
                note="Full 1-mil grid below centre (H59, H32, TREMOR3 approximation)."),
    ReticleSpec("MSR / P4 fine (MRAD)", "MRAD", 10, 1.0, 0.2, labels_every=1,
                note="Schmidt & Bender MSR/P4F, Kahles MSR/SKMR. 0.2 mil hashes."),
    ReticleSpec("MOA hash (MOAR / EBR-2C MOA)", "MOA", 30, 5.0, 1.0, labels_every=10,
                note="Nightforce MOAR, Vortex EBR-2C MOA, Athlon APLR MOA. 1 MOA hashes."),
    ReticleSpec("MOA tree (EBR-7C MOA / TMOA)", "MOA", 30, 5.0, 1.0, labels_every=10,
                tree_rows=5.0, tree_cols=1.0, tree_width_per_unit=0.5,
                note="Vortex EBR-7C MOA, Leupold TMOA. 1 MOA detail, tree below."),
    ReticleSpec("Duplex / plain crosshair", "MRAD", 10, 0.0, 0.0,
                note="No marks — hold is shown as a red dot only."),
]

BY_NAME = {r.name: r for r in RETICLES}


def hold_in_reticle_units(hold_mrad: float, spec: ReticleSpec, sfp_scale: float = 1.0) -> float:
    """Convert a true angular hold (mrad) to marks on this reticle."""
    v = hold_mrad * (MRAD_TO_MOA if spec.unit == "MOA" else 1.0)
    return v * sfp_scale


def render_svg(spec: ReticleSpec, x_units: float, y_units: float, size: int = 480,
               show_target_ring: Optional[float] = None) -> str:
    """SVG of the reticle with the hold dot at (x, y) reticle units.
    y grows downward (positive = hold below centre)."""
    c = size / 2
    k = (size / 2 - 12) / spec.view     # px per unit
    X = lambda u: c + u * k
    Y = lambda u: c + u * k
    col, dim, lab = "#9c9", "#575", "#6a6"
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" style="background:#0a0a0a;">',
        f'<circle cx="{c}" cy="{c}" r="{size/2 - 2}" fill="none" stroke="#1a1a1a" stroke-width="2"/>',
        f'<line x1="8" y1="{c}" x2="{size-8}" y2="{c}" stroke="{col}" stroke-width="1.2"/>',
        f'<line x1="{c}" y1="8" x2="{c}" y2="{size-8}" stroke="{col}" stroke-width="1.2"/>',
    ]
    def hashes(step, length, width, both_axes=True):
        if step <= 0:
            return
        n = int(spec.view // step)
        for i in range(-n, n + 1):
            u = i * step
            if abs(u) < 1e-9:
                continue
            p.append(f'<line x1="{X(u)}" y1="{c-length}" x2="{X(u)}" y2="{c+length}" stroke="{col}" stroke-width="{width}"/>')
            p.append(f'<line x1="{c-length}" y1="{Y(u)}" x2="{c+length}" y2="{Y(u)}" stroke="{col}" stroke-width="{width}"/>')

    if spec.minor:
        hashes(spec.minor, 3, 1)
    if spec.major:
        if spec.dots:
            n = int(spec.view // spec.major)
            for i in range(-n, n + 1):
                u = i * spec.major
                if abs(u) < 1e-9:
                    continue
                p.append(f'<circle cx="{X(u)}" cy="{c}" r="2.6" fill="{col}"/>')
                p.append(f'<circle cx="{c}" cy="{Y(u)}" r="2.6" fill="{col}"/>')
        else:
            hashes(spec.major, 7, 1.4)
    if spec.labels_every and spec.major:
        n = int(spec.view // spec.labels_every)
        for i in range(1, n + 1):
            u = i * spec.labels_every
            t = f"{u:g}"
            p.append(f'<text x="{X(u)+3}" y="{c-9}" fill="{lab}" font-size="10" font-family="monospace">{t}</text>')
            p.append(f'<text x="{X(-u)+3}" y="{c-9}" fill="{lab}" font-size="10" font-family="monospace">{t}</text>')
            p.append(f'<text x="{c+8}" y="{Y(u)+4}" fill="{lab}" font-size="10" font-family="monospace">{t}</text>')
            p.append(f'<text x="{c+8}" y="{Y(-u)+4}" fill="{lab}" font-size="10" font-family="monospace">{t}</text>')

    # tree / grid in the lower half
    if spec.tree_rows:
        rows = int(spec.view // spec.tree_rows)
        for r in range(1, rows + 1):
            u = r * spec.tree_rows
            half = spec.view if spec.grid_full else min(spec.view, u * spec.tree_width_per_unit + spec.tree_cols)
            ncol = int(half // spec.tree_cols)
            for j in range(-ncol, ncol + 1):
                x = j * spec.tree_cols
                if abs(x) < 1e-9:
                    continue
                big = abs(j * spec.tree_cols - round(j * spec.tree_cols / spec.major) * spec.major) < 1e-6 if spec.major else False
                if spec.grid_full:
                    p.append(f'<circle cx="{X(x)}" cy="{Y(u)}" r="{1.6 if big else 1.0}" fill="{dim}"/>')
                else:
                    ln = 4 if big else 2.2
                    p.append(f'<line x1="{X(x)}" y1="{Y(u)-ln}" x2="{X(x)}" y2="{Y(u)+ln}" stroke="{dim}" stroke-width="1"/>')
            if not spec.grid_full:
                p.append(f'<line x1="{X(-half)}" y1="{Y(u)}" x2="{X(half)}" y2="{Y(u)}" stroke="{dim}" stroke-width="0.6"/>')

    # optional target ring (e.g. 45 cm torso at range) around the hold point
    if show_target_ring:
        p.append(f'<circle cx="{X(x_units)}" cy="{Y(y_units)}" r="{show_target_ring*k/2}" fill="none" stroke="#fa4" stroke-width="1" stroke-dasharray="3,3"/>')

    # hold dot (clamped to the view so it stays visible)
    xv = max(-spec.view, min(spec.view, x_units))
    yv = max(-spec.view, min(spec.view, y_units))
    off = (abs(x_units) > spec.view) or (abs(y_units) > spec.view)
    opacity = ' opacity="0.5"' if off else ''
    p.append(f'<circle cx="{X(xv)}" cy="{Y(yv)}" r="6" fill="#ff3030" stroke="#fff" stroke-width="1.5"{opacity}/>')
    p.append(f'<line x1="{X(xv)-10}" y1="{Y(yv)}" x2="{X(xv)+10}" y2="{Y(yv)}" stroke="#ff3030" stroke-width="1"/>')
    p.append(f'<line x1="{X(xv)}" y1="{Y(yv)-10}" x2="{X(xv)}" y2="{Y(yv)+10}" stroke="#ff3030" stroke-width="1"/>')
    p.append('</svg>')
    return ''.join(p)

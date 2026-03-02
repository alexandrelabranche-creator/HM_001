#!/usr/bin/env python3
"""Heatmap renderer lib for Doppelvelt / Rothmorgil.

Reads a state JSON containing:
- levels: dict[str,int] 0..6
- city_positions_norm: dict[str, {x_norm,y_norm}]
- render_standard: {sigma, alpha_min, alpha_max, gamma, floor, alpha_gamma?}

Renders:
- overlay PNG (RGBA)
- on_map PNG (RGBA composited)
- optional PDFs
"""

from __future__ import annotations

import json
import os
from typing import Dict, Tuple, Optional

import numpy as np
from PIL import Image

# 5-color palette: blue->cyan->green->yellow->red
STOPS = np.array(
    [
        [0.0, 0, 0, 255],
        [0.25, 0, 255, 255],
        [0.50, 0, 255, 0],
        [0.75, 255, 255, 0],
        [1.0, 255, 0, 0],
    ],
    dtype=np.float32,
)

def _map_5color(t: np.ndarray) -> np.ndarray:
    t = np.clip(t, 0, 1).astype(np.float32)
    seg = np.minimum((t / 0.25).astype(np.int32), 3)
    t0 = STOPS[seg, 0]
    t1 = STOPS[seg + 1, 0]
    f = (t - t0) / (t1 - t0 + 1e-6)
    c0 = STOPS[seg, 1:4]
    c1 = STOPS[seg + 1, 1:4]
    rgb = c0 + (c1 - c0) * f[..., None]
    return rgb.astype(np.uint8)

def _gaussian_kernel(xx: np.ndarray, yy: np.ndarray, x0: float, y0: float, sigma: float) -> np.ndarray:
    d2 = (xx - x0) ** 2 + (yy - y0) ** 2
    return np.exp(-d2 / (2 * sigma * sigma)).astype(np.float32)

def build_city_px_from_norm(
    city_positions_norm: Dict[str, Dict[str, float]],
    W: int,
    H: int,
    *,
    filter_to_levels: Optional[Dict[str, int]] = None,
) -> Dict[str, Tuple[float, float]]:
    out: Dict[str, Tuple[float, float]] = {}
    for name, p in city_positions_norm.items():
        if filter_to_levels is not None and name not in filter_to_levels:
            continue
        try:
            out[name] = (float(p["x_norm"]) * W, float(p["y_norm"]) * H)
        except Exception:
            continue
    return out

def heat_saturating(
    *,
    levels: Dict[str, int],
    city_px: Dict[str, Tuple[float, float]],
    W: int,
    H: int,
    sigma: float,
) -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    prod = np.ones((H, W), dtype=np.float32)
    for name, lvl in levels.items():
        if lvl <= 0:
            continue
        if name not in city_px:
            continue
        x, y = city_px[name]
        w = min(1.0, max(0.0, float(lvl) / 6.0))
        K = _gaussian_kernel(xx, yy, x, y, sigma)
        prod *= (1.0 - np.clip(w * K, 0, 1))
    heat = 1.0 - prod
    heat = heat / (heat.max() + 1e-6)
    return heat

def render_overlay(
    heat: np.ndarray,
    *,
    alpha_min: int = 90,
    alpha_max: int = 235,
    gamma: float = 1.35,
    floor: float = 0.10,
    alpha_gamma: float = 1.0,
) -> Image.Image:
    """Render RGBA overlay.

    - gamma controls the COLOR curve (how quickly heat turns red)
    - alpha_gamma controls the OPACITY curve (boost low-level visibility without darkening reds)
    """
    heat = np.clip(heat, 0, 1)
    heat_c = heat ** float(gamma)

    # Color mapping
    t = float(floor) + (1.0 - float(floor)) * heat_c
    rgb = _map_5color(t)

    # Opacity mapping (separate curve)
    alpha_curve = np.clip(heat_c, 0, 1) ** float(alpha_gamma)
    a = (int(alpha_min) + (int(alpha_max) - int(alpha_min)) * alpha_curve).astype(np.uint8)

    rgba = np.dstack([rgb, a])
    return Image.fromarray(rgba)

def render_from_state(
    state_path: str,
    map_path: str,
    out_dir: str,
    out_tag: str,
    *,
    write_pdf: bool = True,
) -> Dict[str, str]:
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    base = Image.open(map_path).convert("RGBA")
    W, H = base.size

    levels = state.get("levels", {})
    pos_norm = state.get("city_positions_norm", {})
    rs = state.get("render_standard", {})

    city_px = build_city_px_from_norm(pos_norm, W, H, filter_to_levels=levels)

    heat = heat_saturating(
        levels=levels,
        city_px=city_px,
        W=W,
        H=H,
        sigma=float(rs.get("sigma", 95)),
    )

    overlay = render_overlay(
        heat,
        alpha_min=int(rs.get("alpha_min", 90)),
        alpha_max=int(rs.get("alpha_max", 235)),
        gamma=float(rs.get("gamma", 1.35)),
        floor=float(rs.get("floor", 0.10)),
        alpha_gamma=float(rs.get("alpha_gamma", 1.0)),
    )

    onmap = Image.alpha_composite(base, overlay)

    os.makedirs(out_dir, exist_ok=True)
    ov_path = os.path.join(out_dir, f"Rothmorgil_heatmap_overlay_{out_tag}.png")
    mp_path = os.path.join(out_dir, f"Rothmorgil_heatmap_on_map_{out_tag}.png")
    overlay.save(ov_path)
    onmap.save(mp_path)

    out = {"overlay_png": ov_path, "on_map_png": mp_path}

    if write_pdf:
        ov_pdf = os.path.join(out_dir, f"Rothmorgil_heatmap_overlay_{out_tag}.pdf")
        mp_pdf = os.path.join(out_dir, f"Rothmorgil_heatmap_on_map_{out_tag}.pdf")
        Image.open(ov_path).convert("RGB").save(ov_pdf, "PDF", resolution=300.0)
        Image.open(mp_path).convert("RGB").save(mp_pdf, "PDF", resolution=300.0)
        out["overlay_pdf"] = ov_pdf
        out["on_map_pdf"] = mp_pdf

    return out

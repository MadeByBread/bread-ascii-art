"""Shared helpers for procedural ASCII animations."""

from __future__ import annotations

import math
import random
from typing import Sequence

from .converter import Cell, CellGrid, DEFAULT_CHARSET, grid_size, parse_aspect
from .render import font_char_aspect

RGB = tuple[int, int, int]

# Retro terminal / depth palettes (inspired by asciiart.eu animation vibes).
PALETTES: dict[str, list[RGB]] = {
    "matrix": [(10, 40, 10), (20, 120, 40), (40, 200, 70), (160, 255, 160)],
    "fire": [(20, 0, 0), (120, 20, 0), (220, 80, 10), (255, 180, 40), (255, 250, 200)],
    "neon": [(20, 10, 40), (80, 40, 180), (40, 200, 255), (255, 80, 200), (255, 255, 180)],
    "ember": [(15, 5, 5), (90, 25, 10), (180, 60, 20), (240, 140, 50)],
    "ocean": [(5, 15, 40), (10, 60, 120), (30, 140, 200), (140, 220, 255)],
    "sunset": [(30, 10, 40), (140, 40, 80), (220, 90, 50), (255, 180, 70)],
    "mono": [(30, 30, 30), (90, 90, 90), (160, 160, 160), (230, 230, 230)],
    "galaxy": [(5, 5, 25), (40, 20, 80), (120, 60, 180), (255, 180, 255), (255, 255, 220)],
    "gold": [(20, 12, 0), (100, 60, 10), (200, 140, 30), (255, 220, 100)],
}


def empty_grid(cols: int, rows: int, bg: RGB = (0, 0, 0)) -> CellGrid:
    return [[(" ", bg) for _ in range(cols)] for _ in range(rows)]


def set_cell(grid: CellGrid, x: int, y: int, ch: str, color: RGB) -> None:
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = (ch, color)


def lerp_color(a: RGB, b: RGB, t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def palette_color(palette: Sequence[RGB], t: float) -> RGB:
    if not palette:
        return (200, 200, 200)
    if len(palette) == 1:
        return palette[0]
    t = max(0.0, min(1.0, t))
    scaled = t * (len(palette) - 1)
    i = int(scaled)
    if i >= len(palette) - 1:
        return palette[-1]
    return lerp_color(palette[i], palette[i + 1], scaled - i)


def char_from_intensity(t: float, charset: str = DEFAULT_CHARSET) -> str:
    if t <= 0.02:
        return " "
    n = len(charset) - 1
    return charset[max(1, min(n, round(t * n)))]


def resolve_grid(
    width: int = 120,
    aspect: float | str = "16:9",
    char_aspect: float | None = None,
    font_size: int = 12,
) -> tuple[int, int, float]:
    ca = char_aspect if char_aspect is not None else (font_char_aspect(font_size) or 0.72)
    cols, rows = grid_size(width, parse_aspect(aspect), ca)
    return cols, rows, ca


def clone_grid(grid: CellGrid) -> CellGrid:
    return [row[:] for row in grid]

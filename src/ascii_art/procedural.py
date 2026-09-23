"""Procedural ASCII animation styles inspired by asciiart.eu/animations."""

from __future__ import annotations

import math
import random
from typing import Callable

from .converter import CellGrid, DEFAULT_CHARSET
from .effects import (
    PALETTES,
    RGB,
    char_from_intensity,
    empty_grid,
    palette_color,
    set_cell,
)

GeneratorFn = Callable[..., list[tuple[CellGrid, int]]]


def _rng(seed: int | None) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Individual styles
# ---------------------------------------------------------------------------


def starfield(
    cols: int,
    rows: int,
    *,
    frames: int = 36,
    duration: int = 50,
    seed: int | None = 0,
    density: float = 0.012,
    speed: float = 1.0,
    warp: bool = False,
    palette: str = "neon",
    charset: str = DEFAULT_CHARSET,
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["neon"])
    n = max(8, int(cols * rows * density))
    stars = [
        {
            "x": rng.uniform(-1, 1),
            "y": rng.uniform(-1, 1),
            "z": rng.uniform(0.15, 1.0),
            "c": rng.choice(charset[3:]),
        }
        for _ in range(n)
    ]
    cx, cy = cols / 2, rows / 2
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        for s in stars:
            z = s["z"] - (f * 0.035 * speed) % 0.95
            if z <= 0.05:
                z += 0.95
            k = (0.55 / z) if warp else (0.35 / z)
            x = int(cx + s["x"] * k * cols * 0.5)
            y = int(cy + s["y"] * k * rows * 0.5)
            t = 1.0 - z
            set_cell(grid, x, y, s["c"] if t > 0.4 else ".", palette_color(colors, t))
        out.append((grid, duration))
    return out


def matrix(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 45,
    seed: int | None = 0,
    density: float = 0.55,
    speed: float = 1.0,
    glitch: float = 0.02,
    palette: str = "matrix",
    charset: str = "01アイウエオカキクケコabcdefghijklmnopqrstuvwxyz#$%&",
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["matrix"])
    drops = []
    for x in range(cols):
        if rng.random() < density:
            drops.append(
                {
                    "x": x,
                    "y": rng.uniform(-rows, rows),
                    "len": rng.randint(6, max(8, rows // 2)),
                    "spd": rng.uniform(0.6, 1.6) * speed,
                }
            )
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        for d in drops:
            head = d["y"] + f * d["spd"]
            for i in range(d["len"]):
                y = int(head - i)
                if 0 <= y < rows:
                    t = 1.0 - i / d["len"]
                    ch = rng.choice(charset)
                    if rng.random() < glitch:
                        ch = rng.choice("#@$*")
                    set_cell(grid, d["x"], y, ch, palette_color(colors, t))
        out.append((grid, duration))
    return out


def fire(
    cols: int,
    rows: int,
    *,
    frames: int = 36,
    duration: int = 50,
    seed: int | None = 0,
    wind: float = 0.35,
    intensity: float = 1.0,
    palette: str = "fire",
    charset: str = " .:+*#$&@",
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["fire"])
    heat = [[0.0] * cols for _ in range(rows)]
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        # Ignite bottom row
        for x in range(cols):
            heat[rows - 1][x] = rng.random() * intensity
            if rng.random() < 0.15 * intensity:
                heat[rows - 1][x] = 1.0
        # Rise + cool
        for y in range(rows - 2, -1, -1):
            for x in range(cols):
                src_x = x + int(rng.uniform(-1, 1) + wind)
                src_x = max(0, min(cols - 1, src_x))
                below = (
                    heat[y + 1][src_x]
                    + heat[y + 1][max(0, src_x - 1)]
                    + heat[y + 1][min(cols - 1, src_x + 1)]
                ) / 3.0
                heat[y][x] = max(0.0, below - rng.uniform(0.02, 0.08))
        grid = empty_grid(cols, rows, bg)
        for y in range(rows):
            for x in range(cols):
                t = heat[y][x]
                if t > 0.05:
                    set_cell(
                        grid,
                        x,
                        y,
                        char_from_intensity(t, charset),
                        palette_color(colors, t),
                    )
        out.append((grid, duration))
    return out


def fireworks(
    cols: int,
    rows: int,
    *,
    frames: int = 48,
    duration: int = 40,
    seed: int | None = 0,
    bursts: int = 5,
    palette: str = "neon",
    charset: str = ".:*+oO@#",
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["neon"])
    events = []
    for i in range(bursts):
        events.append(
            {
                "t0": int(i * frames / bursts) + rng.randint(0, 4),
                "cx": rng.randint(cols // 6, cols - cols // 6),
                "cy": rng.randint(rows // 8, rows // 2),
                "n": rng.randint(18, 36),
                "life": rng.randint(12, 20),
                "hue": rng.random(),
            }
        )
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        for e in events:
            age = f - e["t0"]
            if age < 0 or age >= e["life"]:
                continue
            # launch trail
            if age < 4:
                y = int(rows - 1 - age * (rows - e["cy"]) / 4)
                set_cell(grid, e["cx"], y, "|", palette_color(colors, 0.7))
                continue
            explode_age = age - 4
            progress = explode_age / max(1, e["life"] - 4)
            radius = progress * min(cols, rows) * 0.28
            for k in range(e["n"]):
                ang = (k / e["n"]) * math.tau + e["hue"]
                x = int(e["cx"] + math.cos(ang) * radius)
                y = int(e["cy"] + math.sin(ang) * radius * 0.55 + explode_age * 0.35)
                t = 1.0 - progress
                set_cell(
                    grid,
                    x,
                    y,
                    charset[min(len(charset) - 1, int(t * (len(charset) - 1)))],
                    palette_color(colors, (t + e["hue"]) % 1.0),
                )
        out.append((grid, duration))
    return out


def plasma(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 50,
    seed: int | None = 0,
    scale: float = 1.0,
    speed: float = 1.0,
    palette: str = "neon",
    charset: str = DEFAULT_CHARSET,
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["neon"])
    phase = rng.random() * math.tau
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        t = f * 0.12 * speed + phase
        for y in range(rows):
            for x in range(cols):
                v = (
                    math.sin((x / 8.0) * scale + t)
                    + math.sin((y / 6.0) * scale + t * 1.3)
                    + math.sin(((x + y) / 10.0) * scale + t * 0.7)
                    + math.sin(math.hypot(x - cols / 2, y - rows / 2) / 7.0 * scale - t)
                )
                n = (v + 4) / 8.0
                ch = char_from_intensity(n, charset)
                if ch != " ":
                    set_cell(grid, x, y, ch, palette_color(colors, n))
        out.append((grid, duration))
    return out


def rain(
    cols: int,
    rows: int,
    *,
    frames: int = 36,
    duration: int = 50,
    seed: int | None = 0,
    drops: int = 14,
    palette: str = "ocean",
    charset: str = " .:+*oO@",
    bg: RGB = (0, 5, 15),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["ocean"])
    centers = [
        {
            "x": rng.randint(2, cols - 3),
            "y": rng.randint(2, rows - 3),
            "t0": rng.randint(0, frames - 1),
            "max_r": rng.uniform(6, min(cols, rows) * 0.35),
        }
        for _ in range(drops)
    ]
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        for d in centers:
            age = (f - d["t0"]) % frames
            life = 16
            if age >= life:
                continue
            r = (age / life) * d["max_r"]
            for a in range(0, 360, 8):
                rad = math.radians(a)
                x = int(d["x"] + math.cos(rad) * r)
                y = int(d["y"] + math.sin(rad) * r * 0.55)
                t = 1.0 - age / life
                set_cell(grid, x, y, charset[min(len(charset) - 1, int(t * 5) + 1)], palette_color(colors, t))
        out.append((grid, duration))
    return out


def waves(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 45,
    seed: int | None = 0,
    wavelength: float = 10.0,
    thickness: float = 1.6,
    speed: float = 1.0,
    palette: str = "ocean",
    charset: str = " .:~-=+*#",
    bg: RGB = (0, 0, 10),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["ocean"])
    cx, cy = cols / 2 + rng.uniform(-cols * 0.1, cols * 0.1), rows / 2
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        t = f * 0.2 * speed
        for y in range(rows):
            for x in range(cols):
                dist = math.hypot(x - cx, (y - cy) * 1.7)
                v = abs(math.sin(dist / wavelength - t))
                band = math.exp(-((v) ** 2) * 8 / thickness)
                if band > 0.15:
                    set_cell(
                        grid,
                        x,
                        y,
                        char_from_intensity(band, charset),
                        palette_color(colors, band),
                    )
        out.append((grid, duration))
    return out


def bouncing(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 45,
    seed: int | None = 0,
    balls: int = 7,
    palette: str = "neon",
    charset: str = "oO0@",
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["neon"])
    objs = []
    for i in range(balls):
        objs.append(
            {
                "x": rng.uniform(1, cols - 2),
                "y": rng.uniform(1, rows - 2),
                "vx": rng.choice([-1, 1]) * rng.uniform(0.6, 1.4),
                "vy": rng.choice([-1, 1]) * rng.uniform(0.4, 1.1),
                "ch": rng.choice(charset),
                "hue": i / max(1, balls - 1),
            }
        )
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        for b in objs:
            x = b["x"] + b["vx"] * f
            y = b["y"] + b["vy"] * f
            # reflect into bounds
            period_x = (cols - 2) * 2
            period_y = (rows - 2) * 2
            rx = abs((x) % period_x)
            ry = abs((y) % period_y)
            if rx > cols - 2:
                rx = period_x - rx
            if ry > rows - 2:
                ry = period_y - ry
            set_cell(
                grid,
                int(rx) + 1,
                int(ry) + 1,
                b["ch"],
                palette_color(colors, 0.4 + 0.6 * b["hue"]),
            )
            # trail
            set_cell(
                grid,
                int(rx),
                int(ry) + 1,
                ".",
                palette_color(colors, 0.2 + 0.3 * b["hue"]),
            )
        out.append((grid, duration))
    return out


def kaleidoscope(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 50,
    seed: int | None = 0,
    segments: int = 8,
    speed: float = 1.0,
    palette: str = "galaxy",
    charset: str = DEFAULT_CHARSET,
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["galaxy"])
    cx, cy = cols / 2, rows / 2
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        rot = f * 0.08 * speed + rng.random() * 0  # stable per seed via phase below
        phase = (seed or 0) * 0.17
        for y in range(rows):
            for x in range(cols):
                dx, dy = x - cx, (y - cy) * 1.7
                ang = math.atan2(dy, dx) + rot + phase
                seg = abs((ang % (math.tau / segments)) - math.tau / (2 * segments))
                r = math.hypot(dx, dy)
                v = math.sin(r * 0.35 - f * 0.15 * speed) * math.cos(seg * 6)
                n = (v + 1) / 2
                if n > 0.35:
                    set_cell(
                        grid,
                        x,
                        y,
                        char_from_intensity(n, charset),
                        palette_color(colors, n),
                    )
        out.append((grid, duration))
    return out


def galaxy(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 50,
    seed: int | None = 0,
    arms: int = 3,
    speed: float = 1.0,
    palette: str = "galaxy",
    charset: str = " .:+*oO@",
    bg: RGB = (0, 0, 8),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["galaxy"])
    cx, cy = cols / 2, rows / 2
    stars = []
    for _ in range(int(cols * rows * 0.08)):
        stars.append(
            {
                "r": rng.uniform(0.5, min(cols, rows) * 0.48),
                "a": rng.uniform(0, math.tau),
                "arm": rng.randint(0, arms - 1),
                "ch": rng.choice(charset[2:]),
            }
        )
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        rot = f * 0.07 * speed
        for s in stars:
            a = s["a"] + rot + s["arm"] * (math.tau / arms) + s["r"] * 0.08
            x = int(cx + math.cos(a) * s["r"])
            y = int(cy + math.sin(a) * s["r"] * 0.55)
            t = 1.0 - s["r"] / (min(cols, rows) * 0.5)
            set_cell(grid, x, y, s["ch"], palette_color(colors, max(0.15, t)))
        # core
        for dy in range(-1, 2):
            for dx in range(-2, 3):
                set_cell(grid, int(cx) + dx, int(cy) + dy, "@", palette_color(colors, 0.95))
        out.append((grid, duration))
    return out


def donut(
    cols: int,
    rows: int,
    *,
    frames: int = 36,
    duration: int = 50,
    seed: int | None = 0,
    size: float = 1.0,
    speed: float = 1.0,
    palette: str = "gold",
    charset: str = " .,~:;=!+*#$@",
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    """Classic spinning torus projection."""
    _ = seed
    colors = PALETTES.get(palette, PALETTES["gold"])
    out: list[tuple[CellGrid, int]] = []
    R1, R2 = 1.0 * size, 2.0 * size
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        zbuf = [[0.0] * cols for _ in range(rows)]
        A = f * 0.12 * speed
        B = f * 0.07 * speed
        cosA, sinA = math.cos(A), math.sin(A)
        cosB, sinB = math.cos(B), math.sin(B)
        theta = 0.0
        while theta < math.tau:
            cost, sint = math.cos(theta), math.sin(theta)
            phi = 0.0
            while phi < math.tau:
                cosp, sinp = math.cos(phi), math.sin(phi)
                circlex = R2 + R1 * cost
                circley = R1 * sint
                x = circlex * (cosB * cosp + sinA * sinB * sinp) - circley * cosA * sinB
                y = circlex * (sinB * cosp - sinA * cosB * sinp) + circley * cosA * cosB
                z = cols / 3 + circlex * cosA * sinp + circley * sinA
                ooz = 1 / max(z, 0.01)
                xp = int(cols / 2 + (cols * 0.35) * ooz * x)
                yp = int(rows / 2 - (rows * 0.55) * ooz * y)
                L = (
                    cosp * cost * sinB
                    - cosA * cost * sinp
                    - sinA * sint
                    + cosB * (cosA * sint - cost * sinA * sinp)
                )
                if L > 0 and 0 <= xp < cols and 0 <= yp < rows and ooz > zbuf[yp][xp]:
                    zbuf[yp][xp] = ooz
                    idx = min(len(charset) - 1, int(L * 8))
                    set_cell(grid, xp, yp, charset[idx], palette_color(colors, L))
                phi += 0.22
            theta += 0.25
        out.append((grid, duration))
    return out


def shapes(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 45,
    seed: int | None = 0,
    shape: str = "cube",
    speed: float = 1.0,
    palette: str = "neon",
    charset: str = " .:-=+*#%@",
    bg: RGB = (0, 0, 0),
) -> list[tuple[CellGrid, int]]:
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["neon"])
    shape = shape if shape in {"cube", "pyramid", "diamond"} else rng.choice(
        ["cube", "pyramid", "diamond"]
    )

    def verts_for(kind: str) -> list[tuple[float, float, float]]:
        if kind == "pyramid":
            return [(0, -1, 0), (-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)]
        if kind == "diamond":
            return [(0, -1.2, 0), (0, 1.2, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)]
        # cube
        return [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]

    edges = {
        "cube": [
            (0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ],
        "pyramid": [(0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (2, 3), (3, 4), (4, 1)],
        "diamond": [
            (0, 2), (0, 3), (0, 4), (0, 5), (1, 2), (1, 3), (1, 4), (1, 5),
            (2, 4), (4, 3), (3, 5), (5, 2),
        ],
    }[shape]
    verts0 = verts_for(shape)
    out: list[tuple[CellGrid, int]] = []
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        a = f * 0.1 * speed
        b = f * 0.07 * speed
        ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
        proj = []
        for x, y, z in verts0:
            # rotate Y then X
            xz = x * cb + z * sb
            zz = -x * sb + z * cb
            y2 = y * ca - zz * sa
            z2 = y * sa + zz * ca
            depth = z2 + 4
            px = cols / 2 + (xz / depth) * cols * 0.35
            py = rows / 2 + (y2 / depth) * rows * 0.45
            proj.append((px, py, depth))
        for i, j in edges:
            x0, y0, z0 = proj[i]
            x1, y1, z1 = proj[j]
            steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for s in range(steps + 1):
                t = s / steps
                x = int(x0 + (x1 - x0) * t)
                y = int(y0 + (y1 - y0) * t)
                depth = z0 + (z1 - z0) * t
                lum = max(0.2, min(1.0, 1.4 - depth / 5))
                set_cell(
                    grid,
                    x,
                    y,
                    char_from_intensity(lum, charset),
                    palette_color(colors, lum),
                )
        out.append((grid, duration))
    return out


def horizon(
    cols: int,
    rows: int,
    *,
    frames: int = 40,
    duration: int = 45,
    seed: int | None = 0,
    speed: float = 1.0,
    palette: str = "sunset",
    charset: str = " .:=+#",
    bg: RGB = (10, 5, 20),
) -> list[tuple[CellGrid, int]]:
    """Infinite road stretching to the horizon."""
    rng = _rng(seed)
    colors = PALETTES.get(palette, PALETTES["sunset"])
    out: list[tuple[CellGrid, int]] = []
    horizon_y = int(rows * 0.38)
    for f in range(frames):
        grid = empty_grid(cols, rows, bg)
        # sky gradient
        for y in range(horizon_y):
            t = 1.0 - y / max(1, horizon_y)
            ch = "." if t < 0.7 else ":"
            col = palette_color(colors, 0.2 + t * 0.5)
            for x in range(cols):
                set_cell(grid, x, y, ch, col)
        # sun
        sx, sy = int(cols * 0.7), int(rows * 0.18)
        for dy in range(-3, 4):
            for dx in range(-5, 6):
                if dx * dx / 25 + dy * dy / 9 <= 1:
                    set_cell(grid, sx + dx, sy + dy, "@", palette_color(colors, 0.95))
        # road
        offset = (f * 1.5 * speed) % 8
        for y in range(horizon_y, rows):
            p = (y - horizon_y) / max(1, rows - horizon_y)
            half = int(2 + p * cols * 0.42)
            cx = cols // 2
            left, right = cx - half, cx + half
            road_col = palette_color(colors, 0.15 + p * 0.25)
            for x in range(max(0, left), min(cols, right + 1)):
                set_cell(grid, x, y, charset[min(len(charset) - 1, int(p * 3) + 1)], road_col)
            # shoulders
            set_cell(grid, left, y, "#", palette_color(colors, 0.7))
            set_cell(grid, right, y, "#", palette_color(colors, 0.7))
            # center dashes
            if int((y + offset) / 3) % 2 == 0 and half > 4:
                set_cell(grid, cx, y, "=", (255, 220, 100))
        # roadside posts scrolling
        for side in (-1, 1):
            for i in range(6):
                p = ((i / 6) + f * 0.03 * speed) % 1.0
                y = int(horizon_y + p * (rows - horizon_y))
                half = int(2 + p * cols * 0.42)
                x = cols // 2 + side * (half + 2)
                if 0 <= x < cols and horizon_y <= y < rows:
                    set_cell(grid, x, y, "|", palette_color(colors, 0.55))
        # stars above (sparse)
        rng2 = _rng((seed or 0) + 99)
        for _ in range(cols // 8):
            set_cell(
                grid,
                rng2.randint(0, cols - 1),
                rng2.randint(0, max(1, horizon_y - 2)),
                ".",
                (220, 220, 255),
            )
        out.append((grid, duration))
    return out


# Registry -----------------------------------------------------------------

STYLES: dict[str, GeneratorFn] = {
    "starfield": starfield,
    "matrix": matrix,
    "fire": fire,
    "fireworks": fireworks,
    "plasma": plasma,
    "rain": rain,
    "waves": waves,
    "bouncing": bouncing,
    "kaleidoscope": kaleidoscope,
    "galaxy": galaxy,
    "donut": donut,
    "shapes": shapes,
    "horizon": horizon,
}

STYLE_BLURBS = {
    "starfield": "Realtime starfield with warp-style depth",
    "matrix": "Falling glyph rain with glow heads",
    "fire": "Rising flames with wind and heat",
    "fireworks": "Looping bursts, trails, and sparks",
    "plasma": "Colorful plasma / interference fields",
    "rain": "Rippling raindrop rings on a surface",
    "waves": "Pulsing radio / sonar wave rings",
    "bouncing": "Energetic bouncing balls",
    "kaleidoscope": "Mirrored rotating kaleidoscope",
    "galaxy": "Spiral galaxy arms around a bright core",
    "donut": "Classic spinning ASCII torus",
    "shapes": "Rotating wireframe geometric solids",
    "horizon": "Infinite road racing toward the horizon",
}

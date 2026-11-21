"""Grayscale dither and ASCII fields inspired by dithr.app motion cards."""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw, ImageFont

from .render import _load_font

DOT = (232, 232, 232)
BG = (0, 0, 0)
ASCII_RAMP = " .:-=+*#%@"

# 8x8 Bayer, values 0..63
_BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
]

MOTIONS = (
    "cellular",
    "halftone",
    "starfield",
    "moire",
    "smoke",
    "caustics",
    "spiral",
    "tunnel",
    "waves",
    "ripples",
    "stripes",
    "vortex",
    "pulse",
    "drift",
)

# Cards that read as letters rather than a dot screen.
ASCII_MOTIONS = {"cellular", "starfield", "smoke", "stripes", "pulse"}


def _lum(kind: str, x: float, y: float, t: float, seed: int) -> float:
    rng = random.Random(seed)
    phase = rng.random() * math.tau
    if kind == "cellular":
        best = 9.0
        for i in range(16):
            px = (math.sin(t * 0.55 + i * 1.3 + phase) * 0.5 + 0.5)
            py = (math.cos(t * 0.4 + i * 1.9) * 0.5 + 0.5)
            dx = min(abs(x - px), 1 - abs(x - px))
            dy = min(abs(y - py), 1 - abs(y - py))
            best = min(best, math.hypot(dx, dy))
        return max(0.22, min(1.0, 1.15 - best * 5.5))
    if kind == "halftone":
        return 0.55 + 0.45 * math.sin(x * 7 + t) * math.cos(y * 5 - t * 0.7)
    if kind == "starfield":
        dust = 0.42 + 0.18 * math.sin((x + t * 0.05) * 53) * math.sin(y * 47 + phase)
        tw = math.sin(x * 97 + t * 6) * math.sin(y * 89 - t * 4)
        return 1.0 if tw > 0.86 else max(0.28, dust)
    if kind == "moire":
        r1 = math.hypot(x - 0.35, y - 0.5)
        r2 = math.hypot(x - 0.65, y - 0.5)
        a = 0.5 + 0.5 * math.sin(r1 * 48 - t * 2)
        b = 0.5 + 0.5 * math.sin(r2 * 42 + t * 1.6)
        return a * b
    if kind == "smoke":
        rise = y + t * 0.15
        plume = math.sin(x * 8 + rise * 6) + math.sin(x * 17 - rise * 4 + phase)
        column = 0.45 + 0.55 * math.exp(-((x - 0.5) ** 2) * 6)
        return max(0.2, min(1.0, (plume * 0.3 + 0.55) * column * (1.15 - y * 0.55)))
    if kind == "caustics":
        v = (
            math.sin(x * 14 + t)
            + math.sin(y * 11 - t * 1.3)
            + math.sin((x + y) * 9 + t * 0.7)
        )
        return max(0.0, min(1.0, (v + 3) / 6))
    if kind == "spiral":
        dx, dy = x - 0.5, y - 0.5
        ang = math.atan2(dy, dx) + t
        r = math.hypot(dx, dy)
        arm = 0.5 + 0.5 * math.sin(ang * 3 - r * 18)
        return arm * (1.0 - r)
    if kind == "tunnel":
        dx, dy = x - 0.5, (y - 0.5) * 1.4
        r = math.hypot(dx, dy) + 1e-4
        ang = math.atan2(dy, dx)
        ring = 0.5 + 0.5 * math.sin(8 / r - t * 3)
        spoke = 0.5 + 0.5 * math.sin(ang * 6 + t)
        return ring * spoke
    if kind == "waves":
        return 0.5 + 0.5 * math.sin(math.hypot(x - 0.5, y - 0.5) * 22 - t * 2)
    if kind == "ripples":
        cx = 0.5 + 0.2 * math.sin(t * 0.4)
        d = math.hypot(x - cx, y - 0.5)
        return 0.5 + 0.5 * math.sin(d * 30 - t * 2.4) * math.exp(-d * 1.4)
    if kind == "stripes":
        return 0.5 + 0.5 * math.sin(x * 18 + y * 4 + t * 1.5) * math.sin(y * 10 - t)
    if kind == "vortex":
        dx, dy = x - 0.5, y - 0.5
        ang = math.atan2(dy, dx) + t + math.hypot(dx, dy) * 8
        return 0.5 + 0.5 * math.sin(ang * 5)
    if kind == "pulse":
        d = math.hypot(x - 0.5, y - 0.5)
        return 0.5 + 0.5 * math.sin(d * 16 - t * 2) * math.cos(t + x * 6)
    # drift: layered bands boiling sideways
    return max(
        0.0,
        min(
            1.0,
            0.5
            + 0.25 * math.sin(x * 6 + t + y * 2)
            + 0.25 * math.sin(y * 9 - t * 1.4 + phase),
        ),
    )


def _grid(kind: str, cols: int, rows: int, t: float, seed: int) -> list[list[float]]:
    out: list[list[float]] = []
    for y in range(rows):
        row = []
        fy = y / max(1, rows - 1)
        for x in range(cols):
            fx = x / max(1, cols - 1)
            row.append(_lum(kind, fx, fy, t, seed))
        out.append(row)
    return out


def _dot_image(grid: list[list[float]], scale: int = 3) -> Image.Image:
    rows = len(grid)
    cols = len(grid[0])
    buf = bytearray(cols * rows * 3)
    i = 0
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            thr = (_BAYER[y & 7][x & 7] + 0.5) / 64.0
            c = 232 if v > thr else 0
            buf[i] = buf[i + 1] = buf[i + 2] = c
            i += 3
    img = Image.frombytes("RGB", (cols, rows), bytes(buf))
    if scale > 1:
        img = img.resize((cols * scale, rows * scale), Image.Resampling.NEAREST)
    return img


def _halftone_image(grid: list[list[float]], cell: int = 5) -> Image.Image:
    rows = len(grid)
    cols = len(grid[0])
    img = Image.new("RGB", (cols, rows), BG)
    px = img.load()
    for cy in range(0, rows, cell):
        for cx in range(0, cols, cell):
            acc = 0.0
            n = 0
            for y in range(cy, min(rows, cy + cell)):
                for x in range(cx, min(cols, cx + cell)):
                    acc += grid[y][x]
                    n += 1
            rad = 1.1 + (acc / max(1, n)) * cell * 0.32
            mx, my = cx + cell / 2, cy + cell / 2
            r2 = rad * rad
            for y in range(cy, min(rows, cy + cell)):
                for x in range(cx, min(cols, cx + cell)):
                    if (x - mx) ** 2 + (y - my) ** 2 <= r2:
                        px[x, y] = DOT
    return img.resize((cols * 3, rows * 3), Image.Resampling.NEAREST)


def _ascii_image(grid: list[list[float]], font: ImageFont.ImageFont) -> Image.Image:
    rows = len(grid)
    cols = len(grid[0])
    draw_probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bbox = draw_probe.textbbox((0, 0), "M", font=font)
    cw = max(1, bbox[2] - bbox[0])
    ch = max(1, bbox[3] - bbox[1]) + 1
    img = Image.new("RGB", (cols * cw, rows * ch), BG)
    draw = ImageDraw.Draw(img)
    ramp_n = len(ASCII_RAMP) - 1
    for y, row in enumerate(grid):
        x = 0
        while x < cols:
            v = row[x]
            glyph = ASCII_RAMP[max(0, min(ramp_n, round(v * ramp_n)))]
            if glyph == " ":
                x += 1
                continue
            j = x + 1
            chars = [glyph]
            while j < cols:
                v2 = row[j]
                g2 = ASCII_RAMP[max(0, min(ramp_n, round(v2 * ramp_n)))]
                if g2 != glyph:
                    break
                chars.append(g2)
                j += 1
            draw.text((x * cw, y * ch), "".join(chars), fill=DOT, font=font)
            x = j
    return img


def render_motion(
    kind: str,
    *,
    frames: int = 16,
    duration: int = 80,
    seed: int = 0,
    cols: int = 160,
    rows: int = 90,
) -> tuple[list[Image.Image], list[int]]:
    if kind not in MOTIONS:
        raise ValueError(f"unknown motion: {kind}")
    font = _load_font(8) if kind in ASCII_MOTIONS else None
    images: list[Image.Image] = []
    for f in range(frames):
        t = f / frames * math.tau
        grid = _grid(kind, cols, rows, t, seed)
        if kind == "halftone":
            images.append(_halftone_image(grid))
        elif kind in ASCII_MOTIONS:
            images.append(_ascii_image(grid, font))
        else:
            images.append(_dot_image(grid))
    return images, [duration] * frames

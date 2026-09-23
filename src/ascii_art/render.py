"""Render ASCII strings as PNG / animated GIF on a black background."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .converter import CellGrid

# Prefer common monospace fonts; fall back to Pillow default.
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/Library/Fonts/SF-Mono-Regular.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "DejaVuSansMono.ttf",
    "Menlo.ttc",
]


def _load_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _glyph_metrics(font: ImageFont.ImageFont) -> tuple[int, int]:
    """Return (char_width, line_height) for layout."""
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    bbox = probe.textbbox((0, 0), "M", font=font)
    char_w = max(1, bbox[2] - bbox[0])
    char_h = max(1, bbox[3] - bbox[1])
    line_h = char_h + max(1, char_h // 8)
    return char_w, line_h


def font_char_aspect(font_size: int = 14) -> float | None:
    """Width/height of one cell in the render font, or None if unavailable."""
    font = _load_font(font_size)
    if isinstance(font, ImageFont.FreeTypeFont) or hasattr(font, "getbbox"):
        char_w, line_h = _glyph_metrics(font)
        return char_w / line_h
    return None


def _measure(
    cols: int, rows: int, font: ImageFont.ImageFont, padding: int
) -> tuple[int, int, int, int]:
    """Return (img_w, img_h, char_w, line_h)."""
    char_w, line_h = _glyph_metrics(font)
    return cols * char_w + padding * 2, rows * line_h + padding * 2, char_w, line_h


def render_ascii_image(
    ascii_text: str,
    *,
    font_size: int = 14,
    fg: tuple[int, int, int] = (200, 200, 200),
    bg: tuple[int, int, int] = (0, 0, 0),
    padding: int = 24,
) -> Image.Image:
    """Rasterize mono ASCII text onto a solid background."""
    lines = ascii_text.splitlines() or [""]
    cols = max((len(line) for line in lines), default=1)
    rows = max(len(lines), 1)
    font = _load_font(font_size)
    width, height, _, line_h = _measure(cols, rows, font, padding)
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    y = padding
    for line in lines:
        draw.text((padding, y), line, fill=fg, font=font)
        y += line_h
    return img


def render_ascii_cells(
    cells: CellGrid,
    *,
    font_size: int = 14,
    bg: tuple[int, int, int] = (0, 0, 0),
    padding: int = 12,
) -> Image.Image:
    """Rasterize a colored (char, rgb) grid."""
    if not cells:
        return Image.new("RGB", (1, 1), bg)
    rows = len(cells)
    cols = max(len(row) for row in cells)
    font = _load_font(font_size)
    width, height, char_w, line_h = _measure(cols, rows, font, padding)
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Draw runs of same color for speed.
    for y, row in enumerate(cells):
        x = 0
        while x < len(row):
            ch, color = row[x]
            if ch == " ":
                x += 1
                continue
            run_chars = [ch]
            j = x + 1
            while j < len(row) and row[j][0] != " " and row[j][1] == color:
                run_chars.append(row[j][0])
                j += 1
            draw.text(
                (padding + x * char_w, padding + y * line_h),
                "".join(run_chars),
                fill=color,
                font=font,
            )
            x = j
    return img


def render_ascii_gif(
    frames: list[tuple[str, int]],
    *,
    font_size: int = 14,
    fg: tuple[int, int, int] = (200, 200, 200),
    bg: tuple[int, int, int] = (0, 0, 0),
    padding: int = 24,
) -> list[Image.Image]:
    """Rasterize every ASCII frame. Durations stay with the caller."""
    return [
        render_ascii_image(text, font_size=font_size, fg=fg, bg=bg, padding=padding)
        for text, _ in frames
    ]


def render_cells_gif(
    frames: list[tuple[CellGrid, int]],
    *,
    font_size: int = 14,
    bg: tuple[int, int, int] = (0, 0, 0),
    padding: int = 12,
) -> list[Image.Image]:
    return [
        render_ascii_cells(cells, font_size=font_size, bg=bg, padding=padding)
        for cells, _ in frames
    ]


def save_gif(
    images: list[Image.Image],
    durations: list[int],
    path: str | Path,
    *,
    loop: int = 0,
) -> None:
    if not images:
        raise ValueError("no frames to save")
    quantized = [
        im.convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for im in images
    ]
    quantized[0].save(
        path,
        save_all=True,
        append_images=quantized[1:],
        duration=durations,
        loop=loop,
        optimize=False,
        disposal=2,
    )

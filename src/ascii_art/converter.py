"""Map image luminance to ASCII characters."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps, ImageSequence

# Dark → bright ramp matching the attached Cursor-style reference.
DEFAULT_CHARSET = " .:+CU=&$R#"

# Monospace cell width/height. ~0.72 matches Menlo/SF Mono with light leading;
# use ~0.5–0.6 for many terminal emulators if text looks stretched.
DEFAULT_CHAR_ASPECT = 0.72


def parse_aspect(value: str | float) -> float:
    """Parse '16:9', '16/9', or a float into a width/height ratio."""
    if isinstance(value, (int, float)):
        ratio = float(value)
    else:
        text = value.strip().lower().replace("/", ":")
        if ":" in text:
            left, right = text.split(":", 1)
            ratio = float(left) / float(right)
        else:
            ratio = float(text)
    if ratio <= 0:
        raise ValueError("aspect ratio must be positive")
    return ratio


def grid_size(
    width: int,
    aspect: float = 16 / 9,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
) -> tuple[int, int]:
    """Return (cols, rows) for a visually correct aspect ratio."""
    if width < 8:
        raise ValueError("width must be at least 8")
    rows = max(1, round(width * char_aspect / aspect))
    return width, rows


def _to_luma(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        composited = Image.alpha_composite(background, rgba)
        return composited.convert("L")
    return img.convert("L")


def _fit_to_grid(img: Image.Image, cols: int, rows: int) -> Image.Image:
    """Letterbox the image into cols×rows (black fill)."""
    src = _to_luma(img)
    src_w, src_h = src.size
    if src_w == 0 or src_h == 0:
        return Image.new("L", (cols, rows), 0)

    scale = min(cols / src_w, rows / src_h)
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))
    resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("L", (cols, rows), 0)
    offset = ((cols - new_w) // 2, (rows - new_h) // 2)
    canvas.paste(resized, offset)
    return canvas


def _pixels_to_ascii(
    img: Image.Image,
    charset: str,
    invert: bool = False,
    black_point: int = 12,
) -> str:
    if not charset:
        raise ValueError("charset must not be empty")

    pixels = list(img.getdata())
    cols, rows = img.size
    n = len(charset) - 1
    lines: list[str] = []
    for y in range(rows):
        row_chars: list[str] = []
        for x in range(cols):
            value = pixels[y * cols + x]
            if invert:
                value = 255 - value
            # Keep true blacks as spaces so letterboxing stays clean.
            if value <= black_point:
                row_chars.append(charset[0] if charset[0] == " " else " ")
                continue
            # Remap remaining range across the full ramp.
            scaled = (value - black_point) / (255 - black_point)
            idx = max(1, round(scaled * n))
            row_chars.append(charset[min(idx, n)])
        lines.append("".join(row_chars))
    return "\n".join(lines)


def image_to_ascii(
    source: Image.Image | str | Path,
    *,
    width: int = 120,
    aspect: float | str = 16 / 9,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
    charset: str = DEFAULT_CHARSET,
    invert: bool = False,
    contrast: bool = True,
) -> str:
    """Convert a still image to an ASCII string."""
    if not isinstance(source, Image.Image):
        img = Image.open(source)
        img.load()
    else:
        img = source

    cols, rows = grid_size(width, parse_aspect(aspect), char_aspect)
    fitted = _fit_to_grid(img, cols, rows)
    if contrast:
        fitted = ImageOps.autocontrast(fitted)
    return _pixels_to_ascii(fitted, charset, invert=invert)


def iter_frames(source: Image.Image | str | Path) -> Iterable[tuple[Image.Image, int]]:
    """Yield (frame, duration_ms) for each frame of an image/GIF."""
    if not isinstance(source, Image.Image):
        img = Image.open(source)
    else:
        img = source

    for frame in ImageSequence.Iterator(img):
        duration = int(frame.info.get("duration", 100) or 100)
        # Copy so subsequent seeks don't mutate earlier frames.
        yield frame.copy().convert("RGBA"), duration


def frames_to_ascii(
    source: Image.Image | str | Path,
    *,
    width: int = 120,
    aspect: float | str = 16 / 9,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
    charset: str = DEFAULT_CHARSET,
    invert: bool = False,
    contrast: bool = True,
) -> list[tuple[str, int]]:
    """Convert every frame to ASCII. Returns list of (ascii_text, duration_ms)."""
    return [
        (
            image_to_ascii(
                frame,
                width=width,
                aspect=aspect,
                char_aspect=char_aspect,
                charset=charset,
                invert=invert,
                contrast=contrast,
            ),
            duration,
        )
        for frame, duration in iter_frames(source)
    ]

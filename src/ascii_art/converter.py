"""Map image luminance to ASCII characters."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal

from PIL import Image, ImageOps, ImageSequence

# Dark → bright ramp matching the attached Cursor-style reference.
DEFAULT_CHARSET = " .:+CU=&$R#"

# Monospace cell width/height. ~0.72 matches Menlo/SF Mono with light leading;
# use ~0.5–0.6 for many terminal emulators if text looks stretched.
DEFAULT_CHAR_ASPECT = 0.72

FitMode = Literal["fit", "cover"]

# One cell: character + RGB foreground.
Cell = tuple[str, tuple[int, int, int]]
CellGrid = list[list[Cell]]


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


def _to_rgba(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        return Image.alpha_composite(background, rgba)
    return img.convert("RGBA")


def _resize_to_grid(
    img: Image.Image,
    cols: int,
    rows: int,
    *,
    mode: FitMode = "fit",
    fill: tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """Resize RGBA/RGB into cols×rows with letterbox (fit) or crop (cover)."""
    src = _to_rgba(img)
    src_w, src_h = src.size
    if src_w == 0 or src_h == 0:
        return Image.new("RGBA", (cols, rows), (*fill, 255))

    if mode == "cover":
        scale = max(cols / src_w, rows / src_h)
    else:
        scale = min(cols / src_w, rows / src_h)

    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))
    resized = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (cols, rows), (*fill, 255))
    offset = ((cols - new_w) // 2, (rows - new_h) // 2)
    canvas.paste(resized, offset, resized)
    return canvas


def _luma_of(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return int(0.299 * r + 0.587 * g + 0.114 * b)


def _char_for_luma(
    value: int,
    charset: str,
    *,
    invert: bool = False,
    black_point: int = 8,
) -> str:
    n = len(charset) - 1
    if invert:
        value = 255 - value
    if value <= black_point:
        return " "
    scaled = (value - black_point) / (255 - black_point)
    idx = max(1, round(scaled * n))
    return charset[min(idx, n)]


def _boost_contrast_rgb(img: Image.Image) -> Image.Image:
    """Autocontrast on RGB while keeping hue relationships."""
    return ImageOps.autocontrast(img.convert("RGB")).convert("RGBA")


def image_to_cells(
    source: Image.Image | str | Path,
    *,
    width: int = 120,
    aspect: float | str = 16 / 9,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
    charset: str = DEFAULT_CHARSET,
    invert: bool = False,
    contrast: bool = True,
    fit: FitMode = "fit",
    fill: tuple[int, int, int] = (0, 0, 0),
    black_point: int = 8,
    color: bool = True,
) -> CellGrid:
    """Convert an image to a grid of (char, rgb) cells."""
    if not isinstance(source, Image.Image):
        img = Image.open(source)
        img.load()
    else:
        img = source

    if not charset:
        raise ValueError("charset must not be empty")

    cols, rows = grid_size(width, parse_aspect(aspect), char_aspect)
    fitted = _resize_to_grid(img, cols, rows, mode=fit, fill=fill)
    if contrast:
        fitted = _boost_contrast_rgb(fitted)

    rgb = fitted.convert("RGB")
    pixels = list(rgb.getdata())
    default_fg = (200, 200, 200)
    grid: CellGrid = []
    for y in range(rows):
        row: list[Cell] = []
        for x in range(cols):
            pix = pixels[y * cols + x]
            luma = _luma_of(pix)
            ch = _char_for_luma(luma, charset, invert=invert, black_point=black_point)
            if ch == " ":
                row.append((" ", fill))
            elif color:
                row.append((ch, pix))
            else:
                row.append((ch, default_fg))
        grid.append(row)
    return grid


def cells_to_text(cells: CellGrid) -> str:
    return "\n".join("".join(ch for ch, _ in row) for row in cells)


def image_to_ascii(
    source: Image.Image | str | Path,
    *,
    width: int = 120,
    aspect: float | str = 16 / 9,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
    charset: str = DEFAULT_CHARSET,
    invert: bool = False,
    contrast: bool = True,
    fit: FitMode = "fit",
    fill: tuple[int, int, int] = (0, 0, 0),
) -> str:
    """Convert a still image to an ASCII string."""
    cells = image_to_cells(
        source,
        width=width,
        aspect=aspect,
        char_aspect=char_aspect,
        charset=charset,
        invert=invert,
        contrast=contrast,
        fit=fit,
        fill=fill,
        color=False,
    )
    return cells_to_text(cells)


def iter_frames(source: Image.Image | str | Path) -> Iterable[tuple[Image.Image, int]]:
    """Yield (frame, duration_ms) for each frame of an image/GIF."""
    if not isinstance(source, Image.Image):
        img = Image.open(source)
    else:
        img = source

    for frame in ImageSequence.Iterator(img):
        duration = int(frame.info.get("duration", 100) or 100)
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
    fit: FitMode = "fit",
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
                fit=fit,
            ),
            duration,
        )
        for frame, duration in iter_frames(source)
    ]


def frames_to_cells(
    source: Image.Image | str | Path,
    *,
    width: int = 120,
    aspect: float | str = 16 / 9,
    char_aspect: float = DEFAULT_CHAR_ASPECT,
    charset: str = DEFAULT_CHARSET,
    invert: bool = False,
    contrast: bool = True,
    fit: FitMode = "fit",
    fill: tuple[int, int, int] = (0, 0, 0),
    color: bool = True,
) -> list[tuple[CellGrid, int]]:
    """Convert every frame to a colored cell grid."""
    return [
        (
            image_to_cells(
                frame,
                width=width,
                aspect=aspect,
                char_aspect=char_aspect,
                charset=charset,
                invert=invert,
                contrast=contrast,
                fit=fit,
                fill=fill,
                color=color,
            ),
            duration,
        )
        for frame, duration in iter_frames(source)
    ]

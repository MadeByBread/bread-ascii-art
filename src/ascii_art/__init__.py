"""Image / GIF → ASCII art."""

from .converter import (
    DEFAULT_CHARSET,
    cells_to_text,
    frames_to_ascii,
    frames_to_cells,
    image_to_ascii,
    image_to_cells,
)
from .render import (
    render_ascii_cells,
    render_ascii_gif,
    render_ascii_image,
    render_cells_gif,
)

__all__ = [
    "DEFAULT_CHARSET",
    "image_to_ascii",
    "image_to_cells",
    "cells_to_text",
    "frames_to_ascii",
    "frames_to_cells",
    "render_ascii_image",
    "render_ascii_gif",
    "render_ascii_cells",
    "render_cells_gif",
]

__version__ = "0.1.0"

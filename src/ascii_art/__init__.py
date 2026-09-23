"""Image / GIF → ASCII art, plus topic-driven animation inventing."""

from .converter import (
    DEFAULT_CHARSET,
    cells_to_text,
    frames_to_ascii,
    frames_to_cells,
    image_to_ascii,
    image_to_cells,
)
from .invent import invent_animations, load_topic, pick_variations, write_variation
from .procedural import STYLE_BLURBS, STYLES
from .render import (
    render_ascii_cells,
    render_ascii_gif,
    render_ascii_image,
    render_cells_gif,
)

__all__ = [
    "DEFAULT_CHARSET",
    "STYLES",
    "STYLE_BLURBS",
    "image_to_ascii",
    "image_to_cells",
    "cells_to_text",
    "frames_to_ascii",
    "frames_to_cells",
    "render_ascii_image",
    "render_ascii_gif",
    "render_ascii_cells",
    "render_cells_gif",
    "invent_animations",
    "pick_variations",
    "load_topic",
    "write_variation",
]

__version__ = "0.2.0"

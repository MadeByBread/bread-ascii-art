"""Image / GIF → ASCII art."""

from .converter import DEFAULT_CHARSET, image_to_ascii, frames_to_ascii
from .render import render_ascii_image, render_ascii_gif

__all__ = [
    "DEFAULT_CHARSET",
    "image_to_ascii",
    "frames_to_ascii",
    "render_ascii_image",
    "render_ascii_gif",
]

__version__ = "0.1.0"

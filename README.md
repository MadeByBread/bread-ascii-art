# bread-ascii-art

Convert images and GIFs into ASCII art — text, PNG, or animated GIF — in the dense monochrome style of a terminal render on black.

Default output aspect ratio is **16:9** (customizable). Character cells are compensated so the result doesn't look vertically stretched.

## Setup

```bash
cd bread-ascii-art
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Image → .txt + .png (16:9, 120 cols)
ascii-art path/to/photo.jpg

# Custom aspect + width
ascii-art photo.jpg -a 4:3 -w 160

# Text only to stdout
ascii-art photo.jpg -f txt

# Animated GIF → .txt + rendered .gif
ascii-art animation.gif

# Explicit outputs
ascii-art logo.png -o output/logo.png -f png
ascii-art logo.png -o output/logo.txt -f txt
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-w / --width` | `120` | Character columns |
| `-a / --aspect` | `16:9` | Output aspect (`W:H` or float) |
| `--char-aspect` | auto | Monospace cell width÷height (from render font) |
| `--charset` | ` .:+CU=&$R#` | Dark → bright ramp |
| `--invert` | off | Flip luminance mapping |
| `--no-contrast` | off | Skip autocontrast |
| `--font-size` | `14` | Rendered PNG/GIF font size |
| `-f / --format` | `both` | `txt`, `png`, `gif`, or `both` |

## Library

```python
from ascii_art import image_to_ascii, frames_to_ascii, render_ascii_image

text = image_to_ascii("photo.jpg", width=120, aspect="16:9")
print(text)

img = render_ascii_image(text)
img.save("out.png")
```

## Via Cursor agent

Drop an image into the chat (or give a path) and ask to run:

```bash
ascii-art /path/to/upload.jpg -o output/result
```

Outputs land in `output/` as `.txt` plus `.png` or `.gif`.

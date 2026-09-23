# bread-ascii-art

Convert images/GIFs to ASCII — or **invent** looping ASCII animations from a topic or blog post, using styles inspired by [asciiart.eu/animations](https://www.asciiart.eu/animations).

Default aspect ratio is **16:9** (customizable).

## Setup

```bash
cd bread-ascii-art
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Invent from a topic / blog

Give a topic, a local post, or a URL. The tool scores keywords against animation styles (fire, matrix, starfield, donut, horizon, …), then generates **random variations** (palette, speed, density, seed, …).

```bash
# From a short topic — 3 random variations
ascii-art invent "summer road trip through the desert at sunset"

# From a blog post file
ascii-art invent --file posts/launch-day.md -n 5 -o output/launch

# From a URL
ascii-art invent --url https://example.com/blog/our-launch -n 3

# Force styles
ascii-art invent "party" --style fireworks --style bouncing -n 2

# List styles
ascii-art styles
```

Each variation writes `.gif` + `.txt` + `.json` (style, seed, params).

## Convert an image / GIF

```bash
ascii-art convert photo.jpg
ascii-art photo.jpg                 # same (path shorthand)
ascii-art convert anim.gif -a 4:3 -w 160
```

### Convert options

| Flag | Default | Description |
|------|---------|-------------|
| `-w / --width` | `120` | Character columns |
| `-a / --aspect` | `16:9` | Output aspect (`W:H` or float) |
| `--charset` | ` .:+CU=&$R#` | Dark → bright ramp |
| `-f / --format` | `both` | `txt`, `png`, `gif`, or `both` |

## Styles

Drawn from the asciiart.eu animation catalog spirit:

`starfield` · `matrix` · `fire` · `fireworks` · `plasma` · `rain` · `waves` · `bouncing` · `kaleidoscope` · `galaxy` · `donut` · `shapes` · `horizon`

## Library

```python
from ascii_art import invent_animations, write_variation
from pathlib import Path

for variation, frames in invent_animations("bakery launch party", count=3):
    write_variation(variation, frames, Path("output") / variation.style)
```

## Via Cursor agent

Paste a topic or blog link and ask to invent variations:

```bash
ascii-art invent "your topic here" -n 3 -o output/
```

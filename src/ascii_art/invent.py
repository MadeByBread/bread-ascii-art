"""Turn a topic or blog post into random ASCII animation variations."""

from __future__ import annotations

import hashlib
import re
import html
from dataclasses import dataclass, field
from pathlib import Path
from urllib.request import Request, urlopen

from .effects import PALETTES, resolve_grid
from .procedural import STYLE_BLURBS, STYLES
from .render import render_cells_gif, save_gif
from .converter import cells_to_text

# Keyword hints → style names (inspired by https://www.asciiart.eu/animations).
KEYWORD_STYLES: dict[str, list[str]] = {
    "star": ["starfield", "galaxy"],
    "space": ["starfield", "galaxy", "donut"],
    "galaxy": ["galaxy", "starfield"],
    "cosmos": ["galaxy", "starfield"],
    "night": ["starfield", "horizon"],
    "warp": ["starfield"],
    "matrix": ["matrix"],
    "code": ["matrix", "plasma"],
    "hack": ["matrix"],
    "digital": ["matrix", "plasma"],
    "cyber": ["matrix", "plasma"],
    "fire": ["fire", "fireworks"],
    "flame": ["fire"],
    "burn": ["fire"],
    "heat": ["fire"],
    "camp": ["fire", "horizon"],
    "firework": ["fireworks"],
    "celebrate": ["fireworks", "bouncing"],
    "party": ["fireworks", "bouncing", "kaleidoscope"],
    "launch": ["fireworks", "starfield"],
    "new year": ["fireworks"],
    "plasma": ["plasma", "kaleidoscope"],
    "abstract": ["plasma", "kaleidoscope", "waves"],
    "psychedelic": ["kaleidoscope", "plasma"],
    "rain": ["rain", "waves"],
    "storm": ["rain", "waves"],
    "water": ["rain", "waves", "horizon"],
    "ocean": ["waves", "rain", "horizon"],
    "wave": ["waves"],
    "radio": ["waves"],
    "signal": ["waves", "plasma"],
    "pulse": ["waves", "plasma"],
    "bounce": ["bouncing"],
    "ball": ["bouncing"],
    "play": ["bouncing", "shapes"],
    "fun": ["bouncing", "fireworks"],
    "kaleidoscope": ["kaleidoscope"],
    "mirror": ["kaleidoscope"],
    "donut": ["donut"],
    "torus": ["donut"],
    "spin": ["donut", "shapes", "galaxy"],
    "rotate": ["donut", "shapes"],
    "shape": ["shapes"],
    "geometry": ["shapes", "kaleidoscope"],
    "cube": ["shapes"],
    "road": ["horizon"],
    "highway": ["horizon"],
    "travel": ["horizon", "starfield"],
    "journey": ["horizon", "galaxy"],
    "drive": ["horizon"],
    "sunset": ["horizon", "fire"],
    "bread": ["donut", "fire", "horizon"],
    "bake": ["fire", "donut"],
    "oven": ["fire"],
}


@dataclass
class Variation:
    style: str
    seed: int
    params: dict = field(default_factory=dict)
    reason: str = ""


def _tokenize_tokens(text: str) -> set[str]:
    lowered = text.lower()
    tokens = set(re.findall(r"[a-z][a-z0-9'-]{2,}", lowered))
    # also keep a few bigrams for phrases like "new year"
    words = re.findall(r"[a-z]+", lowered)
    for a, b in zip(words, words[1:]):
        tokens.add(f"{a} {b}")
    return tokens


def strip_html(raw: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def load_topic(
    *,
    topic: str | None = None,
    file: Path | str | None = None,
    url: str | None = None,
) -> str:
    parts: list[str] = []
    if topic:
        parts.append(topic)
    if file:
        parts.append(Path(file).read_text(encoding="utf-8"))
    if url:
        req = Request(url, headers={"User-Agent": "bread-ascii-art/0.1"})
        with urlopen(req, timeout=20) as resp:  # noqa: S310 — user-provided URL
            charset = resp.headers.get_content_charset() or "utf-8"
            parts.append(strip_html(resp.read().decode(charset, errors="replace")))
    text = "\n\n".join(p for p in parts if p and p.strip())
    if not text.strip():
        raise ValueError("provide a topic, --file, and/or --url")
    return text


def score_styles(text: str) -> dict[str, float]:
    tokens = _tokenize_tokens(text)
    scores = {name: 0.0 for name in STYLES}
    for key, styles in KEYWORD_STYLES.items():
        hit = key in tokens or key in text.lower()
        if not hit:
            continue
        weight = 2.0 if " " in key else 1.0
        for style in styles:
            if style in scores:
                scores[style] += weight
            # palette aliases aren't styles
    # mild prior so cold topics still get variety
    for name in scores:
        scores[name] += 0.15
    return scores


def pick_variations(
    text: str,
    *,
    count: int = 3,
    seed: int | None = None,
    styles: list[str] | None = None,
) -> list[Variation]:
    """Pick `count` random style variations weighted by topic keywords."""
    import random

    base_seed = seed if seed is not None else int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    rng = random.Random(base_seed)

    if styles:
        chosen_styles = [s for s in styles if s in STYLES]
        if not chosen_styles:
            raise ValueError(f"unknown styles: {styles}")
    else:
        scores = score_styles(text)
        names = list(scores.keys())
        weights = [max(0.05, scores[n]) for n in names]
        chosen_styles = []
        # sample without replacement, weighted
        pool = list(zip(names, weights))
        for _ in range(min(count, len(pool))):
            total = sum(w for _, w in pool)
            r = rng.random() * total
            acc = 0.0
            for i, (name, w) in enumerate(pool):
                acc += w
                if r <= acc:
                    chosen_styles.append(name)
                    pool.pop(i)
                    break

    # pad if user asked for more than unique styles
    while len(chosen_styles) < count:
        chosen_styles.append(rng.choice(list(STYLES.keys())))

    palettes = list(PALETTES.keys())
    variations: list[Variation] = []
    for i, style in enumerate(chosen_styles[:count]):
        vseed = base_seed + i * 9973 + rng.randint(0, 999)
        params: dict = {
            "seed": vseed,
            "palette": rng.choice(palettes),
            "frames": rng.choice([28, 32, 36, 40, 48]),
        }
        # style-specific knobs
        if style == "starfield":
            params.update(density=rng.uniform(0.008, 0.02), speed=rng.uniform(0.7, 1.6), warp=rng.random() < 0.5)
        elif style == "matrix":
            params.update(density=rng.uniform(0.35, 0.75), speed=rng.uniform(0.7, 1.5), glitch=rng.uniform(0, 0.08))
        elif style == "fire":
            params.update(wind=rng.uniform(-0.6, 0.8), intensity=rng.uniform(0.7, 1.3))
        elif style == "fireworks":
            params.update(bursts=rng.randint(3, 8))
        elif style == "plasma":
            params.update(scale=rng.uniform(0.6, 1.6), speed=rng.uniform(0.6, 1.5))
        elif style == "rain":
            params.update(drops=rng.randint(8, 22))
        elif style == "waves":
            params.update(wavelength=rng.uniform(6, 16), thickness=rng.uniform(1.0, 2.4), speed=rng.uniform(0.6, 1.5))
        elif style == "bouncing":
            params.update(balls=rng.randint(4, 12))
        elif style == "kaleidoscope":
            params.update(segments=rng.choice([6, 8, 10, 12]), speed=rng.uniform(0.6, 1.4))
        elif style == "galaxy":
            params.update(arms=rng.randint(2, 5), speed=rng.uniform(0.6, 1.5))
        elif style == "donut":
            params.update(size=rng.uniform(0.8, 1.3), speed=rng.uniform(0.7, 1.4))
        elif style == "shapes":
            params.update(shape=rng.choice(["cube", "pyramid", "diamond"]), speed=rng.uniform(0.7, 1.4))
        elif style == "horizon":
            params.update(speed=rng.uniform(0.7, 1.6))

        reason = STYLE_BLURBS.get(style, style)
        variations.append(Variation(style=style, seed=vseed, params=params, reason=reason))
    return variations


def invent_animations(
    text: str,
    *,
    count: int = 3,
    seed: int | None = None,
    styles: list[str] | None = None,
    width: int = 120,
    aspect: str = "16:9",
    font_size: int = 12,
) -> list[tuple[Variation, list]]:
    """Return list of (variation, cell_frames)."""
    cols, rows, _ = resolve_grid(width=width, aspect=aspect, font_size=font_size)
    variations = pick_variations(text, count=count, seed=seed, styles=styles)
    results = []
    for var in variations:
        fn = STYLES[var.style]
        # filter params to what the generator accepts
        import inspect

        sig = inspect.signature(fn)
        kwargs = {k: v for k, v in var.params.items() if k in sig.parameters}
        frames = fn(cols, rows, **kwargs)
        results.append((var, frames))
    return results


def write_variation(
    variation: Variation,
    cell_frames: list,
    dest_stem: Path,
    *,
    font_size: int = 12,
    bg: tuple[int, int, int] = (0, 0, 0),
) -> dict[str, Path]:
    dest_stem.parent.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    txt_path = dest_stem.with_suffix(".txt")
    txt_path.write_text(cells_to_text(cell_frames[0][0]) + "\n", encoding="utf-8")
    written["txt"] = txt_path

    images = render_cells_gif(cell_frames, font_size=font_size, bg=bg, padding=8)
    gif_path = dest_stem.with_suffix(".gif")
    save_gif(images, [d for _, d in cell_frames], gif_path)
    written["gif"] = gif_path

    meta = dest_stem.with_suffix(".json")
    import json

    meta.write_text(
        json.dumps(
            {
                "style": variation.style,
                "seed": variation.seed,
                "params": variation.params,
                "reason": variation.reason,
                "blurb": STYLE_BLURBS.get(variation.style),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    written["json"] = meta
    return written

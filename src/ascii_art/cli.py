"""CLI for bread-ascii-art."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .converter import DEFAULT_CHAR_ASPECT, DEFAULT_CHARSET, frames_to_ascii, parse_aspect
from .invent import invent_animations, load_topic, write_variation
from .procedural import STYLE_BLURBS, STYLES
from .render import font_char_aspect, render_ascii_gif, render_ascii_image, save_gif


def _slug(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:limit] or "invent").rstrip("-")


def _add_shared_render_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("-w", "--width", type=int, default=120, help="Character columns (default: 120)")
    p.add_argument("-a", "--aspect", default="16:9", help="Aspect ratio (default: 16:9)")
    p.add_argument("--font-size", type=int, default=12, help="Render font size (default: 12)")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ascii-art",
        description="Convert images/GIFs to ASCII, or invent animations from a topic/blog.",
    )
    sub = p.add_subparsers(dest="command")

    # convert (also the default if first arg is a file path)
    c = sub.add_parser("convert", help="Convert an image or GIF to ASCII")
    c.add_argument("input", type=Path, help="Path to an image or GIF")
    c.add_argument("-o", "--output", type=Path, help="Output directory or file path")
    c.add_argument(
        "-f",
        "--format",
        choices=("txt", "png", "gif", "both"),
        default="both",
    )
    c.add_argument("--char-aspect", type=float, default=None)
    c.add_argument("--charset", default=DEFAULT_CHARSET)
    c.add_argument("--invert", action="store_true")
    c.add_argument("--no-contrast", action="store_true")
    _add_shared_render_args(c)
    c.set_defaults(font_size=14)

    # invent
    i = sub.add_parser(
        "invent",
        help="Generate random ASCII animation variations from a topic or blog post",
    )
    i.add_argument(
        "topic",
        nargs="?",
        default=None,
        help="Topic or short brief (optional if --file/--url given)",
    )
    i.add_argument("--file", type=Path, help="Blog post / markdown / text file")
    i.add_argument("--url", help="Blog post URL to fetch")
    i.add_argument(
        "-n",
        "--count",
        type=int,
        default=3,
        help="How many random variations to generate (default: 3)",
    )
    i.add_argument(
        "--style",
        action="append",
        dest="styles",
        help="Force style(s); repeatable. Default: pick from topic keywords",
    )
    i.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    i.add_argument("-o", "--output", type=Path, default=Path("output"), help="Output directory")
    _add_shared_render_args(i)

    # styles
    s = sub.add_parser("styles", help="List available animation styles")
    s.add_argument("--json", action="store_true", help="Machine-readable list")

    return p


def _resolve_targets(
    input_path: Path,
    output: Path | None,
    fmt: str,
    animated: bool,
) -> dict[str, Path | None]:
    suffix = output.suffix.lower() if output and output.suffix else ""
    if output and suffix in {".txt", ".png", ".gif"}:
        return {suffix.lstrip("."): output}

    if output is None:
        base = Path("output") / input_path.stem
    elif output.is_dir() or (suffix == "" and output.exists() and output.is_dir()):
        base = output / input_path.stem
    else:
        base = output

    base.parent.mkdir(parents=True, exist_ok=True)
    targets: dict[str, Path | None] = {}
    if fmt == "txt":
        targets["txt"] = None if output is None else base.with_suffix(".txt")
    elif fmt == "png":
        targets["png"] = base.with_suffix(".png")
    elif fmt == "gif":
        targets["gif"] = base.with_suffix(".gif")
    else:
        targets["txt"] = base.with_suffix(".txt")
        if animated:
            targets["gif"] = base.with_suffix(".gif")
        else:
            targets["png"] = base.with_suffix(".png")
    return targets


def _cmd_convert(args: argparse.Namespace) -> int:
    input_path: Path = args.input
    if not input_path.exists():
        print(f"error: input not found: {input_path}", file=sys.stderr)
        return 1

    char_aspect = args.char_aspect
    if char_aspect is None:
        char_aspect = font_char_aspect(args.font_size) or DEFAULT_CHAR_ASPECT

    frames = frames_to_ascii(
        input_path,
        width=args.width,
        aspect=parse_aspect(args.aspect),
        char_aspect=char_aspect,
        charset=args.charset,
        invert=args.invert,
        contrast=not args.no_contrast,
    )
    animated = input_path.suffix.lower() in {".gif", ".webp"} and len(frames) > 1
    targets = _resolve_targets(input_path, args.output, args.format, animated)

    if "txt" in targets:
        body = (
            "\n\n----- FRAME -----\n\n".join(t for t, _ in frames)
            if animated
            else frames[0][0]
        )
        dest = targets["txt"]
        if dest is None:
            print(body)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body + "\n", encoding="utf-8")
            print(f"wrote {dest}")

    if "png" in targets:
        img = render_ascii_image(frames[0][0], font_size=args.font_size)
        dest = targets["png"]
        assert dest is not None
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest)
        print(f"wrote {dest}")

    if "gif" in targets:
        images = render_ascii_gif(frames, font_size=args.font_size)
        durations = [d for _, d in frames]
        dest = targets["gif"]
        assert dest is not None
        dest.parent.mkdir(parents=True, exist_ok=True)
        if animated:
            save_gif(images, durations, dest)
        else:
            images[0].save(dest)
        print(f"wrote {dest}")
    return 0


def _cmd_invent(args: argparse.Namespace) -> int:
    try:
        text = load_topic(topic=args.topic, file=args.file, url=args.url)
    except Exception as exc:  # noqa: BLE001 — surface fetch/parse errors cleanly
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_dir: Path = args.output
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _slug(args.topic or (args.file.stem if args.file else "blog"))

    print(f"inventing {args.count} variation(s) from topic ({len(text)} chars)…")
    results = invent_animations(
        text,
        count=args.count,
        seed=args.seed,
        styles=args.styles,
        width=args.width,
        aspect=args.aspect,
        font_size=args.font_size,
    )
    for idx, (variation, frames) in enumerate(results, start=1):
        stem = out_dir / f"{slug}-{idx:02d}-{variation.style}"
        written = write_variation(variation, frames, stem, font_size=args.font_size)
        print(
            f"[{idx}/{len(results)}] {variation.style} — {variation.reason} "
            f"(seed={variation.seed}, palette={variation.params.get('palette')})"
        )
        for kind, path in written.items():
            print(f"  {kind}: {path}")
    return 0


def _cmd_styles(args: argparse.Namespace) -> int:
    if args.json:
        import json

        print(json.dumps({k: STYLE_BLURBS[k] for k in STYLES}, indent=2))
        return 0
    print("Available styles (inspired by asciiart.eu/animations):\n")
    for name in sorted(STYLES):
        print(f"  {name:14}  {STYLE_BLURBS.get(name, '')}")
    print("\nPalettes:", ", ".join(sorted(__import__('ascii_art.effects', fromlist=['PALETTES']).PALETTES)))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Back-compat: `ascii-art photo.jpg` → convert
    if argv and not argv[0].startswith("-") and argv[0] not in {
        "convert",
        "invent",
        "styles",
        "help",
    }:
        candidate = Path(argv[0])
        if candidate.exists() or candidate.suffix.lower() in {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".tif",
            ".tiff",
        }:
            argv = ["convert", *argv]

    parser = _build_parser()
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    if args.command == "convert":
        return _cmd_convert(args)
    if args.command == "invent":
        return _cmd_invent(args)
    if args.command == "styles":
        return _cmd_styles(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

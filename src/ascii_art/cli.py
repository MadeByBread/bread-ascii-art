"""CLI for ascii-art."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .converter import DEFAULT_CHAR_ASPECT, DEFAULT_CHARSET, frames_to_ascii, parse_aspect
from .render import font_char_aspect, render_ascii_gif, render_ascii_image, save_gif


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ascii-art",
        description="Convert an image or GIF into ASCII art (text + PNG/GIF).",
    )
    p.add_argument("input", type=Path, help="Path to an image or GIF")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory or file path (extension selects format)",
    )
    p.add_argument(
        "-f",
        "--format",
        choices=("txt", "png", "gif", "both"),
        default="both",
        help="Output format (default: both = .txt + rendered image)",
    )
    p.add_argument(
        "-w",
        "--width",
        type=int,
        default=120,
        help="Character width / columns (default: 120)",
    )
    p.add_argument(
        "-a",
        "--aspect",
        default="16:9",
        help="Output aspect ratio as W:H or float (default: 16:9)",
    )
    p.add_argument(
        "--char-aspect",
        type=float,
        default=None,
        help=f"Monospace cell width/height (default: auto from font, else {DEFAULT_CHAR_ASPECT})",
    )
    p.add_argument(
        "--charset",
        default=DEFAULT_CHARSET,
        help=f'Character ramp dark→bright (default: "{DEFAULT_CHARSET}")',
    )
    p.add_argument("--invert", action="store_true", help="Invert luminance mapping")
    p.add_argument("--no-contrast", action="store_true", help="Disable autocontrast")
    p.add_argument(
        "--font-size",
        type=int,
        default=14,
        help="Font size for PNG/GIF render (default: 14)",
    )
    return p


def _resolve_targets(
    input_path: Path,
    output: Path | None,
    fmt: str,
    animated: bool,
) -> dict[str, Path | None]:
    """Map format keys to destination paths. None means print to stdout."""
    suffix = output.suffix.lower() if output and output.suffix else ""

    # Explicit file path selects a single format
    if output and suffix in {".txt", ".png", ".gif"}:
        return {suffix.lstrip("."): output}

    # Directory → keep input stem inside it; bare path → use as stem
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
    else:  # both
        targets["txt"] = base.with_suffix(".txt")
        if animated:
            targets["gif"] = base.with_suffix(".gif")
        else:
            targets["png"] = base.with_suffix(".png")
    return targets


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    input_path: Path = args.input
    if not input_path.exists():
        print(f"error: input not found: {input_path}", file=sys.stderr)
        return 1

    char_aspect = args.char_aspect
    if char_aspect is None:
        # Match the renderer so PNG/GIF aspect lands on --aspect.
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


if __name__ == "__main__":
    raise SystemExit(main())

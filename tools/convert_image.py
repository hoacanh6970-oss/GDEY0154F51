#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from gdey0154f51.image_converter import ConvertOptions, ImageConverter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert image to GDEY0154F51 native 2bpp buffer"
    )
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output-bin", required=True, help="Output binary buffer path")
    parser.add_argument("--preview", help="Optional preview PNG path")
    parser.add_argument(
        "--fit", default="contain", choices=["contain", "cover", "stretch"]
    )
    parser.add_argument("--rotate", type=int, default=0, choices=[0, 90, 180, 270])
    parser.add_argument("--no-dither", action="store_true", help="Disable dithering")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    converter = ImageConverter()
    options = ConvertOptions(
        dither=not args.no_dither,
        fit=args.fit,
        rotate=args.rotate,
    )

    buffer = converter.convert_file(args.input, options=options)
    out_path = Path(args.output_bin)
    out_path.write_bytes(buffer)
    print(f"buffer saved: {out_path} ({len(buffer)} bytes)")

    if args.preview:
        preview = converter.buffer_to_preview(buffer)
        preview_path = Path(args.preview)
        preview.save(preview_path)
        print(f"preview saved: {preview_path}")


if __name__ == "__main__":
    main()

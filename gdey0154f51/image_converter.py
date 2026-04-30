from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .constants import BUFFER_SIZE, HEIGHT, WIDTH

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageOps = None  # type: ignore[assignment]


@dataclass
class ConvertOptions:
    dither: bool = True
    fit: str = "contain"
    rotate: int = 0


class ImageConverter:
    """Convert regular images to GDEY0154F51 native 2bpp buffer."""

    def __init__(self, width: int = WIDTH, height: int = HEIGHT) -> None:
        self.width = width
        self.height = height

    def convert_file(
        self, image_path: str | Path, options: ConvertOptions | None = None
    ) -> bytes:
        self._ensure_pillow()
        opts = options or ConvertOptions()
        img = Image.open(image_path)  # type: ignore[union-attr]
        try:
            return self.convert_image(img, options=opts)
        finally:
            img.close()

    def convert_image(
        self, image: "Image.Image", options: ConvertOptions | None = None
    ) -> bytes:
        self._ensure_pillow()
        opts = options or ConvertOptions()
        prepared = self._prepare_image(image, fit=opts.fit, rotate=opts.rotate)
        indexed = self._quantize(prepared, dither=opts.dither)
        return self._pack_indexed_pixels(indexed)

    def buffer_to_preview(self, buffer: bytes) -> "Image.Image":
        self._ensure_pillow()
        if len(buffer) != BUFFER_SIZE:
            raise ValueError(f"buffer size must be {BUFFER_SIZE} bytes")

        palette_rgb = [
            (0, 0, 0),
            (255, 255, 255),
            (255, 212, 0),
            (220, 0, 0),
        ]

        out = Image.new("RGB", (self.width, self.height))  # type: ignore[union-attr]
        pixels: list[tuple[int, int, int]] = []
        for value in buffer:
            pixels.append(palette_rgb[(value >> 6) & 0x03])
            pixels.append(palette_rgb[(value >> 4) & 0x03])
            pixels.append(palette_rgb[(value >> 2) & 0x03])
            pixels.append(palette_rgb[value & 0x03])
        out.putdata(pixels)
        return out

    def _prepare_image(
        self, image: "Image.Image", fit: str, rotate: int
    ) -> "Image.Image":
        img = image.convert("RGB")

        if rotate not in {0, 90, 180, 270}:
            raise ValueError("rotate must be one of: 0, 90, 180, 270")
        if rotate:
            img = img.rotate(rotate, expand=True)

        if fit == "contain":
            img.thumbnail((self.width, self.height), self._resample())
            canvas = Image.new("RGB", (self.width, self.height), (255, 255, 255))  # type: ignore[union-attr]
            ox = (self.width - img.width) // 2
            oy = (self.height - img.height) // 2
            canvas.paste(img, (ox, oy))
            return canvas

        if fit == "cover":
            return ImageOps.fit(img, (self.width, self.height), method=self._resample())  # type: ignore[union-attr]

        if fit == "stretch":
            return img.resize((self.width, self.height), self._resample())

        raise ValueError("fit must be one of: contain, cover, stretch")

    def _quantize(self, image: "Image.Image", dither: bool) -> "Image.Image":
        palette = Image.new("P", (1, 1))  # type: ignore[union-attr]
        # Index map: 0=black, 1=white, 2=yellow, 3=red
        palette_data = [0, 0, 0, 255, 255, 255, 255, 212, 0, 220, 0, 0] + [0] * (
            256 * 3 - 12
        )
        palette.putpalette(palette_data)

        dither_mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE  # type: ignore[union-attr]
        return image.quantize(palette=palette, dither=dither_mode)

    def _pack_indexed_pixels(self, indexed: "Image.Image") -> bytes:
        data = list(indexed.getdata())
        if len(data) != self.width * self.height:
            raise ValueError("unexpected image size after quantization")

        packed = bytearray()
        for i in range(0, len(data), 4):
            p0 = data[i] & 0x03
            p1 = data[i + 1] & 0x03
            p2 = data[i + 2] & 0x03
            p3 = data[i + 3] & 0x03
            packed.append((p0 << 6) | (p1 << 4) | (p2 << 2) | p3)

        if len(packed) != BUFFER_SIZE:
            raise ValueError(f"packed result size must be {BUFFER_SIZE} bytes")
        return bytes(packed)

    def _ensure_pillow(self) -> None:
        if Image is None or ImageOps is None:
            raise RuntimeError(
                "Pillow is required for image conversion. Install with: pip install Pillow"
            )

    @staticmethod
    def _resample() -> int:
        try:
            return Image.Resampling.LANCZOS  # type: ignore[union-attr]
        except AttributeError:
            return Image.LANCZOS  # type: ignore[union-attr]

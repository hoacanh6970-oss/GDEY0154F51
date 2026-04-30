from __future__ import annotations

import unittest

from gdey0154f51.constants import BUFFER_SIZE
from gdey0154f51.image_converter import ConvertOptions, ImageConverter

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    Image = None


@unittest.skipIf(Image is None, "Pillow not installed")
class ImageConverterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.converter = ImageConverter()

    def test_convert_solid_red_image(self) -> None:
        img = Image.new("RGB", (152, 152), (255, 0, 0))
        try:
            buffer = self.converter.convert_image(
                img, options=ConvertOptions(dither=False)
            )
        finally:
            img.close()

        self.assertEqual(len(buffer), BUFFER_SIZE)

    def test_convert_resizes_input(self) -> None:
        img = Image.new("RGB", (400, 200), (255, 255, 255))
        try:
            buffer = self.converter.convert_image(
                img, options=ConvertOptions(fit="cover", dither=False)
            )
        finally:
            img.close()

        self.assertEqual(len(buffer), BUFFER_SIZE)


if __name__ == "__main__":
    unittest.main()

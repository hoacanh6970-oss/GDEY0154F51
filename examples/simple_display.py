from __future__ import annotations

from gdey0154f51 import GDEY0154F51

# Replace image path with your local file.
IMAGE_PATH = "test.png"


def main() -> None:
    with GDEY0154F51.from_rpi() as epd:
        epd.display_image(
            IMAGE_PATH, dither=True, fit="contain", rotate=0, auto_sleep=True
        )


if __name__ == "__main__":
    main()

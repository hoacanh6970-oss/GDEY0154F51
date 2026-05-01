from __future__ import annotations

import textwrap

from gdey0154f51.constants import HEIGHT, WIDTH

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]


def render_text_image(text: str, title: str | None = None):
    _ensure_pillow()
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))  # type: ignore[union-attr]
    draw = ImageDraw.Draw(canvas)  # type: ignore[union-attr]
    font = ImageFont.load_default()  # type: ignore[union-attr]

    y = 6
    if title:
        draw.rectangle((0, 0, WIDTH, 18), fill=(255, 212, 0))
        draw.text((4, 4), title[:20], fill=(0, 0, 0), font=font)
        y = 24

    for line in _wrap_lines(text, width=21):
        if y > HEIGHT - 10:
            break
        draw.text((4, y), line, fill=(0, 0, 0), font=font)
        y += 10

    return canvas


def render_todo_image(items: list[tuple[str, bool]], title: str = "TODO"):
    _ensure_pillow()
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))  # type: ignore[union-attr]
    draw = ImageDraw.Draw(canvas)  # type: ignore[union-attr]
    font = ImageFont.load_default()  # type: ignore[union-attr]

    draw.rectangle((0, 0, WIDTH, 18), fill=(255, 212, 0))
    draw.text((4, 4), title[:20], fill=(0, 0, 0), font=font)

    y = 24
    for text, done in items:
        prefix = "[x] " if done else "[ ] "
        wrapped = _wrap_lines(prefix + text, width=21)
        for line in wrapped:
            if y > HEIGHT - 10:
                return canvas
            draw.text((4, y), line, fill=(220, 0, 0) if done else (0, 0, 0), font=font)
            y += 10
        y += 2

    return canvas


def _wrap_lines(text: str, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        if not paragraph:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=width, replace_whitespace=False))
    return lines


def _ensure_pillow() -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError("Pillow is required for rendering text/todo")

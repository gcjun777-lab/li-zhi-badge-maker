from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import BadgeRecord, DEFAULT_SUBHEADLINE, build_headline
from .resources import DEFAULT_FONT, LOWER_TEMPLATE, UPPER_TEMPLATE, ensure_assets_exist, resolve_path


CANVAS_WIDTH = 319
CANVAS_HEIGHT = 508
# Derived from the full SVG template geometry so the portrait sits lower and larger,
# matching the provided reference badge instead of the compressed preview layout.
PERSON_BOX = (44, 22, 275, 344)
TEXT_COLOR = (255, 255, 255, 255)
UPPER_OFFSET_Y = 212


@dataclass(frozen=True)
class TextBlock:
    top: int
    height: int
    left: int = 24
    right: int = CANVAS_WIDTH - 24
    font_size: int = 32
    min_font_size: int = 14
    letter_spacing: int = 0
    space_extra: int = 0


NAME_BLOCK = TextBlock(top=299, height=72, font_size=42, min_font_size=22, letter_spacing=2)
HEADLINE_BLOCK = TextBlock(top=386, height=34, font_size=22, min_font_size=12, letter_spacing=3)
SUBHEADLINE_BLOCK = TextBlock(top=428, height=26, font_size=16, min_font_size=10, letter_spacing=2, space_extra=2)


def _open_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(DEFAULT_FONT), size=size)
    except OSError:
        return ImageFont.load_default()


def _fit_font(
    text: str,
    max_width: int,
    start_size: int,
    min_size: int,
    letter_spacing: int = 0,
) -> ImageFont.ImageFont:
    if not text:
        return _get_font(min_size)
    for size in range(start_size, min_size - 1, -1):
        font = _get_font(size)
        text_width, _ = _measure_text(text, font, letter_spacing)
        if text_width <= max_width:
            return font
    return _get_font(min_size)


def _measure_text(
    text: str,
    font: ImageFont.ImageFont,
    letter_spacing: int = 0,
    space_extra: int = 0,
) -> tuple[int, int]:
    if not text:
        return 0, 0
    if letter_spacing <= 0:
        left, top, right, bottom = font.getbbox(text)
        return right - left, bottom - top

    widths = []
    heights = []
    for char in text:
        left, top, right, bottom = font.getbbox(char)
        char_width = right - left
        if char == " ":
            char_width += space_extra
        widths.append(char_width)
        heights.append(bottom - top)
    total_width = sum(widths) + letter_spacing * max(len(text) - 1, 0)
    return total_width, max(heights, default=0)


def _draw_spaced_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    letter_spacing: int,
    space_extra: int,
) -> None:
    if letter_spacing <= 0:
        draw.text((x, y), text, fill=fill, font=font)
        return

    cursor_x = x
    for char in text:
        draw.text((cursor_x, y), char, fill=fill, font=font)
        left, _, right, _ = font.getbbox(char)
        char_width = right - left
        if char == " ":
            char_width += space_extra
        cursor_x += char_width + letter_spacing


def _center_text(draw: ImageDraw.ImageDraw, text: str, block: TextBlock) -> None:
    if not text:
        return
    width = block.right - block.left
    font = _fit_font(
        text,
        width,
        block.font_size,
        block.min_font_size,
        block.letter_spacing,
    )
    text_width, text_height = _measure_text(text, font, block.letter_spacing, block.space_extra)
    x = block.left + max((width - text_width) // 2, 0)
    y = block.top + max((block.height - text_height) // 2, 0)
    _draw_spaced_text(draw, text, x, y, font, TEXT_COLOR, block.letter_spacing, block.space_extra)


def _person_layer(record: BadgeRecord) -> Image.Image:
    source = _open_rgba(resolve_path(record.image_path))
    alpha_bbox = source.getchannel("A").getbbox()
    cropped = source.crop(alpha_bbox) if alpha_bbox else source

    target_left, target_top, target_right, target_bottom = PERSON_BOX
    target_width = target_right - target_left
    target_height = target_bottom - target_top

    scale_w = target_width / max(cropped.width, 1)
    scale_h = target_height / max(cropped.height, 1)
    base_scale = min(scale_w, scale_h) * max(record.scale_adjust, 0.1)
    new_size = (
        max(int(cropped.width * base_scale), 1),
        max(int(cropped.height * base_scale), 1),
    )
    resized = cropped.resize(new_size, Image.Resampling.LANCZOS)

    layer = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    x = target_left + (target_width - resized.width) // 2 + int(record.x_offset)
    y = target_bottom - resized.height + int(record.y_offset)
    layer.alpha_composite(resized, (x, y))
    return layer


def render_badge(record: BadgeRecord) -> Image.Image:
    ensure_assets_exist()
    lower = _open_rgba(LOWER_TEMPLATE)
    upper = _open_rgba(UPPER_TEMPLATE)
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
    canvas.alpha_composite(lower)
    canvas.alpha_composite(_person_layer(record))
    canvas.alpha_composite(upper, (0, UPPER_OFFSET_Y))

    draw = ImageDraw.Draw(canvas)
    headline = build_headline(record.days)
    _center_text(draw, record.name, NAME_BLOCK)
    _center_text(draw, headline, HEADLINE_BLOCK)
    _center_text(draw, DEFAULT_SUBHEADLINE, SUBHEADLINE_BLOCK)
    return canvas


def export_badge(record: BadgeRecord, output_dir: str | Path) -> Path:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    image = render_badge(record)
    target_path = output_root / record.output_name
    image.save(target_path)
    return target_path

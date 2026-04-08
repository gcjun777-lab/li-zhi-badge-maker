from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .models import BadgeRecord, build_headline
from .resources import DEFAULT_FONT, LOWER_TEMPLATE, UPPER_TEMPLATE, ensure_assets_exist, resolve_path


CANVAS_WIDTH = 319
CANVAS_HEIGHT = 413
PERSON_BOX = (34, 18, 285, 252)
TEXT_COLOR = (255, 255, 255, 255)
UPPER_OFFSET_Y = CANVAS_HEIGHT - 296


@dataclass(frozen=True)
class TextBlock:
    top: int
    height: int
    left: int = 24
    right: int = CANVAS_WIDTH - 24
    font_size: int = 32
    min_font_size: int = 14


NAME_BLOCK = TextBlock(top=245, height=58, font_size=42, min_font_size=22)
HEADLINE_BLOCK = TextBlock(top=314, height=30, font_size=22, min_font_size=12)
SUBHEADLINE_BLOCK = TextBlock(top=350, height=24, font_size=16, min_font_size=10)


def _open_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(DEFAULT_FONT), size=size)
    except OSError:
        return ImageFont.load_default()


def _fit_font(text: str, max_width: int, start_size: int, min_size: int) -> ImageFont.ImageFont:
    if not text:
        return _get_font(min_size)
    for size in range(start_size, min_size - 1, -1):
        font = _get_font(size)
        left, _, right, _ = font.getbbox(text)
        if right - left <= max_width:
            return font
    return _get_font(min_size)


def _center_text(draw: ImageDraw.ImageDraw, text: str, block: TextBlock) -> None:
    if not text:
        return
    width = block.right - block.left
    font = _fit_font(text, width, block.font_size, block.min_font_size)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    x = block.left + max((width - text_width) // 2, 0)
    y = block.top + max((block.height - text_height) // 2, 0)
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)


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
    headline = record.headline or build_headline(record.days)
    _center_text(draw, record.name, NAME_BLOCK)
    _center_text(draw, headline, HEADLINE_BLOCK)
    _center_text(draw, record.subheadline, SUBHEADLINE_BLOCK)
    return canvas


def export_badge(record: BadgeRecord, output_dir: str | Path) -> Path:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    image = render_badge(record)
    target_path = output_root / record.output_name
    image.save(target_path)
    return target_path


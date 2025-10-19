"""
UI Components for Smart Panel
Reusable visual components for the dashboard
"""

import logging
from PIL import ImageFont
from .config import get_colors, load_config

logger = logging.getLogger('SmartPanel.UI')

# Load configuration for font sizes
_config = load_config()
_font_size_small = _config.get('font_size_small', 11)
_font_size_medium = _config.get('font_size_medium', 14)

# Initialize fonts with better readability
try:
    # Try DejaVu Sans Mono (monospace, good for TFT)
    FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", _font_size_small)
    FONT_M = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", _font_size_medium)
    logger.info(f"Loaded bold fonts: S={_font_size_small}px, M={_font_size_medium}px")
except Exception:
    try:
        # Fallback to regular DejaVu
        FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", _font_size_small)
        FONT_M = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", _font_size_medium)
        logger.info(f"Loaded regular fonts: S={_font_size_small}px, M={_font_size_medium}px")
    except Exception as e:
        logger.warning(f"Could not load TrueType fonts: {e}, using default")
        FONT_S = ImageFont.load_default()
        FONT_M = ImageFont.load_default()


def get_font_small():
    """Get small font"""
    return FONT_S


def get_font_medium():
    """Get medium font"""
    return FONT_M


class UIComponent:
    """Base class for UI components"""
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height

    def render(self, draw, **kwargs):
        """Override in subclasses"""
        pass


class ProgressBar(UIComponent):
    """Visual progress bar component"""
    def render(self, draw, value=0.0, max_value=1.0, color=None, bg_color=None, **kwargs):
        colors = get_colors()
        color = color or colors['accent']
        bg_color = bg_color or (50, 50, 50)

        # Background
        draw.rectangle([self.x, self.y, self.x + self.width, self.y + self.height], fill=bg_color)

        # Progress
        if value > 0:
            prog_width = int(self.width * min(1.0, value / max_value))
            draw.rectangle([self.x, self.y, self.x + prog_width, self.y + self.height], fill=color)


class TextDisplay(UIComponent):
    """Text display component with alignment"""
    def render(self, draw, text="", font=None, color=None, align="left", **kwargs):
        colors = get_colors()
        font = font or FONT_S
        color = color or colors['fg']

        if align == "center":
            text_width = draw.textlength(text, font=font)
            x = self.x + (self.width - text_width) // 2
        elif align == "right":
            text_width = draw.textlength(text, font=font)
            x = self.x + self.width - text_width
        else:
            x = self.x

        draw.text((x, self.y), text, font=font, fill=color)


class Button(UIComponent):
    """Interactive button component"""
    def __init__(self, x, y, width, height, text="", callback=None, enabled=True):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.enabled = enabled
        self.pressed = False

    def render(self, draw, **kwargs):
        colors = get_colors()
        color = colors['accent'] if self.enabled else colors['disabled']
        if self.pressed:
            color = colors['highlight']

        # Button background
        draw.rectangle([self.x, self.y, self.x + self.width, self.y + self.height], fill=color)

        # Button text (centered)
        if self.text:
            text_width = draw.textlength(self.text, font=FONT_S)
            text_x = self.x + (self.width - text_width) // 2
            text_y = self.y + (self.height - 12) // 2
            text_color = COLORS['bg'] if self.enabled else COLORS['fg']
            draw.text((text_x, text_y), self.text, font=FONT_S, fill=text_color)


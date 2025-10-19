"""
Display Management for Smart Panel
TFT display initialization and rendering
"""

import logging
from luma.core.interface.serial import spi as luma_spi
from luma.lcd.device import st7735 as LCD_ST7735
from PIL import Image, ImageDraw

try:
    from luma.lcd.device import st7735r as LCD_ST7735R
    HAS_ST7735R = True
except Exception:
    HAS_ST7735R = False

from .config import (
    PIN_DC, PIN_RST, SPI_PORT, SPI_DEVICE, SPI_SPEED,
    TRIM_RIGHT, TRIM_BOTTOM, get_colors, load_config
)

logger = logging.getLogger('SmartPanel.Display')


class Display:
    """Display manager for TFT screen"""
    
    def __init__(self, x_offset=0, y_offset=0, config=None):
        self.config = config or load_config()
        self.colors = get_colors(self.config)
        
        logger.info(f"Initializing display with offset ({x_offset}, {y_offset})")
        self.device = self._create_device(x_offset, y_offset)
        self.width, self.height = self.device.size
        logger.info(f"Display size: {self.width}x{self.height}")
        self.clear()
    
    def _create_device(self, xoff, yoff):
        """Create display device with offsets"""
        rotate = self.config.get('display_rotate', 1)
        bgr = self.config.get('display_bgr', True)
        invert = self.config.get('display_invert', False)
        
        logger.debug(f"Display config: rotate={rotate}, bgr={bgr}, invert={invert}")
        
        try:
            ser = luma_spi(
                port=SPI_PORT,
                device=SPI_DEVICE,
                gpio_DC=PIN_DC,
                gpio_RST=PIN_RST,
                bus_speed_hz=SPI_SPEED
            )
        except Exception as e:
            logger.error(f"Failed to initialize SPI: {e}", exc_info=True)
            raise
        
        def build(dev_cls, w, h):
            # Try h_offset/v_offset
            try:
                return dev_cls(ser, width=w, height=h, rotate=rotate, 
                             invert=invert, bgr=bgr,
                             h_offset=xoff, v_offset=yoff)
            except TypeError:
                pass
            
            # Try offset_left/offset_top
            try:
                return dev_cls(ser, width=w, height=h, rotate=rotate,
                             invert=invert, bgr=bgr,
                             offset_left=xoff, offset_top=yoff)
            except TypeError:
                pass
            
            # No offset params supported
            return dev_cls(ser, width=w, height=h, rotate=rotate,
                         invert=invert, bgr=bgr)
        
        if HAS_ST7735R:
            return build(LCD_ST7735R, 128, 160)
        else:
            return build(LCD_ST7735, 160, 128)
    
    def clear(self):
        """Clear the display"""
        img = Image.new("RGB", (self.width, self.height), self.colors['bg'])
        self.device.display(img)
        logger.debug("Display cleared")
    
    def render(self, render_func):
        """
        Render content using a render function
        render_func should accept (draw, width, height) parameters
        """
        try:
            img = Image.new('RGB', (self.width, self.height), self.colors['bg'])
            draw = ImageDraw.Draw(img)
            
            # Edge cleanup
            if TRIM_RIGHT:
                draw.rectangle([self.width - TRIM_RIGHT, 0, 
                              self.width - 1, self.height - 1], 
                             fill=self.colors['bg'])
            if TRIM_BOTTOM:
                draw.rectangle([0, self.height - TRIM_BOTTOM,
                              self.width - 1, self.height - 1],
                             fill=self.colors['bg'])
            
            # Call render function
            render_func(draw, self.width, self.height)
            
            # Display
            self.device.display(img)
        except Exception as e:
            logger.error(f"Render error: {e}", exc_info=True)
    
    def show_splash(self, text):
        """Show a splash screen with colored bars"""
        def render_splash(draw, w, h):
            bars = [(255,0,0), (0,255,0), (0,0,255), (255,255,255)]
            bar_height = h // len(bars)
            
            for i, color in enumerate(bars):
                draw.rectangle([0, i*bar_height, w-1, (i+1)*bar_height-1], 
                             fill=color)
            
            from .ui_components import FONT_M
            draw.text((6, 6), text, font=FONT_M, fill=(0,0,0))
        
        self.render(render_splash)


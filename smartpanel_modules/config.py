"""
Configuration management for Smart Panel
Handles settings persistence and hardware configuration
"""

import json
import pathlib
import logging

logger = logging.getLogger('SmartPanel.Config')

# ---------- Hardware Configuration ----------
# Display pins
PIN_DC, PIN_RST, PIN_BL = 25, 24, 13
SPI_PORT, SPI_DEVICE, SPI_SPEED = 0, 0, 8_000_000

# Display offsets
OFFSET_PRESETS = [(0, 0), (2, 1), (2, 3)]
OFFSET_STORE = pathlib.Path.home() / ".tft_offset.json"

# Edge cleanup
TRIM_RIGHT = 1
TRIM_BOTTOM = 1

# Input pins
ENC_A, ENC_B, ENC_PUSH = 17, 27, 22

# 6 Configurable buttons (GPIO pins)
BUTTON_PINS = [5, 6, 16, 26, 12, 21]
BUTTON_LABELS = {
    5: "Button 1",
    6: "Button 2", 
    16: "Button 3",
    26: "Button 4",
    12: "Button 5",
    21: "Button 6"
}

# Button functions (configurable via settings)
# Each button is exposed to Matter and can also trigger system functions
BUTTON_FUNCTIONS = {
    'none': 'Matter Button Only',  # Button press only updates Matter state
    'back': 'Back + Matter',
    'select': 'Select + Matter',
    'menu': 'Main Menu + Matter',
    'matter_qr': 'Show QR Code',
    'offset_cycle': 'Cycle Display Offset'
}

# Emergency reset combination (Button 1 + Button 6 for 10 seconds)
EMERGENCY_RESET_BUTTONS = [5, 21]  # First and last button
EMERGENCY_RESET_DURATION = 10.0  # seconds

# UI timing
DT = 0.05  # Main loop delay
TAU = 0.8  # Decay time constant
BUMP_STEP = 0.05  # Encoder bump
BUMP_BTN = 0.10  # Button bump

# Configuration file
CONFIG_FILE = pathlib.Path.home() / ".smartpanel_config.json"

# Default configuration
DEFAULT_CONFIG = {
    'brightness': 100,
    'auto_refresh': True,
    'refresh_interval': 5,
    'gpio_states': {},
    'matter_enabled': True,  # Enabled by default
    'matter_vendor_id': 0xFFF1,
    'matter_product_id': 0x8000,
    'matter_discriminator': 3840,
    'matter_setup_pin': 20202021,
    'display_rotate': 1,
    'display_bgr': True,
    'display_invert': False,
    'font_size_small': 11,  # Increased for better readability
    'font_size_medium': 14,  # Increased for better readability
    'qr_size': 90,  # QR code size for optimal scanning
    'color_scheme': 'default',
    # Button assignments (GPIO pin -> function)
    # All buttons are exposed to Matter, these are additional system functions
    'button_assignments': {
        5: 'none',  # Button 1 - Matter only
        6: 'none',  # Button 2 - Matter only
        16: 'back',  # Button 3 - Back + Matter
        26: 'none',  # Button 4 - Matter only
        12: 'offset_cycle',  # Button 5 - Cycle offset + Matter
        21: 'matter_qr'  # Button 6 - Show QR + Matter
    }
}

# Color schemes for better TFT readability
COLOR_SCHEMES = {
    'default': {
        'bg': (0, 0, 0),
        'fg': (255, 255, 255),  # Pure white for max contrast
        'accent': (0, 255, 0),  # Bright green
        'warning': (255, 200, 0),  # Bright yellow
        'error': (255, 0, 0),  # Bright red
        'disabled': (128, 128, 128),
        'highlight': (0, 150, 255),
        'menu_bg': (0, 40, 80),  # Dark blue
        'menu_fg': (255, 255, 255),
        'menu_sel': (0, 200, 0)  # Bright green
    },
    'high_contrast': {
        'bg': (0, 0, 0),
        'fg': (255, 255, 255),
        'accent': (255, 255, 0),
        'warning': (255, 128, 0),
        'error': (255, 0, 0),
        'disabled': (100, 100, 100),
        'highlight': (0, 255, 255),
        'menu_bg': (0, 0, 0),
        'menu_fg': (255, 255, 255),
        'menu_sel': (255, 255, 0)
    }
}

# ---------- Configuration Management ----------

def get_colors(config=None):
    """Get color scheme based on configuration"""
    if config is None:
        config = load_config()
    
    scheme_name = config.get('color_scheme', 'default')
    return COLOR_SCHEMES.get(scheme_name, COLOR_SCHEMES['default'])


def load_config():
    """Load configuration from file with defaults"""
    config = DEFAULT_CONFIG.copy()
    
    try:
        if CONFIG_FILE.exists():
            user_config = json.loads(CONFIG_FILE.read_text())
            config.update(user_config)
            logger.info(f"Configuration loaded from {CONFIG_FILE}")
        else:
            logger.info("Using default configuration")
            save_config(config)  # Save defaults
    except Exception as e:
        logger.error(f"Error loading config: {e}", exc_info=True)
    
    return config


def save_config(config):
    """Save configuration to file"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(config, indent=2, sort_keys=True))
        logger.info(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)


def reset_config():
    """Reset configuration to defaults"""
    try:
        logger.warning("Resetting configuration to defaults")
        save_config(DEFAULT_CONFIG.copy())
        return True
    except Exception as e:
        logger.error(f"Error resetting config: {e}", exc_info=True)
        return False

def load_offset_idx():
    """Load display offset index"""
    try:
        if OFFSET_STORE.exists():
            data = json.loads(OFFSET_STORE.read_text())
            idx = int(data.get("idx", 1)) % len(OFFSET_PRESETS)
            logger.debug(f"Loaded offset index: {idx}")
            return idx
    except Exception as e:
        logger.error(f"Error loading offset: {e}", exc_info=True)
    
    return 1  # Default to (2,1)


def save_offset_idx(idx):
    """Save display offset index"""
    try:
        OFFSET_STORE.parent.mkdir(parents=True, exist_ok=True)
        OFFSET_STORE.write_text(json.dumps({"idx": idx}))
        logger.debug(f"Saved offset index: {idx}")
    except Exception as e:
        logger.error(f"Error saving offset: {e}", exc_info=True)


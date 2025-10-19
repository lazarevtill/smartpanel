#!/usr/bin/env python3
"""
Smart Panel v2.0 - Enhanced Raspberry Pi Control Dashboard
Modular architecture with menu system, system monitoring, GPIO control, and Matter IoT

Controls:
- Rotary Encoder: Navigate menus and adjust values
- Short Press (Encoder): Select items / Toggle devices
- Long Press (Encoder): Go back to previous menu
- B3: Alternative back button
- B5: Cycle display offset presets
- B6: Rescan Matter devices
- B7: Show/hide Matter QR code
"""

import os
import time
import subprocess
import logging
from datetime import datetime

# Set GPIO factory for Debian 13 (Trixie)
os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

import RPi.GPIO as GPIO

# Configure logging
log_dir = os.path.join(os.path.expanduser("~"), ".smartpanel_logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"smartpanel_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger('SmartPanel')

# Import Smart Panel modules
from smartpanel_modules.config import (
    PIN_BL, DT, OFFSET_PRESETS, BUTTON_LABELS,
    load_config, save_config, load_offset_idx, save_offset_idx
)
from smartpanel_modules.display import Display
from smartpanel_modules.input_handler import InputHandler
from smartpanel_modules.menu_system import Menu, MenuItem
from smartpanel_modules.screens import (
    MenuScreen, SystemInfoScreen, GPIOControlScreen,
    MatterDevicesScreen, SettingsScreen, AboutScreen
)
from smartpanel_modules.gpio_control import init_gpio_control
from smartpanel_modules.config import ENC_A, ENC_B, ENC_PUSH, BUTTON_PINS


# ---------- Menu Actions ----------

def show_system_info(context):
    """Show system information screen"""
    return SystemInfoScreen()


def show_gpio_control(context):
    """Show GPIO control screen"""
    return GPIOControlScreen()


def show_matter_devices(context):
    """Show Matter devices screen"""
    return MatterDevicesScreen()


def show_settings(context):
    """Show settings screen"""
    return SettingsScreen(context['config'])


def show_about(context):
    """Show about screen"""
    return AboutScreen()


def shutdown_system(context):
    """Shutdown the system"""
    logger.warning("System shutdown requested")
    try:
        subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=False)
    except Exception as e:
        logger.error(f"Shutdown failed: {e}")
    return None


def restart_system(context):
    """Restart the system"""
    logger.warning("System restart requested")
    try:
        subprocess.run(['sudo', 'reboot'], check=False)
    except Exception as e:
        logger.error(f"Reboot failed: {e}")
    return None


# ---------- Main Application ----------

class SmartPanel:
    """Main Smart Panel application"""
    
    def __init__(self):
        logger.info("=" * 50)
        logger.info("Smart Panel v2.0 - Initializing")
        logger.info("=" * 50)
        
        # Initialize GPIO
        logger.debug("Initializing GPIO")
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        try:
            GPIO.cleanup()
        except Exception as e:
            logger.debug(f"GPIO cleanup: {e}")
        GPIO.setup(PIN_BL, GPIO.OUT, initial=GPIO.HIGH)
        
        # Load configuration
        logger.info("Loading configuration")
        self.config = load_config()
        self.offset_idx = load_offset_idx()
        logger.debug(f"Config loaded: {len(self.config)} settings")
        
        # Initialize display
        logger.info(f"Initializing display with offset {OFFSET_PRESETS[self.offset_idx]}")
        xoff, yoff = OFFSET_PRESETS[self.offset_idx]
        self.display = Display(xoff, yoff)
        logger.info(f"Display initialized: {self.display.width}x{self.display.height}")
        
        # Initialize input handler
        logger.info("Initializing input handler")
        self.input_handler = InputHandler(ENC_A, ENC_B, ENC_PUSH, BUTTON_PINS)
        
        # Initialize GPIO control
        logger.info("Initializing GPIO control")
        init_gpio_control()
        
        # Create main menu
        logger.debug("Creating main menu")
        self.main_menu = self._create_main_menu()
        
        # Current screen
        self.current_screen = MenuScreen(self.main_menu)
        self.screen_stack = []
        
        logger.info(f"Matter: {'Enabled' if self.config.get('matter_enabled') else 'Disabled'}")
        logger.info("Initialization complete")
        logger.info("Controls: Rotate=Navigate, Short Press=Select, Long Press=Back")
        logger.info("Buttons: B5=Offset, B6=Scan, B7=QR Code")
        logger.info(f"Logs: {log_file}")
    
    def _create_main_menu(self):
        """Create the main menu structure"""
        menu = Menu("Smart Panel")
        menu.add_item(MenuItem("System Info", action=show_system_info))
        menu.add_item(MenuItem("GPIO Control", action=show_gpio_control))
        menu.add_item(MenuItem("Matter Devices", action=show_matter_devices))
        menu.add_item(MenuItem("Settings", action=show_settings))
        menu.add_item(MenuItem("About", action=show_about))
        menu.add_item(MenuItem("Shutdown", action=shutdown_system))
        menu.add_item(MenuItem("Restart", action=restart_system))
        return menu
    
    def run(self):
        """Main application loop"""
        logger.info("Starting main loop")
        try:
            while True:
                # Get input
                enc_delta = self.input_handler.get_encoder_delta()
                enc_button_state = self.input_handler.get_encoder_button_state()
                button_states = self.input_handler.get_button_states()
                
                # Log input events
                if enc_delta != 0:
                    logger.debug(f"Encoder: delta={enc_delta}")
                if enc_button_state != 'none':
                    logger.debug(f"Encoder button: {enc_button_state}")
                if any(button_states.values()):
                    pressed = [BUTTON_LABELS.get(p, f'GPIO{p}') for p, v in button_states.items() if v]
                    logger.debug(f"Buttons pressed: {pressed}")
                
                # Handle special buttons
                if 12 in button_states and button_states[12]:  # B5: cycle offsets
                    logger.info("Cycling display offset")
                    self._cycle_offset()
                    continue
                
                # Handle input
                if enc_delta != 0 or enc_button_state != 'none' or any(button_states.values()):
                    # Create context for menu actions
                    context = {
                        'config': self.config,
                        'panel': self
                    }
                    
                    # Pass context to screen if it's a MenuScreen
                    if isinstance(self.current_screen, MenuScreen):
                        # Store context in menu for actions to use
                        self.current_screen.menu.context = context
                    
                    result = self.current_screen.handle_input(
                        enc_delta, enc_button_state, button_states
                    )
                    
                    # Handle screen transitions
                    if result == 'back':
                        logger.debug("Navigating back")
                        if self.screen_stack:
                            self.current_screen = self.screen_stack.pop()
                            logger.debug(f"Returned to: {self.current_screen.title}")
                        else:
                            self.current_screen = MenuScreen(self.main_menu)
                            logger.debug("Returned to main menu")
                    elif result and result != self.current_screen:
                        logger.debug(f"Screen transition: {self.current_screen.title} -> {result.title}")
                        self.screen_stack.append(self.current_screen)
                        self.current_screen = result
                
                # Render current screen
                self.display.render(self.current_screen.render)
                
                # Sleep
                time.sleep(DT)
        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            logger.info("Shutting down Smart Panel")
            GPIO.cleanup()
            logger.info("Cleanup complete")
    
    def _cycle_offset(self):
        """Cycle through display offset presets"""
        try:
            self.offset_idx = (self.offset_idx + 1) % len(OFFSET_PRESETS)
            save_offset_idx(self.offset_idx)
            
            # Reinitialize display with new offset
            xoff, yoff = OFFSET_PRESETS[self.offset_idx]
            logger.info(f"Changing display offset to: ({xoff}, {yoff})")
            self.display = Display(xoff, yoff)
            
            # Show splash
            self.display.show_splash(f"Offset: {xoff},{yoff}")
            time.sleep(1)
            
            logger.info(f"Display offset changed successfully")
        except Exception as e:
            logger.error(f"Error cycling offset: {e}", exc_info=True)


# ---------- Entry Point ----------

def main():
    """Application entry point"""
    panel = SmartPanel()
    panel.run()


if __name__ == "__main__":
    main()


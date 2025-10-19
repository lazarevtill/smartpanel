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
    load_config, save_config, load_offset_idx, save_offset_idx, get_colors
)
from smartpanel_modules.display import Display
from smartpanel_modules.input_handler import InputHandler
from smartpanel_modules.menu_system import Menu, MenuItem
from smartpanel_modules.screens import (
    MenuScreen, SystemInfoScreen, GPIOControlScreen,
    MatterDevicesScreen, SettingsScreen, AboutScreen, ButtonConfigScreen
)
from smartpanel_modules.button_manager import ButtonManager
from smartpanel_modules.matter_server import MatterServer
from smartpanel_modules.gpio_control import init_gpio_control
from smartpanel_modules.config import ENC_A, ENC_B, ENC_PUSH, BUTTON_PINS


# ---------- Menu Actions ----------

def show_system_info(context):
    """Show system information screen"""
    return SystemInfoScreen()


def show_gpio_control(context):
    """Show GPIO control screen"""
    return GPIOControlScreen()


def show_matter_status(context):
    """Show Matter server status and pairing QR code"""
    return MatterDevicesScreen(context['matter_server'])


def show_button_config(context):
    """Show button configuration screen"""
    return ButtonConfigScreen(context['button_manager'], context.get('matter_server'))


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
        self.display = Display(xoff, yoff, self.config)
        logger.info(f"Display initialized: {self.display.width}x{self.display.height}")
        
        # Initialize input handler
        logger.info("Initializing input handler")
        self.input_handler = InputHandler(ENC_A, ENC_B, ENC_PUSH, BUTTON_PINS)
        
        # Initialize GPIO control
        logger.info("Initializing GPIO control")
        init_gpio_control()
        
        # Initialize button manager
        logger.info("Initializing button manager")
        self.button_manager = ButtonManager(self.config)
        
        # Initialize Matter server
        logger.info("Initializing Matter server")
        self.matter_server = MatterServer(self.config, BUTTON_PINS)
        
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
        menu.add_item(MenuItem("Matter Status", action=show_matter_status))
        menu.add_item(MenuItem("Button Config", action=show_button_config))
        menu.add_item(MenuItem("GPIO Control", action=show_gpio_control))
        menu.add_item(MenuItem("Settings", action=show_settings))
        menu.add_item(MenuItem("About", action=show_about))
        
        # Power submenu
        power_menu = Menu("Power")
        power_menu.add_item(MenuItem("Shutdown", action=shutdown_system))
        power_menu.add_item(MenuItem("Restart", action=restart_system))
        menu.add_item(MenuItem("Power", submenu=power_menu))
        
        return menu
    
    def run(self):
        """Main application loop"""
        logger.info("Starting main loop")
        try:
            while True:
                # Check for emergency reset FIRST
                reset_status, reset_progress = self.input_handler.check_emergency_reset()
                
                if reset_status == 'triggered':
                    logger.critical("EMERGENCY RESET - Restarting Smart Panel")
                    self._emergency_reset()
                    break
                elif reset_status == 'active':
                    # Show emergency reset progress on display
                    self._show_emergency_reset_progress(reset_progress)
                    time.sleep(0.1)
                    continue
                
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
                
                # Handle physical button presses through button manager
                for pin, pressed in button_states.items():
                    if pressed:
                        context = {
                            'config': self.config,
                            'panel': self,
                            'matter_server': self.matter_server,
                            'button_manager': self.button_manager
                        }
                        action = self.button_manager.handle_button_press(pin, context)
                        
                        if action == 'offset_cycle':
                            logger.info("Cycling display offset")
                            self._cycle_offset()
                            continue
                        elif action == 'matter_qr':
                            # Navigate to Matter status screen
                            self.screen_stack.append(self.current_screen)
                            self.current_screen = MatterDevicesScreen(self.matter_server)
                            self.current_screen.show_qr = True
                            continue
                        elif action == 'back':
                            if self.screen_stack:
                                self.current_screen = self.screen_stack.pop()
                            else:
                                self.current_screen = MenuScreen(self.main_menu)
                            continue
                
                # Handle encoder input
                if enc_delta != 0 or enc_button_state != 'none':
                    # Create context for menu actions
                    context = {
                        'config': self.config,
                        'panel': self,
                        'matter_server': self.matter_server,
                        'button_manager': self.button_manager
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
            
            # Stop Matter server
            if hasattr(self, 'matter_server'):
                logger.info("Stopping Matter server")
                self.matter_server.stop()
            
            # Cleanup GPIO
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
            self.display = Display(xoff, yoff, self.config)
            
            # Show splash
            self.display.show_splash(f"Offset: {xoff},{yoff}")
            time.sleep(1)
            
            logger.info(f"Display offset changed successfully")
        except Exception as e:
            logger.error(f"Error cycling offset: {e}", exc_info=True)
    
    def _show_emergency_reset_progress(self, progress):
        """Show emergency reset progress on display"""
        def render_reset(draw, w, h):
            from smartpanel_modules.ui_components import FONT_M, FONT_S
            colors = get_colors(self.config)
            
            # Title - centered and shortened to fit
            title = "EMERGENCY"
            title_width = draw.textlength(title, font=FONT_M)
            draw.text(((w - title_width) // 2, 15), title, font=FONT_M, fill=colors['error'])
            
            subtitle = "RESET"
            subtitle_width = draw.textlength(subtitle, font=FONT_M)
            draw.text(((w - subtitle_width) // 2, 30), subtitle, font=FONT_M, fill=colors['error'])
            
            # Progress bar
            bar_width = w - 16
            bar_height = 28
            bar_x = 8
            bar_y = h//2 - 10
            
            # Background
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                         outline=colors['error'], fill=colors['bg'])
            
            # Progress fill
            fill_width = int(bar_width * progress / 100)
            if fill_width > 4:  # Only draw if wide enough
                draw.rectangle([bar_x + 2, bar_y + 2, 
                              bar_x + fill_width - 2, bar_y + bar_height - 2], 
                             fill=colors['error'])
            
            # Percentage text - centered
            text = f"{progress}%"
            text_width = draw.textlength(text, font=FONT_M)
            draw.text(((w - text_width) // 2, bar_y + 8), text, font=FONT_M, fill=colors['fg'])
            
            # Instructions - centered and shortened
            instruction = "Release=Cancel"
            inst_width = draw.textlength(instruction, font=FONT_S)
            draw.text(((w - inst_width) // 2, h - 25), instruction, font=FONT_S, fill=colors['warning'])
        
        self.display.render(render_reset)
    
    def _emergency_reset(self):
        """Perform emergency reset"""
        from smartpanel_modules.config import reset_config
        
        logger.warning("Performing emergency reset")
        
        # Reset configuration
        if reset_config():
            logger.info("Configuration reset to defaults")
        
        # Show confirmation
        def render_confirm(draw, w, h):
            from smartpanel_modules.ui_components import FONT_M, FONT_S
            colors = get_colors(self.config)
            
            # Center text properly
            text1 = "RESET"
            text1_width = draw.textlength(text1, font=FONT_M)
            draw.text(((w - text1_width) // 2, h//2 - 20), text1, font=FONT_M, fill=colors['accent'])
            
            text2 = "COMPLETE"
            text2_width = draw.textlength(text2, font=FONT_M)
            draw.text(((w - text2_width) // 2, h//2 - 5), text2, font=FONT_M, fill=colors['accent'])
            
            text3 = "Restarting..."
            text3_width = draw.textlength(text3, font=FONT_S)
            draw.text(((w - text3_width) // 2, h//2 + 15), text3, font=FONT_S, fill=colors['fg'])
        
        self.display.render(render_confirm)
        time.sleep(2)
        
        # Restart the application
        import sys
        import os
        python = sys.executable
        os.execl(python, python, *sys.argv)


# ---------- Entry Point ----------

def main():
    """Application entry point"""
    panel = SmartPanel()
    panel.run()


if __name__ == "__main__":
    main()


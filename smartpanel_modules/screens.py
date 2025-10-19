"""
Screen Classes for Smart Panel
All screen implementations for the dashboard
"""

import time
import logging
from .config import BUTTON_LABELS, BUTTON_PINS, get_colors
from .ui_components import FONT_S, FONT_M
from .system_monitor import get_system_info
from .gpio_control import gpio_states, toggle_gpio_pin
from .matter_integration import MatterController
from .matter_qr import generate_matter_qr_code, get_default_matter_payload, render_qr_to_display, HAS_QRCODE

logger = logging.getLogger('SmartPanel.Screens')

# Get default colors
_default_colors = get_colors()


class BaseScreen:
    """Base class for all screens"""
    def __init__(self, title="Screen"):
        self.title = title
        self.last_update = 0
        self.update_interval = 1.0

    def render(self, draw, width, height):
        """Override in subclasses"""
        pass

    def handle_input(self, enc_delta, enc_button_state, button_states):
        """
        Handle input
        enc_button_state: 'none', 'short_press', 'long_press', 'pressed'
        Returns: next screen or self
        """
        # Long press = go back
        if enc_button_state == 'long_press':
            return 'back'
        return self

    def should_update(self):
        """Check if screen should be updated"""
        return time.time() - self.last_update > self.update_interval

    def mark_updated(self):
        """Mark screen as updated"""
        self.last_update = time.time()


class MenuScreen(BaseScreen):
    """Menu display screen with enhanced navigation"""
    def __init__(self, menu):
        super().__init__(menu.title)
        self.menu = menu

    def render(self, draw, width, height):
        # Title bar with background
        draw.rectangle([0, 0, width-1, 16], fill=_default_colors['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=_default_colors['menu_fg'])
        
        # Separator line
        draw.line([0, 17, width-1, 17], fill=_default_colors['accent'])

        # Menu items
        y_offset = 22
        for i, item in enumerate(self.menu.get_visible_items()):
            y = y_offset + i * 14
            
            if i + self.menu.scroll_offset == self.menu.selected_index:
                # Highlight selected item with rounded effect
                draw.rectangle([2, y-2, width-3, y+11], fill=_default_colors['menu_sel'])
                text_color = _default_colors['bg']
                prefix = "▶ "
            else:
                text_color = _default_colors['fg'] if item.enabled else _default_colors['disabled']
                prefix = "  "

            draw.text((6, y), f"{prefix}{item.title}", font=FONT_S, fill=text_color)

        # Scroll indicator
        if len(self.menu.items) > 6:
            total_items = len(self.menu.items)
            visible_start = self.menu.scroll_offset + 1
            visible_end = min(total_items, self.menu.scroll_offset + 6)
            
            # Draw scroll bar
            scroll_height = height - 25
            bar_height = max(10, scroll_height * 6 // total_items)
            bar_pos = 22 + (scroll_height - bar_height) * self.menu.scroll_offset // max(1, total_items - 6)
            
            draw.rectangle([width-4, 22, width-2, height-3], fill=(40, 40, 40))
            draw.rectangle([width-4, int(bar_pos), width-2, int(bar_pos + bar_height)], 
                         fill=_default_colors['accent'])
            
            # Page indicator
            draw.text((width-32, height-12), f"{visible_start}-{visible_end}/{total_items}",
                     font=FONT_S, fill=_default_colors['disabled'])

    def handle_input(self, enc_delta, enc_button_state, button_states):
        # Encoder rotation - navigate menu
        if enc_delta > 0:
            self.menu.navigate(1)
        elif enc_delta < 0:
            self.menu.navigate(-1)

        # Short press - select item
        if enc_button_state == 'short_press':
            return self.menu.select({})
        
        # Long press - go back
        if enc_button_state == 'long_press':
            if self.menu.parent:
                return MenuScreen(self.menu.parent)
            return self

        # B3 button - also goes back
        if 16 in button_states and button_states[16]:
            if self.menu.parent:
                return MenuScreen(self.menu.parent)

        return self


class SystemInfoScreen(BaseScreen):
    """System information display"""
    def __init__(self):
        super().__init__("System Info")
        self.system_info = {}

    def render(self, draw, width, height):
        if self.should_update():
            self.system_info = get_system_info()
            self.mark_updated()

        # Title
        draw.rectangle([0, 0, width-1, 16], fill=_default_colors['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=_default_colors['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=_default_colors['accent'])

        y = 24
        line_height = 14

        # CPU
        draw.text((4, y), "CPU:", font=FONT_S, fill=_default_colors['fg'])
        cpu = self.system_info.get('cpu', 0)
        self._draw_progress_bar(draw, 50, y, width-54, 10, cpu)
        draw.text((width-28, y), f"{cpu:.0f}%", font=FONT_S, fill=_default_colors['fg'])
        y += line_height

        # Memory
        draw.text((4, y), "RAM:", font=FONT_S, fill=_default_colors['fg'])
        mem = self.system_info.get('memory', 0)
        self._draw_progress_bar(draw, 50, y, width-54, 10, mem)
        draw.text((width-28, y), f"{mem:.0f}%", font=FONT_S, fill=_default_colors['fg'])
        y += line_height

        # Disk
        draw.text((4, y), "Disk:", font=FONT_S, fill=_default_colors['fg'])
        disk = self.system_info.get('disk', 0)
        self._draw_progress_bar(draw, 50, y, width-54, 10, disk)
        draw.text((width-28, y), f"{disk:.0f}%", font=FONT_S, fill=_default_colors['fg'])
        y += line_height

        # Temperature
        temp = self.system_info.get('temperature', 0)
        temp_color = _default_colors['accent'] if temp < 60 else _default_colors['warning'] if temp < 80 else _default_colors['error']
        draw.text((4, y), f"Temp: {temp:.1f}°C", font=FONT_S, fill=temp_color)
        y += line_height

        # Network
        network = self.system_info.get('network', {})
        draw.text((4, y), f"IP: {network.get('ip', 'N/A')}", font=FONT_S, fill=_default_colors['fg'])
        y += line_height

        # Uptime
        draw.text((4, y), f"Up: {self.system_info.get('uptime', 'N/A')}", 
                 font=FONT_S, fill=_default_colors['fg'])

        # Help text
        draw.text((4, height-12), "Long=back", 
                 font=FONT_S, fill=_default_colors['disabled'])

    def _draw_progress_bar(self, draw, x, y, width, height, percentage):
        percentage = max(0, min(100, percentage))
        fill_width = int(width * percentage / 100)

        draw.rectangle([x, y, x + width, y + height], outline=_default_colors['fg'])
        if fill_width > 0:
            color = _default_colors['accent'] if percentage < 80 else _default_colors['warning'] if percentage < 95 else _default_colors['error']
            draw.rectangle([x + 1, y + 1, x + fill_width, y + height - 1], fill=color)


class GPIOControlScreen(BaseScreen):
    """GPIO pin control interface"""
    def __init__(self):
        super().__init__("GPIO Control")
        self.selected_pin = 0
        self.pin_list = sorted(gpio_states.keys())

    def render(self, draw, width, height):
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=_default_colors['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=_default_colors['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=_default_colors['accent'])

        y = 24
        line_height = 14

        if not self.pin_list:
            draw.text((4, y), "No GPIO pins", 
                     font=FONT_S, fill=_default_colors['disabled'])
        else:
            for i, pin in enumerate(self.pin_list[:8]):
                if i == self.selected_pin:
                    draw.rectangle([2, y-2, width-3, y+11], fill=_default_colors['menu_sel'])

                state = gpio_states.get(pin, False)
                state_text = "ON " if state else "OFF"
                state_color = _default_colors['accent'] if state else _default_colors['error']

                pin_text = f"GPIO{pin:2d}"
                draw.text((6, y), pin_text, font=FONT_S, 
                         fill=_default_colors['bg'] if i == self.selected_pin else _default_colors['fg'])
                
                # State indicator
                draw.rectangle([width-38, y, width-8, y+10], fill=state_color)
                draw.text((width-34, y), state_text, font=FONT_S, fill=_default_colors['bg'])

                y += line_height

        # Help text
        draw.text((4, height-12), "Press=toggle", 
                 font=FONT_S, fill=_default_colors['disabled'])

    def handle_input(self, enc_delta, enc_button_state, button_states):
        if not self.pin_list:
            if enc_button_state == 'long_press':
                return 'back'
            return self

        # Navigate pins
        if enc_delta > 0:
            self.selected_pin = (self.selected_pin + 1) % len(self.pin_list)
        elif enc_delta < 0:
            self.selected_pin = (self.selected_pin - 1) % len(self.pin_list)

        # Short press - toggle selected pin
        if enc_button_state == 'short_press':
            pin = self.pin_list[self.selected_pin]
            toggle_gpio_pin(pin)

        # Long press - go back
        if enc_button_state == 'long_press':
            return 'back'

        return self


class MatterDevicesScreen(BaseScreen):
    """Matter server status and pairing information"""
    def __init__(self, matter_server):
        super().__init__("Matter Status")
        self.matter_server = matter_server
        self.show_qr = False  # Toggle for QR code display
        self.scroll_offset = 0
        logger.info("Matter status screen initialized")

    def render(self, draw, width, height):
        colors = get_colors()
        
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=colors['menu_bg'])
        title_text = "Matter QR Code" if self.show_qr else "Matter Status"
        draw.text((4, 2), title_text, font=FONT_M, fill=colors['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=colors['accent'])

        y = 24

        if not self.matter_server.enabled:
            draw.text((4, y), "Matter disabled", font=FONT_S, fill=colors['disabled'])
            draw.text((4, y+15), "Enable in Settings", font=FONT_S, fill=colors['warning'])
        elif self.show_qr:
            # Show QR code for pairing
            self._render_qr_code(draw, width, height, y, colors)
        else:
            # Show Matter server status
            status = self.matter_server.get_status()
            
            # Status line
            status_text = "Running" if status['running'] else "Stopped"
            status_color = colors['accent'] if status['running'] else colors['error']
            draw.text((4, y), f"Status: {status_text}", font=FONT_S, fill=status_color)
            y += 14
            
            # Pairing status
            paired_text = "Paired" if status['paired'] else "Not Paired"
            paired_color = colors['accent'] if status['paired'] else colors['warning']
            draw.text((4, y), f"Pairing: {paired_text}", font=FONT_S, fill=paired_color)
            y += 14
            
            # Simulation mode indicator
            if status['simulation_mode']:
                draw.text((4, y), "Mode: SIMULATION", font=FONT_S, fill=colors['warning'])
                y += 14
            
            # Button count
            draw.text((4, y), f"Buttons: {status['button_count']}", font=FONT_S, fill=colors['fg'])
            y += 16
            
            # Show button states
            draw.text((4, y), "Button States:", font=FONT_S, fill=colors['fg'])
            y += 12
            
            button_states = self.matter_server.get_all_button_states()
            for btn in button_states[:4]:  # Show first 4 buttons
                state_text = "ON " if btn['state'] else "OFF"
                state_color = colors['accent'] if btn['state'] else colors['disabled']
                draw.text((4, y), f"B{btn['id']}: {state_text}", font=FONT_S, fill=state_color)
                y += 12

        # Help text
        if self.show_qr:
            draw.text((4, height-12), "Long press=back", 
                     font=FONT_S, fill=colors['disabled'])
        else:
            draw.text((4, height-12), "Press=QR L=back", 
                     font=FONT_S, fill=colors['disabled'])

    def _render_qr_code(self, draw, width, height, start_y, colors):
        """Render Matter QR code for device commissioning"""
        if not HAS_QRCODE:
            draw.text((4, start_y), "QR code library", font=FONT_S, fill=colors['error'])
            draw.text((4, start_y+12), "not installed", font=FONT_S, fill=colors['error'])
            draw.text((4, start_y+30), "Install qrcode:", font=FONT_S, fill=colors['fg'])
            draw.text((4, start_y+42), "pip3 install", font=FONT_S, fill=colors['fg'])
            draw.text((4, start_y+54), "qrcode[pil]", font=FONT_S, fill=colors['fg'])
            return

        # Generate QR code
        payload = self.matter_server.get_pairing_qr_payload()
        qr_img = generate_matter_qr_code(payload)
        
        if qr_img:
            # Calculate QR size to fit display (leave room for manual code at bottom)
            # Reserve 30 pixels for manual code (2 lines of text + spacing)
            available_height = height - start_y - 42  # 30 for code + 12 for help text
            qr_size = min(width - 16, available_height)
            qr_resized = render_qr_to_display(qr_img, (qr_size, qr_size))
            
            # Center QR code horizontally
            qr_x = (width - qr_size) // 2
            qr_y = start_y + 2
            
            # Draw QR code pixel by pixel (inverted for better visibility on dark bg)
            if qr_resized:
                qr_resized = qr_resized.convert('1')  # Convert to 1-bit black/white
                pixels = qr_resized.load()
                for py in range(qr_resized.height):
                    for px in range(qr_resized.width):
                        if pixels[px, py] == 0:  # Black pixel in QR = white on screen
                            draw.point((qr_x + px, qr_y + py), fill=(255, 255, 255))
                        # White pixels stay as background color (no need to draw)
            
            # Show manual pairing code below QR (ensure it doesn't overlap help text)
            manual_code = self.matter_server.get_manual_pairing_code()
            code_y = qr_y + qr_size + 6
            
            # Clear area for manual code to prevent overlap
            draw.rectangle([0, code_y, width-1, code_y + 24], fill=colors['bg'])
            
            # Draw manual code
            draw.text((4, code_y), "Manual Code:", font=FONT_S, fill=colors['fg'])
            draw.text((4, code_y + 12), manual_code, font=FONT_S, fill=colors['accent'])
        else:
            draw.text((4, start_y), "QR generation", font=FONT_S, fill=colors['error'])
            draw.text((4, start_y+12), "failed", font=FONT_S, fill=colors['error'])

    def handle_input(self, enc_delta, enc_button_state, button_states):
        # Short press - toggle QR code display
        if enc_button_state == 'short_press':
            self.show_qr = not self.show_qr
            logger.info(f"QR code display: {self.show_qr}")
            return self

        # Long press - go back
        if enc_button_state == 'long_press':
            if self.show_qr:
                self.show_qr = False
            else:
                return 'back'

        return self


class SettingsScreen(BaseScreen):
    """Settings configuration screen"""
    def __init__(self, config):
        super().__init__("Settings")
        self.config = config
        self.settings_items = [
            ("Brightness", config.get('brightness', 100), 0, 100, 10),
            ("Auto Refresh", config.get('auto_refresh', True), True, False, 1),
            ("Refresh Interval", config.get('refresh_interval', 5), 1, 30, 1),
            ("Matter Enabled", config.get('matter_enabled', False), True, False, 1)
        ]
        self.selected_setting = 0

    def render(self, draw, width, height):
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=_default_colors['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=_default_colors['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=_default_colors['accent'])

        y = 24
        line_height = 16

        for i, (name, value, min_val, max_val, step) in enumerate(self.settings_items):
            if i == self.selected_setting:
                draw.rectangle([2, y-2, width-3, y+12], fill=_default_colors['menu_sel'])
                text_color = _default_colors['bg']
            else:
                text_color = _default_colors['fg']

            # Setting name
            draw.text((6, y), name, font=FONT_S, fill=text_color)

            # Setting value
            if isinstance(value, bool):
                val_text = "ON" if value else "OFF"
                val_color = _default_colors['accent'] if value else _default_colors['error']
                if i == self.selected_setting:
                    val_color = _default_colors['bg']
            else:
                val_text = str(value)
                val_color = text_color

            draw.text((width-35, y), val_text, font=FONT_S, fill=val_color)
            y += line_height

        # Help text
        draw.text((4, height-12), "Rot=chg Press=next", 
                 font=FONT_S, fill=_default_colors['disabled'])

    def handle_input(self, enc_delta, enc_button_state, button_states):
        # Encoder rotation - adjust value
        if enc_delta != 0:
            name, value, min_val, max_val, step = self.settings_items[self.selected_setting]
            
            if isinstance(value, bool):
                new_value = not value
            else:
                new_value = value + (step * enc_delta)
                new_value = max(min_val, min(max_val, new_value))
            
            self.settings_items[self.selected_setting] = (name, new_value, min_val, max_val, step)
            
            # Update config
            setting_name = name.lower().replace(" ", "_")
            self.config[setting_name] = new_value
            from .config import save_config
            save_config(self.config)

        # Short press - next setting
        if enc_button_state == 'short_press':
            self.selected_setting = (self.selected_setting + 1) % len(self.settings_items)

        # Long press - go back
        if enc_button_state == 'long_press':
            return 'back'

        return self


class ButtonConfigScreen(BaseScreen):
    """Button configuration screen"""
    def __init__(self, button_manager, matter_controller=None):
        super().__init__("Button Config")
        self.button_manager = button_manager
        self.matter_controller = matter_controller
        self.selected_button = 0
        self.editing_mode = False  # False = select button, True = select function
        self.function_scroll = 0
        self.available_functions = button_manager.get_available_functions()
        logger.info("Button config screen initialized")
    
    def render(self, draw, width, height):
        colors = get_colors()
        
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=colors['menu_bg'])
        title_text = "Edit Function" if self.editing_mode else "Button Config"
        draw.text((4, 2), title_text, font=FONT_M, fill=colors['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=colors['accent'])
        
        if not self.editing_mode:
            # Show button list
            y = 24
            line_height = 14
            
            assignments = self.button_manager.get_all_assignments()
            for i, assignment in enumerate(assignments[:6]):
                if i == self.selected_button:
                    draw.rectangle([2, y-2, width-3, y+11], fill=colors['menu_sel'])
                    text_color = colors['bg']
                else:
                    text_color = colors['fg']
                
                # Button label
                label = assignment['label'][:3]  # Shorten to fit
                draw.text((4, y), label, font=FONT_S, fill=text_color)
                
                # Function name (truncated)
                func_name = assignment['function_name'][:12]
                draw.text((30, y), func_name, font=FONT_S, fill=text_color)
                
                # Matter device indicator
                if assignment['matter_device']:
                    draw.text((width-12, y), "M", font=FONT_S, fill=colors['accent'])
                
                y += line_height
            
            # Help text
            draw.text((4, height-12), "P=edit L=back", 
                     font=FONT_S, fill=colors['disabled'])
        else:
            # Show function selection
            y = 24
            line_height = 14
            
            visible_functions = self.available_functions[self.function_scroll:self.function_scroll+7]
            for i, func_key in enumerate(visible_functions):
                actual_idx = i + self.function_scroll
                current_func = self.button_manager.get_button_function(
                    BUTTON_PINS[self.selected_button]
                )
                
                if func_key == current_func:
                    draw.rectangle([2, y-2, width-3, y+11], fill=colors['accent'])
                    text_color = colors['bg']
                else:
                    text_color = colors['fg']
                
                func_name = self.button_manager.get_function_name(func_key)
                draw.text((6, y), func_name[:18], font=FONT_S, fill=text_color)
                y += line_height
            
            # Help text
            draw.text((4, height-12), "P=sel L=cancel", 
                     font=FONT_S, fill=colors['disabled'])
    
    def handle_input(self, enc_delta, enc_button_state, button_states):
        if not self.editing_mode:
            # Navigate button list
            if enc_delta != 0:
                self.selected_button = (self.selected_button + enc_delta) % len(BUTTON_PINS)
                logger.debug(f"Selected button: {self.selected_button}")
            
            # Enter edit mode
            if enc_button_state == 'short_press':
                self.editing_mode = True
                logger.info(f"Editing button {BUTTON_PINS[self.selected_button]}")
            
            # Go back
            if enc_button_state == 'long_press':
                return 'back'
        else:
            # Navigate function list
            if enc_delta > 0:
                if self.function_scroll < len(self.available_functions) - 7:
                    self.function_scroll += 1
            elif enc_delta < 0:
                if self.function_scroll > 0:
                    self.function_scroll -= 1
            
            # Select function
            if enc_button_state == 'short_press':
                # Find selected function
                visible_functions = self.available_functions[self.function_scroll:self.function_scroll+7]
                if visible_functions:
                    # For now, select the first visible (we'd need more logic to track selection)
                    # Let's use a simpler approach: cycle through functions
                    pin = BUTTON_PINS[self.selected_button]
                    current_func = self.button_manager.get_button_function(pin)
                    current_idx = self.available_functions.index(current_func) if current_func in self.available_functions else 0
                    next_idx = (current_idx + 1) % len(self.available_functions)
                    new_func = self.available_functions[next_idx]
                    
                    self.button_manager.set_button_function(pin, new_func)
                    logger.info(f"Button {pin} function changed to: {new_func}")
                    self.editing_mode = False
            
            # Cancel edit
            if enc_button_state == 'long_press':
                self.editing_mode = False
                logger.info("Button edit cancelled")
        
        return self


class AboutScreen(BaseScreen):
    """About information screen"""
    def __init__(self):
        super().__init__("About")

    def render(self, draw, width, height):
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=_default_colors['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=_default_colors['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=_default_colors['accent'])

        y = 28
        lines = [
            "Smart Panel v2.0",
            "",
            "Raspberry Pi",
            "Control Dashboard",
            "",
            "Features:",
            "- System Monitor",
            "- GPIO Control",
            "- Matter IoT",
            "- Menu System"
        ]

        for line in lines:
            draw.text((4, y), line, font=FONT_S, fill=_default_colors['fg'])
            y += 12

        # Help text
        draw.text((4, height-12), "Long=back", 
                 font=FONT_S, fill=_default_colors['disabled'])


"""
Screen Classes for Smart Panel
All screen implementations for the dashboard
"""

import time
from .config import COLORS, BUTTON_LABELS
from .ui_components import FONT_S, FONT_M
from .system_monitor import get_system_info
from .gpio_control import gpio_states, toggle_gpio_pin
from .matter_integration import MatterController
from .matter_qr import generate_matter_qr_code, get_default_matter_payload, render_qr_to_display, HAS_QRCODE


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
        draw.rectangle([0, 0, width-1, 16], fill=COLORS['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=COLORS['menu_fg'])
        
        # Separator line
        draw.line([0, 17, width-1, 17], fill=COLORS['accent'])

        # Menu items
        y_offset = 22
        for i, item in enumerate(self.menu.get_visible_items()):
            y = y_offset + i * 14
            
            if i + self.menu.scroll_offset == self.menu.selected_index:
                # Highlight selected item with rounded effect
                draw.rectangle([2, y-2, width-3, y+11], fill=COLORS['menu_sel'])
                text_color = COLORS['bg']
                prefix = "▶ "
            else:
                text_color = COLORS['fg'] if item.enabled else COLORS['disabled']
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
                         fill=COLORS['accent'])
            
            # Page indicator
            draw.text((width-32, height-12), f"{visible_start}-{visible_end}/{total_items}",
                     font=FONT_S, fill=COLORS['disabled'])

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
        draw.rectangle([0, 0, width-1, 16], fill=COLORS['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=COLORS['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=COLORS['accent'])

        y = 24
        line_height = 14

        # CPU
        draw.text((4, y), "CPU:", font=FONT_S, fill=COLORS['fg'])
        cpu = self.system_info.get('cpu', 0)
        self._draw_progress_bar(draw, 50, y, width-54, 10, cpu)
        draw.text((width-28, y), f"{cpu:.0f}%", font=FONT_S, fill=COLORS['fg'])
        y += line_height

        # Memory
        draw.text((4, y), "RAM:", font=FONT_S, fill=COLORS['fg'])
        mem = self.system_info.get('memory', 0)
        self._draw_progress_bar(draw, 50, y, width-54, 10, mem)
        draw.text((width-28, y), f"{mem:.0f}%", font=FONT_S, fill=COLORS['fg'])
        y += line_height

        # Disk
        draw.text((4, y), "Disk:", font=FONT_S, fill=COLORS['fg'])
        disk = self.system_info.get('disk', 0)
        self._draw_progress_bar(draw, 50, y, width-54, 10, disk)
        draw.text((width-28, y), f"{disk:.0f}%", font=FONT_S, fill=COLORS['fg'])
        y += line_height

        # Temperature
        temp = self.system_info.get('temperature', 0)
        temp_color = COLORS['accent'] if temp < 60 else COLORS['warning'] if temp < 80 else COLORS['error']
        draw.text((4, y), f"Temp: {temp:.1f}°C", font=FONT_S, fill=temp_color)
        y += line_height

        # Network
        network = self.system_info.get('network', {})
        draw.text((4, y), f"IP: {network.get('ip', 'N/A')}", font=FONT_S, fill=COLORS['fg'])
        y += line_height

        # Uptime
        draw.text((4, y), f"Up: {self.system_info.get('uptime', 'N/A')}", 
                 font=FONT_S, fill=COLORS['fg'])

        # Help text
        draw.text((4, height-12), "Long press to go back", 
                 font=FONT_S, fill=COLORS['disabled'])

    def _draw_progress_bar(self, draw, x, y, width, height, percentage):
        percentage = max(0, min(100, percentage))
        fill_width = int(width * percentage / 100)

        draw.rectangle([x, y, x + width, y + height], outline=COLORS['fg'])
        if fill_width > 0:
            color = COLORS['accent'] if percentage < 80 else COLORS['warning'] if percentage < 95 else COLORS['error']
            draw.rectangle([x + 1, y + 1, x + fill_width, y + height - 1], fill=color)


class GPIOControlScreen(BaseScreen):
    """GPIO pin control interface"""
    def __init__(self):
        super().__init__("GPIO Control")
        self.selected_pin = 0
        self.pin_list = sorted(gpio_states.keys())

    def render(self, draw, width, height):
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=COLORS['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=COLORS['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=COLORS['accent'])

        y = 24
        line_height = 14

        if not self.pin_list:
            draw.text((4, y), "No GPIO pins available", 
                     font=FONT_S, fill=COLORS['disabled'])
        else:
            for i, pin in enumerate(self.pin_list[:8]):
                if i == self.selected_pin:
                    draw.rectangle([2, y-2, width-3, y+11], fill=COLORS['menu_sel'])

                state = gpio_states.get(pin, False)
                state_text = "ON " if state else "OFF"
                state_color = COLORS['accent'] if state else COLORS['error']

                pin_text = f"GPIO{pin:2d}"
                draw.text((6, y), pin_text, font=FONT_S, 
                         fill=COLORS['bg'] if i == self.selected_pin else COLORS['fg'])
                
                # State indicator
                draw.rectangle([width-38, y, width-8, y+10], fill=state_color)
                draw.text((width-34, y), state_text, font=FONT_S, fill=COLORS['bg'])

                y += line_height

        # Help text
        draw.text((4, height-12), "Short press=toggle", 
                 font=FONT_S, fill=COLORS['disabled'])

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
    """Matter device control interface"""
    def __init__(self):
        super().__init__("Matter Devices")
        self.controller = MatterController()
        self.selected_device = 0
        self.controller.scan_devices()
        self.show_qr = False

    def render(self, draw, width, height):
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=COLORS['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=COLORS['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=COLORS['accent'])

        y = 24

        if not self.controller.enabled:
            draw.text((4, y), "Matter disabled", font=FONT_S, fill=COLORS['disabled'])
            draw.text((4, y+15), "Enable in Settings", font=FONT_S, fill=COLORS['warning'])
        elif self.show_qr:
            # Show QR code for pairing
            self._render_qr_code(draw, width, height, y)
        elif not self.controller.devices:
            draw.text((4, y), "No devices found", font=FONT_S, fill=COLORS['disabled'])
            draw.text((4, y+15), "Press B6 to scan", font=FONT_S, fill=COLORS['fg'])
            y += 30
            draw.text((4, y), "Press B7 for QR", font=FONT_S, fill=COLORS['accent'])
        else:
            for i, device in enumerate(self.controller.devices[:7]):
                if i == self.selected_device:
                    draw.rectangle([2, y-2, width-3, y+11], fill=COLORS['menu_sel'])

                status_color = COLORS['fg'] if device.online else COLORS['disabled']
                state_color = COLORS['accent'] if device.state == 'ON' else COLORS['disabled']

                # Device name
                draw.text((6, y), device.name[:14], font=FONT_S, 
                         fill=COLORS['bg'] if i == self.selected_device else status_color)

                # State
                if device.type == 'light':
                    brightness = device.properties.get('brightness', 0)
                    draw.text((width-35, y), f"{brightness}%", font=FONT_S, fill=state_color)
                else:
                    draw.text((width-28, y), str(device.state)[:4], font=FONT_S, fill=state_color)

                y += 14

        # Help text
        if self.show_qr:
            draw.text((4, height-12), "B7=hide QR", 
                     font=FONT_S, fill=COLORS['disabled'])
        else:
            draw.text((4, height-12), "B6=scan B7=QR", 
                     font=FONT_S, fill=COLORS['disabled'])

    def _render_qr_code(self, draw, width, height, start_y):
        """Render Matter QR code for device commissioning"""
        if not HAS_QRCODE:
            draw.text((4, start_y), "QR code library", font=FONT_S, fill=COLORS['error'])
            draw.text((4, start_y+12), "not installed", font=FONT_S, fill=COLORS['error'])
            draw.text((4, start_y+30), "Install qrcode:", font=FONT_S, fill=COLORS['fg'])
            draw.text((4, start_y+42), "pip3 install", font=FONT_S, fill=COLORS['fg'])
            draw.text((4, start_y+54), "qrcode[pil]", font=FONT_S, fill=COLORS['fg'])
            return

        # Generate QR code
        payload = get_default_matter_payload()
        qr_img = generate_matter_qr_code(payload)
        
        if qr_img:
            # Resize to fit display
            qr_size = min(width - 8, height - start_y - 30)
            qr_resized = render_qr_to_display(qr_img, (qr_size, qr_size))
            
            # Center QR code
            qr_x = (width - qr_size) // 2
            qr_y = start_y + 5
            
            # Paste QR code onto display
            # Note: PIL's ImageDraw doesn't directly support pasting images
            # We'll draw a placeholder box and text
            draw.rectangle([qr_x, qr_y, qr_x + qr_size, qr_y + qr_size], 
                         outline=COLORS['fg'], fill=COLORS['bg'])
            
            # Show pairing code as text
            draw.text((4, qr_y + qr_size + 8), "Pairing Code:", 
                     font=FONT_S, fill=COLORS['fg'])
            draw.text((4, qr_y + qr_size + 20), payload[:16], 
                     font=FONT_S, fill=COLORS['accent'])
        else:
            draw.text((4, start_y), "QR generation", font=FONT_S, fill=COLORS['error'])
            draw.text((4, start_y+12), "failed", font=FONT_S, fill=COLORS['error'])

    def handle_input(self, enc_delta, enc_button_state, button_states):
        # B7 - toggle QR code display
        if 4 in button_states and button_states[4]:
            self.show_qr = not self.show_qr
            return self

        if self.show_qr:
            # In QR mode, long press to go back
            if enc_button_state == 'long_press':
                self.show_qr = False
            return self

        if not self.controller.enabled or not self.controller.devices:
            if enc_button_state == 'long_press':
                return 'back'
            # B6 - rescan
            if 21 in button_states and button_states[21]:
                self.controller.scan_devices()
            return self

        # Navigate devices
        if enc_delta > 0:
            self.selected_device = (self.selected_device + 1) % len(self.controller.devices)
        elif enc_delta < 0:
            self.selected_device = (self.selected_device - 1) % len(self.controller.devices)

        # Short press - toggle device
        if enc_button_state == 'short_press':
            device = self.controller.devices[self.selected_device]
            device.toggle()
            self.controller.control_device(device)

        # Long press - go back
        if enc_button_state == 'long_press':
            return 'back'

        # B6 - rescan
        if 21 in button_states and button_states[21]:
            self.controller.scan_devices()

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
        draw.rectangle([0, 0, width-1, 16], fill=COLORS['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=COLORS['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=COLORS['accent'])

        y = 24
        line_height = 16

        for i, (name, value, min_val, max_val, step) in enumerate(self.settings_items):
            if i == self.selected_setting:
                draw.rectangle([2, y-2, width-3, y+12], fill=COLORS['menu_sel'])
                text_color = COLORS['bg']
            else:
                text_color = COLORS['fg']

            # Setting name
            draw.text((6, y), name, font=FONT_S, fill=text_color)

            # Setting value
            if isinstance(value, bool):
                val_text = "ON" if value else "OFF"
                val_color = COLORS['accent'] if value else COLORS['error']
                if i == self.selected_setting:
                    val_color = COLORS['bg']
            else:
                val_text = str(value)
                val_color = text_color

            draw.text((width-35, y), val_text, font=FONT_S, fill=val_color)
            y += line_height

        # Help text
        draw.text((4, height-12), "Rotate=change Press=next", 
                 font=FONT_S, fill=COLORS['disabled'])

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


class AboutScreen(BaseScreen):
    """About information screen"""
    def __init__(self):
        super().__init__("About")

    def render(self, draw, width, height):
        # Title
        draw.rectangle([0, 0, width-1, 16], fill=COLORS['menu_bg'])
        draw.text((4, 2), self.title, font=FONT_M, fill=COLORS['menu_fg'])
        draw.line([0, 17, width-1, 17], fill=COLORS['accent'])

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
            draw.text((4, y), line, font=FONT_S, fill=COLORS['fg'])
            y += 12

        # Help text
        draw.text((4, height-12), "Long press to go back", 
                 font=FONT_S, fill=COLORS['disabled'])


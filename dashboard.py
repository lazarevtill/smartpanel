# dashboard.py — Enhanced Pi 3B+ Smart Control Panel with Menu System
# Display: ST7735/ST7735R via luma.lcd (portrait, fixed orientation)
# Inputs: KY-040 encoder (+push) + 7 buttons
# Features: Menu system, system monitoring, GPIO control, Matter integration framework
#
# Wiring:
#   TFT: GND→GND, VCC→3V3, SCL→GPIO11(SCLK pin23), SDA→GPIO10(MOSI pin19),
#        RES→GPIO24(pin18), DC→GPIO25(pin22), CS→CE0(pin24) [or CE1 pin26],
#        BL→GPIO13(pin33) or tie BL → 3V3.
#   Encoder: CLK→GPIO17, DT→GPIO27, SW→GPIO22, +→3V3, GND→GND
#   Buttons to GND: B1→GPIO5, B2→GPIO6, B3→GPIO16, B4→GPIO26, B5→GPIO12, B6→GPIO21, B7→GPIO4

import os, time, math, json, pathlib, threading, subprocess, psutil
os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")  # Debian 13 (Trixie)

import RPi.GPIO as GPIO
from gpiozero import RotaryEncoder, Button as GPIOBUTTON

from luma.core.interface.serial import spi as luma_spi
from luma.lcd.device import st7735 as LCD_ST7735
try:
    from luma.lcd.device import st7735r as LCD_ST7735R  # native 128x160
    HAS_ST7735R = True
except Exception:
    HAS_ST7735R = False

from PIL import Image, ImageDraw, ImageFont, Image

# ---------- Config ----------
PIN_DC, PIN_RST, PIN_BL = 25, 24, 13
SPI_PORT, SPI_DEVICE, SPI_SPEED = 0, 0, 8_000_000  # set SPI_DEVICE=1 if CS on CE1
ROTATE, BGR, INVERT = 1, True, False               # flipped portrait; tweak if needed

# Offsets to kill panel border junk; cycle with B5, persist to file
OFFSET_PRESETS = [(0, 0), (2, 1), (2, 3)]
OFFSET_STORE = pathlib.Path.home() / ".tft_offset.json"

# Edge cleanup: explicitly paint last pixel rows/cols every frame
TRIM_RIGHT = 1   # 1 px right edge to overpaint
TRIM_BOTTOM = 1  # 1 px bottom edge to overpaint

# Inputs
ENC_A, ENC_B, ENC_PUSH = 17, 27, 22
BUTTON_PINS = [5, 6, 16, 26, 12, 21, 4]
BUTTON_LABELS = {5:"B1", 6:"B2", 16:"B3", 26:"B4", 12:"B5", 21:"B6", 4:"B7"}

# UI kinetics
DT, TAU = 0.05, 0.8
BUMP_STEP, BUMP_BTN = 0.05, 0.10

# Menu colors
COLORS = {
    'bg': (0, 0, 0),
    'fg': (220, 220, 220),
    'accent': (80, 200, 80),
    'warning': (255, 165, 0),
    'error': (255, 0, 0),
    'disabled': (100, 100, 100),
    'highlight': (0, 100, 255),
    'menu_bg': (20, 20, 40),
    'menu_fg': (255, 255, 255),
    'menu_sel': (80, 200, 80)
}

# Configuration file
CONFIG_FILE = pathlib.Path.home() / ".smartpanel_config.json"

# ---------- Menu System Architecture ----------

class MenuItem:
    def __init__(self, title, action=None, submenu=None, data=None, enabled=True):
        self.title = title
        self.action = action
        self.submenu = submenu
        self.data = data
        self.enabled = enabled

    def execute(self, context):
        if self.action and self.enabled:
            return self.action(context)
        return None

class Menu:
    def __init__(self, title, items=None, parent=None):
        self.title = title
        self.items = items or []
        self.parent = parent
        self.selected_index = 0
        self.scroll_offset = 0

    def add_item(self, item):
        self.items.append(item)

    def get_visible_items(self, max_items=6):
        """Get items visible on screen, handling scrolling"""
        if len(self.items) <= max_items:
            return self.items

        # Ensure selected item is visible
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + max_items:
            self.scroll_offset = self.selected_index - max_items + 1

        return self.items[self.scroll_offset:self.scroll_offset + max_items]

    def navigate(self, direction):
        """Navigate menu: direction = 1 (down) or -1 (up)"""
        if not self.items:
            return

        old_index = self.selected_index
        self.selected_index = max(0, min(len(self.items) - 1, self.selected_index + direction))

        # Handle scrolling
        max_visible = 6
        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + max_visible:
            self.scroll_offset = self.selected_index - max_visible + 1

    def select(self, context):
        """Select current item"""
        if not self.items or not self.items[self.selected_index].enabled:
            return self

        item = self.items[self.selected_index]
        if item.submenu:
            return item.submenu
        elif item.action:
            result = item.execute(context)
            if result is not None:
                return result
        return self

# ---------- UI Components ----------

class UIComponent:
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height

    def render(self, draw, **kwargs):
        """Override in subclasses"""
        pass

class ProgressBar(UIComponent):
    def render(self, draw, value=0.0, max_value=1.0, color=None, bg_color=None, **kwargs):
        color = color or COLORS['accent']
        bg_color = bg_color or (50, 50, 50)

        # Background
        draw.rectangle([self.x, self.y, self.x + self.width, self.y + self.height], fill=bg_color)

        # Progress
        if value > 0:
            prog_width = int(self.width * min(1.0, value / max_value))
            draw.rectangle([self.x, self.y, self.x + prog_width, self.y + self.height], fill=color)

class TextDisplay(UIComponent):
    def render(self, draw, text="", font=None, color=None, align="left", **kwargs):
        font = font or FONT_S
        color = color or COLORS['fg']

        if align == "center":
            # Simple center alignment - could be improved
            text_width = draw.textlength(text, font=font)
            x = self.x + (self.width - text_width) // 2
        elif align == "right":
            text_width = draw.textlength(text, font=font)
            x = self.x + self.width - text_width
        else:
            x = self.x

        draw.text((x, self.y), text, font=font, fill=color)

class Button(UIComponent):
    def __init__(self, x, y, width, height, text="", callback=None, enabled=True):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback
        self.enabled = enabled
        self.pressed = False

    def render(self, draw, **kwargs):
        color = COLORS['accent'] if self.enabled else COLORS['disabled']
        if self.pressed:
            color = COLORS['highlight']

        # Button background
        draw.rectangle([self.x, self.y, self.x + self.width, self.y + self.height], fill=color)

        # Button text (centered)
        if self.text:
            text_width = draw.textlength(self.text, font=FONT_S)
            text_x = self.x + (self.width - text_width) // 2
            text_y = self.y + (self.height - 12) // 2
            text_color = COLORS['bg'] if self.enabled else COLORS['fg']
            draw.text((text_x, text_y), self.text, font=FONT_S, fill=text_color)

# ---------- GPIO ----------
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
try: GPIO.cleanup()
except: pass
GPIO.setup(PIN_BL, GPIO.OUT, initial=GPIO.HIGH)

# ---------- System Monitoring ----------

def get_system_info():
    """Get comprehensive system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        temperature = get_cpu_temperature()
        network = get_network_info()

        return {
            'cpu': cpu_percent,
            'memory': memory.percent,
            'memory_used': memory.used // (1024*1024),  # MB
            'memory_total': memory.total // (1024*1024),  # MB
            'disk': disk.percent,
            'disk_used': disk.used // (1024*1024*1024),  # GB
            'disk_total': disk.total // (1024*1024*1024),  # GB
            'temperature': temperature,
            'network': network,
            'uptime': get_uptime()
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {}

def get_cpu_temperature():
    """Get CPU temperature"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
        return temp
    except:
        return 0.0

def get_network_info():
    """Get network information"""
    try:
        addrs = psutil.net_if_addrs()
        for interface, addresses in addrs.items():
            if interface.startswith(('eth', 'wlan')):
                for addr in addresses:
                    if addr.family.name == 'AF_INET':
                        return {
                            'interface': interface,
                            'ip': addr.address,
                            'netmask': addr.netmask
                        }
        return {'interface': 'none', 'ip': '0.0.0.0', 'netmask': '0.0.0.0'}
    except:
        return {'interface': 'error', 'ip': '0.0.0.0', 'netmask': '0.0.0.0'}

def get_uptime():
    """Get system uptime"""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            days = int(uptime_seconds // (24 * 3600))
            hours = int((uptime_seconds % (24 * 3600)) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{days}d {hours}h {minutes}m"
    except:
        return "unknown"

# ---------- GPIO Control ----------

gpio_states = {}

def init_gpio_control():
    """Initialize GPIO pins for control"""
    controllable_pins = [2, 3, 4, 5, 6, 12, 13, 16, 17, 18, 19, 20, 21, 22, 26, 27]
    for pin in controllable_pins:
        if pin not in [PIN_DC, PIN_RST, PIN_BL, ENC_A, ENC_B, ENC_PUSH] + BUTTON_PINS:
            try:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
                gpio_states[pin] = False
            except:
                pass

def toggle_gpio_pin(pin):
    """Toggle GPIO pin state"""
    if pin in gpio_states:
        new_state = not gpio_states[pin]
        GPIO.output(pin, GPIO.HIGH if new_state else GPIO.LOW)
        gpio_states[pin] = new_state
        return new_state
    return False

# ---------- Inputs ----------
enc = RotaryEncoder(ENC_A, ENC_B, max_steps=0, wrap=False, bounce_time=0.002)
enc_button = GPIOBUTTON(ENC_PUSH)
buttons = [GPIOBUTTON(p) for p in BUTTON_PINS]
button_states = {p: False for p in BUTTON_PINS}

def button_pressed(pin):
    """Button press handler"""
    button_states[pin] = True

for b in buttons:
    b.when_pressed = lambda button=b: button_pressed(button.pin.number)

# ---------- Configuration Management ----------

def load_config():
    """Load configuration from file"""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text())
    except Exception:
        pass
    return {
        'brightness': 100,
        'auto_refresh': True,
        'refresh_interval': 5,
        'gpio_states': {},
        'matter_enabled': False
    }

def save_config(config):
    """Save configuration to file"""
    try:
        CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except Exception as e:
        print(f"Error saving config: {e}")

config = load_config()

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
    return SettingsScreen()

def back_to_main(context):
    """Go back to main menu"""
    return main_menu

def show_about(context):
    """Show about screen"""
    return AboutScreen()

def shutdown_system(context):
    """Shutdown the system"""
    try:
        subprocess.run(['sudo', 'shutdown', '-h', 'now'], check=True)
    except Exception as e:
        print(f"Shutdown failed: {e}")
    return main_menu

def restart_system(context):
    """Restart the system"""
    try:
        subprocess.run(['sudo', 'reboot'], check=True)
    except Exception as e:
        print(f"Reboot failed: {e}")
    return main_menu

# ---------- Menu Definition ----------

main_menu = Menu("Smart Panel")
main_menu.add_item(MenuItem("System Info", action=show_system_info))
main_menu.add_item(MenuItem("GPIO Control", action=show_gpio_control))
main_menu.add_item(MenuItem("Matter Devices", action=show_matter_devices))
main_menu.add_item(MenuItem("Settings", action=show_settings))
main_menu.add_item(MenuItem("About", action=show_about))
main_menu.add_item(MenuItem("Shutdown", action=shutdown_system))
main_menu.add_item(MenuItem("Restart", action=restart_system))

# ---------- Offset persistence ----------
def load_offset_idx():
    try:
        data = json.loads(OFFSET_STORE.read_text())
        return int(data.get("idx", 1)) % len(OFFSET_PRESETS)
    except Exception:
        return 1  # (2,1) works for most boards

def save_offset_idx(idx):
    try:
        OFFSET_STORE.write_text(json.dumps({"idx": idx}))
    except Exception:
        pass

offset_idx = load_offset_idx()

# ---------- Screen Classes ----------

class BaseScreen:
    def __init__(self, title="Screen"):
        self.title = title
        self.last_update = 0
        self.update_interval = 1.0  # seconds

    def render(self, draw):
        """Override in subclasses"""
        pass

    def handle_input(self, enc_delta, enc_pressed, button_states):
        """Handle input, return next screen or self"""
        return self

    def should_update(self):
        """Check if screen should be updated"""
        return time.time() - self.last_update > self.update_interval

    def mark_updated(self):
        """Mark screen as updated"""
        self.last_update = time.time()

class MenuScreen(BaseScreen):
    def __init__(self, menu):
        super().__init__(menu.title)
        self.menu = menu
        self.selected_index = 0

    def render(self, draw):
        # Title
        draw.text((4, 4), self.title, font=FONT_M, fill=COLORS['fg'])

        # Menu items
        y_offset = 20
        for i, item in enumerate(self.menu.get_visible_items()):
            y = y_offset + i * 12
            if i + self.menu.scroll_offset == self.menu.selected_index:
                # Highlight selected item
                draw.rectangle([2, y-1, TW-3, y+10], fill=COLORS['menu_sel'])
                color = COLORS['bg']
            else:
                color = COLORS['fg'] if item.enabled else COLORS['disabled']

            prefix = "▶ " if i + self.menu.scroll_offset == self.menu.selected_index else "  "
            draw.text((6, y), f"{prefix}{item.title}", font=FONT_S, fill=color)

        # Scroll indicator
        if len(self.menu.items) > 6:
            total_items = len(self.menu.items)
            visible_start = self.menu.scroll_offset + 1
            visible_end = min(total_items, self.menu.scroll_offset + 6)
            draw.text((TW-30, TH-12), f"{visible_start}-{visible_end}/{total_items}",
                     font=FONT_S, fill=COLORS['disabled'])

    def handle_input(self, enc_delta, enc_pressed, button_states):
        # Handle encoder rotation
        if enc_delta > 0:
            self.menu.navigate(1)
        elif enc_delta < 0:
            self.menu.navigate(-1)

        # Handle encoder button (select)
        if enc_pressed:
            return self.menu.select({})

        # Handle back button (B3)
        if 16 in button_states and button_states[16]:  # B3
            if self.menu.parent:
                return self.menu.parent

        return self

class SystemInfoScreen(BaseScreen):
    def __init__(self):
        super().__init__("System Information")
        self.system_info = {}

    def render(self, draw):
        if self.should_update():
            self.system_info = get_system_info()
            self.mark_updated()

        y = 20
        line_height = 12

        # CPU
        draw.text((4, y), "CPU Usage:", font=FONT_S, fill=COLORS['fg'])
        self.draw_progress_bar(draw, 80, y, 40, 8, self.system_info.get('cpu', 0))
        draw.text((TW-25, y), f"{self.system_info.get('cpu', 0):.1f}%", font=FONT_S, fill=COLORS['fg'])
        y += line_height + 2

        # Memory
        draw.text((4, y), "Memory:", font=FONT_S, fill=COLORS['fg'])
        self.draw_progress_bar(draw, 80, y, 40, 8, self.system_info.get('memory', 0))
        mem_used = self.system_info.get('memory_used', 0)
        mem_total = self.system_info.get('memory_total', 0)
        draw.text((TW-35, y), f"{mem_used}/{mem_total}MB", font=FONT_S, fill=COLORS['fg'])
        y += line_height + 2

        # Disk
        draw.text((4, y), "Disk Usage:", font=FONT_S, fill=COLORS['fg'])
        self.draw_progress_bar(draw, 80, y, 40, 8, self.system_info.get('disk', 0))
        disk_used = self.system_info.get('disk_used', 0)
        disk_total = self.system_info.get('disk_total', 0)
        draw.text((TW-35, y), f"{disk_used}/{disk_total}GB", font=FONT_S, fill=COLORS['fg'])
        y += line_height + 2

        # Temperature
        temp = self.system_info.get('temperature', 0)
        temp_color = COLORS['accent'] if temp < 60 else COLORS['warning'] if temp < 80 else COLORS['error']
        draw.text((4, y), f"Temperature: {temp:.1f}°C", font=FONT_S, fill=temp_color)
        y += line_height + 2

        # Network
        network = self.system_info.get('network', {})
        draw.text((4, y), f"IP: {network.get('ip', '0.0.0.0')}", font=FONT_S, fill=COLORS['fg'])
        y += line_height

        # Uptime
        draw.text((4, y), f"Uptime: {self.system_info.get('uptime', 'unknown')}", font=FONT_S, fill=COLORS['fg'])

    def draw_progress_bar(self, draw, x, y, width, height, percentage):
        percentage = max(0, min(100, percentage))
        fill_width = int(width * percentage / 100)

        # Background
        draw.rectangle([x, y, x + width, y + height], outline=COLORS['fg'])

        # Fill
        if fill_width > 0:
            draw.rectangle([x + 1, y + 1, x + fill_width, y + height - 1], fill=COLORS['accent'])

class GPIOControlScreen(BaseScreen):
    def __init__(self):
        super().__init__("GPIO Control")
        self.selected_pin = 0
        self.pin_list = sorted(gpio_states.keys())
        self.blink_states = {}

    def render(self, draw):
        y = 20
        line_height = 12

        for i, pin in enumerate(self.pin_list[:6]):  # Show up to 6 pins
            if i == self.selected_pin:
                draw.rectangle([2, y-1, TW-3, y+10], fill=COLORS['menu_sel'])

            state = gpio_states.get(pin, False)
            state_text = "ON" if state else "OFF"
            color = COLORS['accent'] if state else COLORS['disabled']

            draw.text((6, y), f"GPIO{pin}:", font=FONT_S, fill=COLORS['fg'])
            draw.text((TW-30, y), state_text, font=FONT_S, fill=color)
            y += line_height + 2

    def handle_input(self, enc_delta, enc_pressed, button_states):
        # Navigate pins
        if enc_delta > 0:
            self.selected_pin = (self.selected_pin + 1) % len(self.pin_list)
        elif enc_delta < 0:
            self.selected_pin = (self.selected_pin - 1) % len(self.pin_list)

        # Toggle pin
        if enc_pressed and self.pin_list:
            pin = self.pin_list[self.selected_pin]
            toggle_gpio_pin(pin)

        # Handle B1-B7 for direct pin control (if available)
        for btn_pin, btn_idx in [(5, 0), (6, 1), (16, 2), (26, 3), (12, 4), (21, 5), (4, 6)]:
            if btn_pin in button_states and button_states[btn_pin] and btn_idx < len(self.pin_list):
                pin = self.pin_list[btn_idx]
                toggle_gpio_pin(pin)

        return self

class MatterDevicesScreen(BaseScreen):
    def __init__(self):
        super().__init__("Matter Devices")
        self.devices = []
        self.selected_device = 0
        self.matter_enabled = config.get('matter_enabled', False)
        self.scan_for_devices()

    def scan_for_devices(self):
        """Scan for Matter devices on the network"""
        self.devices = []

        if not self.matter_enabled:
            return

        try:
            # Placeholder for Matter device discovery
            # In a real implementation, this would use Matter SDK
            # For now, we'll simulate some devices for demo purposes
            self.devices = [
                {
                    'id': 'light_1',
                    'name': 'Living Room Light',
                    'type': 'light',
                    'state': 'ON',
                    'online': True,
                    'brightness': 80
                },
                {
                    'id': 'switch_1',
                    'name': 'Kitchen Switch',
                    'type': 'switch',
                    'state': 'OFF',
                    'online': True
                },
                {
                    'id': 'sensor_1',
                    'name': 'Temperature Sensor',
                    'type': 'sensor',
                    'state': '22.5°C',
                    'online': True
                }
            ]

            # Try to load real Matter devices if Matter SDK is available
            self.load_real_matter_devices()

        except Exception as e:
            print(f"Matter device scan error: {e}")

    def load_real_matter_devices(self):
        """Load real Matter devices using Matter SDK (if available)"""
        try:
            # This would use the actual Matter SDK when available
            # import chip
            # from chip.clusters import Objects as clusters

            # For now, just log that we're ready for Matter integration
            print("Matter SDK not installed - using demo devices")
            print("To enable Matter support, install: pip install chip-matter")

        except ImportError:
            pass

    def render(self, draw):
        y = 20

        if not self.matter_enabled:
            draw.text((4, y), "Matter support disabled", font=FONT_S, fill=COLORS['disabled'])
            draw.text((4, y+15), "Enable in Settings menu", font=FONT_S, fill=COLORS['warning'])
        elif not self.devices:
            draw.text((4, y), "Scanning for devices...", font=FONT_S, fill=COLORS['fg'])
            draw.text((4, y+15), "Please wait", font=FONT_S, fill=COLORS['disabled'])
        else:
            for i, device in enumerate(self.devices[:5]):
                if i == self.selected_device:
                    draw.rectangle([2, y-1, TW-3, y+10], fill=COLORS['menu_sel'])

                # Device icon/type indicator
                type_icon = {
                    'light': '💡',
                    'switch': '🔘',
                    'sensor': '📊'
                }.get(device['type'], '📱')

                status_color = COLORS['fg'] if device['online'] else COLORS['disabled']
                state_color = COLORS['accent'] if device['state'] == 'ON' else COLORS['disabled']

                draw.text((6, y), f"{type_icon} {device['name']}", font=FONT_S, fill=status_color)

                if device['type'] == 'light':
                    draw.text((TW-35, y), f"B:{device.get('brightness', 0)}%", font=FONT_S, fill=state_color)
                else:
                    draw.text((TW-25, y), str(device['state']), font=FONT_S, fill=state_color)

                y += 12

            # Show device count
            draw.text((4, TH-15), f"Devices: {len(self.devices)}", font=FONT_S, fill=COLORS['disabled'])

    def handle_input(self, enc_delta, enc_pressed, button_states):
        if not self.matter_enabled:
            return self

        if self.devices:
            if enc_delta > 0:
                self.selected_device = (self.selected_device + 1) % len(self.devices)
            elif enc_delta < 0:
                self.selected_device = (self.selected_device - 1) % len(self.devices)

            if enc_pressed:
                device = self.devices[self.selected_device]
                if device['type'] in ['light', 'switch']:
                    # Toggle device state
                    if device['type'] == 'light':
                        device['state'] = "OFF" if device['state'] == "ON" else "ON"
                        # In real implementation, this would control the actual device
                        self.control_matter_device(device)
                    else:  # switch
                        device['state'] = "OFF" if device['state'] == "ON" else "ON"
                        self.control_matter_device(device)

        # Rescan for devices on B6 press
        if 21 in button_states and button_states[21]:
            self.scan_for_devices()

        return self

    def control_matter_device(self, device):
        """Control a Matter device (placeholder for actual implementation)"""
        try:
            print(f"Controlling Matter device: {device['name']} -> {device['state']}")

            # Placeholder for actual Matter control
            # In real implementation, this would use Matter SDK:
            # device = await chip.interaction.Command(
            #     node_id=device['node_id'],
            #     endpoint=device['endpoint'],
            #     command=clusters.OnOff.Commands.Toggle()
            # )

        except Exception as e:
            print(f"Error controlling Matter device: {e}")

class SettingsScreen(BaseScreen):
    def __init__(self):
        super().__init__("Settings")
        self.settings_items = [
            ("Brightness", config.get('brightness', 100), 0, 100),
            ("Auto Refresh", config.get('auto_refresh', True), True, False),
            ("Refresh Interval", config.get('refresh_interval', 5), 1, 30),
            ("Matter Enabled", config.get('matter_enabled', False), True, False)
        ]
        self.selected_setting = 0

    def render(self, draw):
        y = 20
        line_height = 14

        for i, (name, value, min_val, max_val) in enumerate(self.settings_items):
            if i == self.selected_setting:
                draw.rectangle([2, y-1, TW-3, y+11], fill=COLORS['menu_sel'])

            # Setting name
            draw.text((6, y), name, font=FONT_S, fill=COLORS['fg'])

            # Setting value
            if isinstance(value, bool):
                val_text = "ON" if value else "OFF"
                val_color = COLORS['accent'] if value else COLORS['disabled']
            else:
                val_text = str(value)
                val_color = COLORS['fg']

            draw.text((TW-40, y), val_text, font=FONT_S, fill=val_color)
            y += line_height

    def handle_input(self, enc_delta, enc_pressed, button_states):
        # Navigate settings
        if enc_delta > 0:
            self.selected_setting = (self.selected_setting + 1) % len(self.settings_items)
        elif enc_delta < 0:
            self.selected_setting = (self.selected_setting - 1) % len(self.settings_items)

        # Adjust setting value
        if enc_pressed:
            name, value, min_val, max_val = self.settings_items[self.selected_setting]

            if isinstance(value, bool):
                new_value = not value
            else:
                if enc_delta > 0 or (hasattr(self, '_last_enc') and self._last_enc < 0):
                    new_value = min(max_val, value + 1)
                else:
                    new_value = max(min_val, value - 1)

            self.settings_items[self.selected_setting] = (name, new_value, min_val, max_val)

            # Update config
            setting_name = name.lower().replace(" ", "_")
            config[setting_name] = new_value
            save_config(config)

        self._last_enc = enc_delta
        return self

class AboutScreen(BaseScreen):
    def __init__(self):
        super().__init__("About")

    def render(self, draw):
        y = 25
        lines = [
            "Smart Panel v2.0",
            "Raspberry Pi Control",
            "Menu System & GPIO",
            "Matter Integration",
            "System Monitoring",
            "",
            "Built with Python",
            "& Raspberry Pi"
        ]

        for line in lines:
            draw.text((4, y), line, font=FONT_S, fill=COLORS['fg'])
            y += 12

# ---------- TFT helpers ----------
def make_tft_with_offsets(xoff, yoff):
    ser = luma_spi(port=SPI_PORT, device=SPI_DEVICE, gpio_DC=PIN_DC, gpio_RST=PIN_RST,
                   bus_speed_hz=SPI_SPEED)

    def build(dev_cls, w, h):
        # try h_offset/v_offset
        try:
            return dev_cls(ser, width=w, height=h, rotate=ROTATE, invert=INVERT, bgr=BGR,
                           h_offset=xoff, v_offset=yoff)
        except TypeError:
            pass
        # try offset_left/offset_top
        try:
            return dev_cls(ser, width=w, height=h, rotate=ROTATE, invert=INVERT, bgr=BGR,
                           offset_left=xoff, offset_top=yoff)
        except TypeError:
            pass
        # no offset params supported
        return dev_cls(ser, width=w, height=h, rotate=ROTATE, invert=INVERT, bgr=BGR)

    if HAS_ST7735R:
        return build(LCD_ST7735R, 128, 160)
    else:
        return build(LCD_ST7735, 160, 128)

def full_clear(dev):
    w, h = dev.size
    dev.display(Image.new("RGB", (w, h), (0, 0, 0)))

def new_tft(idx):
    xoff, yoff = OFFSET_PRESETS[idx]
    dev = make_tft_with_offsets(xoff, yoff)
    full_clear(dev)  # hard clear to avoid ghost edges after reinit
    return dev

# initial device
tft = new_tft(offset_idx)
TW, TH = tft.size

# ---------- Fonts ----------
try:
    FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 10)
    FONT_M = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
except Exception:
    FONT_S = ImageFont.load_default(); FONT_M = ImageFont.load_default()

# ---------- Render ----------
def splash(label):
    img = Image.new('RGB', (TW, TH), 'black')
    d = ImageDraw.Draw(img)
    bars = [(255,0,0),(0,255,0),(0,0,255),(255,255,255)]
    h = TH // len(bars)
    for i,c in enumerate(bars):
        d.rectangle([0, i*h, TW-1, (i+1)*h-1], fill=c)
    d.text((6, 6), label, font=FONT_M, fill=(0,0,0))
    # paint edge cleanup
    if TRIM_RIGHT:  d.rectangle([TW-TRIM_RIGHT, 0, TW-1, TH-1], fill=(0,0,0))
    if TRIM_BOTTOM: d.rectangle([0, TH-TRIM_BOTTOM, TW-1, TH-1], fill=(0,0,0))
    tft.display(img)

def draw_tft(level, last_btn_label, enc_total, enc_pressed):
    img = Image.new('RGB', (TW, TH), 'black')
    d = ImageDraw.Draw(img)

    # hard-paint right/bottom edges to bury 1px noise
    if TRIM_RIGHT:  d.rectangle([TW-TRIM_RIGHT, 0, TW-1, TH-1], fill=(0,0,0))
    if TRIM_BOTTOM: d.rectangle([0, TH-TRIM_BOTTOM, TW-1, TH-1], fill=(0,0,0))

    d.text((4, 4), "Pi Panel", font=FONT_M, fill=(220,220,220))

    # Use effective height so bar doesn't collide with bottom trim
    eff_TH = TH - TRIM_BOTTOM
    meter_x, meter_y = 4, 24
    meter_w, meter_h = 28, eff_TH - meter_y - 8
    lvl = max(0.0, min(1.0, level))
    fill_h = int(meter_h * lvl)

    d.rectangle([meter_x, meter_y, meter_x + meter_w, meter_y + meter_h], outline=(80,80,80))
    x0 = meter_x + 2
    x1 = meter_x + meter_w - 2
    yb = meter_y + meter_h - 2
    yt = max(meter_y + 2, yb - fill_h)
    if yt <= yb:
        d.rectangle([x0, yt, x1, yb], fill=(80,200,80))

    d.text((40, 36), f"Last: {last_btn_label}", font=FONT_S, fill=(180,180,180))
    d.text((40, 54), f"Enc: {enc_total:+d}",   font=FONT_S, fill=(180,180,220))
    d.text((40, 66), f"Push: {'YES' if enc_pressed else 'NO'}", font=FONT_S, fill=(180,220,180))
    xoff, yoff = OFFSET_PRESETS[offset_idx]
    d.text((4, TH-14), f"{TW}x{TH} off={xoff},{yoff}", font=FONT_S, fill=(120,120,120))

    tft.display(img)

# ---------- Enhanced Main Loop ----------

def render_screen(screen, draw):
    """Render current screen with edge cleanup"""
    # Clear screen
    draw.rectangle([0, 0, TW-1, TH-1], fill=COLORS['bg'])

    # Edge cleanup - paint border pixels to avoid artifacts
    if TRIM_RIGHT:
        draw.rectangle([TW-TRIM_RIGHT, 0, TW-1, TH-1], fill=COLORS['bg'])
    if TRIM_BOTTOM:
        draw.rectangle([0, TH-TRIM_BOTTOM, TW-1, TH-1], fill=COLORS['bg'])

    # Render current screen
    screen.render(draw)

def main():
    global offset_idx, tft, TW, TH

    # Initialize GPIO control
    init_gpio_control()

    # Start with main menu
    current_screen = MenuScreen(main_menu)

    print(f"Smart Panel v2.0 - TFT {TW}x{TH}")
    print(f"Display: rotate={ROTATE} bgr={BGR} invert={INVERT}")
    print(f"Offset: {OFFSET_PRESETS[offset_idx]}")
    print("Controls: Encoder (navigate/select), B3 (back), B5 (offset cycle)")

    enc_total = 0

    try:
        while True:
            # Handle encoder input - use steps for proper delta calculation
            enc_delta = enc.steps
            enc.steps = 0  # Reset after reading
            if enc_delta != 0:
                enc_total += enc_delta

            # Handle button presses - collect current states before clearing
            current_button_states = button_states.copy()
            pressed_buttons = []
            for p in BUTTON_PINS:
                if button_states[p]:
                    pressed_buttons.append(p)
                    button_states[p] = False  # Clear after copying state

            # Handle encoder button press
            enc_pressed = enc_button.is_pressed

            # Process all input together
            if enc_delta != 0 or pressed_buttons or enc_pressed:
                # Debug output (remove in production)
                if enc_delta != 0:
                    print(f"Encoder delta: {enc_delta}, total: {enc_total}")
                if pressed_buttons:
                    print(f"Buttons pressed: {[BUTTON_LABELS.get(p, f'GPIO{p}') for p in pressed_buttons]}")
                if enc_pressed:
                    print("Encoder button pressed")

                current_screen = current_screen.handle_input(enc_delta, enc_pressed, current_button_states) or current_screen

            # Handle special buttons
            if 12 in pressed_buttons:  # B5: cycle offsets
                offset_idx = (offset_idx + 1) % len(OFFSET_PRESETS)
                save_offset_idx(offset_idx)
                tft = new_tft(offset_idx)
                TW, TH = tft.size
                print(f"Display offset changed to: {OFFSET_PRESETS[offset_idx]}")

            # Render current screen
            img = Image.new('RGB', (TW, TH), COLORS['bg'])
            draw = ImageDraw.Draw(img)
            render_screen(current_screen, draw)
            tft.display(img)

            time.sleep(DT)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

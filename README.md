# Smart Panel v2.0 - REAL Matter Device

A Raspberry Pi-based smart home control panel with **REAL Matter protocol support** using CircuitMatter. Control your smart home and expose 6 physical buttons as Matter devices that work with Samsung SmartThings, Apple Home, Google Home, and Amazon Alexa.

![Smart Panel](https://img.shields.io/badge/Matter-Certified-green) ![Python](https://img.shields.io/badge/Python-3.13-blue) ![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-3B%2B-red)

## ✨ Features

### Core Features
- **🎮 6 Physical Buttons** - Exposed as Matter On/Off switches
- **📱 REAL Matter Device** - Works with ALL Matter-compatible smart home apps
- **🖥️ 1.8" TFT Display** (ST7735, 128x160) - Portrait orientation UI
- **🔄 Rotary Encoder** - Intuitive menu navigation (short press = select, long press = back)
- **📊 System Monitoring** - CPU, memory, disk, temperature, network, uptime
- **⚙️ GPIO Control** - Toggle GPIO pins from the UI
- **🔧 Full Configuration** - All settings accessible via on-screen menus
- **🚨 Emergency Reset** - Hold buttons 1+6 for 10 seconds

### Matter Integration
- **CircuitMatter** - Pure Python Matter implementation
- **mDNS Discovery** - Automatic device discovery
- **QR Code Commissioning** - Scan to add to your smart home
- **Manual Pairing Code** - Alternative pairing method
- **Real-time Sync** - Button presses update instantly in your smart home app
- **Bi-directional Control** - Control buttons from your phone

## 🔌 Hardware Requirements

### Required Components
- **Raspberry Pi 3B+** (or newer)
- **ST7735/ST7735R TFT Display** (1.8", 128x160, SPI)
- **KY-040 Rotary Encoder**
- **6x Tactile Buttons** (with pull-down resistors)
- **MicroSD Card** (16GB+ recommended)
- **Power Supply** (5V, 2.5A minimum)

### Wiring Diagram

#### TFT Display (ST7735 - SPI)
```
TFT Pin  →  Raspberry Pi Pin
VCC      →  3.3V (Pin 1)
GND      →  GND (Pin 6)
CS       →  GPIO 8 (CE0, Pin 24)
RESET    →  GPIO 25 (Pin 22)
A0/DC    →  GPIO 24 (Pin 18)
SDA      →  GPIO 10 (MOSI, Pin 19)
SCK      →  GPIO 11 (SCLK, Pin 23)
LED      →  GPIO 18 (Pin 12) - Backlight control
```

#### Rotary Encoder (KY-040)
```
Encoder Pin  →  Raspberry Pi Pin
CLK (A)      →  GPIO 17 (Pin 11)
DT (B)       →  GPIO 27 (Pin 13)
SW (Button)  →  GPIO 22 (Pin 15)
+            →  3.3V (Pin 17)
GND          →  GND (Pin 9)
```

#### Physical Buttons (with pull-down resistors)
```
Button  →  GPIO Pin  →  Raspberry Pi Pin
Button 1  →  GPIO 5   →  Pin 29
Button 2  →  GPIO 6   →  Pin 31
Button 3  →  GPIO 16  →  Pin 36
Button 4  →  GPIO 26  →  Pin 37
Button 5  →  GPIO 12  →  Pin 32
Button 6  →  GPIO 21  →  Pin 40

Each button connects:
- One side to GPIO pin
- Other side to 3.3V
- 10kΩ pull-down resistor to GND
```

## 🚀 Installation

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/smartpanel.git
cd smartpanel

# Run setup script (installs all dependencies)
chmod +x setup.sh
./setup.sh

# Start the Smart Panel
./run.sh
```

### Manual Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv python3-dev \
    python3-lgpio python3-spidev git libopenblas-dev \
    libtiff6 libopenjp2-7 fonts-dejavu-core

# Enable SPI interface
sudo raspi-config nonint do_spi 0

# Create virtual environment
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install CircuitMatter for REAL Matter device
pip install circuitmatter HAP-python

# Run the application
python3 dashboard_new.py
```

## 📱 Adding to Your Smart Home

### Samsung SmartThings
1. Run `./run.sh` on your Raspberry Pi
2. Navigate to **Matter Status** on the TFT screen
3. Press the encoder button to show QR code
4. Open SmartThings app → **Add Device** → **Scan QR Code**
5. Scan the QR code from your Smart Panel screen
6. Follow on-screen instructions to complete pairing
7. Your 6 buttons will appear as switches!

### Apple Home
1. Open Home app → **Add Accessory**
2. Tap **More Options**
3. Select your Smart Panel from the list
4. Scan QR code or enter manual code: `3840-2020-20214`
5. Complete setup
6. Buttons appear as switches in your home

### Google Home
1. Open Google Home app → **Add Device**
2. Select **Matter**
3. Scan QR code from Smart Panel
4. Complete setup
5. Control buttons with "Hey Google, turn on Button 1"

### Manual Pairing Code
If QR scanning doesn't work:
- **Code**: `3840-2020-20214`
- Enter this in your smart home app's manual pairing option

## 🎮 Controls

### Encoder Navigation
- **Rotate**: Navigate menus / Adjust values
- **Short Press**: Select item / Confirm
- **Long Press**: Go back / Cancel

### Physical Buttons
- **Button 1-6**: Configurable actions (default: Matter switches)
- **Button 3**: Quick back button
- **Button 5**: Cycle display offset presets
- **Button 6**: Show/hide Matter QR code
- **Button 1 + Button 6 (hold 10s)**: Emergency reset

## 📋 Menu Structure

```
Smart Panel
├── System Info
│   ├── CPU Usage
│   ├── Memory
│   ├── Disk Space
│   ├── Temperature
│   ├── Network
│   └── Uptime
├── Matter Status
│   ├── Device Status
│   ├── Pairing Status
│   ├── Button States
│   └── QR Code (press to toggle)
├── Button Config
│   ├── Button 1-6 Function Assignment
│   └── Matter Integration Status
├── GPIO Control
│   └── Toggle GPIO Pins
├── Settings
│   ├── Brightness
│   ├── Auto Refresh
│   ├── Refresh Interval
│   └── Matter Enabled
├── About
│   └── Version Info
└── Power
    ├── Shutdown
    └── Restart
```

## ⚙️ Configuration

Configuration is stored in `~/.smartpanel_config.json`

### Key Settings
```json
{
  "brightness": 100,
  "auto_refresh": true,
  "refresh_interval": 5,
  "matter_enabled": true,
  "matter_vendor_id": 65521,
  "matter_product_id": 32768,
  "matter_discriminator": 3840,
  "matter_setup_pin": 20202021,
  "color_scheme": "default",
  "font_size_small": 11,
  "font_size_medium": 14
}
```

### Button Configuration
Each button can be assigned to:
- `none` - No action
- `back` - Go back in menus
- `offset_cycle` - Cycle display offset
- `matter_qr` - Show/hide Matter QR code
- `gpio_toggle` - Toggle GPIO pin
- Custom functions (extend in `button_manager.py`)

## 🔧 Customization

### Adding Custom Screens
1. Create a new screen class in `smartpanel_modules/screens.py`:
```python
class MyCustomScreen(BaseScreen):
    def __init__(self):
        super().__init__("My Screen")
    
    def render(self, draw, width, height):
        # Your rendering code here
        pass
    
    def handle_input(self, enc_delta, enc_button_state, button_states):
        # Your input handling code here
        return self
```

2. Add to menu in `dashboard_new.py`:
```python
menu.add_item(MenuItem("My Screen", action=show_my_screen))
```

### Customizing Colors
Edit `COLOR_SCHEMES` in `smartpanel_modules/config.py`:
```python
COLOR_SCHEMES = {
    'default': {
        'bg': (0, 0, 0),
        'fg': (255, 255, 255),
        'accent': (0, 120, 215),
        # ... more colors
    }
}
```

## 📊 System Architecture

```
dashboard_new.py (Main Application)
│
├── smartpanel_modules/
│   ├── config.py              # Configuration management
│   ├── display.py             # TFT display control
│   ├── input_handler.py       # Encoder & button input
│   ├── menu_system.py         # Menu navigation
│   ├── screens.py             # All screen implementations
│   ├── ui_components.py       # Reusable UI elements
│   ├── system_monitor.py      # System information
│   ├── gpio_control.py        # GPIO management
│   ├── button_manager.py      # Button action management
│   ├── matter_device_real.py  # REAL Matter device (CircuitMatter)
│   ├── matter_server.py       # Fallback Matter implementation
│   ├── matter_qr.py           # QR code generation
│   └── matter_integration.py  # Matter controller (deprecated)
│
├── setup.sh                   # Installation script
├── run.sh                     # Startup script
└── requirements.txt           # Python dependencies
```

## 🐛 Troubleshooting

### Display Issues
```bash
# Check SPI is enabled
lsmod | grep spi

# Enable SPI if needed
sudo raspi-config nonint do_spi 0

# Test display
python3 -c "from smartpanel_modules.display import Display; d = Display(0, 0, {}); print('Display OK')"
```

### GPIO Issues
```bash
# Check lgpio is installed
python3 -c "import lgpio; print('lgpio OK')"

# Install if missing
sudo apt install python3-lgpio

# Check GPIO permissions
groups | grep gpio
```

### Matter Device Not Discoverable
```bash
# Check CircuitMatter is installed
python3 -c "import circuitmatter; print('CircuitMatter OK')"

# Install if missing
pip install circuitmatter HAP-python

# Check mDNS/Avahi is running
sudo systemctl status avahi-daemon

# Restart if needed
sudo systemctl restart avahi-daemon
```

### Button Not Working
- Check wiring connections
- Verify pull-down resistors are installed
- Check GPIO pin configuration in `config.py`
- View logs: `tail -f ~/.smartpanel_logs/smartpanel_*.log`

### Emergency Reset Not Working
- Ensure you're holding BOTH Button 1 AND Button 6
- Hold for full 10 seconds
- Check logs for "Emergency reset" messages

## 📝 Logs

Logs are stored in `~/.smartpanel_logs/`

```bash
# View current log
tail -f ~/.smartpanel_logs/smartpanel_$(date +%Y%m%d).log

# View Matter-specific logs
tail -f ~/.smartpanel_logs/smartpanel_*.log | grep Matter

# Clear old logs
rm ~/.smartpanel_logs/*.log
```

## 🔄 Updates

```bash
cd ~/smartpanel
git pull
./setup.sh  # Reinstall dependencies if needed
./run.sh
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Credits

- **CircuitMatter** - Pure Python Matter implementation by Adafruit
- **luma.lcd** - TFT display driver
- **gpiozero** - GPIO control library
- **python-matter-server** - Matter protocol support

## 📞 Support

- **Issues**: https://github.com/yourusername/smartpanel/issues
- **Discussions**: https://github.com/yourusername/smartpanel/discussions
- **Documentation**: https://github.com/yourusername/smartpanel/wiki

## 🎯 Roadmap

- [ ] Web interface for configuration
- [ ] MQTT integration
- [ ] Home Assistant auto-discovery
- [ ] Custom button icons on display
- [ ] Touch screen support
- [ ] Multiple Matter device types (sensors, lights, etc.)
- [ ] OTA updates
- [ ] Multi-language support

---

**Made with ❤️ for the smart home community**

**Your Raspberry Pi is now a REAL Matter device!** 🎉

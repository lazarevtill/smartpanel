# Smart Panel v2.0 - Matter-Enabled Raspberry Pi Control Panel

A modular, Matter-enabled control panel for Raspberry Pi with TFT display and 6 configurable buttons.

## 🌟 Key Features

- **Matter Device Server**: Exposes Smart Panel as a Matter device with 6 buttons
- **Encoder-Only Navigation**: Full menu system controlled via rotary encoder
- **Configurable Buttons**: Each button can trigger system functions AND be exposed to Matter
- **QR Code Pairing**: Easy Matter device commissioning via on-screen QR code
- **System Monitoring**: Real-time CPU, RAM, disk, temperature, network, and uptime
- **GPIO Control**: Manage GPIO pins directly from the panel
- **Emergency Reset**: Hold buttons 1+6 for 10 seconds to reset configuration
- **Modular Architecture**: Clean, maintainable code following KISS principles

## 📋 Hardware Requirements

- **Raspberry Pi 3B+** (or newer)
- **ST7735/ST7735R TFT Display** (128x160 or 160x128)
- **KY-040 Rotary Encoder** (with push button)
- **6x Push Buttons** (GPIO-connected)

## 🔌 Wiring

### TFT Display (SPI)
- VCC → 3.3V
- GND → Ground
- CS → CE0 (GPIO 8)
- RESET → GPIO 25
- A0/DC → GPIO 24
- SDA/MOSI → GPIO 10 (MOSI)
- SCK → GPIO 11 (SCLK)
- LED/BL → GPIO 18 (PWM)

### Rotary Encoder
- CLK → GPIO 17
- DT → GPIO 27
- SW → GPIO 22
- VCC → 3.3V
- GND → Ground

### 6 Buttons
- Button 1 → GPIO 5
- Button 2 → GPIO 6
- Button 3 → GPIO 16
- Button 4 → GPIO 26
- Button 5 → GPIO 12
- Button 6 → GPIO 21

## 🚀 Installation

### Quick Setup

```bash
cd /home/lazarev/smartpanel
chmod +x setup.sh run.sh
./setup.sh
```

### Manual Setup

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-dev python3-pip python3-venv \
    python3-lgpio python3-spidev libfreetype6-dev libjpeg-dev \
    libopenjp2-7 libtiff6 libatlas3-base

# Create virtual environment
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install Python packages
pip3 install --upgrade pip
pip3 install luma.lcd pillow psutil qrcode[pil] gpiozero RPi.GPIO

# Enable SPI
sudo raspi-config nonint do_spi 0
```

## 🎮 Usage

### Starting the Panel

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python3 dashboard_new.py
```

### Controls

- **Rotate Encoder**: Navigate menus, adjust values
- **Short Press (Encoder)**: Select item, confirm action
- **Long Press (Encoder)**: Go back to previous screen
- **Physical Buttons**: Configurable functions (see Button Configuration)

### Default Button Functions

- **Button 1-2, 4**: Matter-only (no system function)
- **Button 3**: Back navigation + Matter
- **Button 5**: Cycle display offset + Matter
- **Button 6**: Show Matter QR code + Matter

### Emergency Reset

Hold **Button 1 + Button 6** for 10 seconds to:
- Reset all configuration to defaults
- Restart the Smart Panel

## 📱 Matter Integration

### What is Matter?

Matter is a universal smart home protocol that works with:
- Apple HomeKit (iPhone, iPad, HomePod)
- Google Home (Android, Google Nest)
- Amazon Alexa
- Samsung SmartThings
- And more!

### How It Works

The Smart Panel acts as a **Matter device** with 6 buttons. Each button:
1. **Appears in your smart home app** as a switch/button
2. **Can trigger automations** when pressed
3. **Can be controlled remotely** from your phone
4. **Updates state in real-time** via Matter protocol

### Pairing with Matter

1. Navigate to **Main Menu → Matter Status**
2. Press encoder to **show QR code**
3. Open your smart home app (Apple Home, Google Home, etc.)
4. Select **"Add Device"** or **"Add Accessory"**
5. Scan the QR code on the TFT display
6. Follow app instructions to complete pairing

**Manual Pairing Code**: Also displayed if QR scanning doesn't work

### Example Use Cases

- **Button 1**: Turn on living room lights
- **Button 2**: Start coffee maker
- **Button 3**: Activate "Good Morning" scene
- **Button 4**: Toggle garage door
- **Button 5**: Arm security system
- **Button 6**: Emergency alert

## 🎛️ Menu Structure

```
Smart Panel
├── System Info          # CPU, RAM, Disk, Temp, Network, Uptime
├── Matter Status        # Server status, button states, QR code
├── Button Config        # Configure button functions
├── GPIO Control         # Toggle GPIO pins
├── Settings             # Display, Matter, system settings
├── About                # Version and information
└── Power
    ├── Shutdown
    └── Restart
```

## ⚙️ Configuration

### Button Configuration

1. Navigate to **Main Menu → Button Config**
2. Rotate encoder to select button
3. Short press to edit function
4. Rotate to cycle through functions:
   - `Matter Button Only`: No system function
   - `Back + Matter`: Go back in menus
   - `Select + Matter`: Select items
   - `Main Menu + Matter`: Jump to main menu
   - `Show QR Code`: Display Matter pairing QR
   - `Cycle Display Offset`: Adjust screen alignment

### Display Settings

1. Navigate to **Main Menu → Settings**
2. Adjust:
   - **Brightness**: 0-100%
   - **Auto Refresh**: Enable/disable automatic updates
   - **Refresh Interval**: 1-30 seconds
   - **Matter Enabled**: Enable/disable Matter server

### Display Offset

If your TFT display has alignment issues:
1. Press **Button 5** (or assigned offset button)
2. Cycles through presets: (0,0), (2,1), (2,3), (0,25)
3. Setting is saved automatically

## 📁 Project Structure

```
smartpanel/
├── dashboard_new.py              # Main application
├── smartpanel_modules/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── display.py                # TFT display driver
│   ├── input_handler.py          # Encoder & button input
│   ├── button_manager.py         # Button function management
│   ├── matter_server.py          # Matter device server
│   ├── matter_qr.py              # QR code generation
│   ├── menu_system.py            # Menu navigation
│   ├── screens.py                # All screen implementations
│   ├── ui_components.py          # Reusable UI elements
│   ├── system_monitor.py         # System information
│   ├── gpio_control.py           # GPIO management
│   └── matter_integration.py     # Legacy Matter controller
├── setup.sh                      # Installation script
├── run.sh                        # Startup script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔧 Advanced Configuration

### Configuration File

Location: `~/.smartpanel_config.json`

```json
{
  "brightness": 100,
  "matter_enabled": true,
  "matter_vendor_id": "0xFFF1",
  "matter_product_id": "0x8000",
  "matter_discriminator": 3840,
  "matter_setup_pin": 20202021,
  "button_assignments": {
    "5": "none",
    "6": "none",
    "16": "back",
    "26": "none",
    "12": "offset_cycle",
    "21": "matter_qr"
  },
  "display_rotate": 1,
  "display_bgr": true,
  "font_size_small": 11,
  "font_size_medium": 14
}
```

### Logs

Location: `~/.smartpanel_logs/smartpanel_YYYYMMDD.log`

View logs:
```bash
tail -f ~/.smartpanel_logs/smartpanel_$(date +%Y%m%d).log
```

## 🐛 Troubleshooting

### Display Not Working

1. Check SPI is enabled: `lsmod | grep spi`
2. Verify wiring connections
3. Try different offset presets (Button 5)
4. Check logs for errors

### Matter Pairing Fails

1. Ensure Matter is enabled in Settings
2. Verify QR code is visible and clear
3. Try manual pairing code instead
4. Check smart home app compatibility
5. Note: Currently runs in **simulation mode** (python-matter-server not installed)

### Buttons Not Responding

1. Check GPIO connections
2. Verify button configuration in Button Config menu
3. Check logs for input events
4. Test with `gpio readall` command

### Emergency Reset Not Working

1. Hold **both** Button 1 AND Button 6
2. Hold for full 10 seconds
3. Watch for progress bar on screen
4. Release only after "RESET COMPLETE" message

## 📚 Development

### Adding New Screens

1. Create screen class in `smartpanel_modules/screens.py`
2. Inherit from `BaseScreen`
3. Implement `render()` and `handle_input()` methods
4. Add menu item in `dashboard_new.py`

### Adding Button Functions

1. Add function key to `BUTTON_FUNCTIONS` in `config.py`
2. Handle function in `button_manager.py`'s `handle_button_press()`
3. Function will automatically appear in Button Config menu

### Matter Integration

For real Matter functionality:
```bash
pip3 install python-matter-server
```

Then update `matter_server.py` to use the actual Matter SDK.

## 📄 License

MIT License - Feel free to modify and distribute

## 🙏 Acknowledgments

- **luma.lcd**: TFT display library
- **gpiozero**: GPIO interface
- **Matter**: Universal smart home protocol
- **Raspberry Pi Foundation**: Amazing hardware platform

## 📞 Support

Check logs first: `~/.smartpanel_logs/`

For issues:
1. Review troubleshooting section
2. Check wiring diagrams
3. Verify all dependencies installed
4. Test with minimal configuration

---

**Smart Panel v2.0** - Making your Raspberry Pi smarter, one button at a time! 🎛️✨

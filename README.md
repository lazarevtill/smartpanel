# Smart Panel v2.0 - Modular Raspberry Pi Control Dashboard

A professional, modular control panel for Raspberry Pi with TFT display, featuring an enhanced menu system with gesture controls, system monitoring, GPIO control, and Matter IoT integration with QR code commissioning.

## 🎉 What's New in v2.0

### ✨ **Modular Architecture**
- Clean separation of concerns with dedicated modules
- Easy to extend and customize
- Professional code organization

### 🎮 **Enhanced Input System**
- **Short Press**: Select items / Toggle devices
- **Long Press**: Go back to previous menu
- **Encoder Rotation**: Navigate menus smoothly
- **Fast Scroll Detection**: Accelerated navigation

### 🏠 **Matter IoT Integration**
- **Enabled by default** on Raspberry Pi
- **QR Code Display** for easy device commissioning (Press B7)
- Device discovery and control
- Framework ready for full Matter SDK

### 🎨 **Redesigned UI**
- Modern menu system with visual indicators
- Scroll bars for long lists
- Color-coded status indicators
- Professional title bars and separators

## 📦 Quick Start

### 1. **Setup (First Time)**
```bash
cd /home/lazarev/smartpanel
./setup.sh
```

This will:
- Install system dependencies
- Create a Python virtual environment
- Install all required packages
- Configure everything automatically

### 2. **Run Smart Panel**
```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python3 dashboard_new.py
```

## 🎯 Features

### 📊 **System Monitoring**
- Real-time CPU, memory, and disk usage
- Temperature monitoring with color warnings
- Network information (IP address, interface)
- System uptime tracking
- Auto-refresh with configurable intervals

### 🔌 **GPIO Control**
- Control up to 16 GPIO pins
- Visual ON/OFF indicators
- Safe pin initialization
- Direct encoder control

### 🏠 **Matter Device Control**
- Scan and discover Matter devices
- Control lights, switches, and sensors
- **QR Code Display** for commissioning (B7 button)
- Demo devices included for testing
- Ready for real Matter SDK integration

### ⚙️ **Settings**
- Brightness control
- Auto-refresh toggle
- Refresh interval adjustment
- Matter enable/disable
- Persistent configuration

## 🎮 Controls

### Rotary Encoder
- **Rotate**: Navigate menus, adjust values
- **Short Press**: Select item, toggle device
- **Long Press**: Go back to previous menu

### Hardware Buttons
- **B3 (GPIO16)**: Alternative back button
- **B5 (GPIO12)**: Cycle display offset presets
- **B6 (GPIO21)**: Rescan Matter devices
- **B7 (GPIO4)**: Show/hide Matter QR code

## 📁 Project Structure

```
smartpanel/
├── dashboard_new.py          # Main application entry point
├── setup.sh                  # Setup script (creates venv)
├── run.sh                    # Run script (activates venv)
├── requirements.txt          # Python dependencies
├── test_modular.py          # Module testing script
│
├── smartpanel_modules/       # Modular components
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration management
│   ├── display.py           # TFT display management
│   ├── input_handler.py     # Enhanced input handling
│   ├── menu_system.py       # Menu navigation system
│   ├── ui_components.py     # Reusable UI components
│   ├── screens.py           # All screen implementations
│   ├── system_monitor.py    # System monitoring
│   ├── gpio_control.py      # GPIO pin management
│   ├── matter_integration.py # Matter IoT framework
│   └── matter_qr.py         # QR code generation
│
└── venv/                     # Virtual environment (created by setup.sh)
```

## 🔧 Hardware Requirements

### Required
- **Raspberry Pi 3B+** (or compatible)
- **TFT Display**: ST7735 or ST7735R (128x160 or 160x128)
- **Rotary Encoder**: KY-040 with push button

### Optional
- **7 Push Buttons** for additional controls

### Wiring
See original README or comments in `config.py` for detailed wiring diagram.

## 🐍 Virtual Environment

The setup script creates an isolated Python virtual environment to avoid conflicts with system packages.

### Manual venv Management

**Create venv:**
```bash
python3 -m venv venv
```

**Activate venv:**
```bash
source venv/bin/activate
```

**Install packages:**
```bash
pip install -r requirements.txt
```

**Deactivate venv:**
```bash
deactivate
```

## 📦 Dependencies

### Core (Required)
- `gpiozero` - GPIO interface
- `luma.lcd` - TFT display driver
- `Pillow` - Image processing
- `psutil` - System monitoring
- `RPi.GPIO` - GPIO control

### Optional
- `qrcode[pil]` - QR code generation for Matter commissioning
- `chip-matter` - Full Matter SDK (when available)

## 🎨 Customization

### Adding New Menu Items

Edit `dashboard_new.py`:

```python
def my_custom_action(context):
    return MyCustomScreen()

# In _create_main_menu():
menu.add_item(MenuItem("My Feature", action=my_custom_action))
```

### Creating Custom Screens

Create a new screen in `smartpanel_modules/screens.py`:

```python
class MyCustomScreen(BaseScreen):
    def __init__(self):
        super().__init__("My Screen")
    
    def render(self, draw, width, height):
        # Your rendering code
        draw.text((4, 20), "Hello World!", font=FONT_M, fill=COLORS['fg'])
    
    def handle_input(self, enc_delta, enc_button_state, button_states):
        if enc_button_state == 'long_press':
            return 'back'
        return self
```

### Configuring Matter

Edit `~/.smartpanel_config.json`:

```json
{
  "matter_enabled": true,
  "matter_vendor_id": 65521,
  "matter_product_id": 32768,
  "matter_discriminator": 3840,
  "matter_setup_pin": 20202021
}
```

## 🧪 Testing

Run the test suite:
```bash
python3 test_modular.py
```

This verifies:
- All modules load correctly
- Configuration system works
- Menu navigation functions
- System monitoring retrieves data
- Matter integration initializes
- QR code generation works
- UI components render

## 🚀 Running as Service

To run Smart Panel automatically on boot, create a systemd service:

```bash
sudo nano /etc/systemd/system/smartpanel.service
```

```ini
[Unit]
Description=Smart Panel Dashboard
After=network.target

[Service]
Type=simple
User=lazarev
WorkingDirectory=/home/lazarev/smartpanel
ExecStart=/home/lazarev/smartpanel/run.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable smartpanel
sudo systemctl start smartpanel
```

## 🐛 Troubleshooting

### Virtual Environment Issues
```bash
# Remove and recreate venv
rm -rf venv
./setup.sh
```

### Display Not Working
- Check SPI is enabled: `sudo raspi-config` → Interface Options → SPI
- Try different offset presets (B5 button)
- Verify wiring connections

### Import Errors
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### Matter QR Code Not Showing
```bash
# Install QR code library
pip install qrcode[pil]
```

## 📝 Configuration Files

- `~/.smartpanel_config.json` - User settings
- `~/.tft_offset.json` - Display offset calibration

## 🔄 Updating

Pull latest changes and update:
```bash
git pull
./setup.sh  # Updates venv and dependencies
```

## 📄 License

MIT License - Feel free to modify and distribute

## 🙏 Credits

Built with:
- **Raspberry Pi** and Raspbian OS
- **luma.lcd** - Display control
- **gpiozero** - GPIO management  
- **psutil** - System monitoring
- **Pillow** - Image processing
- **qrcode** - QR code generation

---

**Smart Panel v2.0** - Professional Raspberry Pi Control Dashboard with Modular Architecture and Matter IoT Integration

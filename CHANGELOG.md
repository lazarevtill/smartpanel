# Changelog

All notable changes to Smart Panel will be documented in this file.

## [2.0.0] - 2025-10-19

### 🎉 Major Release - Matter-Enabled Control Panel

Complete refactoring with Matter support, encoder-only navigation, and modular architecture.

### Added
- **Matter Device Server**: Smart Panel now acts as a Matter device with 6 buttons
- **Button Manager**: Configurable button functions with dual-purpose (Matter + system)
- **Encoder-Only Navigation**: Full menu system controlled via rotary encoder
- **Emergency Reset**: Hold Button 1 + Button 6 for 10 seconds to reset configuration
- **Button Configuration Screen**: Configure button functions via UI
- **Matter Status Screen**: View server status, button states, and QR code
- **Comprehensive Logging**: Python logging throughout all modules
- **Color Schemes**: Configurable color schemes for better TFT readability
- **Font Configuration**: Adjustable font sizes for optimal display clarity
- **QR Code Pairing**: Generate Matter pairing QR code on-screen
- **Configuration Management**: All settings saved to `~/.smartpanel_config.json`
- **Display Settings**: Rotation, BGR mode, invert, brightness all configurable
- **Enhanced Setup Script**: Automatic dependency installation and SPI enablement
- **Enhanced Run Script**: Pre-flight checks and colorful status display
- **Documentation**: README.md, QUICKSTART.md, REFACTORING_SUMMARY.md

### Changed
- **Button Count**: Reduced from 7 to 6 buttons (cleaner design)
- **Matter Architecture**: Changed from Matter controller to Matter device
- **Navigation**: All menu navigation now via encoder (short press = select, long press = back)
- **Module Structure**: Split monolithic code into 10 specialized modules
- **Configuration**: Moved all settings to UI (no more manual config editing)
- **Default Settings**: Matter enabled by default, improved font sizes
- **Log Location**: Moved to `~/.smartpanel_logs/` with daily rotation

### Removed
- **Button 7**: Reduced to 6 buttons total
- **Matter Controller**: No longer controls other Matter devices
- **Button-Based Navigation**: Replaced with encoder-only navigation
- **Hardcoded Settings**: All settings now configurable

### Fixed
- **Import Errors**: Fixed COLORS import issue in screens.py
- **GPIO Compatibility**: Better support for Debian 13 (Trixie) with lgpio
- **SPI Initialization**: Improved error handling for display initialization
- **Configuration Persistence**: Settings now properly save and load
- **Display Offset**: Multiple presets for different TFT displays

### Technical Details

#### New Modules
- `smartpanel_modules/matter_server.py` - Matter device server implementation
- `smartpanel_modules/button_manager.py` - Button function management
- `smartpanel_modules/input_handler.py` - Enhanced input handling with emergency reset

#### Updated Modules
- `smartpanel_modules/config.py` - Centralized configuration with color schemes
- `smartpanel_modules/display.py` - Configurable display settings
- `smartpanel_modules/screens.py` - New Matter status and button config screens
- `smartpanel_modules/ui_components.py` - Improved fonts and colors
- `dashboard_new.py` - Integrated all new components

#### Configuration Schema
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
  "display_invert": false,
  "font_size_small": 11,
  "font_size_medium": 14,
  "qr_size": 90,
  "color_scheme": "default"
}
```

### Migration from v1.x

1. Backup your old configuration
2. Run `./setup.sh` to install new dependencies
3. Start with `./run.sh`
4. Reconfigure buttons via UI (Main Menu → Button Config)
5. Re-pair with Matter controllers if previously paired

### Known Issues
- Matter runs in simulation mode (requires `python-matter-server` for real functionality)
- QR code shows placeholder box (PIL image pasting limitation)
- Button config UI could be more intuitive

### Dependencies
- Python 3.9+
- gpiozero >= 1.6.0
- luma.lcd >= 2.9.0
- Pillow >= 10.0.0
- psutil >= 5.8.0
- RPi.GPIO >= 0.7.0
- qrcode[pil] >= 7.0
- python3-lgpio (system package)
- python3-spidev (system package)

---

## [1.0.0] - Previous Version

### Initial Release
- Basic dashboard with TFT display
- 7 physical buttons
- Rotary encoder input
- System monitoring
- GPIO control
- Basic Matter controller (experimental)
- Monolithic architecture

---

## Version History

- **v2.0.0** (2025-10-19): Matter-enabled control panel with modular architecture
- **v1.0.0** (Previous): Initial release

---

## Upgrade Path

### From v1.0.0 to v2.0.0

**Breaking Changes:**
- Button count reduced (7 → 6)
- Matter controller → Matter device
- Configuration file format changed
- Navigation changed to encoder-only

**Steps:**
```bash
# Backup
cp ~/.smartpanel_config.json ~/.smartpanel_config.json.v1.backup

# Update code
cd /home/lazarev/smartpanel
git pull  # or download new version

# Reinstall
./setup.sh

# Run
./run.sh
```

**Post-Upgrade:**
1. Reconfigure buttons via UI
2. Re-pair with Matter controllers
3. Adjust display settings if needed
4. Test all functions

---

## Future Releases

### Planned for v2.1.0
- Real Matter server integration (python-matter-server)
- Improved QR code rendering
- Better button config UX
- Automated tests
- More color schemes

### Planned for v2.5.0
- WiFi configuration screen
- Network diagnostics
- Custom automations
- Voice control integration
- Bluetooth support

### Planned for v3.0.0
- Touch screen support
- Web interface
- Mobile app
- Plugin system
- Multi-panel support

---

For detailed changes, see [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)


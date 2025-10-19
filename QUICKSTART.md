# Smart Panel v2.0 - Quick Start Guide

## 🚀 Installation (5 minutes)

```bash
cd /home/lazarev/smartpanel
chmod +x setup.sh run.sh
./setup.sh
```

The setup script will:
- ✓ Install system dependencies
- ✓ Enable SPI interface
- ✓ Create Python virtual environment
- ✓ Install all required packages
- ✓ Verify installation

## ▶️ Running

```bash
./run.sh
```

## 🎮 Basic Controls

### Encoder (Primary Control)
- **Rotate**: Navigate menus, scroll lists, adjust values
- **Short Press**: Select item, confirm action
- **Long Press**: Go back to previous screen

### Physical Buttons (Default)
- **Button 1-2, 4**: Matter-only (no system function)
- **Button 3**: Back navigation
- **Button 5**: Cycle display offset
- **Button 6**: Show Matter QR code

### Emergency Reset
- Hold **Button 1 + Button 6** for 10 seconds
- Resets all configuration to defaults

## 📱 Adding to Matter Smart Home

### Apple Home (iPhone/iPad)

1. On Smart Panel:
   - Navigate to **Main Menu → Matter Status**
   - Press encoder to show QR code

2. On iPhone:
   - Open **Home** app
   - Tap **+** → **Add Accessory**
   - Scan QR code on TFT screen
   - Follow prompts to add "Smart Panel"

3. Configure buttons:
   - Each button appears as a switch
   - Rename: "Living Room Light", "Coffee Maker", etc.
   - Create automations based on button presses

### Google Home (Android)

1. On Smart Panel:
   - Navigate to **Main Menu → Matter Status**
   - Press encoder to show QR code

2. On Android:
   - Open **Google Home** app
   - Tap **+** → **Set up device** → **New device**
   - Scan QR code on TFT screen
   - Follow prompts to add device

3. Configure buttons:
   - Assign to rooms
   - Create routines triggered by buttons

## 🎛️ Menu Navigation

```
Main Menu
├── System Info          # View CPU, RAM, temperature, etc.
├── Matter Status        # View server status, show QR code
├── Button Config        # Assign functions to buttons
├── GPIO Control         # Toggle GPIO pins
├── Settings             # Configure display, Matter, system
├── About                # Version information
└── Power                # Shutdown/Restart
```

## ⚙️ Configuring Buttons

1. Navigate to **Main Menu → Button Config**
2. Rotate encoder to select button (1-6)
3. Short press to edit
4. Rotate to cycle through functions:
   - `Matter Button Only`
   - `Back + Matter`
   - `Select + Matter`
   - `Main Menu + Matter`
   - `Show QR Code`
   - `Cycle Display Offset`
5. Short press to confirm

**Note**: All buttons are always exposed to Matter. The function just adds a local system action.

## 🔧 Common Tasks

### View System Status
1. Main Menu → **System Info**
2. See real-time CPU, RAM, disk, temperature, network, uptime

### Adjust Display Alignment
1. Press **Button 5** repeatedly to cycle through offsets
2. Or: Main Menu → Settings → (configure offset in future update)

### Pair with Smart Home
1. Main Menu → **Matter Status**
2. Short press encoder → QR code appears
3. Scan with smart home app
4. Long press encoder to exit QR view

### Configure Settings
1. Main Menu → **Settings**
2. Rotate to select setting
3. Rotate to adjust value
4. Short press to move to next setting
5. Long press to save and exit

### Emergency Reset
1. Hold **Button 1 + Button 6** simultaneously
2. Progress bar appears
3. Keep holding for 10 seconds
4. Panel resets and restarts

## 📊 Understanding Matter Status

When you view **Matter Status**, you'll see:

- **Status**: Running/Stopped
- **Pairing**: Paired/Not Paired
- **Mode**: SIMULATION (until python-matter-server installed)
- **Buttons**: 6
- **Button States**: Current on/off state of each button

Press encoder to toggle QR code display.

## 🔍 Troubleshooting

### Display not working
```bash
# Check SPI is enabled
lsmod | grep spi

# If not, enable it
sudo raspi-config nonint do_spi 0
sudo reboot
```

### Display misaligned
- Press **Button 5** to cycle through offset presets
- Try: (0,0), (2,1), (2,3), (0,25)

### Buttons not responding
- Check GPIO connections
- View logs: `tail -f ~/.smartpanel_logs/smartpanel_$(date +%Y%m%d).log`
- Test button config: Main Menu → Button Config

### Matter pairing fails
- Ensure Matter is enabled: Main Menu → Settings
- Try manual pairing code (shown below QR)
- Check smart home app compatibility
- Note: Real Matter requires `python-matter-server` package

### Can't navigate menus
- Use **encoder rotation** to navigate
- Use **short press** to select
- Use **long press** to go back
- Physical buttons have specific functions only

## 📁 File Locations

- **Configuration**: `~/.smartpanel_config.json`
- **Logs**: `~/.smartpanel_logs/`
- **Code**: `/home/lazarev/smartpanel/`

## 🔄 Updating

```bash
cd /home/lazarev/smartpanel
git pull  # If using git
./setup.sh  # Rebuild environment
./run.sh   # Start panel
```

## 📖 More Information

- Full documentation: `README.md`
- Hardware wiring: `README.md` → Wiring section
- Configuration options: `README.md` → Configuration section

## 💡 Example Use Cases

### Home Automation
- Button 1: "Good Morning" scene (lights, coffee, news)
- Button 2: "Leaving Home" (lock doors, arm security, turn off lights)
- Button 3: Back navigation (system function)
- Button 4: "Movie Time" (dim lights, close blinds, turn on TV)
- Button 5: Cycle display offset (system function)
- Button 6: Show Matter QR (system function)

### Smart Office
- Button 1: Start work session (lights on, focus mode)
- Button 2: Break time (ambient lighting, music)
- Button 3: Navigation
- Button 4: End work (save, backup, turn off equipment)
- Button 5: Display adjustment
- Button 6: QR code access

### Workshop/Garage
- Button 1: Main lights
- Button 2: Workbench lights
- Button 3: Navigation
- Button 4: Ventilation fan
- Button 5: Display adjustment
- Button 6: QR code access

## 🎯 Next Steps

1. ✓ Install and run Smart Panel
2. ✓ Navigate menus with encoder
3. ✓ View system information
4. ✓ Configure button functions
5. ✓ Pair with Matter smart home
6. ✓ Create automations in smart home app
7. ✓ Enjoy your smart control panel!

---

**Need help?** Check `README.md` for detailed documentation or review logs in `~/.smartpanel_logs/`


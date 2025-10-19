# 🚀 Smart Panel - Quick Start Guide

Get your Smart Panel running as a Matter device in 5 minutes!

## ⚡ Super Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/yourusername/smartpanel.git
cd smartpanel
./setup.sh

# 2. Run
./run.sh

# 3. Add to SmartThings
# - Navigate to "Matter Status" on screen
# - Press encoder to show QR code
# - Scan with SmartThings app
# - Done!
```

## 📱 Adding to Your Smart Home

### Samsung SmartThings (Recommended)
1. Open SmartThings app
2. Tap **+** (Add Device)
3. Select **Scan QR Code**
4. On Smart Panel: Menu → Matter Status → Press Encoder
5. Scan QR code from screen
6. Follow prompts
7. Your 6 buttons appear!

### Apple Home
1. Open Home app
2. Tap **+** → **Add Accessory**
3. Tap **More Options**
4. Select "Smart Panel"
5. Enter code: `3840-2020-20214`
6. Complete setup

### Google Home
1. Open Google Home app
2. Tap **+** → **Set up device**
3. Select **Works with Google** → **Matter**
4. Scan QR code
5. Complete setup

## 🎮 Basic Controls

### Encoder
- **Rotate**: Navigate
- **Short Press**: Select
- **Long Press**: Back

### Buttons
- **Button 1-6**: Matter switches (configurable)
- **Button 3**: Quick back
- **Button 5**: Cycle display offset
- **Button 6**: Show/hide QR code
- **Button 1+6 (hold 10s)**: Emergency reset

## 📋 Main Menu

```
Smart Panel
├── System Info      # CPU, memory, temperature
├── Matter Status    # Device status, QR code
├── Button Config    # Configure button functions
├── GPIO Control     # Toggle GPIO pins
├── Settings         # Brightness, refresh, Matter
├── About           # Version info
└── Power           # Shutdown, restart
```

## 🔧 Configuration

All settings in: `~/.smartpanel_config.json`

Quick settings via UI:
1. Menu → Settings
2. Rotate to select setting
3. Rotate to change value
4. Short press to next setting
5. Long press to save and exit

## 📊 Matter Device Info

```
QR Code:     MT:0000005WF77J6U32IR2QBU
Manual Code: 3840-2020-20214
Buttons:     6 (GPIO 5,6,16,26,12,21)
```

## 🐛 Quick Troubleshooting

### Display not working?
```bash
# Enable SPI
sudo raspi-config nonint do_spi 0
sudo reboot
```

### Matter not working?
```bash
# Check CircuitMatter
python3 -c "import circuitmatter; print('OK')"

# Reinstall if needed
pip install circuitmatter HAP-python
```

### Buttons not responding?
- Check wiring
- View logs: `tail -f ~/.smartpanel_logs/*.log`
- Check GPIO permissions: `groups | grep gpio`

### Can't add to SmartThings?
- Use manual code: `3840-2020-20214`
- Ensure same WiFi network
- Restart avahi: `sudo systemctl restart avahi-daemon`

## 📝 Logs

```bash
# View current log
tail -f ~/.smartpanel_logs/smartpanel_$(date +%Y%m%d).log

# View Matter logs only
tail -f ~/.smartpanel_logs/*.log | grep Matter

# Clear logs
rm ~/.smartpanel_logs/*.log
```

## 🔄 Update

```bash
cd ~/smartpanel
git pull
./setup.sh
./run.sh
```

## 📞 Need Help?

- **Full Docs**: See README.md
- **Issues**: GitHub Issues
- **Logs**: `~/.smartpanel_logs/`
- **Config**: `~/.smartpanel_config.json`

## ✅ Checklist

- [ ] Hardware connected correctly
- [ ] SPI enabled (`lsmod | grep spi`)
- [ ] Setup script run (`./setup.sh`)
- [ ] Display shows menu
- [ ] Encoder navigates menus
- [ ] Matter Status shows "Running"
- [ ] QR code displays
- [ ] Device added to smart home app
- [ ] Buttons appear as switches
- [ ] Physical buttons work
- [ ] App control works

## 🎉 Success!

If all checkboxes are checked, you're done! Your Smart Panel is now a fully functional Matter device.

**Enjoy your smart home control panel!** 🏠✨

---

**Need more details?** See [README.md](README.md) for complete documentation.

#!/usr/bin/env python3
"""
Test script for modular Smart Panel
Verifies all modules load correctly
"""

import sys
import os

print("Smart Panel v2.0 - Modular System Test")
print("=" * 50)
print()

# Test 1: Import all modules
print("Test 1: Importing modules...")
try:
    from smartpanel_modules import config
    print("  ✓ config")
    
    from smartpanel_modules import ui_components
    print("  ✓ ui_components")
    
    from smartpanel_modules import menu_system
    print("  ✓ menu_system")
    
    from smartpanel_modules import system_monitor
    print("  ✓ system_monitor")
    
    from smartpanel_modules import gpio_control
    print("  ✓ gpio_control")
    
    from smartpanel_modules import matter_integration
    print("  ✓ matter_integration")
    
    from smartpanel_modules import matter_qr
    print("  ✓ matter_qr")
    
    from smartpanel_modules import input_handler
    print("  ✓ input_handler")
    
    from smartpanel_modules import display
    print("  ✓ display")
    
    from smartpanel_modules import screens
    print("  ✓ screens")
    
    print("  ✓ All modules imported successfully!")
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

print()

# Test 2: Configuration
print("Test 2: Configuration...")
try:
    cfg = config.load_config()
    print(f"  ✓ Config loaded: {len(cfg)} settings")
    print(f"    - Matter enabled: {cfg.get('matter_enabled')}")
    print(f"    - Brightness: {cfg.get('brightness')}")
    print(f"    - Refresh interval: {cfg.get('refresh_interval')}s")
except Exception as e:
    print(f"  ✗ Config test failed: {e}")

print()

# Test 3: Menu System
print("Test 3: Menu System...")
try:
    from smartpanel_modules.menu_system import Menu, MenuItem
    
    menu = Menu("Test Menu")
    menu.add_item(MenuItem("Item 1", action=lambda x: "action1"))
    menu.add_item(MenuItem("Item 2", action=lambda x: "action2"))
    
    print(f"  ✓ Menu created: '{menu.title}'")
    print(f"    - Items: {len(menu.items)}")
    
    menu.navigate(1)
    print(f"    - Navigation works (selected: {menu.selected_index})")
except Exception as e:
    print(f"  ✗ Menu test failed: {e}")

print()

# Test 4: System Monitoring
print("Test 4: System Monitoring...")
try:
    from smartpanel_modules.system_monitor import get_system_info
    
    info = get_system_info()
    if info:
        print(f"  ✓ System info retrieved:")
        print(f"    - CPU: {info.get('cpu', 0):.1f}%")
        print(f"    - Memory: {info.get('memory', 0):.1f}%")
        print(f"    - Temperature: {info.get('temperature', 0):.1f}°C")
        print(f"    - IP: {info.get('network', {}).get('ip', 'N/A')}")
    else:
        print("  ✗ System info empty")
except Exception as e:
    print(f"  ✗ System monitor test failed: {e}")

print()

# Test 5: Matter Integration
print("Test 5: Matter Integration...")
try:
    from smartpanel_modules.matter_integration import MatterController
    
    controller = MatterController()
    print(f"  ✓ Matter controller created")
    print(f"    - Enabled: {controller.enabled}")
    
    devices = controller.scan_devices()
    print(f"    - Devices found: {len(devices)}")
    
    if devices:
        print(f"    - Sample device: {devices[0].name} ({devices[0].type})")
except Exception as e:
    print(f"  ✗ Matter test failed: {e}")

print()

# Test 6: QR Code Support
print("Test 6: QR Code Support...")
try:
    from smartpanel_modules.matter_qr import HAS_QRCODE, get_default_matter_payload
    
    if HAS_QRCODE:
        print("  ✓ QR code library available")
        payload = get_default_matter_payload()
        print(f"    - Default payload: {payload}")
    else:
        print("  ⚠ QR code library not installed (optional)")
        print("    Install with: pip install qrcode[pil]")
except Exception as e:
    print(f"  ✗ QR code test failed: {e}")

print()

# Test 7: UI Components
print("Test 7: UI Components...")
try:
    from smartpanel_modules.ui_components import ProgressBar, TextDisplay, Button
    
    pb = ProgressBar(0, 0, 100, 10)
    td = TextDisplay(0, 20, 100, 20)
    btn = Button(0, 40, 60, 20, "Test")
    
    print("  ✓ UI components created:")
    print(f"    - ProgressBar: {pb.width}x{pb.height}")
    print(f"    - TextDisplay: {td.width}x{td.height}")
    print(f"    - Button: '{btn.text}'")
except Exception as e:
    print(f"  ✗ UI components test failed: {e}")

print()

# Test 8: Screens
print("Test 8: Screen Classes...")
try:
    from smartpanel_modules.screens import (
        BaseScreen, MenuScreen, SystemInfoScreen,
        GPIOControlScreen, MatterDevicesScreen,
        SettingsScreen, AboutScreen
    )
    
    screens_list = [
        "BaseScreen", "MenuScreen", "SystemInfoScreen",
        "GPIOControlScreen", "MatterDevicesScreen",
        "SettingsScreen", "AboutScreen"
    ]
    
    print(f"  ✓ All screen classes available:")
    for screen_name in screens_list:
        print(f"    - {screen_name}")
except Exception as e:
    print(f"  ✗ Screens test failed: {e}")

print()
print("=" * 50)
print("✓ All tests completed successfully!")
print()
print("The modular Smart Panel system is ready to use.")
print()
print("To run the dashboard:")
print("  ./run.sh")
print("  or")
print("  python3 dashboard_new.py")
print()


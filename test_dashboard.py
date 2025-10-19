#!/usr/bin/env python3
"""
Test script for Smart Panel dashboard functionality
Run this to verify the dashboard components work correctly
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import dashboard
        print("✓ Dashboard module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_menu_system():
    """Test the menu system components"""
    try:
        from dashboard import Menu, MenuItem, MenuScreen

        # Create a test menu
        test_menu = Menu("Test Menu")
        test_menu.add_item(MenuItem("Item 1", action=lambda x: print("Action 1")))
        test_menu.add_item(MenuItem("Item 2", action=lambda x: print("Action 2")))

        print("✓ Menu system components created successfully")
        print(f"  - Menu: {test_menu.title}")
        print(f"  - Items: {len(test_menu.items)}")

        return True
    except Exception as e:
        print(f"✗ Menu system test failed: {e}")
        return False

def test_system_monitoring():
    """Test system monitoring functions"""
    try:
        from dashboard import get_system_info, get_cpu_temperature

        # Test system info
        info = get_system_info()
        if info:
            print("✓ System monitoring working")
            print(f"  - CPU: {info.get('cpu', 'N/A')}%")
            print(f"  - Memory: {info.get('memory', 'N/A')}%")
            print(f"  - Temperature: {info.get('temperature', 'N/A')}°C")
        else:
            print("✗ System info returned empty data")
            return False

        # Test temperature
        temp = get_cpu_temperature()
        if temp > 0:
            print(f"✓ CPU temperature: {temp}°C")
        else:
            print("✗ Temperature reading failed")

        return True
    except Exception as e:
        print(f"✗ System monitoring test failed: {e}")
        return False

def test_ui_components():
    """Test UI component creation"""
    try:
        from dashboard import ProgressBar, TextDisplay, Button

        # Create test components
        pb = ProgressBar(0, 0, 50, 10)
        td = TextDisplay(0, 20, 100, 20)
        btn = Button(0, 40, 60, 20, "Test Button")

        print("✓ UI components created successfully")
        print(f"  - ProgressBar: {pb.width}x{pb.height}")
        print(f"  - TextDisplay: {td.width}x{td.height}")
        print(f"  - Button: '{btn.text}'")

        return True
    except Exception as e:
        print(f"✗ UI components test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Smart Panel Dashboard - Test Suite")
    print("=" * 40)

    tests = [
        ("Import Test", test_imports),
        ("Menu System", test_menu_system),
        ("System Monitoring", test_system_monitoring),
        ("UI Components", test_ui_components),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1

    print(f"\n{'=' * 40}")
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Dashboard is ready to run.")
        print("\nTo run the dashboard:")
        print("  python3 dashboard.py")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

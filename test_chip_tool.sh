#!/bin/bash
#
# Test Matter Device with chip-tool (Official Matter CLI)
#
# This script helps you commission your Smart Panel using the official
# Matter command-line tool, which is more lenient than SmartThings.
#

echo "=========================================="
echo "Smart Panel - chip-tool Test Script"
echo "=========================================="
echo ""

# Check if chip-tool is installed
if ! command -v chip-tool &> /dev/null; then
    echo "❌ chip-tool not found!"
    echo ""
    echo "To install chip-tool:"
    echo "  1. Install build dependencies:"
    echo "     sudo apt-get update"
    echo "     sudo apt-get install git gcc g++ pkg-config libssl-dev libdbus-1-dev libglib2.0-dev libavahi-client-dev ninja-build python3-venv python3-dev python3-pip unzip libgirepository1.0-dev libcairo2-dev libreadline-dev"
    echo ""
    echo "  2. Clone Matter SDK:"
    echo "     git clone --depth 1 --branch v1.3.0.0 https://github.com/project-chip/connectedhomeip.git"
    echo "     cd connectedhomeip"
    echo "     ./scripts/checkout_submodules.py --shallow --platform linux"
    echo ""
    echo "  3. Build chip-tool:"
    echo "     source scripts/activate.sh"
    echo "     gn gen out/host"
    echo "     ninja -C out/host chip-tool"
    echo ""
    echo "  4. Install:"
    echo "     sudo cp out/host/chip-tool /usr/local/bin/"
    echo ""
    exit 1
fi

echo "✓ chip-tool found"
echo ""

# Get QR code from matter-device-state.json or use default
QR_CODE="MT:Y.K90IRV0161BR4YU10"
MANUAL_CODE="3840-2020-20214"

if [ -f "matter-device-state.json" ]; then
    # Try to extract manual code from state file
    if command -v jq &> /dev/null; then
        MANUAL_CODE_FROM_FILE=$(jq -r '.manual_code' matter-device-state.json 2>/dev/null)
        if [ -n "$MANUAL_CODE_FROM_FILE" ] && [ "$MANUAL_CODE_FROM_FILE" != "null" ]; then
            MANUAL_CODE="$MANUAL_CODE_FROM_FILE"
        fi
    fi
fi

echo "Matter Pairing Information:"
echo "  QR Code: $QR_CODE"
echo "  Manual Code: $MANUAL_CODE"
echo ""

# Check if Smart Panel is running
if ! pgrep -f dashboard_new.py > /dev/null; then
    echo "⚠️  Smart Panel is not running!"
    echo ""
    echo "Please start it first:"
    echo "  ./run.sh"
    echo ""
    exit 1
fi

echo "✓ Smart Panel is running"
echo ""

# Commission the device
echo "Commissioning Smart Panel with chip-tool..."
echo ""
echo "This will:"
echo "  1. Discover the device via mDNS"
echo "  2. Establish PASE session with PIN"
echo "  3. Exchange certificates (DAC/PAI)"
echo "  4. Complete commissioning with AddNOC"
echo ""

read -p "Press Enter to start commissioning..."

# Commission using QR code
echo ""
echo "Running: chip-tool pairing code 1 $QR_CODE"
echo ""

chip-tool pairing code 1 "$QR_CODE"

RESULT=$?

echo ""
echo "=========================================="

if [ $RESULT -eq 0 ]; then
    echo "✅ SUCCESS! Device commissioned!"
    echo ""
    echo "Your Smart Panel is now paired and ready to use."
    echo ""
    echo "Try controlling the buttons:"
    echo "  # Turn on button 1"
    echo "  chip-tool onoff on 1 1"
    echo ""
    echo "  # Turn off button 1"
    echo "  chip-tool onoff off 1 1"
    echo ""
    echo "  # Read button 1 state"
    echo "  chip-tool onoff read on-off 1 1"
    echo ""
else
    echo "❌ Commissioning failed (exit code: $RESULT)"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check that Smart Panel is running: ps aux | grep dashboard_new"
    echo "  2. Check network connectivity: ping $(hostname -I | awk '{print $1}')"
    echo "  3. Check Matter logs: tail -f ~/.smartpanel_logs/smartpanel_*.log"
    echo "  4. Try resetting Matter state: rm matter-device-state.json && ./run.sh"
    echo ""
fi

echo "=========================================="


#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "  Testing Matter Device Commissioning"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Kill any existing instances
pkill -9 -f dashboard_new 2>/dev/null
sleep 2

# Start the Smart Panel in background
echo "Starting Smart Panel..."
./run.sh > /tmp/matter_test.log 2>&1 &
PID=$!
echo "PID: $PID"

# Wait for initialization
echo "Waiting for Matter device to start..."
sleep 8

# Check if it's running
if ps -p $PID > /dev/null; then
    echo "✓ Smart Panel is running"
else
    echo "✗ Smart Panel failed to start"
    cat /tmp/matter_test.log | tail -20
    exit 1
fi

# Check for Matter device
echo ""
echo "Checking Matter device status..."
grep -q "Matter device server started successfully" /tmp/matter_test.log && echo "✓ Matter server started" || echo "✗ Matter server not started"
grep -q "Listening on UDP port 5541" /tmp/matter_test.log && echo "✓ UDP port 5541 listening" || echo "✗ UDP port not listening"
grep -q "with OnOff cluster" /tmp/matter_test.log && echo "✓ OnOff clusters added" || echo "✗ OnOff clusters missing"

echo ""
echo "QR Code: $(grep 'QR code data:' /tmp/matter_test.log | awk '{print $NF}')"
echo "Manual:  $(grep 'Manual code:' /tmp/matter_test.log | awk '{print $NF}')"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Smart Panel is ready for commissioning!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "To test commissioning:"
echo "  1. Open your smart home app (SmartThings/Home/etc)"
echo "  2. Add new Matter device"
echo "  3. Scan QR code from TFT screen or use manual code"
echo ""
echo "To stop: kill $PID"
echo ""
echo "Logs: tail -f /tmp/matter_test.log"
echo ""


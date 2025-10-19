#!/bin/bash
# Smart Panel v2.0 - Run Script
# Matter-Enabled Raspberry Pi Control Panel
# Activates virtual environment and starts the dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
LOG_DIR="$HOME/.smartpanel_logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Smart Panel v2.0"
echo "Matter-Enabled Control Panel"
echo -e "==========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}ERROR: Virtual environment not found!${NC}"
    echo "Please run setup first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Check if dashboard exists
if [ ! -f "$SCRIPT_DIR/dashboard_new.py" ]; then
    echo -e "${RED}ERROR: dashboard_new.py not found!${NC}"
    exit 1
fi

# Check if smartpanel_modules exists
if [ ! -d "$SCRIPT_DIR/smartpanel_modules" ]; then
    echo -e "${RED}ERROR: smartpanel_modules directory not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Dashboard files found"

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}WARNING: Running as root is not recommended${NC}"
    echo "Press Ctrl+C to cancel, or wait 3 seconds to continue..."
    sleep 3
fi

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo -e "${GREEN}✓${NC} Created log directory: $LOG_DIR"
fi

# Display current log file
TODAY=$(date +%Y%m%d)
LOG_FILE="$LOG_DIR/smartpanel_$TODAY.log"
echo -e "${GREEN}✓${NC} Logs will be written to: $LOG_FILE"

echo ""
echo -e "${BLUE}Starting Smart Panel...${NC}"
echo ""
echo "Controls:"
echo "  • Rotate encoder: Navigate menus"
echo "  • Short press: Select/Confirm"
echo "  • Long press: Go back"
echo "  • Button 5: Cycle display offset"
echo "  • Button 6: Show Matter QR code"
echo "  • Button 1+6 (hold 10s): Emergency reset"
echo ""
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo ""

# Change to script directory
cd "$SCRIPT_DIR"

# Run the dashboard
python3 dashboard_new.py

# Capture exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}Smart Panel exited normally${NC}"
else
    echo -e "${RED}Smart Panel exited with error code: $EXIT_CODE${NC}"
    echo "Check logs for details: $LOG_FILE"
fi

exit $EXIT_CODE


#!/bin/bash
# Smart Panel v2.0 - Run Script
# Activates virtual environment and starts the dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found!"
    echo "Please run setup first: ./setup.sh"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if dashboard exists
if [ ! -f "$SCRIPT_DIR/dashboard_new.py" ]; then
    echo "ERROR: dashboard_new.py not found!"
    exit 1
fi

# Run the dashboard
echo "Starting Smart Panel v2.0..."
echo "Press Ctrl+C to exit"
echo ""

cd "$SCRIPT_DIR"
python3 dashboard_new.py


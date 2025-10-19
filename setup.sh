#!/bin/bash
# Smart Panel v2.0 - Setup Script
# Creates/updates virtual environment and installs dependencies

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=========================================="
echo "Smart Panel v2.0 - Setup"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Install with: sudo apt install python3 python3-venv python3-full"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Found: $PYTHON_VERSION"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-venv \
    python3-full \
    libopenjp2-7 \
    libtiff6 \
    libatlas3-base \
    python3-numpy \
    python3-lgpio \
    python3-spidev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev

echo ""

# Create or update virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at: $VENV_DIR"
    echo "Updating virtual environment..."
else
    echo "Creating virtual environment at: $VENV_DIR"
    python3 -m venv "$VENV_DIR" --system-site-packages
fi

echo ""

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "Virtual environment activated"
echo "Python: $(which python)"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo ""

# Install Python packages from requirements.txt
echo "Installing Python packages..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    echo "WARNING: requirements.txt not found"
    echo "Installing core packages manually..."
    pip install gpiozero luma.lcd Pillow psutil RPi.GPIO qrcode[pil]
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run Smart Panel:"
echo "  ./run.sh"
echo "  or"
echo "  source venv/bin/activate && python3 dashboard_new.py"
echo ""
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo ""


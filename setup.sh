#!/bin/bash
# Smart Panel v2.0 - Setup Script
# Matter-Enabled Raspberry Pi Control Panel
# Creates/updates virtual environment and installs dependencies

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=========================================="
echo "Smart Panel v2.0 - Setup"
echo "Matter-Enabled Control Panel"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "WARNING: Not running on Raspberry Pi"
    echo "Some features may not work correctly"
    echo ""
fi

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
echo "This may take a few minutes..."
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-venv \
    python3-full \
    python3-pip \
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
    libwebp-dev \
    libopenblas-dev

echo ""
echo "✓ System dependencies installed"
echo ""

# Enable SPI if not already enabled
echo "Checking SPI interface..."
if ! lsmod | grep -q spi_bcm2835; then
    echo "Enabling SPI interface..."
    sudo raspi-config nonint do_spi 0
    echo "✓ SPI enabled (reboot may be required)"
else
    echo "✓ SPI already enabled"
fi

echo ""

# Create or update virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at: $VENV_DIR"
    read -p "Do you want to rebuild it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf "$VENV_DIR"
        echo "Creating new virtual environment..."
        python3 -m venv "$VENV_DIR" --system-site-packages
    else
        echo "Keeping existing virtual environment"
    fi
else
    echo "Creating virtual environment at: $VENV_DIR"
    python3 -m venv "$VENV_DIR" --system-site-packages
fi

echo ""

# Activate virtual environment
source "$VENV_DIR/bin/activate"

echo "✓ Virtual environment activated"
echo "  Python: $(which python)"
echo "  Version: $(python --version)"
echo ""

# Upgrade pip
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel --quiet

echo "✓ Build tools upgraded"
echo ""

# Install Python packages from requirements.txt
echo "Installing Python packages..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "✓ Python packages installed"
else
    echo "WARNING: requirements.txt not found"
    echo "Installing core packages manually..."
    pip install gpiozero luma.lcd Pillow psutil RPi.GPIO qrcode[pil]
    echo "✓ Core packages installed"
fi

echo ""

# Verify installation
echo "Verifying installation..."
python3 -c "import gpiozero, luma.lcd, PIL, psutil, qrcode; print('✓ All core modules imported successfully')" || {
    echo "ERROR: Module import failed"
    echo "Please check the error messages above"
    exit 1
}

echo ""

# Create log directory
LOG_DIR="$HOME/.smartpanel_logs"
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "✓ Created log directory: $LOG_DIR"
fi

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Smart Panel v2.0 is ready to run!"
echo ""
echo "Features:"
echo "  • 6 configurable buttons exposed to Matter"
echo "  • Encoder-only menu navigation"
echo "  • System monitoring (CPU, RAM, temp, etc.)"
echo "  • QR code pairing for Matter devices"
echo "  • Emergency reset (hold B1+B6 for 10s)"
echo ""
echo "To run Smart Panel:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 dashboard_new.py"
echo ""
echo "Configuration: ~/.smartpanel_config.json"
echo "Logs: ~/.smartpanel_logs/"
echo ""
echo "For help, see: README.md"
echo ""


#!/bin/bash
set -e

echo "🐾 Installing Pomo Pet..."
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone
INSTALL_DIR="$HOME/.pomo-pet"
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/someshfengde/pomo_pet.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install
echo "Installing dependencies..."
uv sync
uv pip install -e .

echo ""
echo "✅ Pomo Pet installed!"
echo ""
echo "Usage:"
echo "  pomo-pet --list-pets          # See available pets"
echo "  pomo-pet --pet avocado        # Launch with avocado"
echo "  pomo-pet --pet avocado --work 30 --break 10"
echo ""
echo "Or run from the install directory:"
echo "  cd $INSTALL_DIR"
echo "  make run"

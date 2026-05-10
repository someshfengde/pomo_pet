#!/bin/bash
set -e

echo "🐾 Installing Pomo Pet..."
echo ""

# Check if Homebrew is available — prefer brew install
if command -v brew &> /dev/null; then
    echo "Homebrew detected! Installing via brew..."
    brew tap someshfengde/pomo-pet
    brew install pomo-pet
    echo ""
    echo "✅ Pomo Pet installed via Homebrew!"
    echo "   Run: pomo-pet start"
    exit 0
fi

echo "Homebrew not found. Installing manually..."
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone or update
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

# Install dependencies
echo "Installing dependencies..."
uv sync

# Create wrapper script in ~/.local/bin
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

WRAPPER="$BIN_DIR/pomo-pet"
cat > "$WRAPPER" << 'EOF'
#!/bin/bash
cd "$HOME/.pomo-pet"
exec uv run python -m src "$@"
EOF
chmod +x "$WRAPPER"

echo ""
echo "✅ Pomo Pet installed!"
echo ""
echo "Usage:"
echo "  pomo-pet --list-pets          # See available pets"
echo "  pomo-pet --pet avocado        # Launch with avocado"
echo "  pomo-pet --stats              # View statistics"
echo ""
echo "Make sure ~/.local/bin is in your PATH:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "Add this to your ~/.zshrc or ~/.bashrc to make it permanent."

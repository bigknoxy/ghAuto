#!/bin/bash
#
# ghAuto Install Script
# One-line install: curl -fsSL https://raw.githubusercontent.com/bigknoxy/ghAuto/main/scripts/install.sh | bash
#

set -e

GHAUTO_DIR="${GHAUTO_DIR:-$HOME/.ghauto}"
GHAUTO_BIN="$GHAUTO_DIR/bin"
GHAUTO_SRC="$GHAUTO_DIR/src"

echo "🚀 Installing ghAuto..."

# Create directories
mkdir -p "$GHAUTO_DIR"
mkdir -p "$GHAUTO_DIR/data"
mkdir -p "$GHAUTO_BIN"

# Clone or update repository
if [[ -d "$GHAUTO_SRC/.git" ]]; then
    echo "Updating existing installation..."
    cd "$GHAUTO_SRC"
    git pull
else
    echo "Cloning repository..."
    git clone https://github.com/bigknoxy/ghAuto.git "$GHAUTO_SRC"
    cd "$GHAUTO_SRC"
fi

# Install dependencies
if command -v pip &> /dev/null; then
    pip install -e "$GHAUTO_SRC" --quiet
else
    echo "Python pip not found. Please install Python 3.10+ and pip."
    exit 1
fi

# Create wrapper script
cat > "$GHAUTO_BIN/ghauto" << EOF
#!/bin/bash
cd "$GHAUTO_SRC"
exec python3 -m src.cli "\$@"
EOF

chmod +x "$GHAUTO_BIN/ghauto"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$GHAUTO_BIN:"* ]]; then
    shell_config=""
    if [[ -f "$HOME/.zshrc" ]]; then
        shell_config="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        shell_config="$HOME/.bashrc"
    fi
    
    if [[ -n "$shell_config" ]]; then
        echo "" >> "$shell_config"
        echo "# ghAuto" >> "$shell_config"
        echo "export PATH=\"\$HOME/.ghauto/bin:\$PATH\"" >> "$shell_config"
        echo "Added to $shell_config - run 'source $shell_config' or restart terminal"
    fi
fi

echo "✅ ghAuto installed!"
echo ""
echo "Next steps:"
echo "  1. Run: ghauto init  (will auto-detect gh CLI token if authenticated)"
echo "  2. Run: ghauto analyze"
echo "  3. Run: ghauto serve"
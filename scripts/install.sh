#!/bin/bash
#
# ghAuto Install Script
# One-line install: curl -fsSL https://raw.githubusercontent.com/ghAuto/install/main/install.sh | bash
#

set -e

GHAUTO_DIR="${GHAUTO_DIR:-$HOME/.ghauto}"
GHAUTO_BIN="$GHAUTO_DIR/bin"

echo "🚀 Installing ghAuto..."

# Create directories
mkdir -p "$GHAUTO_DIR"
mkdir -p "$GHAUTO_DIR/data"
mkdir -p "$GHAUTO_BIN"

# Install to bin
if command -v pip &> /dev/null; then
    pip install --user ghauto 2>/dev/null || pip install ghauto
else
    echo "Python pip not found. Please install Python 3.10+ and pip."
    exit 1
fi

# Create wrapper script
cat > "$GHAUTO_BIN/ghauto" << 'EOF'
#!/bin/bash
exec python3 -m ghauto "$@"
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
echo "  1. Run: ghauto init"
echo "  2. Enter your GitHub token when prompted"
echo "  3. Run: ghauto analyze"
echo "  4. Run: ghauto serve"
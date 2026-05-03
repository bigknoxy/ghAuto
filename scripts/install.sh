#!/bin/bash
#
# ghAuto Install Script
# One-line install: curl -fsSL https://raw.githubusercontent.com/bigknoxy/ghAuto/main/scripts/install.sh | bash
#

set -e

GHAUTO_DIR="${GHAUTO_DIR:-$HOME/.ghauto}"
GHAUTO_BIN="$GHAUTO_DIR/bin"
GHAUTO_SRC="$GHAUTO_DIR/src"
GHAUTO_VENV="$GHAUTO_DIR/venv"
FORCE="${GHAUTO_FORCE:-false}"

# Allow force flag via environment variable
if [[ "$1" == "--force" ]]; then
    FORCE=true
fi

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

# Create or recreate virtual environment
if [[ "$FORCE" == "true" ]] || [[ ! -d "$GHAUTO_VENV" ]]; then
    if [[ -d "$GHAUTO_VENV" ]]; then
        echo "Recreating virtual environment (--force)..."
        rm -rf "$GHAUTO_VENV"
    else
        echo "Creating virtual environment..."
    fi
    python3 -m venv "$GHAUTO_VENV"
else
    # Check if venv is healthy (has python executable)
    if [[ ! -x "$GHAUTO_VENV/bin/python" ]]; then
        echo "Virtual environment appears corrupted, recreating..."
        rm -rf "$GHAUTO_VENV"
        python3 -m venv "$GHAUTO_VENV"
    fi
fi

# Install dependencies in venv
echo "Installing dependencies..."
"$GHAUTO_VENV/bin/pip" install -e "$GHAUTO_SRC" --quiet

# Create wrapper script
cat > "$GHAUTO_BIN/ghauto" << EOF
#!/bin/bash
cd "$GHAUTO_SRC"
exec "$GHAUTO_VENV/bin/python" -m src.cli "\$@"
EOF

chmod +x "$GHAUTO_BIN/ghauto"

# Add to PATH if not already in shell config file
path_in_config=false
shell_config=""
if [[ -f "$HOME/.zshrc" ]]; then
    shell_config="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    shell_config="$HOME/.bashrc"
fi

if [[ -n "$shell_config" ]]; then
    # Check if PATH entry already exists in shell config
    if grep -q "PATH.*\.ghauto/bin" "$shell_config" 2>/dev/null; then
        path_in_config=true
    fi
    
    if [[ "$path_in_config" != "true" ]]; then
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
echo ""
echo "Use --force flag to reinstall: curl -fsSL ... | bash --force"
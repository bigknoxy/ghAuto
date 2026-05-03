#!/bin/bash
#
# ghAuto Install Script
# One-line install with immediate use: eval "$(curl -fsSL https://raw.githubusercontent.com/bigknoxy/ghAuto/main/scripts/install.sh)"
# Standard install (requires terminal restart): curl -fsSL https://raw.githubusercontent.com/bigknoxy/ghAuto/main/scripts/install.sh | bash
#

set -e

GHAUTO_DIR="${GHAUTO_DIR:-$HOME/.ghauto}"
GHAUTO_BIN="$GHAUTO_DIR/bin"
GHAUTO_SRC="$GHAUTO_DIR/src"
GHAUTO_VENV="$GHAUTO_DIR/venv"
FORCE="${GHAUTO_FORCE:-false}"

# Allow force flag via environment variable or argument
if [[ "$1" == "--force" ]]; then
    FORCE=true
fi

# Output to stderr so eval only captures the PATH export
exec 1>&2

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
cat > "$GHAUTO_BIN/ghauto" << 'WRAPPER'
#!/bin/bash
GHAUTO_SRC="${GHAUTO_SRC:-$HOME/.ghauto/src}"
GHAUTO_VENV="${GHAUTO_VENV:-$HOME/.ghauto/venv}"
cd "$GHAUTO_SRC"
exec "$GHAUTO_VENV/bin/python" -m src.cli "$@"
WRAPPER

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
    fi
fi

echo "✅ ghAuto installed!"
echo ""
echo "Next steps:"
echo "  ghauto --version    # Check version"
echo "  ghauto init         # Initialize configuration"
echo ""

# Restore stdout for the PATH export line only
exec 1>&1
echo "export PATH=\"$GHAUTO_BIN:\$PATH\""
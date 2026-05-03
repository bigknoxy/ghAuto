#!/bin/bash
#
# ghAuto Uninstall Script
#

GHAUTO_DIR="${GHAUTO_DIR:-$HOME/.ghauto}"

echo "🗑️ Uninstalling ghAuto..."

# Remove ghAuto directory
if [[ -d "$GHAUTO_DIR" ]]; then
    rm -rf "$GHAUTO_DIR"
    echo "✓ Removed $GHAUTO_DIR"
fi

# Remove from PATH in shell config
shell_config=""
if [[ -f "$HOME/.zshrc" ]]; then
    shell_config="$HOME/.zshrc"
elif [[ -f "$HOME/.bashrc" ]]; then
    shell_config="$HOME/.bashrc"
fi

if [[ -n "$shell_config" && -f "$shell_config" ]]; then
    # Remove ghAuto lines from shell config
    sed -i '/# ghAuto/,+1d' "$shell_config" 2>/dev/null || true
    sed -i '/export PATH.*\.ghauto/d' "$shell_config" 2>/dev/null || true
    echo "✓ Cleaned up shell configuration"
fi

# Uninstall pip package (for source installs, this removes the editable install)
pip uninstall -y ghauto 2>/dev/null || true

echo ""
echo "✅ ghAuto uninstalled!"
echo "Run: source $shell_config (or restart terminal) to refresh PATH"
#!/bin/bash

set -e

# Check for root
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root. Use: sudo $0"
   exit 1
fi

# URL of the raw vercli.py script
VERCLI_SCRIPT_URL="http://forgejo.local/Neo/VersionCI/raw/branch/main/vercli.py"

# Install paths
INSTALL_DIR="/usr/local/lib/vercli"
SCRIPT_PATH="$INSTALL_DIR/vercli.py"
WRAPPER_PATH="/usr/local/bin/vercli"

echo "📁 Creating installation directory..."
mkdir -p "$INSTALL_DIR"

echo "📥 Downloading vercli.py from $VERCLI_SCRIPT_URL..."
curl -fsSL "$VERCLI_SCRIPT_URL" -o "$SCRIPT_PATH"

echo "🔒 Making vercli.py executable..."
chmod +x "$SCRIPT_PATH"

echo "⚙️ Creating wrapper script at $WRAPPER_PATH..."
cat > "$WRAPPER_PATH" << EOF
#!/bin/bash
python3 $SCRIPT_PATH "\$@"
EOF

chmod +x "$WRAPPER_PATH"

echo "✅ vercli installed successfully."
echo "👉 Run it using: vercli"
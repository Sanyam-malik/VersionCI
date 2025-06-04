#!/bin/bash

set -e

if [[ $EUID -ne 0 ]]; then
   echo "❌ Run as root: sudo $0"
   exit 1
fi

VERCLI_SCRIPT_URL="http://forgejo.local/Neo/VersionCI/raw/branch/main/vercli.py"
REQUIREMENTS_URL="http://forgejo.local/Neo/VersionCI/raw/branch/main/requirements.txt"

INSTALL_DIR="/usr/local/lib/vercli"
SCRIPT_PATH="$INSTALL_DIR/vercli.py"
WRAPPER_PATH="/usr/local/bin/vercli"
TMP_REQ="/tmp/vercli_requirements.txt"

echo "📁 Creating directory $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

echo "📥 Downloading vercli.py..."
curl -fsSL "$VERCLI_SCRIPT_URL" -o "$SCRIPT_PATH"

echo "📥 Downloading requirements.txt..."
curl -fsSL "$REQUIREMENTS_URL" -o "$TMP_REQ"

echo "📦 Installing Python dependencies for vercli..."
pip3 install --upgrade -r "$TMP_REQ"

rm -f "$TMP_REQ"

chmod +x "$SCRIPT_PATH"

echo "⚙️ Creating wrapper script at $WRAPPER_PATH..."
cat > "$WRAPPER_PATH" << EOF
#!/bin/bash
python3 $SCRIPT_PATH "\$@"
EOF

chmod +x "$WRAPPER_PATH"

echo "✅ vercli installed."
echo "👉 Run with: vercli"

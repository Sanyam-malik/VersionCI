#!/bin/bash

set -e

if [[ $EUID -ne 0 ]]; then
    echo "❌ Run as root: sudo $0"
    exit 1
fi

if [[ -z "$GIT_USER" || -z "$GIT_PASS" ]]; then
    echo "❌ Please set GIT_USER and GIT_PASS environment variables for authentication."
    exit 1
fi

AUTH_CREDENTIALS="$GIT_USER:$GIT_PASS"

BASE_URL="http://forgejo.local/Neo/VersionCI/raw/branch/main"
INSTALL_BASE="/usr/local/lib/version_ci"
TMP_REQ="/tmp/version_ci_requirements.txt"

declare -A components=(
    ["vercli"]="vercli.py"
    ["versionci"]="versionci.py"
)

# Determine what to install (interactive or via argument)
choice="${1:-}"

if [[ -z "$choice" ]]; then
    echo "🛠 What do you want to install?"
    echo "1) vercli"
    echo "2) versionci"
    echo "3) Both"
    read -rp "Enter your choice [1-3]: " choice
fi

case "$choice" in
    1) to_install=("vercli") ;;
    2) to_install=("versionci") ;;
    3) to_install=("vercli" "versionci") ;;
    *) echo "❌ Invalid choice."; exit 1 ;;
esac

echo "📁 Creating base install directory: $INSTALL_BASE"
mkdir -p "$INSTALL_BASE"

echo "📥 Downloading requirements.txt..."
curl -fsSL -u "$AUTH_CREDENTIALS" "$BASE_URL/requirements.txt" -o "$TMP_REQ"

echo "📦 Installing Python dependencies..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install Python 3 pip before running this script."
    exit 1
fi
pip3 install --upgrade --break-system-packages -r "$TMP_REQ"
rm -f "$TMP_REQ"

# Install selected components
for name in "${to_install[@]}"; do
    script_file="${components[$name]}"
    script_path="$INSTALL_BASE/$script_file"
    wrapper_path="/usr/local/bin/$name"

    echo "📥 Downloading $script_file..."
    curl -fsSL -u "$AUTH_CREDENTIALS" "$BASE_URL/$script_file" -o "$script_path"
    chmod +x "$script_path"

    echo "⚙️ Creating wrapper script at $wrapper_path..."
    cat > "$wrapper_path" << EOF
#!/bin/bash
python3 $script_path "\$@"
EOF
    chmod +x "$wrapper_path"

    echo "✅ $name installed. 👉 Run with: $name"

    # Special handling for versionci: set up systemd service
    if [[ "$name" == "versionci" ]]; then
        echo "🛠 Setting up systemd service for versionci..."

        SERVICE_FILE="/etc/systemd/system/versionci.service"

        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=VersionCI API Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 $script_path
WorkingDirectory=$INSTALL_BASE
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

        echo "🔄 Reloading systemd daemon..."
        systemctl daemon-reexec
        systemctl daemon-reload

        echo "✅ Enabling and starting versionci service..."
        systemctl enable --now versionci

        echo "🚀 versionci service is active. Use: systemctl status versionci"
    fi
done

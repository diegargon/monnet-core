#!/bin/sh

APP_DIR="/opt/monnet-core/monnet_gateway"
VENV_DIR="$APP_DIR/venv"
SYSTEMD_DIR="/etc/systemd/system"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed."
    exit 1
fi

if ! command -v pip >/dev/null 2>&1; then
    echo "Error: pip is not installed."
    exit 1
fi

echo "Creating python/pip virtual environment $VENV_DIR..."
python3 -m venv "$VENV_DIR"

echo "Installing dependencies..."
. "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"
deactivate

ANSIBLE_CFG="/etc/ansible/ansible.cfg"
echo "Configuring ansible: $ANSIBLE_CFG..."

# Ansible configuration
mkdir -p "/etc/ansible"
cat <<EOF > "$ANSIBLE_CFG"
[defaults]
stdout_callback=json
callback_whitelist=json
EOF

# Allow continuing to use docker without systemd

if [ -d "$SYSTEMD_DIR" ] && pidof systemd >/dev/null 2>&1; then
    SERVICE_FILE="$SYSTEMD_DIR/monnet-gateway.service"
    echo "Configuring systemd: $SERVICE_FILE..."

    cp ../files/monnet-gateway.service "$SERVICE_FILE"
    chmod 644 "$SERVICE_FILE"

    echo "Reloading/Enabling systemd..."
    systemctl daemon-reload
    systemctl enable monnet-gateway
    systemctl start monnet-gateway

    echo "You can check the service status with: systemctl status monnet-gateway"
    echo "You can check the logs with: journalctl -u monnet-gateway"
else
    echo "Systemd not detected or not running. Skipping systemd setup."
fi

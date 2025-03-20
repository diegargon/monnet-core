#!/bin/bash

APP_DIR="/opt/monnet-core/monnet_gateway"
VENV_DIR="$APP_DIR/venv"

if ! command -v pip &> /dev/null; then
    echo "Error: pip no está instalado."
    exit 1
fi

echo "Creating python/pip virtual environment $VENV_DIR..."
python3 -m venv $VENV_DIR


echo "Installing dependencies..."
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
deactivate

echo "Settings permissions..."
sudo chown -R root:root $APP_DIR
sudo chmod -R 755 $APP_DIR

SERVICE_FILE="/etc/systemd/system/monnet-gateway.service"
echo "Configuring systemd $SERVICE_FILE..."
cp ../files/monnet-gateway.service  $SERVICE_FILE
chmod 644 $SERVICE_FILE

ANSIBLE_CFG="/etc/ansible/ansible.cfg"
echo "Configuring ansible: $ANSIBLE_CFG..."

cat <<EOF | sudo tee $ANSIBLE_CFG > /dev/null
[defaults]
stdout_callback=json
callback_whitelist=json
EOF

echo "Reloading/Enabling systemd ..."
sudo systemctl daemon-reload
sudo systemctl enable monnet-gateway
sudo systemctl start monnet-gateway

echo "Installation completed."
echo "You can check the service status with: sudo systemctl status monnet-gateway"
echo "You can check the logs with: sudo journalctl -u monnet-gateway"

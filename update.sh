#!/bin/sh

APP_DIR="/opt/monnet-core/monnet_gateway"
VENV_DIR="$APP_DIR/venv"

echo "Updating Monnet Gateway..."

if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not installed."
    exit 1
fi

cd "$APP_DIR" || exit
echo "Fetching latest changes from Git..."
git pull origin main || { echo "Error: Failed to update the repository."; exit 1; }

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: The virtual environment does not exist. Run install.sh first."
    exit 1
fi

echo "Activating virtual environment..."
. "$VENV_DIR/bin/activate"

echo "Checking for dependency updates..."
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

deactivate

echo "Update completed successfully!"
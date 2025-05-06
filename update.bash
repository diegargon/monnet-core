#!/bin/bash

APP_DIR="/opt/monnet-core/monnet_gateway"
VENV_DIR="$APP_DIR/venv"

echo "Updating Monnet Gateway..."

if ! command -v git &> /dev/null; then
    echo "Error: git no está instalado."
    exit 1
fi

cd "$APP_DIR" || exit
echo "Fetching latest changes from Git..."
git pull origin main || { echo "Error: No se pudo actualizar el repositorio."; exit 1; }

if [ ! -d "$VENV_DIR" ]; then
    echo "Error: El entorno virtual no existe. Ejecute install.bash primero."
    exit 1
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Checking for dependency updates..."
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

deactivate

echo "Update completed successfully!"
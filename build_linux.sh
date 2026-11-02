#!/bin/bash
set -e

echo "=================================================="
echo "📦 Building AeroInfluencer for Linux (AppImage/Binary)..."
echo "=================================================="

VENV_PYTHON="/home/sapista/aero_influencer/venv/bin/python3"
VENV_PYINSTALLER="/home/sapista/aero_influencer/venv/bin/pyinstaller"

# PyInstaller single binary bundle
$VENV_PYINSTALLER --noconfirm --onedir --windowed \
    --name "AeroInfluencer" \
    --add-data "aero_engine:aero_engine" \
    --add-data "assets:assets" \
    --hidden-import "uvicorn" \
    --hidden-import "fastapi" \
    --hidden-import "webview" \
    --hidden-import "PIL" \
    --hidden-import "edge_tts" \
    --hidden-import "faster_whisper" \
    desktop_app.py

echo "✅ Linux build completed: dist/AeroInfluencer/"

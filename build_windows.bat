@echo off
echo ==================================================
echo 📦 Building AeroInfluencer for Windows (.EXE)...
echo ==================================================

python -m pip install -r requirements.txt pywebview pyinstaller

pyinstaller --noconfirm --onedir --windowed ^
    --name "AeroInfluencer" ^
    --add-data "aero_engine;aero_engine" ^
    --add-data "assets;assets" ^
    --hidden-import "uvicorn" ^
    --hidden-import "fastapi" ^
    --hidden-import "webview" ^
    --hidden-import "PIL" ^
    --hidden-import "edge_tts" ^
    --hidden-import "faster_whisper" ^
    desktop_app.py

echo.
echo ✅ Windows build completed: dist\AeroInfluencer\AeroInfluencer.exe
pause

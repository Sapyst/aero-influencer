#!/bin/bash
# AeroInfluencer - Mobile Standalone Engine Setup (100% On-Device Execution)
# Runs the full video rendering engine locally on Android using native ARM64 CPU & FFmpeg
set -e

echo "=========================================================="
echo "🚀 AeroInfluencer Studio - Instalação Nativa no Celular"
echo "=========================================================="
echo "Instalando interpretador Python 3, FFmpeg e compilador..."

pkg update -y
pkg install -y python ffmpeg git

echo "📦 Instalando pacotes do motor de IA e vídeo..."
pip install --upgrade pip
pip install fastapi uvicorn pillow requests edge-tts google-genai duckduckgo-search pydantic python-multipart

if [ ! -d "$HOME/aero-influencer" ]; then
    echo "📥 Baixando AeroInfluencer..."
    git clone https://github.com/Sapyst/aero-influencer.git "$HOME/aero-influencer"
else
    echo "🔄 Atualizando AeroInfluencer..."
    cd "$HOME/aero-influencer" && git pull
fi

cd "$HOME/aero-influencer"

# Criar atalho 'aero' executável
mkdir -p "$PREFIX/bin"
cat << 'EOF' > "$PREFIX/bin/aero"
#!/bin/bash
cd "$HOME/aero-influencer"
echo "🎬 Iniciando AeroInfluencer Studio no celular..."
python3 run_app.py &
SERVER_PID=$!
sleep 2

# Abre no navegador padrão do Android
if command -v termux-open-url &> /dev/null; then
    termux-open-url http://127.0.0.1:8000
elif command -v xdg-open &> /dev/null; then
    xdg-open http://127.0.0.1:8000
else
    echo "Acesse no navegador: http://127.0.0.1:8000"
fi

wait $SERVER_PID
EOF
chmod +x "$PREFIX/bin/aero"

echo ""
echo "=========================================================="
echo "✅ Pronto! O AeroInfluencer agora roda 100% no seu celular."
echo "Para abrir o estúdio a qualquer momento, basta digitar:"
echo "👉 aero"
echo "=========================================================="
echo ""
aero

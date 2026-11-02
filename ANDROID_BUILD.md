# Guia Oficial Android - Execução 100% Local no Celular 📱

O **AeroInfluencer** foi projetado para rodar **100% de forma autônoma e local no próprio aparelho celular Android**, sem depender de nenhum PC, servidor externo ou nuvem proprietária.

---

### Opção 1: Inicializador Nativo 1-Clique (100% On-Device Standalone) 🚀

Esta é a maneira mais rápida e eficiente de rodar o motor Python completo e o FFmpeg nativo aproveitando todos os núcleos do processador ARM64 do seu celular:

1. **Baixe o Termux** no seu celular:
   - [Termux no F-Droid](https://f-droid.org/packages/com.termux/) ou [GitHub Oficial do Termux](https://github.com/termux/termux-app/releases) *(evite a versão antiga da Play Store)*.

2. **Abra o Termux e cole este comando único:**
   ```bash
   curl -sL https://raw.githubusercontent.com/Sapyst/aero-influencer/main/android_setup.sh | bash
   ```

3. **O que acontece automaticamente:**
   - O instalador configura o interpretador Python 3 ARM64, FFmpeg nativo e bibliotecas de vídeo.
   - Baixa o AeroInfluencer e cria o comando de atalho `aero`.
   - Inicia o motor em `127.0.0.1:8000` e abre a interface do estúdio direto no seu navegador mobile em tela cheia.
   - **Para abrir o estúdio quando quiser no celular, basta abrir o Termux e digitar:**
     ```bash
     aero
     ```

---

### Opção 2: APK Standalone com Motor Embutido (Chaquopy + FFmpegKit) 📦

Para transformar todo o motor em um único arquivo `.apk` auto-instalável que roda em segundo plano:

1. **Chaquopy Runtime:**
   - O plugin Gradle `com.chaquo.python:17.2.0` compila o CPython 3.11 para arquiteturas `arm64-v8a`.
   - Empacota os módulos (`fastapi`, `uvicorn`, `pillow`, `edge-tts`, `google-genai`).

2. **FFmpegKit Integrado:**
   - Adicione `dev.ffmpegkit-maintained:ffmpeg-kit-full:8.1.7` ao `build.gradle` para permitir renderização de vídeo nativa dentro do processo do APK.

3. **Ciclo de Vida do App:**
   - Ao clicar no ícone do aplicativo, o `MainActivity` inicia o interpretador Python em uma thread de background.
   - O WebView carrega a interface do estúdio e executa o pipeline localmente.

---

### 🛡️ Privacidade e Custos Zero
- Todo o processamento (roteiro, download de áudio, renderização e animação) roda no processador do seu aparelho.
- As chamadas de IA utilizam a sua própria chave gratuita do Google AI Studio configurada no app.
- Zero tráfego enviado para servidores de terceiros.

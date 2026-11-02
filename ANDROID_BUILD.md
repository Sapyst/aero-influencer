# Guia Oficial Android - Execução 100% Local no Celular 📱

O **AeroInfluencer** roda **100% de forma autônoma e interna no próprio aparelho celular Android**, sem depender de nenhum PC, servidor externo ou comando de terminal.

---

### Opção 1: APK Standalone Nativo (Recomendado - 1-Clique) 📦

Todo o motor de inteligência artificial, o interpretador Python 3, o backend FastAPI e o binário estático do FFmpeg ARM64 estão **embutidos diretamente dentro do arquivo APK** (~110-130 MB).

1. **Baixe o APK:**
   - Acesse os [Releases do GitHub](https://github.com/Sapyst/aero-influencer/releases/tag/v1.0.0-standalone) e baixe `AeroInfluencer-Android.apk`.
2. **Instale:**
   - Toque no arquivo `.apk` baixado e confirme a instalação no Android (permita instalar de fontes desconhecidas se solicitado).
3. **Abra e Use:**
   - Ao tocar no ícone do aplicativo, o **AeroInfluencer** inicia o interpretador Python e o servidor local de forma invisível em segundo plano.
   - A interface do estúdio Dark Cyber-Glass se abre em tela cheia.
   - Digite o tema que desejar ou cole uma notícia, escolha a voz e o avatar, e toque em **Iniciar Produção Autônoma**.
   - Os vídeos gerados são salvos automaticamente na pasta pública de Filmes/Downloads do celular (`/storage/emulated/0/Movies/AeroInfluencer`) e aparecem instantaneamente na sua Galeria e no Google Fotos!

---

### Como o Motor Roda Internamente no APK ⚙️

- **Runtime Python:** Embutido via Chaquopy (`com.chaquo.python:17.2.0`), compilado especificamente para processadores ARM64 (`arm64-v8a`).
- **Renderizador de Vídeo FFmpeg:** Binário estático ELF 64-bit ARM64 empacotado em `jniLibs/arm64-v8a/libffmpeg.so`, executado diretamente com aceleração nativa.
- **Vozes Neurais:** Síntese neural Edge TTS em alta definição com alinhamento acústico automatizado.
- **Armazenamento e Privacidade:** 100% offline para renderização, usando a sua própria chave gratuita do Google AI Studio para geração de roteiros. Zero dados enviados para terceiros.

---

### Opção 2: Instalação Manual via Termux (Avançado) 💻

Para desenvolvedores que desejam modificar o código-fonte diretamente no celular:

```bash
curl -sL https://raw.githubusercontent.com/Sapyst/aero-influencer/main/android_setup.sh | bash
```

Abra o Termux e digite `aero` a qualquer momento para abrir o estúdio.

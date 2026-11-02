# AeroInfluencer 🚀

Motor autônomo de criação e renderização de vídeos verticais (YouTube Shorts / TikTok / Reels) e vídeos longos investigativos em formato widescreen (16:9).

Apresentado pela mascote **Nova** — uma personagem 2D doodle estilizada em hoodie lilás pastel, óculos redondos e coques duplos, com expressões faciais puras, alinhamento labial acústico e troca inteligente de lados da tela (*pattern interrupts* e desobstrução de conteúdo).

---

## ✨ Principais Funcionalidades

### 1. Mascote Nova (Animação Orgânica & Pura)
- **Zero Ruídos Externos:** Sem estrelinhas, rabiscos ou traços fora da silhueta. Apenas a personagem pura com traço preto nítido (*ink line art*).
- **Consistência Visual Estrita:** Paleta de cores imutável (cabelo roxo claro, casaco lilás pastel `#d0b0e8`, pele branca doodle, calça chumbo `#282840`).
- **Composição em Duas Camadas:**
  - *Camada de Trás:* Sombra projetada com desfoque Gaussiano suave (`radius=5, opacity=58%`, offset direcional).
  - *Camada da Frente:* Linha preta 100% sólida e nítida.
- **Squash & Stretch Elástico ($1.07\times$):** Salto elástico na troca de emoções, ancorado na base da tela.
- **Troca Contextual de Lados:**
  - *Lado Direito:* Posição neutra e conclusões.
  - *Lado Esquerdo (Espelhado Horizontalmente):* Ativado em momentos de segredo/sussurro (`whispering`), deboche (`smug`), descrença (`facepalm`), choque mental (`mindblown`) e contraste de perspectivas.
  - *Regra de Estabilidade:* Permanência mínima de 3.5 segundos por lado (evita oscilação frenética).

### 2. Switch de Orientação de Tela
- 📱 **Vertical (9:16):** Ambiente mobile simulado (Safari iOS com Dynamic Island, relógio `9:41`, bateria e barra de endereço).
- 💻 **Horizontal (16:9):** Ambiente desktop simulado (janela macOS/Chrome com botões vermelho/amarelo/verde, abas e barra de navegação).

### 3. Switch de Formato de Conteúdo
- ⚡ **Shorts (Curto & Direto):** 30 a 50 segundos, ritmo acelerado, corte total de pausas silenciosas do TTS, retenção máxima, gancho imediato e encerramento característico: *"Want to know more curious things like this? Just follow!"*.
- 🎬 **Vídeo (Full Content Video):** Vídeo longo investigativo/documental (2 a 6+ minutos), dividido em capítulos estruturados (Gancho, Contexto Histórico, Quebra Cronológica, Falha Técnica, Danos Econômicos e Conclusão).

### 4. Política de Geração de Imagens (Settings)
- 🚫 **NEVER:** 100% de páginas reais raspadas e capturadas via Selenium headless com Smart DOM Auto-Framing (zero IA em imagens).
- ⚡ **AUTO (Recomendado):** Modo híbrido inteligente. Prioriza prints reais de notícias; gera imagens por IA apenas para preencher lacunas conceituais.
- 🎨 **ALWAYS:** 100% de cenários e ilustrações gerados por IA para consistência artística contínua.

### 5. Onboarding Inteligente & Google AI Studio
- Na primeira inicialização, guia o usuário passo a passo para criar sua chave de API gratuita no [Google AI Studio](https://aistudio.google.com/).
- Recomenda a assinatura do **Google AI Pro / Gemini Advanced** para limites mais altos de requisições, velocidade relâmpago e roteirização ultra detalhada.
- Validação em tempo real da chave diretamente pelo frontend.

---

## 🚀 Como Executar

### Pré-requisitos
- Python 3.10+
- FFmpeg instalado no sistema
- Firefox & Geckodriver (para captura de notícias headless)

### Iniciar o Estúdio
```bash
python3 run_app.py
```
Acesse no seu navegador (Desktop ou Android):
```
http://localhost:8080
```

---

## 🏗️ Arquitetura do Backend (`aero_engine/`)

- `config.py`: Gerenciamento de configurações em `~/.aeroinfluencer/config.json`.
- `ai_director.py`: Roteirizador inteligente baseado no Gemini 2.5 Flash / Pro (chamada estruturada única, zero desperdício de tokens).
- `web_hunter.py`: Busca DuckDuckGo, Selenium headless e enquadramento DOM inteligente (`h1Rect.top - headerBottom`).
- `voice_engine.py`: Síntese Edge-TTS, remoção de silêncios residuais (`trim_silence_wav`), alinhamento acústico com Faster-Whisper e legendas ASS de alta retenção.
- `animator.py`: Multi-pose PNGtuber com inversão horizontal, sombra gaussiana em camada traseira e elastic bump.
- `image_generator.py`: Integração com Google Imagen/Gemini conforme a política configurada.
- `renderer.py`: Compositor final FFmpeg multitrack com ducking automático de trilha de tensão.
- `api_server.py`: Servidor FastAPI com endpoints REST e frontend integrado.

---

## 📦 Downloads dos Executáveis Prontos

Para rodar direto na sua máquina sem precisar instalar Python ou configurar ambiente:

- 🐧 **Linux (x86_64):** Baixe a versão standalone na [Aba de Releases](https://github.com/Sapyst/aero-influencer/releases/latest) e rode:
  ```bash
  tar -xzvf AeroInfluencer-Linux-x86_64.tar.gz
  cd AeroInfluencer
  ./AeroInfluencer
  ```
- 🪟 **Windows (.exe):** Em breve via GitHub Actions na página de Releases.
- 📱 **Android (.apk):** Consulte o guia em [ANDROID_BUILD.md](ANDROID_BUILD.md).

---

## 📄 Licença (MIT License)

Este projeto está sob a licença **MIT** — livre para qualquer pessoa usar, copiar, modificar, distribuir e integrar em seus projetos, com a única exigência de manter o aviso de copyright e a menção/crédito ao autor original (**Sapyst**).


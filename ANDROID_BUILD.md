# Guia de Empacotamento Android (APK) 📱

O **AeroInfluencer** foi desenhado com frontend 100% responsivo para mobile (Touch friendly, UI em viewport vertical de smartphone, modais adaptativos).

Para transformar o AeroInfluencer em um aplicativo instalável **`.apk`** para Android, existem duas abordagens testadas:

---

### Opção 1: Capacitor / Trusted Web Activity (TWA) - Recomendado
Gera um `.apk` nativo que empacota a interface como um aplicativo de sistema, com ícone próprio na gaveta de apps, splash screen e tela cheia:

1. **Instalar Capacitor CLI:**
   ```bash
   npm install @capacitor/core @capacitor/cli @capacitor/android
   npx cap init AeroInfluencer com.sapyst.aeroinfluencer --web-dir aero_engine/ui
   npx cap add android
   ```

2. **Compilar o APK no Android Studio:**
   ```bash
   npx cap open android
   # No Android Studio: Build -> Build Bundle(s) / APK(s) -> Build APK(s)
   ```

---

### Opção 2: Chaquopy / BeeWare Briefcase (Motor Python Nativo Dentro do APK)
Para quem deseja rodar o interpretador Python do FastAPI diretamente dentro do processo do Android no aparelho do usuário:

1. Utiliza o plugin Gradle **Chaquopy** (`com.chaquo.python`) no `app/build.gradle`.
2. O Chaquopy compila o runtime do Python 3.11 para as arquiteturas `arm64-v8a` e `armeabi-v7a`.
3. Ao tocar no ícone do app, o Android inicia a thread do FastAPI em `127.0.0.1` e carrega o WebView nativo em tela cheia.

---

### Zero Custos de Servidor:
Cada usuário que instalar o APK no seu celular:
- Insere a sua **própria chave de API do Google AI Studio** no onboarding.
- Renderiza ou consome diretamente pelo seu dispositivo.
- **Você (o criador) não gasta nem 1 centavo com tráfego, CPU ou chamadas de API de terceiros!**

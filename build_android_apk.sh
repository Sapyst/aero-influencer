#!/usr/bin/env bash
set -e

echo "=== Building Standalone On-Device AeroInfluencer Android APK ==="

# 1. Clean previous build artifacts
rm -rf android package.json package-lock.json node_modules /tmp/ffmpeg_extracted

# 2. Setup Capacitor project
npm init -y
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap init "AeroInfluencer" "com.sapyst.aeroinfluencer" --web-dir aero_engine/ui
echo "n" | npx cap add android

# 3. Configure variables.gradle
cat << 'EOF' > android/variables.gradle
ext {
    minSdkVersion = 24
    compileSdkVersion = 35
    targetSdkVersion = 35
    androidxActivityVersion = '1.11.0'
    androidxAppCompatVersion = '1.7.1'
    androidxCoordinatorLayoutVersion = '1.3.0'
    androidxCoreVersion = '1.17.0'
    androidxFragmentVersion = '1.8.9'
    coreSplashScreenVersion = '1.2.0'
    androidxWebkitVersion = '1.14.0'
    junitVersion = '4.13.2'
    androidxJunitVersion = '1.3.0'
    androidxEspressoCoreVersion = '3.7.0'
    cordovaAndroidVersion = '14.0.1'
}
EOF

# 4. Top-level build.gradle with Chaquopy
cat << 'EOF' > android/build.gradle
buildscript {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
        maven { url "https://chaquo.com/maven" }
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.7.2'
        classpath 'com.chaquo.python:gradle:17.2.0'
    }
}

apply from: "variables.gradle"

allprojects {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
        maven { url "https://chaquo.com/maven" }
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
EOF

# 5. app/build.gradle with Chaquopy and ARM64
cat << 'EOF' > android/app/build.gradle
apply plugin: 'com.android.application'
apply plugin: 'com.chaquo.python'

android {
    namespace = "com.sapyst.aeroinfluencer"
    compileSdk = rootProject.ext.compileSdkVersion
    defaultConfig {
        applicationId "com.sapyst.aeroinfluencer"
        minSdkVersion rootProject.ext.minSdkVersion
        targetSdkVersion rootProject.ext.targetSdkVersion
        versionCode 1
        versionName "1.0.0"
        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
        ndk {
            abiFilters "arm64-v8a"
        }
        python {
            version "3.10"
            pip {
                install "fastapi<0.100.0"
                install "pydantic<2.0.0"
                install "uvicorn"
                install "pillow"
                install "requests"
                install "edge-tts"
                install "python-multipart"
            }
        }
        aaptOptions {
            ignoreAssetsPattern = '!.svn:!.git:!.ds_store:!*.scc:.*:!CVS:!thumbs.db:!picasa.ini:!*~'
        }
    }
    packagingOptions {
        jniLibs {
            useLegacyPackaging = true
        }
    }
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}

repositories {
    flatDir{
        dirs '../capacitor-cordova-android-plugins/src/main/libs', 'libs'
    }
}

dependencies {
    implementation fileTree(include: ['*.jar'], dir: 'libs')
    implementation "androidx.appcompat:appcompat:$androidxAppCompatVersion"
    implementation "androidx.coordinatorlayout:coordinatorlayout:$androidxCoordinatorLayoutVersion"
    implementation "androidx.core:core-splashscreen:$coreSplashScreenVersion"
    implementation project(':capacitor-android')
    testImplementation "junit:junit:$junitVersion"
    androidTestImplementation "androidx.test.ext:junit:$androidxJunitVersion"
    androidTestImplementation "androidx.test.espresso:espresso-core:$androidxEspressoCoreVersion"
    implementation project(':capacitor-cordova-android-plugins')
}

apply from: 'capacitor.build.gradle'
EOF

# 6. Bundle native ARM64 FFmpeg
mkdir -p android/app/src/main/jniLibs/arm64-v8a
if [ ! -f /tmp/ffmpeg-android-arm64.zip ]; then
    curl -sL https://github.com/Tyrrrz/FFmpegBin/releases/download/9.0.2/ffmpeg-android-arm64.zip -o /tmp/ffmpeg-android-arm64.zip
fi
mkdir -p /tmp/ffmpeg_extracted
unzip -qo /tmp/ffmpeg-android-arm64.zip -d /tmp/ffmpeg_extracted
cp /tmp/ffmpeg_extracted/ffmpeg android/app/src/main/jniLibs/arm64-v8a/libffmpeg.so
chmod 755 android/app/src/main/jniLibs/arm64-v8a/libffmpeg.so

# 7. Bundle Python engine code and assets
mkdir -p android/app/src/main/python/aero_engine
mkdir -p android/app/src/main/python/assets
cp -r aero_engine/* android/app/src/main/python/aero_engine/
cp -r assets/* android/app/src/main/python/assets/

# 8. Setup MainActivity.java
cat << 'EOF' > android/app/src/main/java/com/sapyst/aeroinfluencer/MainActivity.java
package com.sapyst.aeroinfluencer;

import android.os.Bundle;
import android.util.Log;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private static final String TAG = "AeroInfluencer";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try {
            if (!Python.isStarted()) {
                Python.start(new AndroidPlatform(this));
            }

            String nativeLibDir = getApplicationInfo().nativeLibraryDir;
            String ffmpegPath = nativeLibDir + "/libffmpeg.so";
            String filesDir = getFilesDir().getAbsolutePath();

            new Thread(() -> {
                try {
                    Python py = Python.getInstance();
                    py.getModule("os").get("environ").callAttr("setdefault", "FFMPEG_PATH", ffmpegPath);
                    py.getModule("os").get("environ").callAttr("setdefault", "AERO_DATA_DIR", filesDir);
                    py.getModule("os").get("environ").callAttr("setdefault", "AERO_MOBILE", "1");
                    
                    Log.i(TAG, "Starting on-device AeroInfluencer engine on 127.0.0.1:8000...");
                    py.getModule("aero_engine.api_server").callAttr("start_mobile_server", 8000);
                } catch (Exception e) {
                    Log.e(TAG, "Failed to run mobile server", e);
                }
            }).start();
        } catch (Exception e) {
            Log.e(TAG, "Error initializing Chaquopy", e);
        }
    }
}
EOF

# 9. Configure AndroidManifest.xml (Permissions & cleartextTraffic)
python3 -c '
from pathlib import Path
manifest_file = Path("android/app/src/main/AndroidManifest.xml")
text = manifest_file.read_text(encoding="utf-8")

permissions = """
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <uses-permission android:name="android.permission.READ_MEDIA_AUDIO" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
"""

if "<uses-permission" not in text:
    text = text.replace("<application", permissions + "\n    <application")

if "android:usesCleartextTraffic" not in text:
    text = text.replace("<application", "<application\n        android:usesCleartextTraffic=\"true\"\n        android:extractNativeLibs=\"true\"")

manifest_file.write_text(text, encoding="utf-8")
print("AndroidManifest.xml updated with permissions and cleartextTraffic!")
'

# 10. Compile Standalone APK with Gradle
cd android
chmod +x gradlew
./gradlew assembleDebug --no-daemon
cp app/build/outputs/apk/debug/app-debug.apk ../AeroInfluencer-Android.apk

echo "=== APK Successfully Generated: AeroInfluencer-Android.apk ==="
ls -lh ../AeroInfluencer-Android.apk

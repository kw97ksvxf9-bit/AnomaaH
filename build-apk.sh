#!/bin/bash

# Build Android APK using Docker
# This avoids needing Android Studio or SDK installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building Docker image for Android APK build..."
docker build -t android-apk-builder -f "$SCRIPT_DIR/build-apk.dockerfile" "$SCRIPT_DIR"

echo "Running Gradle assembleDebug inside container..."
docker run --rm \
  -v "$SCRIPT_DIR/rider-app":/workspace \
  -w /workspace \
  android-apk-builder \
  "chmod +x ./gradlew && ./gradlew assembleDebug --no-daemon"

echo "APK build completed!"
echo "Output: $SCRIPT_DIR/rider-app/build/outputs/apk/debug/"

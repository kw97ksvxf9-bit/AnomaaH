#!/bin/bash

# Build Android APK using Docker
# This avoids needing Android Studio or SDK installation

docker run --rm \
  -v /home/packnet777/R1/rider-app:/workspace \
  -w /workspace \
  mcr.microsoft.com/dotnet/framework/sdk:4.8 \
  bash -c "apt-get update && apt-get install -y gradle openjdk-17-jdk && gradle assembleDebug"

echo "APK build completed!"
echo "Output: /home/packnet777/R1/rider-app/build/outputs/apk/debug/"

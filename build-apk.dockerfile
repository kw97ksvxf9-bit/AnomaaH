FROM ubuntu:22.04

# Install Java and build tools
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Install Android SDK
RUN mkdir -p /opt/android-sdk && \
    cd /opt/android-sdk && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip && \
    unzip -q commandlinetools-linux-10406996_latest.zip && \
    rm commandlinetools-linux-10406996_latest.zip

ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Install SDK tools
RUN mkdir -p $ANDROID_SDK_ROOT/cmdline-tools/latest && \
    cd $ANDROID_SDK_ROOT && \
    echo "yes" | cmdline-tools/bin/sdkmanager --sdk_root=$ANDROID_SDK_ROOT "platform-tools" "build-tools;34.0.0" "platforms;android-34" 2>&1 | grep -v "Warning"

WORKDIR /workspace

ENTRYPOINT ["gradle"]
CMD ["assembleDebug"]

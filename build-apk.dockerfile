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

# Install Android SDK (with retries for network reliability)
RUN mkdir -p /opt/android-sdk/cmdline-tools && \
    cd /tmp && \
    for i in 1 2 3; do \
        wget --tries=3 --timeout=60 --continue \
            https://dl.google.com/android/repository/commandlinetools-linux-10406996_latest.zip \
            && break || sleep 10; \
    done && \
    unzip -q commandlinetools-linux-10406996_latest.zip && \
    mv cmdline-tools /opt/android-sdk/cmdline-tools/latest && \
    rm commandlinetools-linux-10406996_latest.zip

ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools

# Accept licenses and install SDK tools
RUN yes | sdkmanager --licenses > /dev/null 2>&1 || true && \
    sdkmanager --sdk_root=$ANDROID_SDK_ROOT \
        "platform-tools" \
        "build-tools;34.0.0" \
        "platforms;android-34" \
    2>&1 | grep -v "Warning"

WORKDIR /workspace

# The container expects rider-app to be mounted at /workspace
# Use gradlew from the project
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["chmod +x ./gradlew && ./gradlew assembleDebug --no-daemon"]

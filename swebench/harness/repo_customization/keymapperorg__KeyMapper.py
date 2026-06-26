REPO = "keymapperorg/KeyMapper"

# The evdev module requires the Android NDK to generate event name headers
# from input.h and to build native Rust code via mozilla/rust-android-gradle.
# The base env image only installs platform-tools, platforms, and build-tools.
# Rust toolchain is needed for the mozilla/rust-android-gradle cargo builds.
COMMANDS = [
    "apt-get update && apt-get install -y gcc python3 python-is-python3",
    'sdkmanager --install "ndk;27.3.13750724"',
    "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
    ". $HOME/.cargo/env && rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android",
]

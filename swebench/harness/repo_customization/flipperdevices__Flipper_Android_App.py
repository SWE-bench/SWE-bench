REPO = "flipperdevices/Flipper-Android-App"

# This repo uses git submodules for protobuf definitions, metrics protos,
# and NFC native tools.  Without initializing them, the protobuf Gradle
# plugin finds NO-SOURCE and the build fails with unresolved references
# (e.g. 'protobuf', 'Main', 'encode' in ProtobufKtx.kt).
COMMANDS = [
    "git submodule update --init --recursive",
]

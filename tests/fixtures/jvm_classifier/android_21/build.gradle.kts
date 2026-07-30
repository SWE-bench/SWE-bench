plugins {
    id("com.android.application")
}
android {
    compileSdk = 35
    defaultConfig { targetSdk = 35 }
}
kotlin { jvmToolchain(21) }

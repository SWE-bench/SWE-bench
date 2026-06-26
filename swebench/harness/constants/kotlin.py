from swebench.harness.constants.jvm_base import (
    SPECS_ANDROID_17,
    SPECS_ANDROID_21,
    SPECS_ANDROID_17_X86,
    SPECS_JVM_LIBRARY_17,
    SPECS_JVM_LIBRARY_17_KMP_BROWSER,
    SPECS_JVM_LIBRARY_17_LOW_MEM,
)
from swebench.harness.repo_customization.InsertKoinIO__koin import (
    SPECS as _SPECS_KOIN,
)
from swebench.harness.repo_customization.JetBrains__Exposed import (
    SPECS as _SPECS_EXPOSED,
)
from swebench.harness.repo_customization.Kotlin__kotlinx_serialization import (
    SPECS as _SPECS_SERIALIZATION,
)
from swebench.harness.repo_customization.ReVanced__revanced_manager import (
    SPECS as _SPECS_REVANCED,
)
from swebench.harness.repo_customization.arrow_kt__arrow import (
    SPECS as _SPECS_ARROW,
)
from swebench.harness.repo_customization.nextcloud__talk_android import (
    SPECS as _SPECS_TALK,
)
from swebench.harness.repo_customization.pinterest__ktlint import (
    SPECS as _SPECS_KTLINT,
)
from swebench.harness.repo_customization.slackhq__circuit import (
    SPECS as _SPECS_CIRCUIT,
)
from swebench.harness.repo_customization.wireapp__wire_android import (
    SPECS as _SPECS_WIRE,
)

MAP_REPO_VERSION_TO_SPECS_KOTLIN = {
    **{
        repo: SPECS_ANDROID_21
        for repo in [
            "DroidKaigi/conference-app-2024",
            "MMRLApp/MMRL",
            "NordicSemiconductor/Android-DFU-Library",
            "Stypox/dicio-android",
            "T8RIN/ImageToolbox",
            "jarnedemeulemeester/findroid",
            "nextcloud/android",
            "thunderbird/thunderbird-android",
            "accrescent/accrescent",
            "stripe/stripe-android",
        ]
    },
    **{
        repo: SPECS_ANDROID_17
        for repo in [
            "Aliucord/Aliucord",
            "AllanWang/Frost-for-Facebook",
            "AppIntro/AppIntro",
            "Automattic/pocket-casts-android",
            "GetStream/whatsApp-clone-compose",
            "GrapheneOS/Camera",
            "HabitRPG/habitica-android",
            "IacobIonut01/Gallery",
            "LemmyNet/jerboa",
            "LibChecker/LibChecker",
            "Mahmud0808/ColorBlendr",
            "MohamedRejeb/Compose-Rich-Editor",
            "NordicSemiconductor/Android-nRF-Toolbox",
            "Pool-Of-Tears/GreenStash",
            "Pool-Of-Tears/Myne",
            "RikkaApps/Shizuku",
            "Tapadoo/Alerter",
            "TrianguloY/URLCheck",
            "android/nowinandroid",
            "android/socialite",
            "android/sunflower",
            "android/uamp",
            "aniyomiorg/aniyomi",
            "avluis/Hentoid",
            "beemdevelopment/Aegis",
            "d4rken-org/capod",
            "element-hq/element-android",
            "flipperdevices/Flipper-Android-App",
            "getodk/collect",
            "gradle/gradle",
            "iSoron/uhabits",
            "jaredsburrows/android-gradle-java-app-template",
            "keymapperorg/KeyMapper",
            "kylecorry31/Trail-Sense",
            "leonlatsch/Photok",
            "mihonapp/mihon",
            "nextcloud/notes-android",
            "owncloud/android",
            "oxygen-updater/oxygen-updater",
            "patzly/grocy-android",
            "recloudstream/cloudstream",
            "spacecowboy/Feeder",
            "tasks/tasks",
            "wikimedia/apps-android-wikipedia",
            "you-apps/ClockYou",
            "you-apps/RecordYou",
        ]
    },
    # Repos that use Kotlin/Native (e.g. Kotlin Multiplatform with iOS targets)
    # with Kotlin versions < 1.8 that lack linux-aarch64 prebuilt binaries.
    # These must build under x86_64 (QEMU emulation on ARM hosts).
    **{
        repo: SPECS_ANDROID_17_X86
        for repo in [
            "DroidKaigi/conference-app-2021",
            "DroidKaigi/conference-app-2022",
            "DroidKaigi/conference-app-2023",
            "Shabinder/SpotiFlyer",
            "kasem-sm/SlimeKT",
        ]
    },
    # Pure Kotlin/JVM/multiplatform libraries — no Android app module,
    # install compiles sources without running tests.
    **{
        repo: SPECS_JVM_LIBRARY_17_LOW_MEM
        for repo in [
            "Kotlin/dokka",
            "Kotlin/kotlinx.coroutines",
        ]
    },
    **{"InsertKoinIO/koin": _SPECS_KOIN},
    **{"pinterest/ktlint": _SPECS_KTLINT},
    **{"Kotlin/kotlinx.serialization": _SPECS_SERIALIZATION},
    **{"JetBrains/Exposed": _SPECS_EXPOSED},
    **{"slackhq/circuit": _SPECS_CIRCUIT},
    **{"ReVanced/revanced-manager": _SPECS_REVANCED},
    **{
        repo: SPECS_JVM_LIBRARY_17_KMP_BROWSER
        for repo in [
            "kotest/kotest",
            "ktorio/ktor",
            "sqldelight/sqldelight",
        ]
    },
    **{"arrow-kt/arrow": _SPECS_ARROW},
    **{"nextcloud/talk-android": _SPECS_TALK},
    **{"wireapp/wire-android": _SPECS_WIRE},
    **{
        repo: SPECS_JVM_LIBRARY_17
        for repo in [
            "JetBrains/compose-multiplatform",
            "ReactiveX/RxKotlin",
            "detekt/detekt",
            "google/ksp",
        ]
    },
}

MAP_REPO_TO_INSTALL_KOTLIN = {
    repo: f"git clone https://github.com/{repo}.git"
    for repo in MAP_REPO_VERSION_TO_SPECS_KOTLIN.keys()
}

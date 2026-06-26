from .common import google_services_commands

REPO = "wikimedia/apps-android-wikipedia"

COMMANDS = google_services_commands([
    ("app", ["org.wikipedia", "org.wikipedia.alpha", "org.wikipedia.beta", "org.wikipedia.dev"]),
])

REPO = "owncloud/android"

# The build.gradle calls getGitOriginRemote() which runs `git remote -v` and
# expects an "origin" remote to exist.  The harness removes origin after clone
# to hide newer commits, so we re-add a placeholder to prevent the NPE at
# configuration time ("Cannot invoke method replace() on null object").
COMMANDS = [
    "git remote add origin https://github.com/owncloud/android.git",
]

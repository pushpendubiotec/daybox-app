[app]

# (str) Title of your application
title = Plendar

# (str) Package name
package.name = plendar

# (str) Package domain (needed for android packaging)
package.domain = com.plendar.app

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (leave empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .venv, .git, .github

# (string) Application versioning
version = 0.1

# (list) Application requirements
# NOTE: do not pin an exact python3 version here (e.g. python3==3.11.0) -
# it breaks python-for-android's recipe resolution. Just "python3" is safest.
requirements = python3,kivy

# (str) Presplash image filename
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon filename
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

#
# Android specific configurations
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, touch this only if you know what you are doing
android.api = 33

# (int) Minimum API required to run the app
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25c

# (str) Android NDK directory (if empty, it will be automatically downloaded)
# We pre-download this ourselves in the CI workflow instead of leaving it
# empty, because buildozer's built-in downloader requests
# "android-ndk-r25b-linux-x86_64.zip", which 404s - Google renamed the file
# to "android-ndk-r25c-linux.zip" (no "-x86_64") when NDK 23+ shipped.
# This path must match the "Download Android NDK" step in build.yml.
android.ndk_path = /home/runner/ndk-cache/android-ndk-r25c

# (bool) Automatically accept Android SDK license agreements.
# Required for unattended CI builds.
android.accept_sdk_license = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (str) The format used to package the app for release (aab or apk)
android.release_artifact = apk

# (str) The format used to package the app for debug (apk)
android.debug_artifact = apk


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
# Keep this at 0 - GitHub Actions runners execute as a non-root "runner" user
# by default anyway; this just silences a harmless warning if that ever changes.
warn_on_root = 0

# NOTE: do not try to override this from the command line with
# "buildozer --warn_on_version_defaults 0 android debug" - that is not valid
# buildozer CLI syntax and buildozer will misread "0" as the build target.
# This setting only works as a config line, like this one:
warn_on_version_defaults = 1

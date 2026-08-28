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
requirements = python3==3.11.5,kivy==2.3.1

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
android.ndk_path = /home/runner/ndk-cache/android-ndk-r25c

# (bool) Automatically accept Android SDK license agreements.
android.accept_sdk_license = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (str) The format used to package the app for release (aab or apk)
android.release_artifact = apk

# (str) The format used to package the app for debug (apk)
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use
p4a.branch = master

# (str) python-for-android specific commit/tag to use
p4a.commit = v2024.01.21


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 0

warn_on_version_defaults = 1

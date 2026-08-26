[app]

# (str) Title of your application
title = Daybox

# (str) Package name
package.name = daybox

# (str) Package domain (needed for android packaging)
package.domain = com.daybox.app

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (leave empty to include all files)
source.include_exts = py,png,jpg,kv,atlas,json

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .venv, .git, .github

# (string) Application versioning
version = 0.1

# (list) Application requirements
# Add any extra Python libraries here separated by commas (e.g., requests, urllib3)
requirements = python3==3.11.0,kivy

# (str) Custom source folders for requirements
# Sets custom source for any requirement with recipes or source code

# (list) Garden requirements
#garden_requirements =

# (str) Presplash image filename
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon filename
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = my service:./service.py

#
# Android specific configurations
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain v26+)
#android.presplash_color = #FFFFFF

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, touch this only if you know what you are doing
android.api = 33

# (int) Minimum API required to run the app
android.minapi = 21

# (str) Android NDK version to use (Using 25b prevents 404 download errors)
android.ndk = 25c

# (int) Android NDK API version
android.ndk_api = 21

# (bool) Automatically accept Android SDK licenses
android.accept_sdk_license = True

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable Android logcat output filtering
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libdir and symlinking
#android.copy_libs = 1

# (str) The format used to package the app for release (aab or apk)
android.release_artifact = apk

# (str) The format used to package the app for debug (apk)
android.debug_artifact = apk


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_version_defaults = 1

# (str) Path to build artifact storage
# build_dir = ./.buildozer

# (str) Path to build output (where the APK will be placed)
# bin_dir = ./bin

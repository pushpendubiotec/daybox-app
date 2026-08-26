[app]
title = Daybox
package.name = daybox
package.domain = com.daybox.app
source.dir = .
source.include_exts = py,png,jpg,kv,db
version = 1.0.0

# Requirements matching Python dependencies
requirements = python3,kivy,sqlite3

# Display & Orientation
orientation = portrait
fullscreen = 0

# Android specific configurations
android.minapi = 21
# android.sdk = 33
android.ndk = 25.2.9519653
android.accept_sdk_license = True
android.permissions = INTERNET,VIBRATE,POST_NOTIFICATIONS

# Icon configuration
# icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

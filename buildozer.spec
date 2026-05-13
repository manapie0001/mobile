[app]

# (str) Title of your application
title = Navigator

# (str) Package name
package.name = navigator

# (str) Package domain (reverse domain notation)
package.domain = org.example

version = 0.1
python_version = 3.11
python_requires = 3.11

# (str) Source code directory
source.dir = .

# (list) Source files to include (Python, images, etc.)
source.include_exts = py,png,jpg,kv,atlas

# (list) Requirements (Python packages)
requirements = python3==3.11s,kivy==2.2.1,plyer==2.1,requests==2.31.0,kivy-garden.mapview==23.09.0

# (str) Entry point for the app (main file)
source.main = main.py

# (list) Permissions for Android
android.permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, ACCESS_NETWORK_STATE

android.accept_sdk_license = True
android.build_tools = 33.0.2

# (int) Target Android API level
android.api = 33

# (int) Minimum Android API level
android.minapi = 21

# (int) Android SDK version
android.sdk = 33

# (str) Android NDK version (optional)
 android.ndk = 25c

# (bool) Use AndroidX instead of Android support library
android.use_androidx = True

# (list) Gradle dependencies for Android (e.g., Google Play Services)
android.gradle_dependencies = 'com.google.android.gms:play-services-location:21.0.1'

# (bool) Enable or disable debugging logs
log_level = 2

# (str) Presplash image (optional)
# presplash.filename = %(source.dir)s/presplash.png

# (str) Icon for the app (optional)
# icon.filename = %(source.dir)s/icon.png

# (list) Non-Python files to include (e.g., images, kv)
source.include_patterns = marker.png, wing.png

# (bool) Allow the app to be built in debug mode
android.debug = 1

# (list) Android services (e.g., for background GPS)
# android.services = MyService

# (str) Android manifest metadata (optional)
# android.manifest_metadata =

# (bool) Enable or disable Kivy's garden (already handled via requirements)
# garden_requirements =

[buildozer]

# (str) Path to the Android SDK (automatic detection if empty)
android.sdk_path =

# (str) Path to the Android NDK (automatic detection if empty)
android.ndk_path =

# (str) Path to the Ant binary (Apache Ant)
android.ant_path =

# (bool) Use the system's Java (OpenJDK) instead of downloaded one
android.use_openjdk = True

# (str) Android logcat filters (e.g., *:S MyApp:D)
android.logcat_filters = *:S python:D

# Конец файла

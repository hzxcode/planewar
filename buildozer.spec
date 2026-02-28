[app]
title = PlaneWar
package.name = planewar
package.domain = org.planewar

source.dir = .
source.include_exts = py,txt,ttf,otf
source.exclude_dirs = build,dist,.venv,.vscode,__pycache__,images,.git,.github,apk-output,build-log-output

version = 1.0.0

requirements = python3==3.10.12,hostpython3==3.10.12,pygame

orientation = portrait
fullscreen = 1

android.presplash_color = #000008

android.permissions = INTERNET

android.api = 34
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.skip_update = False

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1

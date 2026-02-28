[app]
title = PlaneWar
package.name = planewar
package.domain = org.planewar

source.dir = .
source.include_exts = py,txt
source.exclude_dirs = build,dist,.venv,.vscode,__pycache__,fonts,images,.git,.github

version = 1.0.0

requirements = python3==3.11.14,hostpython3==3.11.14,pygame==2.5.2,sdl2_ttf==2.20.2

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

p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

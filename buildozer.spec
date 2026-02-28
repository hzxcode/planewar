[app]
title = 飞机大战
package.name = planewar
package.domain = org.planewar

source.dir = .
source.include_exts = py,txt
source.exclude_dirs = build,dist,.venv,.vscode,__pycache__,fonts,images

version = 1.0.0

requirements = python3,pygame

orientation = portrait
fullscreen = 1

android.presplash_color = #000008
android.icon = %(source.dir)s/icon.png

android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 1

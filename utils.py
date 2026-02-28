"""
工具函数：字体加载等
"""
import os
import sys
import pygame

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 支持中文的字体候选（按优先级）
_FONT_CANDIDATES = [
    "/system/fonts/NotoSansSC-Regular.otf",
    "/system/fonts/NotoSansCJKsc-Regular.otf",
    "/system/fonts/DroidSansFallback.ttf",
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyh.ttc"),
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyhbd.ttf"),
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simhei.ttf"),
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "simsun.ttc"),
    os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "msyh.ttf"),
    os.path.join(_BASE_DIR, "fonts", "msyh.ttc"),
    os.path.join(_BASE_DIR, "fonts", "simhei.ttf"),
    os.path.join(_BASE_DIR, "fonts", "NotoSansSC-Regular.ttf"),
    os.path.join(_BASE_DIR, "fonts", "NotoSansSC-Regular.otf"),
]

_cached_fonts: dict[tuple[str, int], pygame.font.Font] = {}


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """获取支持中文的字体，失败时回退到默认字体"""
    key = ("bold" if bold else "normal", size)
    if key in _cached_fonts:
        return _cached_fonts[key]
    for path in _FONT_CANDIDATES:
        if os.path.isfile(path):
            try:
                font = pygame.font.Font(path, size)
                _cached_fonts[key] = font
                return font
            except (OSError, pygame.error):
                continue
    try:
        font = pygame.font.SysFont(["microsoftyahei", "simhei", "simsun", "kaiti"], size, bold=bold)
        _cached_fonts[key] = font
        return font
    except (OSError, pygame.error):
        pass
    font = pygame.font.Font(None, size)
    _cached_fonts[key] = font
    return font

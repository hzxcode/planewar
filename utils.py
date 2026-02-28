"""
工具函数：字体加载等
"""
import os
import sys
import pygame

IS_ANDROID = "ANDROID_ROOT" in os.environ or "ANDROID_STORAGE" in os.environ

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _build_font_candidates() -> list[str]:
    paths: list[str] = []

    # Bundled font (highest priority — always works if packaged)
    paths.append(os.path.join(_BASE_DIR, "fonts", "simhei.ttf"))

    if IS_ANDROID:
        # p4a extracts assets next to main.py; also check common Android paths
        for d in (".", "fonts"):
            paths.append(os.path.join(_BASE_DIR, d, "simhei.ttf"))
        paths += [
            "/system/fonts/NotoSansSC-Regular.otf",
            "/system/fonts/NotoSansCJKsc-Regular.otf",
            "/system/fonts/NotoSansCJK-Regular.ttc",
            "/system/fonts/DroidSansFallback.ttf",
        ]
    else:
        windir = os.environ.get("WINDIR", "C:\\Windows")
        for name in ("msyh.ttc", "msyhbd.ttf", "simhei.ttf",
                      "simsun.ttc", "msyh.ttf"):
            paths.append(os.path.join(windir, "Fonts", name))
        for name in ("msyh.ttc", "simhei.ttf",
                      "NotoSansSC-Regular.ttf", "NotoSansSC-Regular.otf"):
            paths.append(os.path.join(_BASE_DIR, "fonts", name))

    return paths


_FONT_CANDIDATES = _build_font_candidates()
_cached_fonts: dict[tuple[str, int], pygame.font.Font] = {}
_resolved_font_path: str | None = None


def _find_font_path() -> str | None:
    global _resolved_font_path
    if _resolved_font_path is not None:
        return _resolved_font_path
    for path in _FONT_CANDIDATES:
        if os.path.isfile(path):
            _resolved_font_path = path
            return path
    return None


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """获取支持中文的字体，失败时回退到默认字体"""
    key = ("bold" if bold else "normal", size)
    if key in _cached_fonts:
        return _cached_fonts[key]

    font_path = _find_font_path()
    if font_path:
        try:
            font = pygame.font.Font(font_path, size)
            _cached_fonts[key] = font
            return font
        except (OSError, pygame.error):
            pass

    if not IS_ANDROID:
        try:
            font = pygame.font.SysFont(
                ["microsoftyahei", "simhei", "simsun", "kaiti"],
                size, bold=bold,
            )
            _cached_fonts[key] = font
            return font
        except (OSError, pygame.error):
            pass

    font = pygame.font.Font(None, size)
    _cached_fonts[key] = font
    return font

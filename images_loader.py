"""
图片加载：从 images 文件夹加载精灵图，支持多种命名格式
将图片放入项目根目录的 images 文件夹，支持文件名：
- player1.png / player2.png / player.png - 玩家飞机
- enemy_small.png / enemy_medium.png / enemy_large.png - 敌机
- boss.png - Boss
- bullet.png - 子弹
"""
import os
import pygame

_images_cache: dict[str, pygame.Surface] = {}
_images_dir = ""


def _get_images_dir() -> str:
    global _images_dir
    if not _images_dir:
        try:
            import settings
            _images_dir = getattr(settings, "IMAGES_DIR", "")
        except ImportError:
            pass
        if not _images_dir:
            _images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    return _images_dir


def _load(path: str) -> pygame.Surface | None:
    if path in _images_cache:
        return _images_cache[path]
    if not os.path.isfile(path):
        return None
    try:
        surf = pygame.image.load(path).convert_alpha()
        _images_cache[path] = surf
        return surf
    except (pygame.error, OSError):
        return None


def _try_load(names: list[str]) -> pygame.Surface | None:
    base = _get_images_dir()
    for name in names:
        for ext in (".png", ".jpg", ".jpeg", ".bmp"):
            path = os.path.join(base, name + ext)
            if os.path.isfile(path):
                return _load(path)
    return None


def load_player(player_id: int = 1) -> pygame.Surface | None:
    return _try_load([f"player{player_id}", f"player_{player_id}", "player", "hero", "plane"])


def load_enemy(etype: str) -> pygame.Surface | None:
    return _try_load([f"enemy_{etype}", f"enemy{etype}", "enemy", "enemy1"])


def load_boss() -> pygame.Surface | None:
    return _try_load(["boss", "enemy_boss"])


def load_bullet() -> pygame.Surface | None:
    return _try_load(["bullet", "bullet1"])

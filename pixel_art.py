"""
像素风格美术资源生成 v4
使用字符网格精心绘制每一个像素
Hue-shifted 调色板，光源从右上方照射
"""
import math
import pygame

PX = 3

BLACK       = (0, 0, 0)
DARK_BLUE   = (29, 43, 83)
DARK_PURPLE = (126, 37, 83)
DARK_GREEN  = (0, 135, 81)
BROWN       = (171, 82, 54)
DARK_GRAY   = (95, 87, 79)
LIGHT_GRAY  = (194, 195, 199)
WHITE       = (255, 241, 232)
RED         = (255, 0, 77)
ORANGE      = (255, 163, 0)
YELLOW      = (255, 236, 39)
GREEN       = (0, 228, 54)
BLUE        = (41, 173, 255)
LAVENDER    = (131, 118, 156)
PINK        = (255, 119, 168)
PEACH       = (255, 204, 170)
CYAN        = (0, 255, 204)

DEEP_NAVY   = (8, 12, 30)
DEEP_RED    = (170, 35, 35)
LIGHT_BLUE  = (120, 210, 255)
LIGHT_GREEN = (120, 255, 160)
SHIELD_BLUE = (60, 150, 255)
GOLD        = (255, 215, 0)

_cache: dict[str, pygame.Surface] = {}


def _r(inner: str, w: int) -> str:
    pad = (w - len(inner)) // 2
    return '.' * pad + inner + '.' * (w - len(inner) - pad)


def _grid(rows: list[str], palette: dict, scale: int = PX) -> pygame.Surface:
    h = len(rows)
    w = len(rows[0]) if rows else 0
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in palette:
                s.set_at((x, y), palette[ch])
    return pygame.transform.scale(s, (w * scale, h * scale))


def _fix_row(row: str, w: int) -> str:
    if len(row) == w:
        return row
    if len(row) < w:
        diff = w - len(row)
        left = diff // 2
        return '.' * left + row + '.' * (diff - left)
    diff = len(row) - w
    left = diff // 2
    return row[left:left + w]


# ═══════════════════════════════════════════════════════════
#  Player Sprites  (20×24 → 60×72)
# ═══════════════════════════════════════════════════════════

_P1_PAL = {
    'o': (10, 20, 70),
    'd': (18, 55, 145),
    'b': (30, 100, 200),
    'B': (41, 173, 255),
    'l': (100, 200, 255),
    'h': (175, 225, 255),
    'w': WHITE,
    'c': (0, 185, 175),
    'g': (110, 255, 225),
    'E': (255, 163, 0),
    'F': (255, 236, 39),
    'e': (175, 95, 18),
    'r': (255, 75, 55),
}

_P2_PAL = {
    'o': (0, 30, 18),
    'd': (0, 75, 35),
    'b': (0, 140, 48),
    'B': (0, 228, 54),
    'l': (85, 255, 115),
    'h': (175, 255, 195),
    'w': WHITE,
    'c': (195, 195, 25),
    'g': (255, 255, 135),
    'E': (255, 163, 0),
    'F': (255, 236, 39),
    'e': (175, 95, 18),
    'r': (255, 75, 55),
}

_PW = 20

_P_BODY = [
    _r("wh", _PW),
    _r("hBBl", _PW),
    _r("dBBl", _PW),
    _r("dBBBBl", _PW),
    _r("dBcgBl", _PW),
    _r("dBccBl", _PW),
    _r("dBBBBBBl", _PW),
    _r("dBBBBBBBBl", _PW),
    _r("dBBBBBBBBBBl", _PW),
    _r("dBBBBBBBBBBBBl", _PW),
    _r("dBBrBBBBBBBBrBBl", _PW),
    _r("dBBBBBBBBBBBBBBBBBl", _PW),
    "dBBhBBrBBBBBBrBBhBBl",
    "dBd..dBBBBBBBBl..lBl",
    _r("dBBBBBBBBl", _PW),
    _r("dBBBBBBl", _PW),
    _r("dBBBBl", _PW),
    ".....dBo....oBl.....",
    ".....do......ol.....",
]

_P_TAIL_F0 = [
    _r("EEEEEE", _PW),
    _r("EFEFEF", _PW),
    _r("rFFr", _PW),
    _r("FF", _PW),
    _r("FF", _PW),
]

_P_TAIL_F1 = [
    _r("eEEEEe", _PW),
    _r("EEEEEE", _PW),
    _r("FEFE", _PW),
    _r("Fe", _PW),
    _r("ee", _PW),
]


def player_sprite(pid: int, frame: int = 0) -> pygame.Surface:
    key = f"player_{pid}_{frame}"
    if key in _cache:
        return _cache[key]
    pal = _P1_PAL if pid == 1 else _P2_PAL
    rows = _P_BODY + (_P_TAIL_F0 if frame == 0 else _P_TAIL_F1)
    result = _grid(rows, pal)
    _cache[key] = result
    return result


# ═══════════════════════════════════════════════════════════
#  Enemy Sprites
# ═══════════════════════════════════════════════════════════

_ES_PAL = {
    'o': (72, 6, 20),
    'd': (135, 18, 26),
    'R': (215, 38, 48),
    'l': (255, 88, 78),
    'h': (255, 148, 108),
    'Y': (255, 236, 39),
    'W': (255, 200, 100),
    'E': (255, 163, 0),
}

_ESW = 14
_ENEMY_S = [
    _r("EE", _ESW),
    _r("dRRl", _ESW),
    _r("dRRRRl", _ESW),
    _r("dRRRRRRl", _ESW),
    _r("dRRRYYRRRl", _ESW),
    _r("dRRRYWRRRl", _ESW),
    _r("dRRRRRRRRRRl", _ESW),
    "dRhRRRRRRRRhRl",
    "dR..dRRRRl..Rl",
    _r("dRRRRRRl", _ESW),
    _r("dRRRRl", _ESW),
    _r("dRRl", _ESW),
    _r("dl", _ESW),
    _r("ol", _ESW),
]

_EM_PAL = {
    'o': (68, 6, 22),
    'd': (125, 16, 30),
    'R': (195, 32, 42),
    'l': (255, 82, 72),
    'h': (255, 138, 102),
    'Y': (255, 236, 39),
    'W': (255, 200, 100),
    'E': (255, 163, 0),
    'P': (145, 38, 88),
}

_EMW = 16
_ENEMY_M = [
    _r("EooE", _EMW),
    _r("dRRRRl", _EMW),
    _r("dRRRRRRl", _EMW),
    _r("dRRRRRRRRl", _EMW),
    _r("dRRRRYYRRRRl", _EMW),
    _r("dRRRRYWRRRRl", _EMW),
    _r("dRRRRRRRRRRRRl", _EMW),
    "dRhRRRRRRRRRRhRl",
    "dR..dRRRRRRl..Rl",
    _r("dPRRRRRRPl", _EMW),
    _r("dRRRRRRRRl", _EMW),
    _r("dRRRRRRl", _EMW),
    _r("dRRRRl", _EMW),
    _r("dRRl", _EMW),
    _r("dl", _EMW),
    _r("ol", _EMW),
]

_EL_PAL = {
    'o': (52, 4, 30),
    'd': (95, 12, 38),
    'R': (155, 28, 36),
    'l': (205, 52, 52),
    'h': (255, 92, 72),
    'Y': (255, 236, 39),
    'W': (255, 200, 100),
    'E': (255, 163, 0),
    'P': (88, 14, 68),
}

_ELW = 20
_ENEMY_L = [
    _r("EEooEE", _ELW),
    _r("dRRRRRRl", _ELW),
    _r("dRRRRRRRRl", _ELW),
    _r("dPRRRRRRRRPl", _ELW),
    _r("dRRRRRRRRRRRRl", _ELW),
    _r("dRRRRRYYRRRRRl", _ELW),
    _r("dRRRRRYWRRRRRl", _ELW),
    _r("dRRRRRRRRRRRRRRRRl", _ELW),
    "dRhRRRRRRRRRRRRRRhRl",
    "dRd..dRRRRRRRRl..lRl",
    _r("dRRRRRRRRRRRRl", _ELW),
    _r("dPRRRRRRRRPl", _ELW),
    _r("dRRRRRRRRl", _ELW),
    _r("dRRRRRRl", _ELW),
    _r("dRRRRl", _ELW),
    _r("dRRl", _ELW),
    _r("dRRl", _ELW),
    _r("dl", _ELW),
    _r("dl", _ELW),
    _r("ol", _ELW),
]


def enemy_sprite(etype: str) -> pygame.Surface:
    key = f"enemy_{etype}"
    if key in _cache:
        return _cache[key]

    if etype == "small":
        pal, rows, w = _ES_PAL, _ENEMY_S, _ESW
    elif etype == "large":
        pal, rows, w = _EL_PAL, _ENEMY_L, _ELW
    else:
        pal, rows, w = _EM_PAL, _ENEMY_M, _EMW

    fixed = [_fix_row(r, w) for r in rows]
    result = _grid(fixed, pal)
    _cache[key] = result
    return result


# ═══════════════════════════════════════════════════════════
#  Boss Sprite  (40×28 → 120×84)
# ═══════════════════════════════════════════════════════════

def boss_sprite(frame: int = 0) -> pygame.Surface:
    key = f"boss_{frame}"
    if key in _cache:
        return _cache[key]

    w, h = 40, 28
    s = pygame.Surface((w, h), pygame.SRCALPHA)

    hull_dark = (70, 12, 18)
    hull_mid = (140, 28, 32)
    hull_main = (190, 42, 45)
    hull_light = (230, 70, 65)
    hull_bright = (255, 110, 90)
    armor = (100, 18, 35)

    hull_pts = [
        (12, 0), (27, 0), (33, 5), (37, 10), (39, 16),
        (37, 21), (31, 25), (20, 27), (19, 27),
        (8, 25), (2, 21), (0, 16), (2, 10), (6, 5),
    ]
    pygame.draw.polygon(s, hull_mid, hull_pts)

    left_shade = [
        (12, 0), (6, 5), (2, 10), (0, 16), (2, 21), (8, 25),
        (19, 27), (19, 14), (12, 7),
    ]
    pygame.draw.polygon(s, hull_dark, left_shade)
    right_shade = [
        (27, 0), (33, 5), (37, 10), (39, 16), (37, 21), (31, 25),
        (20, 27), (20, 14), (27, 7),
    ]
    pygame.draw.polygon(s, hull_light, right_shade)

    pygame.draw.polygon(s, armor, [(13, 1), (26, 1), (30, 5), (9, 5)])
    pygame.draw.polygon(s, (180, 45, 50), [(13, 1), (26, 1), (30, 5), (9, 5)], 1)

    pygame.draw.polygon(s, hull_dark, [(2, 10), (0, 14), (0, 18), (2, 21), (5, 16)])
    pygame.draw.polygon(s, hull_light, [(37, 10), (39, 14), (39, 18), (37, 21), (34, 16)])
    pygame.draw.polygon(s, hull_bright, [(37, 10), (39, 14), (39, 18), (37, 21), (34, 16)], 1)

    for tx, tc in [(8, hull_dark), (30, hull_light)]:
        pygame.draw.rect(s, tc, (tx, 11, 4, 7))
        pygame.draw.rect(s, ORANGE, (tx + 1, 12, 2, 5))
        pygame.draw.rect(s, YELLOW, (tx + 1, 12, 2, 2))

    pygame.draw.rect(s, (80, 20, 25), (15, 8, 10, 12))
    pygame.draw.rect(s, hull_main, (16, 9, 8, 10))
    if frame % 2 == 0:
        pygame.draw.rect(s, ORANGE, (17, 10, 6, 8))
        pygame.draw.rect(s, YELLOW, (18, 11, 4, 6))
        pygame.draw.rect(s, WHITE, (19, 12, 2, 4))
    else:
        pygame.draw.rect(s, (200, 80, 30), (17, 10, 6, 8))
        pygame.draw.rect(s, ORANGE, (18, 11, 4, 6))
        pygame.draw.rect(s, YELLOW, (19, 12, 2, 4))

    pygame.draw.polygon(s, hull_bright, hull_pts, 1)

    for ly in [5, 20]:
        pygame.draw.line(s, hull_bright, (6, ly), (14, ly))
        pygame.draw.line(s, hull_bright, (25, ly), (33, ly))

    pygame.draw.rect(s, ORANGE, (14, 0, 3, 2))
    pygame.draw.rect(s, ORANGE, (23, 0, 3, 2))
    pygame.draw.rect(s, YELLOW, (15, 0, 1, 1))
    pygame.draw.rect(s, YELLOW, (24, 0, 1, 1))

    pygame.draw.rect(s, hull_bright, (18, 25, 4, 2))
    pygame.draw.rect(s, WHITE, (19, 26, 2, 1))

    result = pygame.transform.scale(s, (w * PX, h * PX))
    _cache[key] = result
    return result


# ═══════════════════════════════════════════════════════════
#  Power-Up Sprites  (10×10 → 30×30)
# ═══════════════════════════════════════════════════════════

_PU_B_PAL = {
    'o': (0, 65, 25),
    'G': (0, 170, 50),
    'g': (55, 210, 95),
    'w': WHITE,
}
_PU_B = [
    "oooooooooo",
    "oGGGGGGGGo",
    "oGGGgwGGGo",
    "oGGgwwwGGo",
    "oGGGgwGGGo",
    "oGGGgwGGGo",
    "oGGGgwGGGo",
    "oGGGGGGGGo",
    "oGGGGGGGGo",
    "oooooooooo",
]

_PU_L_PAL = {
    'o': (105, 6, 16),
    'R': (210, 28, 48),
    'r': (255, 65, 75),
    'w': WHITE,
}
_PU_L = [
    "oooooooooo",
    "oRRRRRRRRo",
    "oRRrwRRRRo",
    "oRrwwwRRRo",
    "oRrwwwwRRo",
    "oRRrwwwRRo",
    "oRRRrwRRRo",
    "oRRRRRRRRo",
    "oRRRRRRRRo",
    "oooooooooo",
]

_PU_M_PAL = {
    'o': (125, 72, 6),
    'Y': (225, 175, 28),
    'y': (255, 215, 75),
    'w': WHITE,
}
_PU_M = [
    "oooooooooo",
    "oYYYYYYYYo",
    "oYYYywYYYo",
    "oYYywwwYYo",
    "oYywwwwwYo",
    "oYYywwwYYo",
    "oYYYywYYYo",
    "oYYYYYYYYo",
    "oYYYYYYYYo",
    "oooooooooo",
]

_PU_S_PAL = {
    'o': (10, 40, 105),
    'B': (30, 120, 210),
    'b': (80, 180, 255),
    'w': WHITE,
}
_PU_S = [
    "oooooooooo",
    "oBBBBBBBBo",
    "oBBBbwBBBo",
    "oBBbwwwBBo",
    "oBbwwwwwBo",
    "oBBbwwwBBo",
    "oBBBbwBBBo",
    "oBBBBBBBBo",
    "oBBBBBBBBo",
    "oooooooooo",
]


def powerup_sprite(ptype: str) -> pygame.Surface:
    key = f"powerup_{ptype}"
    if key in _cache:
        return _cache[key]
    if ptype == "bullet":
        rows, pal = _PU_B, _PU_B_PAL
    elif ptype == "life":
        rows, pal = _PU_L, _PU_L_PAL
    elif ptype == "shield":
        rows, pal = _PU_S, _PU_S_PAL
    else:
        rows, pal = _PU_M, _PU_M_PAL
    result = _grid(rows, pal)
    _cache[key] = result
    return result


# ═══════════════════════════════════════════════════════════
#  Title Screen Scene
# ═══════════════════════════════════════════════════════════

def create_title_scene(w: int, h: int) -> pygame.Surface:
    import random
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((8, 12, 30))

    rng = random.Random(42)
    for _ in range(50):
        x = rng.randint(0, w - PX)
        y = rng.randint(0, h - PX)
        c = rng.choice([(80, 80, 100), (140, 140, 165), WHITE, CYAN, (100, 100, 130)])
        pygame.draw.rect(s, c, (x, y, PX, PX))

    em = enemy_sprite("medium")
    es1 = enemy_sprite("small")
    es2 = enemy_sprite("small")
    el = enemy_sprite("large")

    s.blit(pygame.transform.scale(es1, (26, 26)), (w // 6 - 13, 18))
    s.blit(pygame.transform.scale(em, (34, 34)), (w // 2 - 17, 8))
    s.blit(pygame.transform.scale(es2, (26, 26)), (5 * w // 6 - 13, 22))
    s.blit(pygame.transform.scale(el, (42, 42)), (2 * w // 3 - 21, 14))

    bx = w // 2
    for by in range(h - 58, 38, -16):
        pygame.draw.rect(s, BULLET_YELLOW, (bx - 2, by, 4, 10))
        pygame.draw.rect(s, WHITE, (bx - 2, by, 4, PX))

    for ex_x, by0 in [(w // 6, 50), (5 * w // 6, 54)]:
        for by in range(by0, h - 10, 22):
            pygame.draw.rect(s, ENEMY_BULLET_CORE, (ex_x - 2, by, 4, 8))
            pygame.draw.rect(s, ENEMY_BULLET_TIP, (ex_x - 2, by + 6, 4, 2))

    ex_cx, ex_cy = w // 6 + 16, 30
    for dx, dy, c, sz in [
        (0, 0, WHITE, PX * 2), (7, -5, YELLOW, PX * 2),
        (-6, 4, ORANGE, PX), (5, 6, RED, PX), (-4, -6, YELLOW, PX),
        (8, 2, ORANGE, PX), (-7, -2, RED, PX),
    ]:
        pygame.draw.rect(s, c, (ex_cx + dx, ex_cy + dy, sz, sz))

    ps = player_sprite(1, 0)
    scaled_ps = pygame.transform.scale(ps, (38, 46))
    s.blit(scaled_ps, (w // 2 - 19, h - 52))

    glow = pygame.Surface((24, PX * 3), pygame.SRCALPHA)
    glow.fill((255, 163, 0, 50))
    s.blit(glow, (w // 2 - 12, h - 8))

    return s


# ═══════════════════════════════════════════════════════════
#  Enhanced bullet/projectile colors
# ═══════════════════════════════════════════════════════════

BULLET_YELLOW     = (255, 240, 120)
BULLET_WHITE      = (255, 255, 240)
LASER_CORE        = (180, 240, 255)
LASER_EDGE        = (80, 180, 255)
PLASMA_CORE       = (255, 200, 255)
PLASMA_MID        = (200, 100, 255)
PLASMA_EDGE       = (120, 50, 180)
ELEC_CORE         = (255, 255, 200)
ELEC_BOLT         = (255, 255, 80)
ENEMY_BULLET_CORE = (255, 120, 100)
ENEMY_BULLET_TIP  = (255, 200, 180)
BOSS_BULLET_COLOR = (255, 80, 200)
BOSS_BULLET_CORE  = (255, 180, 255)


# ═══════════════════════════════════════════════════════════
#  UI Helpers
# ═══════════════════════════════════════════════════════════

def draw_pixel_border(surface: pygame.Surface, x: int, y: int,
                      w: int, h: int, color: tuple, width: int = 2) -> None:
    for i in range(width):
        pygame.draw.rect(surface, color, (x + i, y + i, w - i * 2, h - i * 2), 1)
    corner_size = PX * 2
    for cx, cy in [(x, y), (x + w - corner_size, y),
                   (x, y + h - corner_size), (x + w - corner_size, y + h - corner_size)]:
        pygame.draw.rect(surface, color, (cx, cy, corner_size, corner_size))


def draw_panel(surface: pygame.Surface, x: int, y: int,
               w: int, h: int, bg_color: tuple = (15, 15, 35),
               border_color: tuple = BLUE) -> None:
    pygame.draw.rect(surface, bg_color, (x, y, w, h))
    draw_pixel_border(surface, x, y, w, h, border_color)


def create_scanlines(w: int, h: int, alpha: int = 18) -> pygame.Surface:
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(0, h, 2):
        pygame.draw.line(s, (0, 0, 0, alpha), (0, y), (w, y))
    return s


def create_bg_gradient(w: int, h: int) -> pygame.Surface:
    s = pygame.Surface((w, h))
    step = PX * 2
    for y in range(0, h, step):
        t = y / h
        r = int(5 + t * 10)
        g = int(8 + t * 4)
        b = int(25 + t * 18)
        pygame.draw.rect(s, (r, g, b), (0, y, w, step))
    return s


def draw_pixel_heart(surface: pygame.Surface, x: int, y: int,
                     color: tuple, size: int = PX) -> None:
    s = size
    pygame.draw.rect(surface, color, (x + s, y, s, s))
    pygame.draw.rect(surface, color, (x + 3 * s, y, s, s))
    pygame.draw.rect(surface, color, (x, y + s, s * 5, s))
    pygame.draw.rect(surface, color, (x + s, y + 2 * s, s * 3, s))
    pygame.draw.rect(surface, color, (x + 2 * s, y + 3 * s, s, s))


def draw_pixel_bar(surface: pygame.Surface, x: int, y: int,
                   w: int, h: int, ratio: float,
                   fg_color: tuple, bg_color: tuple,
                   border_color: tuple = LIGHT_GRAY) -> None:
    pygame.draw.rect(surface, bg_color, (x, y, w, h))
    fill_w = int(w * max(0, min(1, ratio)))
    if fill_w > 0:
        pygame.draw.rect(surface, fg_color, (x, y, fill_w, h))
    pygame.draw.rect(surface, border_color, (x, y, w, h), 1)


def draw_shield_effect(surface: pygame.Surface, cx: int, cy: int,
                       radius: int, ticks: int) -> None:
    """Draw a rotating pixel shield ring around a point."""
    num_dots = 12
    angle_offset = ticks / 300.0
    for i in range(num_dots):
        angle = angle_offset + (2 * math.pi * i / num_dots)
        x = cx + int(math.cos(angle) * radius)
        y = cy + int(math.sin(angle) * radius)
        phase = (i + ticks // 80) % 3
        if phase == 0:
            c = SHIELD_BLUE
        elif phase == 1:
            c = LIGHT_BLUE
        else:
            c = WHITE
        pygame.draw.rect(surface, c, (x - PX, y - PX, PX * 2, PX * 2))

    glow_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    glow_alpha = int(20 + 10 * math.sin(ticks / 150.0))
    pygame.draw.circle(glow_surf, (*SHIELD_BLUE, glow_alpha),
                       (radius + 2, radius + 2), radius)
    surface.blit(glow_surf, (cx - radius - 2, cy - radius - 2))


def draw_boss_hp_bar(surface: pygame.Surface, x: int, y: int,
                     w: int, h: int, ratio: float, ticks: int) -> None:
    """Segmented, glowing boss HP bar."""
    pygame.draw.rect(surface, (30, 5, 5), (x - 1, y - 1, w + 2, h + 2))
    segments = 20
    seg_w = w / segments
    filled = int(segments * max(0, min(1, ratio)))
    for i in range(segments):
        sx = x + int(i * seg_w)
        sw = max(1, int(seg_w) - 1)
        if i < filled:
            pulse = math.sin(ticks / 200.0 + i * 0.3) * 0.15 + 0.85
            if ratio < 0.3:
                base_r, base_g, base_b = 255, 40, 40
            elif ratio < 0.6:
                base_r, base_g, base_b = 255, 140, 40
            else:
                base_r, base_g, base_b = 255, 40, 60
            c = (int(base_r * pulse), int(base_g * pulse), int(base_b * pulse))
            pygame.draw.rect(surface, c, (sx, y, sw, h))
        else:
            pygame.draw.rect(surface, (25, 8, 8), (sx, y, sw, h))
    pygame.draw.rect(surface, (180, 50, 50), (x, y, w, h), 1)
    if ratio > 0:
        glow_w = max(1, int(w * ratio))
        glow = pygame.Surface((glow_w, h + 4), pygame.SRCALPHA)
        glow.fill((255, 60, 60, 25))
        surface.blit(glow, (x, y - 2))

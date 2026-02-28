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

_BOSS_PALETTES = {
    1: {"dark": (70, 12, 18), "mid": (140, 28, 32), "main": (190, 42, 45),
        "light": (230, 70, 65), "bright": (255, 110, 90), "armor": (100, 18, 35),
        "eye": ORANGE, "eye_core": YELLOW, "glow": RED},
    2: {"dark": (40, 10, 80), "mid": (80, 25, 140), "main": (120, 40, 180),
        "light": (160, 70, 220), "bright": (200, 120, 255), "armor": (60, 15, 100),
        "eye": (200, 100, 255), "eye_core": (255, 180, 255), "glow": (180, 60, 255)},
    3: {"dark": (8, 50, 20), "mid": (15, 100, 40), "main": (25, 150, 60),
        "light": (50, 200, 90), "bright": (100, 240, 140), "armor": (10, 70, 30),
        "eye": GREEN, "eye_core": (200, 255, 200), "glow": (0, 255, 100)},
    4: {"dark": (10, 30, 80), "mid": (20, 60, 140), "main": (35, 90, 190),
        "light": (60, 130, 230), "bright": (100, 180, 255), "armor": (15, 40, 100),
        "eye": CYAN, "eye_core": WHITE, "glow": (0, 200, 255)},
    5: {"dark": (80, 60, 10), "mid": (160, 130, 20), "main": (210, 175, 30),
        "light": (240, 210, 50), "bright": (255, 240, 100), "armor": (120, 90, 15),
        "eye": (255, 215, 0), "eye_core": WHITE, "glow": GOLD},
    6: {"dark": (20, 10, 30), "mid": (50, 20, 60), "main": (80, 30, 100),
        "light": (120, 50, 150), "bright": (170, 80, 200), "armor": (30, 15, 45),
        "eye": (200, 50, 255), "eye_core": WHITE, "glow": (150, 0, 200)},
    7: {"dark": (50, 5, 5), "mid": (120, 15, 15), "main": (200, 25, 25),
        "light": (240, 50, 40), "bright": (255, 100, 80), "armor": (80, 10, 10),
        "eye": (255, 50, 0), "eye_core": YELLOW, "glow": (255, 80, 30)},
}


def _draw_boss_type1(s, w, h, pal, frame):
    """Standard fighter boss"""
    cx = w // 2
    hull = [(cx - 8, 0), (cx + 8, 0), (cx + 14, 5), (cx + 18, 10), (cx + 19, 16),
            (cx + 17, 21), (cx + 11, 25), (cx, 27), (cx - 1, 27),
            (cx - 12, 25), (cx - 18, 21), (cx - 20, 16), (cx - 18, 10), (cx - 14, 5)]
    pygame.draw.polygon(s, pal["mid"], hull)
    pygame.draw.polygon(s, pal["dark"], hull[:7] + [(cx, 14)])
    pygame.draw.polygon(s, pal["light"], hull[1:8] + [(cx, 14)])
    pygame.draw.polygon(s, pal["armor"], [(cx - 7, 1), (cx + 7, 1), (cx + 11, 5), (cx - 11, 5)])
    for tx in [cx - 12, cx + 9]:
        pygame.draw.rect(s, pal["dark"], (tx, 11, 4, 7))
        ec = pal["eye"] if frame == 0 else pal["eye_core"]
        pygame.draw.rect(s, ec, (tx + 1, 12, 2, 5))
    pygame.draw.rect(s, (40, 10, 15), (cx - 5, 8, 10, 12))
    ec = pal["eye"] if frame == 0 else pal["eye_core"]
    pygame.draw.rect(s, ec, (cx - 3, 10, 6, 8))
    pygame.draw.rect(s, pal["eye_core"], (cx - 1, 12, 2, 4))
    pygame.draw.polygon(s, pal["bright"], hull, 1)


def _draw_boss_type2(s, w, h, pal, frame):
    """Stealth cruiser — flat with wide wings"""
    cx, cy = w // 2, h // 2
    body = [(cx, 1), (cx + 18, cy - 2), (cx + 16, cy + 8), (cx + 8, h - 2),
            (cx - 8, h - 2), (cx - 16, cy + 8), (cx - 18, cy - 2)]
    pygame.draw.polygon(s, pal["mid"], body)
    pygame.draw.polygon(s, pal["dark"], body[:4] + [(cx, cy)])
    pygame.draw.polygon(s, pal["light"], [body[0]] + body[4:] + [(cx, cy)])
    wing_l = [(cx - 8, cy), (0, cy + 4), (2, cy + 8), (cx - 6, cy + 6)]
    wing_r = [(cx + 8, cy), (w - 1, cy + 4), (w - 3, cy + 8), (cx + 6, cy + 6)]
    pygame.draw.polygon(s, pal["armor"], wing_l)
    pygame.draw.polygon(s, pal["light"], wing_r)
    for wx in [3, w - 6]:
        ec = pal["eye"] if frame == 0 else pal["glow"]
        pygame.draw.rect(s, ec, (wx, cy + 2, 3, 4))
    ec = pal["eye"] if frame == 0 else pal["eye_core"]
    pygame.draw.rect(s, ec, (cx - 3, cy - 4, 6, 6))
    pygame.draw.rect(s, pal["eye_core"], (cx - 1, cy - 2, 2, 2))
    pygame.draw.polygon(s, pal["bright"], body, 1)


def _draw_boss_type3(s, w, h, pal, frame):
    """Organic bio-boss — irregular, tentacle-like"""
    cx, cy = w // 2, h // 2
    body = [(cx, 0), (cx + 12, 4), (cx + 16, cy), (cx + 14, cy + 8),
            (cx + 8, h - 1), (cx - 8, h - 1), (cx - 14, cy + 8),
            (cx - 16, cy), (cx - 12, 4)]
    pygame.draw.polygon(s, pal["mid"], body)
    for i in range(3):
        bx = cx - 10 + i * 10
        bump_r = 4 + (frame + i) % 2
        pygame.draw.circle(s, pal["light"], (bx, cy - 2 + i * 3), bump_r)
        pygame.draw.circle(s, pal["bright"], (bx, cy - 2 + i * 3), bump_r, 1)
    for tx, ty in [(cx - 14, h - 4), (cx - 8, h - 1), (cx + 7, h - 1), (cx + 13, h - 4)]:
        tent_len = 5 + (frame + tx) % 3
        pygame.draw.line(s, pal["dark"], (tx, ty), (tx + (1 if tx > cx else -1) * 3, ty + tent_len), 2)
    ec = pal["eye"] if frame == 0 else pal["glow"]
    pygame.draw.circle(s, ec, (cx, cy - 3), 5)
    pygame.draw.circle(s, pal["eye_core"], (cx, cy - 3), 2)
    pygame.draw.polygon(s, pal["bright"], body, 1)


def _draw_boss_type4(s, w, h, pal, frame):
    """Mechanical battleship — angular, heavy"""
    cx = w // 2
    body = [(cx - 10, 0), (cx + 10, 0), (cx + 18, 6), (cx + 19, h - 6),
            (cx + 14, h - 1), (cx - 14, h - 1), (cx - 19, h - 6), (cx - 18, 6)]
    pygame.draw.polygon(s, pal["mid"], body)
    pygame.draw.polygon(s, pal["dark"], body[:4] + [(cx, h // 2)])
    pygame.draw.polygon(s, pal["light"], [body[0]] + body[5:] + [(cx, h // 2)])
    for sy in range(3, h - 3, 4):
        pygame.draw.line(s, pal["armor"], (cx - 16, sy), (cx + 16, sy))
    for bx, by in [(cx - 16, 8), (cx + 13, 8), (cx - 16, h - 10), (cx + 13, h - 10)]:
        pygame.draw.rect(s, pal["armor"], (bx, by, 4, 6))
        ec = pal["eye"] if frame == 0 else pal["glow"]
        pygame.draw.rect(s, ec, (bx + 1, by + 1, 2, 4))
    ec = pal["eye"] if frame == 0 else pal["eye_core"]
    pygame.draw.rect(s, (20, 20, 30), (cx - 5, 5, 10, 8))
    pygame.draw.rect(s, ec, (cx - 3, 6, 6, 6))
    pygame.draw.rect(s, pal["eye_core"], (cx - 1, 7, 2, 4))
    cannon_y = h - 3
    for bx in [cx - 12, cx - 4, cx + 3, cx + 11]:
        pygame.draw.rect(s, pal["bright"], (bx, cannon_y, 2, 3))
    pygame.draw.polygon(s, pal["bright"], body, 1)


def _draw_boss_type5(s, w, h, pal, frame):
    """Ancient golden weapon — diamond shape with ornate details"""
    cx, cy = w // 2, h // 2
    diamond = [(cx, 0), (cx + 18, cy), (cx, h - 1), (cx - 18, cy)]
    pygame.draw.polygon(s, pal["mid"], diamond)
    pygame.draw.polygon(s, pal["dark"], diamond[:2] + [(cx, cy)])
    pygame.draw.polygon(s, pal["light"], [diamond[0], diamond[3], (cx, cy)])
    inner = [(cx, 4), (cx + 12, cy), (cx, h - 5), (cx - 12, cy)]
    pygame.draw.polygon(s, pal["armor"], inner, 1)
    for ring_r in [3, 6]:
        pygame.draw.circle(s, pal["bright"], (cx, cy), ring_r, 1)
    ec = pal["eye"] if frame == 0 else pal["eye_core"]
    pygame.draw.circle(s, ec, (cx, cy), 4)
    pygame.draw.circle(s, WHITE, (cx, cy), 2)
    for dx, dy in [(-14, 0), (14, 0), (0, -cy + 2), (0, cy - 2)]:
        pygame.draw.rect(s, pal["glow"], (cx + dx - 1, cy + dy - 1, 3, 3))
    pygame.draw.polygon(s, pal["bright"], diamond, 1)


def _draw_boss_type6(s, w, h, pal, frame):
    """Void wraith — dark, ethereal with floating parts"""
    cx, cy = w // 2, h // 2
    body = [(cx, 2), (cx + 10, 6), (cx + 14, cy), (cx + 12, h - 4),
            (cx, h - 1), (cx - 12, h - 4), (cx - 14, cy), (cx - 10, 6)]
    pygame.draw.polygon(s, pal["mid"], body)
    for ox in [-16, 14]:
        orb = [(cx + ox, cy - 6), (cx + ox + 5, cy), (cx + ox, cy + 6), (cx + ox - 5, cy)]
        pygame.draw.polygon(s, pal["dark"], orb)
        ec = pal["glow"] if frame == 0 else pal["eye"]
        pygame.draw.circle(s, ec, (cx + ox, cy), 3)
        pygame.draw.circle(s, WHITE, (cx + ox, cy), 1)
        pygame.draw.line(s, pal["bright"], (cx + (ox // 2), cy), (cx + ox, cy))
    ec = pal["eye"] if frame == 0 else pal["eye_core"]
    pygame.draw.circle(s, pal["dark"], (cx, cy - 2), 6)
    pygame.draw.circle(s, ec, (cx, cy - 2), 4)
    pygame.draw.circle(s, WHITE, (cx, cy - 2), 2)
    pygame.draw.polygon(s, pal["bright"], body, 1)


def _draw_boss_type7(s, w, h, pal, frame):
    """Ultimate crimson overlord — massive, many weapons"""
    cx, cy = w // 2, h // 2
    body = [(cx - 12, 0), (cx + 12, 0), (cx + 19, 5), (cx + 19, h - 5),
            (cx + 12, h - 1), (cx - 12, h - 1), (cx - 19, h - 5), (cx - 19, 5)]
    pygame.draw.polygon(s, pal["mid"], body)
    pygame.draw.polygon(s, pal["dark"], body[:4] + [(cx, cy)])
    pygame.draw.polygon(s, pal["light"], [body[0]] + body[5:] + [(cx, cy)])
    for sy in [5, 10, h - 8, h - 13]:
        pygame.draw.line(s, pal["armor"], (cx - 17, sy), (cx + 17, sy))
    pygame.draw.rect(s, pal["armor"], (cx - 8, 2, 16, 10))
    ec = pal["eye"] if frame == 0 else pal["glow"]
    pygame.draw.rect(s, ec, (cx - 5, 4, 10, 6))
    pygame.draw.rect(s, WHITE, (cx - 2, 5, 4, 4))
    for bx in [cx - 17, cx + 14]:
        for by in [8, cy, h - 10]:
            pygame.draw.rect(s, pal["armor"], (bx, by, 4, 5))
            gc = pal["glow"] if (frame + by) % 2 == 0 else pal["eye"]
            pygame.draw.rect(s, gc, (bx + 1, by + 1, 2, 3))
    for bx in [cx - 10, cx - 3, cx + 2, cx + 9]:
        pygame.draw.rect(s, pal["bright"], (bx, h - 2, 2, 3))
    horn_l = [(cx - 12, 0), (cx - 16, -3), (cx - 14, 3)]
    horn_r = [(cx + 12, 0), (cx + 16, -3), (cx + 14, 3)]
    pygame.draw.polygon(s, pal["armor"], horn_l)
    pygame.draw.polygon(s, pal["armor"], horn_r)
    pygame.draw.polygon(s, pal["bright"], body, 1)


_BOSS_DRAW_FUNCS = {
    1: _draw_boss_type1, 2: _draw_boss_type2, 3: _draw_boss_type3,
    4: _draw_boss_type4, 5: _draw_boss_type5, 6: _draw_boss_type6,
    7: _draw_boss_type7,
}


def boss_sprite(level: int = 1, frame: int = 0) -> pygame.Surface:
    key = f"boss_L{level}_{frame}"
    if key in _cache:
        return _cache[key]

    w, h = 40, 28
    s = pygame.Surface((w, h), pygame.SRCALPHA)

    pal_key = ((level - 1) % 7) + 1
    pal = _BOSS_PALETTES[pal_key]
    draw_fn = _BOSS_DRAW_FUNCS[pal_key]
    draw_fn(s, w, h, pal, frame)

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

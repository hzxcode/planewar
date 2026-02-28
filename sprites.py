"""
游戏精灵类：玩家、子弹、敌机、星空、爆炸 —— 像素风格版 v2
新增：FloatingText, HitSpark, ScreenShake, ShootingStar
"""
import math
import random
import pygame

import pixel_art as pa
from utils import get_font


class ScreenShake:
    """屏幕震动效果"""

    def __init__(self):
        self.intensity = 0
        self.duration = 0

    def trigger(self, intensity: int = 5, duration: int = 10) -> None:
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)

    def update(self) -> None:
        if self.duration > 0:
            self.duration -= 1
            t = self.duration / max(1, self.duration + 5)
            self.intensity = int(self.intensity * t)
            if self.duration <= 0:
                self.intensity = 0

    def get_offset(self) -> tuple[int, int]:
        if self.duration > 0 and self.intensity > 0:
            return (random.randint(-self.intensity, self.intensity),
                    random.randint(-self.intensity, self.intensity))
        return (0, 0)


class FloatingText:
    """浮动文字效果（得分、连杀提示等）"""

    _font_cache: dict[int, pygame.font.Font] = {}

    def __init__(self, x: int, y: int, text: str, color: tuple,
                 duration: int = 45, size: int = 16):
        self.x = x
        self.y = float(y)
        self.text = text
        self.color = color
        self.duration = duration
        self.frame = 0
        self.size = size
        if size not in FloatingText._font_cache:
            FloatingText._font_cache[size] = get_font(size)
        self.font = FloatingText._font_cache[size]

    def update(self) -> bool:
        self.frame += 1
        self.y -= 1.2
        return self.frame >= self.duration

    def draw(self, surface: pygame.Surface) -> None:
        alpha = max(0, 255 - int(255 * (self.frame / self.duration) ** 2))
        scale = 1.0 + 0.3 * max(0, 1 - self.frame / 8)
        txt = self.font.render(self.text, False, self.color)
        if scale > 1.05:
            sw = int(txt.get_width() * scale)
            sh = int(txt.get_height() * scale)
            txt = pygame.transform.scale(txt, (sw, sh))
        txt.set_alpha(alpha)
        surface.blit(txt, (self.x - txt.get_width() // 2, int(self.y)))


class HitSpark:
    """子弹命中时的火花粒子"""

    def __init__(self, x: int, y: int, color: tuple = None):
        self.particles: list[list] = []
        colors = [pa.WHITE, pa.YELLOW, pa.ORANGE] if color is None else [color, pa.WHITE]
        for _ in range(8):
            angle = random.random() * 2 * math.pi
            spd = random.uniform(2, 6)
            self.particles.append([
                float(x), float(y),
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.randint(4, 10),
                random.choice(colors),
            ])

    def update(self) -> bool:
        all_dead = True
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.88
            p[3] *= 0.88
            p[4] -= 1
            if p[4] > 0:
                all_dead = False
        return all_dead

    def draw(self, surface: pygame.Surface) -> None:
        px = pa.PX
        for x, y, _, _, life, color in self.particles:
            if life > 0:
                size = px * 2 if life > 6 else px
                pygame.draw.rect(surface, color,
                                 (int(x) - size // 2, int(y) - size // 2, size, size))


class ShootingStar:
    """流星效果"""

    def __init__(self, screen_width: int, screen_height: int):
        self.sw = screen_width
        self.sh = screen_height
        self.active = False
        self.timer = random.randint(200, 500)
        self.x = self.y = self.dx = self.dy = 0.0
        self.trail: list[tuple[float, float, int]] = []
        self.life = 0

    def update(self) -> None:
        if not self.active:
            self.timer -= 1
            if self.timer <= 0:
                self.active = True
                self.x = float(random.randint(0, self.sw))
                self.y = float(random.randint(-20, self.sh // 4))
                angle = random.uniform(0.3, 1.0)
                speed = random.uniform(10, 18)
                self.dx = math.cos(angle) * speed
                self.dy = math.sin(angle) * speed
                self.trail = []
                self.life = random.randint(20, 40)
            return

        self.trail.append((self.x, self.y, 15))
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

        new_trail = []
        for tx, ty, tl in self.trail:
            if tl > 1:
                new_trail.append((tx, ty, tl - 1))
        self.trail = new_trail

        if self.life <= 0 or self.x < -20 or self.x > self.sw + 20 or self.y > self.sh:
            self.active = False
            self.timer = random.randint(200, 500)

    def draw(self, surface: pygame.Surface) -> None:
        px = pa.PX
        for tx, ty, tl in self.trail:
            alpha = min(255, tl * 18)
            size = px if tl < 5 else px * 2
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            s.fill((255, 255, 255, alpha))
            surface.blit(s, (int(tx), int(ty)))
        if self.active:
            pygame.draw.rect(surface, pa.WHITE,
                             (int(self.x) - 1, int(self.y) - 1, px * 2, px * 2))


class StarBackground:
    """多层像素星空背景 —— 带颜色、大小分层和闪烁效果"""

    STAR_COLORS_DIM = [(80, 80, 100), (60, 60, 80), (100, 80, 100), (70, 70, 90)]
    STAR_COLORS_MID = [pa.WHITE, (200, 200, 255), (255, 255, 200), pa.LIGHT_GRAY]
    STAR_COLORS_BRIGHT = [pa.WHITE, pa.CYAN, pa.YELLOW, pa.PINK, pa.LIGHT_BLUE]

    def __init__(self, screen_width: int, screen_height: int, star_count: int = 120):
        self.sw = screen_width
        self.sh = screen_height
        self.stars: list[dict] = []
        for _ in range(star_count):
            layer = random.choices([0, 1, 2], weights=[3, 4, 3])[0]
            if layer == 0:
                speed = random.uniform(0.3, 0.8)
                color = random.choice(self.STAR_COLORS_DIM)
                size = pa.PX
            elif layer == 1:
                speed = random.uniform(1.0, 2.0)
                color = random.choice(self.STAR_COLORS_MID)
                size = pa.PX
            else:
                speed = random.uniform(2.0, 3.5)
                color = random.choice(self.STAR_COLORS_BRIGHT)
                size = pa.PX * 2
            self.stars.append({
                "x": random.randint(0, screen_width),
                "y": random.randint(0, screen_height),
                "speed": speed,
                "color": color,
                "size": size,
                "phase": random.random() * 6.28,
            })
        self.shooting_stars = [ShootingStar(screen_width, screen_height) for _ in range(2)]

    def update(self) -> None:
        for s in self.stars:
            s["y"] += s["speed"]
            if s["y"] > self.sh:
                s["y"] = -s["size"]
                s["x"] = random.randint(0, self.sw)
        for ss in self.shooting_stars:
            ss.update()

    def draw(self, surface: pygame.Surface) -> None:
        t = pygame.time.get_ticks() / 600.0
        for s in self.stars:
            twinkle = math.sin(t + s["phase"]) * 0.3 + 0.7
            r, g, b = s["color"]
            c = (max(0, min(255, int(r * twinkle))),
                 max(0, min(255, int(g * twinkle))),
                 max(0, min(255, int(b * twinkle))))
            pygame.draw.rect(surface, c,
                             (int(s["x"]), int(s["y"]), s["size"], s["size"]))
        for ss in self.shooting_stars:
            ss.draw(surface)


class Missile:
    """导弹：向上飞行，像素风格尾焰"""

    def __init__(self, x: int, y: int, speed: int = 14):
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.trail: list[tuple[float, float, int]] = []

    def update(self, screen_height: int) -> bool:
        self.y -= self.speed
        self.trail.append((self.x, self.y + self.speed * 2, 8))
        for i in range(len(self.trail) - 1, -1, -1):
            tx, ty, life = self.trail[i]
            self.trail[i] = (tx, ty, life - 1)
            if life <= 0:
                self.trail.pop(i)
        return self.y < -30

    def draw(self, surface: pygame.Surface) -> None:
        px = pa.PX
        for tx, ty, life in self.trail:
            size = max(px, life // 2 * px)
            t = 1 - life / 8
            if t < 0.25:
                c = pa.WHITE
            elif t < 0.45:
                c = pa.YELLOW
            elif t < 0.7:
                c = pa.ORANGE
            else:
                c = pa.RED
            pygame.draw.rect(surface, c,
                             (int(tx) - size // 2, int(ty) - size // 2, size, size))
        mx, my = int(self.x), int(self.y)
        pygame.draw.rect(surface, pa.CYAN,
                         (mx - px - 1, my - px * 3, px * 2 + 2, px * 4 + 2))
        pygame.draw.rect(surface, pa.WHITE,
                         (mx - px, my - px * 2, px * 2, px * 3))
        pygame.draw.rect(surface, pa.LIGHT_BLUE,
                         (mx - px, my - px * 3, px * 2, px))

    @property
    def explosion_pos(self) -> tuple[int, int]:
        return int(self.x), int(self.y) + 20


class MissileExplosion:
    """导弹爆炸：低分辨率渲染后放大，保持像素风格"""

    def __init__(self, x: int, y: int, radius: int = 110, duration: int = 35):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.frame = 0
        self.particles: list[list] = []
        for _ in range(55):
            angle = random.random() * 2 * math.pi
            spd = random.uniform(1.5, 7)
            dist = random.uniform(0, radius * 0.25)
            self.particles.append([
                x + dist * math.cos(angle),
                y + dist * math.sin(angle),
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.randint(15, duration),
            ])

    def update(self) -> bool:
        self.frame += 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.94
            p[3] *= 0.94
            p[4] -= 1
        return self.frame >= self.duration

    def draw(self, surface: pygame.Surface) -> None:
        px = pa.PX
        progress = self.frame / self.duration
        if progress < 0.5:
            lo_r = self.radius // px
            lo_size = lo_r * 2 + 4
            lo = pygame.Surface((lo_size, lo_size), pygame.SRCALPHA)
            cx, cy = lo_size // 2, lo_size // 2
            outer = int(lo_r * progress * 2)
            inner = max(1, int(outer * 0.6))
            core = max(1, int(outer * 0.3))
            if outer > 0:
                pygame.draw.circle(lo, pa.ORANGE, (cx, cy), outer)
            if inner > 0:
                pygame.draw.circle(lo, pa.YELLOW, (cx, cy), inner)
            if core > 0:
                pygame.draw.circle(lo, pa.WHITE, (cx, cy), core)
            hi = pygame.transform.scale(lo, (lo_size * px, lo_size * px))
            surface.blit(hi,
                         (self.x - lo_size * px // 2, self.y - lo_size * px // 2))
        for x, y, _, _, life in self.particles:
            if life > 0:
                t = 1 - life / self.duration
                if t < 0.2:
                    c = pa.WHITE
                elif t < 0.4:
                    c = pa.YELLOW
                elif t < 0.6:
                    c = pa.ORANGE
                else:
                    c = pa.RED
                size = px * 2 if life > self.duration * 0.5 else px
                pygame.draw.rect(surface, c,
                                 (int(x) - size // 2, int(y) - size // 2, size, size))


class Explosion:
    """像素风格爆炸效果：方形粒子 + 闪光核心 + 碎片"""

    def __init__(self, x: int, y: int, duration: int = 16):
        self.x = x
        self.y = y
        self.duration = duration
        self.frame = 0
        self.particles: list[list] = []
        for _ in range(20):
            angle = random.random() * 2 * math.pi
            spd = random.uniform(1.5, 6)
            self.particles.append([
                float(x), float(y),
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.randint(6, duration),
                random.choice([0, 1]),
            ])

    def update(self) -> bool:
        self.frame += 1
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.92
            p[3] *= 0.92
            p[4] -= 1
        return self.frame >= self.duration

    def draw(self, surface: pygame.Surface) -> None:
        px = pa.PX
        progress = self.frame / self.duration
        if progress < 0.5:
            cr = int((1 - progress * 2) * 5) * px
            if cr > 0:
                pygame.draw.rect(surface, pa.YELLOW,
                                 (self.x - cr // 2 - 1, self.y - cr // 2 - 1,
                                  cr + 2, cr + 2))
                pygame.draw.rect(surface, pa.WHITE,
                                 (self.x - cr // 2, self.y - cr // 2, cr, cr))
        for x, y, _, _, life, ptype in self.particles:
            if life > 0:
                t = 1 - life / self.duration
                if ptype == 0:
                    if t < 0.2:
                        c = pa.WHITE
                    elif t < 0.4:
                        c = pa.YELLOW
                    elif t < 0.7:
                        c = pa.ORANGE
                    else:
                        c = pa.RED
                else:
                    if t < 0.3:
                        c = pa.LIGHT_GRAY
                    elif t < 0.6:
                        c = pa.DARK_GRAY
                    else:
                        c = (60, 50, 45)
                size = px * 2 if life > self.duration * 0.6 else px
                pygame.draw.rect(surface, c,
                                 (int(x) - size // 2, int(y) - size // 2,
                                  size, size))


class Player:
    """玩家飞机类 - 像素风格精灵，支持引擎动画和护盾"""

    FORM_STATS = {"normal": (6, 1.0), "agile": (8, 0.85), "heavy": (4, 1.2)}

    def __init__(
        self, screen_width: int, screen_height: int,
        player_id: int = 1, two_player: bool = False,
        width: int = 50, height: int = 60
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = width
        self.height = height
        self.player_id = player_id
        self.two_player = two_player
        self.bullet_type = "normal"
        self.bullet_style = "normal"
        self.plane_form = "normal"
        speed, _ = self.FORM_STATS[self.plane_form]
        self.speed = speed
        if player_id == 1:
            x = (screen_width - width) // 2 if not two_player else screen_width // 4 - width // 2
        else:
            x = screen_width * 3 // 4 - width // 2
        y = screen_height - height - 20
        self.rect = pygame.Rect(x, y, width, height)
        self.invincible = False
        self.invincible_timer = 0
        self.shield_timer = 0
        self.trail_particles: list[list] = []

    def _get_form_stats(self) -> tuple[int, float]:
        speed, scale = self.FORM_STATS.get(self.plane_form, (6, 1.0))
        return speed, scale

    def apply_form(self, form: str) -> None:
        self.plane_form = form
        self.speed, _ = self._get_form_stats()

    def update(self, keys=None, touch_target: tuple[float, float] | None = None) -> None:
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        if self.shield_timer > 0:
            self.shield_timer -= 1
        self.speed, _ = self._get_form_stats()
        old_x, old_y = self.rect.x, self.rect.y

        if touch_target is not None:
            self.rect.centerx = int(touch_target[0])
            self.rect.centery = int(touch_target[1])
        elif keys is not None:
            dx = dy = 0
            if self.player_id == 1:
                if keys[pygame.K_a]:
                    dx -= self.speed
                if keys[pygame.K_d]:
                    dx += self.speed
                if keys[pygame.K_w]:
                    dy -= self.speed
                if keys[pygame.K_s]:
                    dy += self.speed
            else:
                if keys[pygame.K_LEFT]:
                    dx -= self.speed
                if keys[pygame.K_RIGHT]:
                    dx += self.speed
                if keys[pygame.K_UP]:
                    dy -= self.speed
                if keys[pygame.K_DOWN]:
                    dy += self.speed
            self.rect.x += dx
            self.rect.y += dy
        self.rect.x = max(0, min(self.screen_width - self.width, self.rect.x))
        self.rect.y = max(0, min(self.screen_height - self.height, self.rect.y))

        moved = (self.rect.x != old_x or self.rect.y != old_y)
        if moved:
            self.trail_particles.append([
                float(self.rect.centerx + random.randint(-3, 3)),
                float(self.rect.bottom),
                random.uniform(-0.5, 0.5),
                random.uniform(1.0, 3.0),
                random.randint(6, 12),
            ])

        new_trail = []
        for tp in self.trail_particles:
            tp[0] += tp[2]
            tp[1] += tp[3]
            tp[4] -= 1
            if tp[4] > 0:
                new_trail.append(tp)
        self.trail_particles = new_trail[-30:]

    def hit(self, invincibility_frames: int) -> None:
        self.invincible = True
        self.invincible_timer = invincibility_frames

    def draw(self, surface: pygame.Surface) -> None:
        px = pa.PX
        ticks = pygame.time.get_ticks()

        for tp in self.trail_particles:
            t = 1 - tp[4] / 12
            if t < 0.3:
                c = pa.YELLOW
            elif t < 0.6:
                c = pa.ORANGE
            else:
                c = (180, 60, 20)
            alpha = max(0, min(255, int(tp[4] * 25)))
            s = pygame.Surface((px, px), pygame.SRCALPHA)
            s.fill((*c, alpha))
            surface.blit(s, (int(tp[0]), int(tp[1])))

        if self.invincible and (self.invincible_timer // 5) % 2 == 0:
            return
        frame = (ticks // 100) % 2
        sprite = pa.player_sprite(self.player_id, frame)
        scaled = pygame.transform.scale(sprite, (self.rect.width, self.rect.height))

        glow_alpha = int(40 + 20 * math.sin(ticks / 200.0))
        glow_h = px * 4
        glow_w = self.rect.width // 3
        glow_surf = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
        glow_surf.fill((255, 163, 0, glow_alpha))
        glow_x = self.rect.centerx - glow_w // 2
        glow_y = self.rect.bottom - px
        surface.blit(glow_surf, (glow_x, glow_y))

        surface.blit(scaled, self.rect)

        blink = (ticks // 500) % 2 == 0
        if blink:
            tip_y = self.rect.y + int(self.rect.height * 0.52)
            left_x = self.rect.x + px
            right_x = self.rect.right - px * 2
            c = pa.RED if self.player_id == 1 else pa.GREEN
            pygame.draw.rect(surface, c, (left_x, tip_y, px, px))
            pygame.draw.rect(surface, c, (right_x, tip_y, px, px))

        if self.shield_timer > 0:
            radius = max(self.rect.width, self.rect.height) // 2 + 6
            pa.draw_shield_effect(surface, self.rect.centerx, self.rect.centery,
                                  radius, ticks)


class Bullet:
    """像素风格子弹"""

    def __init__(self, x: float, y: float, width: int = 4, height: int = 12,
                 speed: int = 12, style: str = "normal"):
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = speed
        self.style = style

    def update(self) -> None:
        self.rect.y -= self.speed

    def is_off_screen(self, screen_height: int) -> bool:
        return self.rect.bottom < 0

    def draw(self, surface: pygame.Surface) -> None:
        r = self.rect
        px = pa.PX
        cx, cy = r.centerx, r.centery
        t = (pygame.time.get_ticks() // 60) % 4

        if self.style == "laser":
            pygame.draw.rect(surface, pa.LASER_EDGE,
                             (cx - px, r.top - px, px * 2, r.height + px * 2))
            pygame.draw.rect(surface, pa.LASER_CORE,
                             (cx - px // 2, r.top, px, r.height))
            pygame.draw.rect(surface, pa.WHITE,
                             (cx - 1, r.top, 2, px * 2))
        elif self.style == "plasma":
            size = px * 3
            pygame.draw.rect(surface, pa.PLASMA_EDGE,
                             (cx - size // 2, cy - size // 2, size, size))
            pygame.draw.rect(surface, pa.PLASMA_MID,
                             (cx - px, cy - px, px * 2, px * 2))
            pygame.draw.rect(surface, pa.PLASMA_CORE,
                             (cx - 1, cy - 1, 3, 3))
        elif self.style == "electric":
            offsets = [((t + i) % 3 - 1) * px for i in range(3)]
            for i, ox in enumerate(offsets):
                yy = r.top + i * r.height // 3
                pygame.draw.rect(surface, pa.ELEC_BOLT,
                                 (cx + ox - 1, yy, px, r.height // 3))
            pygame.draw.rect(surface, pa.ELEC_CORE,
                             (cx - 1, r.top, 2, r.height))
        else:
            pygame.draw.rect(surface, pa.BULLET_YELLOW, r)
            pygame.draw.rect(surface, pa.BULLET_WHITE,
                             (r.x, r.y, r.width, px))


class EnemyBullet:
    """敌机子弹 - 像素风格，支持方向速度"""

    def __init__(self, x: int, y: int, speed: int = 5,
                 vx: float = 0, vy: float | None = None,
                 is_boss: bool = False):
        self.rect = pygame.Rect(x - 3, y, 6, 14)
        self.vx = float(vx)
        self.vy = float(vy) if vy is not None else float(speed)
        self.is_boss = is_boss

    def update(self) -> None:
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

    def is_off_screen(self, screen_height: int) -> bool:
        return (self.rect.top > screen_height or self.rect.bottom < 0
                or self.rect.right < 0 or self.rect.left > 600)

    def draw(self, surface: pygame.Surface) -> None:
        r = self.rect
        px = pa.PX
        if self.is_boss:
            pygame.draw.rect(surface, pa.BOSS_BULLET_COLOR, r)
            pygame.draw.rect(surface, pa.BOSS_BULLET_CORE,
                             (r.centerx - 1, r.top, 2, r.height))
            ticks = pygame.time.get_ticks()
            glow = pygame.Surface((r.width + 4, r.height + 4), pygame.SRCALPHA)
            glow_alpha = int(30 + 15 * math.sin(ticks / 100.0))
            glow.fill((*pa.BOSS_BULLET_COLOR, glow_alpha))
            surface.blit(glow, (r.x - 2, r.y - 2))
        else:
            pygame.draw.rect(surface, pa.ENEMY_BULLET_CORE, r)
            pygame.draw.rect(surface, pa.ENEMY_BULLET_TIP,
                             (r.x, r.bottom - px, r.width, px))
            pygame.draw.rect(surface, pa.WHITE,
                             (r.centerx - 1, r.top, 2, px))


class Enemy:
    """敌机类 - 像素风格精灵"""

    TYPES = {
        "small": (32, 32, 6, (220, 90, 90)),
        "medium": (40, 40, 4, (200, 70, 70)),
        "large": (52, 52, 2, (180, 50, 50)),
    }

    def __init__(self, screen_width: int, etype: str = "medium"):
        w, h, speed, color = self.TYPES[etype]
        self.width = w
        self.height = h
        self.speed = speed
        self.etype = etype
        x = random.randint(0, max(0, screen_width - w))
        y = -h
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.points = {"small": 2, "medium": 1, "large": 3}.get(etype, 1)
        self.fire_timer = random.randint(0, 50)

    def update(self) -> None:
        self.rect.y += self.speed
        self.fire_timer += 1

    def is_off_screen(self, screen_height: int) -> bool:
        return self.rect.top > screen_height

    def draw(self, surface: pygame.Surface) -> None:
        sprite = pa.enemy_sprite(self.etype)
        scaled = pygame.transform.scale(sprite, (self.rect.width, self.rect.height))
        surface.blit(scaled, self.rect)


class PowerUp:
    """道具 - 像素风格带脉冲动画"""

    def __init__(self, x: int, y: int, ptype: str, speed: float = 2):
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        self.ptype = ptype
        self.speed = speed

    def update(self) -> None:
        self.rect.y += self.speed

    def is_off_screen(self, screen_height: int) -> bool:
        return self.rect.top > screen_height

    def draw(self, surface: pygame.Surface) -> None:
        sprite = pa.powerup_sprite(self.ptype)
        scaled = pygame.transform.scale(sprite, (self.rect.width, self.rect.height))
        t = pygame.time.get_ticks() / 300.0
        pulse = math.sin(t) * 0.3 + 0.7
        glow_size = int(self.rect.width * (1 + pulse * 0.15))
        glow_offset = (glow_size - self.rect.width) // 2
        glow = pygame.transform.scale(sprite, (glow_size, glow_size))
        glow.set_alpha(int(80 * pulse))
        surface.blit(glow,
                     (self.rect.x - glow_offset, self.rect.y - glow_offset))
        surface.blit(scaled, self.rect)


class Boss:
    """Boss 敌机 - 像素风格大型精灵，会射击"""

    def __init__(self, screen_width: int, screen_height: int, level: int):
        self.width = 120
        self.height = 80
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.level = level
        self.max_hp = 25 + level * 8
        self.hp = self.max_hp
        x = (screen_width - self.width) // 2
        self.rect = pygame.Rect(x, -self.height, self.width, self.height)
        self.target_y = 60
        self.entering = True
        self.speed = 2 + level * 0.3
        self.direction = 1
        self.points = 20 + level * 5
        self.fire_timer = 0
        self.pattern_timer = 0

    def update(self) -> None:
        if self.entering:
            self.rect.y += 2
            if self.rect.y >= self.target_y:
                self.rect.y = self.target_y
                self.entering = False
            return

        self.fire_timer += 1
        self.pattern_timer += 1

        sway = math.sin(self.pattern_timer / 60.0) * 1.5
        self.rect.x += int(self.speed * self.direction + sway)
        if self.rect.right >= self.screen_width or self.rect.left <= 0:
            self.direction *= -1
        self.rect.x = max(0, min(self.screen_width - self.width, self.rect.x))

    def should_fire(self, interval: int) -> bool:
        return not self.entering and self.fire_timer >= interval

    def reset_fire_timer(self) -> None:
        self.fire_timer = 0

    def take_damage(self, amount: int = 1) -> None:
        self.hp = max(0, self.hp - amount)

    @property
    def is_dead(self) -> bool:
        return self.hp <= 0

    def draw(self, surface: pygame.Surface) -> None:
        frame = (pygame.time.get_ticks() // 200) % 2
        sprite = pa.boss_sprite(frame)
        scaled = pygame.transform.scale(sprite, (self.rect.width, self.rect.height))
        surface.blit(scaled, self.rect)

        bar_w = self.width + 20
        bar_h = pa.PX * 3
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.top - bar_h - pa.PX * 4
        if not self.entering:
            pa.draw_boss_hp_bar(surface, bar_x, bar_y, bar_w, bar_h,
                                self.hp / self.max_hp, pygame.time.get_ticks())

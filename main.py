"""
飞机大战 - 主程序入口（像素风格版 v2）
支持 PC 键盘操作 和 安卓触屏操作
"""
import math
import os
import random
import pygame
import sys

import pixel_art as pa
import settings
from sprites import (
    Boss, Bullet, Enemy, EnemyBullet, Explosion, FloatingText,
    HitSpark, Missile, MissileExplosion, Player, PowerUp,
    ScreenShake, StarBackground,
)
from utils import get_font

IS_ANDROID = "ANDROID_ROOT" in os.environ or "ANDROID_STORAGE" in os.environ

if IS_ANDROID:
    from touch_controls import TouchControls


def load_leaderboard() -> list[int]:
    try:
        with open(settings.LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            return [int(line.strip()) for line in f if line.strip()]
    except (FileNotFoundError, ValueError):
        return []


def save_leaderboard(scores: list[int]) -> None:
    try:
        with open(settings.LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            for s in scores[: settings.LEADERBOARD_SIZE]:
                f.write(str(s) + "\n")
    except OSError:
        pass


def add_to_leaderboard(score: int) -> list[int]:
    scores = load_leaderboard()
    scores.append(score)
    scores.sort(reverse=True)
    scores = scores[: settings.LEADERBOARD_SIZE]
    save_leaderboard(scores)
    return scores


def get_spawn_interval(score: int) -> int:
    step = score // settings.DIFFICULTY_SCORE_STEP
    interval = settings.INITIAL_SPAWN_INTERVAL - step * 4
    return max(settings.MIN_SPAWN_INTERVAL, interval)


def spawn_enemy(screen_width: int) -> Enemy:
    r = random.random()
    if r < 0.4:
        return Enemy(screen_width, "medium")
    if r < 0.75:
        return Enemy(screen_width, "small")
    return Enemy(screen_width, "large")


def spawn_formation(screen_width: int) -> list[Enemy]:
    """生成编队敌机"""
    pattern = random.choice(["v", "line", "diagonal"])
    etype = random.choice(["small", "medium"])
    count = random.randint(3, 5)
    enemies = []
    cx = random.randint(80, screen_width - 80)
    for i in range(count):
        e = Enemy(screen_width, etype)
        if pattern == "v":
            offset = (i - count // 2) * 40
            e.rect.x = max(0, min(screen_width - e.width, cx + offset))
            e.rect.y = -(abs(i - count // 2) * 30 + e.height)
        elif pattern == "line":
            spacing = screen_width // (count + 1)
            e.rect.x = spacing * (i + 1) - e.width // 2
            e.rect.y = -e.height - random.randint(0, 10)
        else:
            e.rect.x = max(0, min(screen_width - e.width, cx + i * 35))
            e.rect.y = -(i * 25 + e.height)
        enemies.append(e)
    return enemies


def spawn_powerup(x: int, y: int) -> PowerUp:
    ptype = random.choice(settings.POWERUP_TYPES)
    return PowerUp(x, y, ptype, settings.POWERUP_SPEED)


def _draw_text_shadow(surface: pygame.Surface, font: pygame.font.Font,
                      text: str, color: tuple, x: int, y: int,
                      shadow_color: tuple = (0, 0, 0)) -> None:
    shadow = font.render(text, False, shadow_color)
    main = font.render(text, False, color)
    surface.blit(shadow, (x + 2, y + 2))
    surface.blit(main, (x, y))


def _draw_text_center(surface: pygame.Surface, font: pygame.font.Font,
                      text: str, color: tuple, y: int,
                      shadow: bool = True) -> None:
    main = font.render(text, False, color)
    x = settings.SCREEN_WIDTH // 2 - main.get_width() // 2
    if shadow:
        sh = font.render(text, False, (0, 0, 0))
        surface.blit(sh, (x + 2, y + 2))
    surface.blit(main, (x, y))


def run_start_screen(screen: pygame.Surface, font: pygame.font.Font,
                     clock: pygame.time.Clock, bg_grad: pygame.Surface,
                     stars: StarBackground, scanlines: pygame.Surface) -> tuple[bool, bool]:
    title_font = get_font(48)
    sub_font = get_font(20)
    info_font = get_font(16)
    selected = 0
    blink_timer = 0

    sw = settings.SCREEN_WIDTH
    scene_w, scene_h = sw - 40, 130
    scene_surf = pa.create_title_scene(scene_w, scene_h)

    prev_keys = pygame.key.get_pressed()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False, False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False, False
                if e.key == pygame.K_1 or e.key == pygame.K_KP1:
                    return True, False
                if e.key == pygame.K_2 or e.key == pygame.K_KP2:
                    return True, True
                if e.key == pygame.K_UP or e.key == pygame.K_w:
                    selected = 0
                if e.key == pygame.K_DOWN or e.key == pygame.K_s:
                    selected = 1
            if IS_ANDROID and e.type == pygame.FINGERDOWN:
                return True, False

        cur_keys = pygame.key.get_pressed()
        if cur_keys[pygame.K_1] and not prev_keys[pygame.K_1]:
            return True, False
        if cur_keys[pygame.K_2] and not prev_keys[pygame.K_2]:
            return True, True
        if cur_keys[pygame.K_w] and not prev_keys[pygame.K_w]:
            selected = 0
        if cur_keys[pygame.K_s] and not prev_keys[pygame.K_s]:
            selected = 1
        prev_keys = cur_keys

        stars.update()
        blink_timer += 1

        screen.blit(bg_grad, (0, 0))
        stars.draw(screen)

        _draw_text_center(screen, title_font, "飞 机 大 战", pa.CYAN, 15)
        _draw_text_center(screen, sub_font, "- PIXEL EDITION -", pa.LAVENDER, 68)

        scene_x = 20
        scene_y = 95
        pa.draw_panel(screen, scene_x, scene_y, scene_w, scene_h,
                      bg_color=(8, 12, 30), border_color=pa.BLUE)
        screen.blit(scene_surf, (scene_x, scene_y))
        pa.draw_pixel_border(screen, scene_x, scene_y, scene_w, scene_h, pa.BLUE)

        ctrl_y = 235
        if IS_ANDROID:
            ctrl_h = 280
            pa.draw_panel(screen, 20, ctrl_y, sw - 40, ctrl_h,
                          bg_color=(10, 10, 30), border_color=pa.DARK_BLUE)
            _draw_text_center(screen, sub_font, "=  操 作 说 明  =", pa.YELLOW, ctrl_y + 8)
            row_y = ctrl_y + 40
            for txt_str, clr in [
                ("拖动屏幕 ── 移动飞机", pa.LIGHT_BLUE),
                ("自动射击 ── 无需操作", pa.LIGHT_GREEN),
                ("右下按钮 ── 发射导弹", pa.ORANGE),
            ]:
                _draw_text_center(screen, info_font, txt_str, clr, row_y)
                row_y += 26
            pygame.draw.rect(screen, pa.DARK_BLUE, (40, row_y + 4, sw - 80, 1))
            row_y += 14
            _draw_text_center(screen, info_font, "=  道 具 说 明  =", pa.YELLOW, row_y)
            row_y += 24
            pu_x = 45
            for ptype, color, desc in [
                ("bullet", pa.GREEN, "绿色 ── 火力升级"),
                ("life",   pa.RED,   "红色 ── 生命恢复"),
                ("morph",  pa.ORANGE, "黄色 ── 机甲切换"),
                ("shield", pa.SHIELD_BLUE, "蓝色 ── 能量护盾"),
            ]:
                pygame.draw.rect(screen, color, (pu_x, row_y + 2, 10, 10))
                pygame.draw.rect(screen, pa.WHITE, (pu_x, row_y + 2, 10, 10), 1)
                txt = info_font.render(desc, False, pa.LIGHT_GRAY)
                screen.blit(txt, (pu_x + 16, row_y))
                row_y += 22
            pygame.draw.rect(screen, pa.DARK_BLUE, (40, row_y + 4, sw - 80, 1))
            row_y += 12
            _draw_text_shadow(screen, info_font,
                              "每 80 分出现 Boss · 击败 Boss 进入下一关",
                              pa.DARK_GRAY, 45, row_y)
            menu_y = 540
            if (blink_timer // 25) % 2 == 0:
                _draw_text_center(screen, font, "点击屏幕开始游戏",
                                  pa.YELLOW, menu_y)
        else:
            ctrl_h = 280
            pa.draw_panel(screen, 20, ctrl_y, sw - 40, ctrl_h,
                          bg_color=(10, 10, 30), border_color=pa.DARK_BLUE)
            _draw_text_center(screen, sub_font, "=  操 作 说 明  =", pa.YELLOW, ctrl_y + 8)
            col_left = 40
            col_right = sw // 2 + 10
            row_y = ctrl_y + 38
            _draw_text_shadow(screen, info_font, "── 玩家 1 ──", pa.LIGHT_BLUE, col_left, row_y)
            _draw_text_shadow(screen, info_font, "── 玩家 2 ──", pa.LIGHT_GREEN, col_right, row_y)
            row_y += 24
            for label, val1, val2 in [
                ("移动", "W A S D", "↑ ↓ ← →"),
                ("射击", "J", "小键盘 1"),
                ("导弹", "K", "小键盘 2"),
            ]:
                _draw_text_shadow(screen, info_font, f"{label}: {val1}",
                                  pa.LIGHT_GRAY, col_left, row_y)
                _draw_text_shadow(screen, info_font, f"{label}: {val2}",
                                  pa.LIGHT_GRAY, col_right, row_y)
                row_y += 22
            pygame.draw.rect(screen, pa.DARK_BLUE, (40, row_y + 4, sw - 80, 1))
            row_y += 14
            _draw_text_center(screen, info_font, "=  道 具 说 明  =", pa.YELLOW, row_y)
            row_y += 24
            pu_x = 45
            for ptype, color, desc in [
                ("bullet", pa.GREEN, "绿色 ── 火力升级（连射/激光/等离子/雷电）"),
                ("life",   pa.RED,   "红色 ── 生命恢复（+1 HP）"),
                ("morph",  pa.ORANGE, "黄色 ── 机甲切换（标准/疾速/重甲）"),
                ("shield", pa.SHIELD_BLUE, "蓝色 ── 能量护盾（抵挡一次伤害）"),
            ]:
                pygame.draw.rect(screen, color, (pu_x, row_y + 2, 10, 10))
                pygame.draw.rect(screen, pa.WHITE, (pu_x, row_y + 2, 10, 10), 1)
                txt = info_font.render(desc, False, pa.LIGHT_GRAY)
                screen.blit(txt, (pu_x + 16, row_y))
                row_y += 22
            pygame.draw.rect(screen, pa.DARK_BLUE, (40, row_y + 4, sw - 80, 1))
            row_y += 12
            _draw_text_shadow(screen, info_font,
                              "每 80 分出现 Boss · 击败 Boss 进入下一关",
                              pa.DARK_GRAY, 45, row_y)
            menu_y = 530
            pa.draw_panel(screen, 20, menu_y, sw - 40, 90,
                          bg_color=(10, 10, 30), border_color=pa.BLUE)
            for i, (label, key_hint) in enumerate([("单人模式", "按 1"),
                                                    ("双人模式", "按 2")]):
                oy = menu_y + 12 + i * 34
                if i == selected:
                    color = pa.YELLOW
                    ind = "▸ " if (blink_timer // 20) % 2 == 0 else "  "
                else:
                    color = pa.LIGHT_GRAY
                    ind = "  "
                text = f"{ind}{label}  [{key_hint}]"
                _draw_text_center(screen, font, text, color, oy)
            _draw_text_center(screen, info_font, "[ ESC 退出 ]",
                              (55, 55, 75), menu_y + 90 + 8)

        screen.blit(scanlines, (0, 0))
        pygame.display.flip()
        clock.tick(settings.FPS)


def run_game_over(
    screen: pygame.Surface, font: pygame.font.Font, score: int,
    leaderboard: list[int], clock: pygame.time.Clock,
    bg_grad: pygame.Surface, scanlines: pygame.Surface,
    total_kills: int = 0, max_combo: int = 0, level: int = 1,
) -> bool:
    big_font = get_font(42)
    sm_font = get_font(20)
    rank_font = get_font(17)
    stat_font = get_font(16)
    label_font = get_font(14)
    blink = 0
    stars = StarBackground(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, 60)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return False
                if e.key in (pygame.K_KP1, pygame.K_KP_ENTER,
                             pygame.K_RETURN, pygame.K_j):
                    return True
            if IS_ANDROID and e.type == pygame.FINGERDOWN:
                return True
        _kp = pygame.key.get_pressed()
        if _kp[pygame.K_RETURN] or _kp[pygame.K_j] or _kp[pygame.K_KP1]:
            return True

        blink += 1
        stars.update()
        screen.blit(bg_grad, (0, 0))
        stars.draw(screen)

        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT

        pw, ph = 330, 0
        px_l = sw // 2 - pw // 2

        cy = 55
        _draw_text_center(screen, big_font, "GAME OVER", pa.RED, cy)

        cy += 58
        score_panel_h = 50
        pa.draw_panel(screen, px_l, cy, pw, score_panel_h,
                      bg_color=(25, 8, 12), border_color=pa.DEEP_RED)
        _draw_text_center(screen, font, f"得分: {score}", pa.YELLOW, cy + 10)
        cy += score_panel_h + 10

        stat_panel_h = 80
        pa.draw_panel(screen, px_l, cy, pw, stat_panel_h,
                      bg_color=(12, 12, 30), border_color=pa.DARK_BLUE)
        _draw_text_center(screen, label_font, "─── 战斗统计 ───",
                          pa.DARK_GRAY, cy + 4)
        stat_y = cy + 22
        stat_col1 = px_l + 30
        stat_col2 = px_l + pw // 2 + 20
        _draw_text_shadow(screen, stat_font, f"关卡: {level}",
                          pa.CYAN, stat_col1, stat_y)
        _draw_text_shadow(screen, stat_font, f"击杀: {total_kills}",
                          pa.LIGHT_GREEN, stat_col2, stat_y)
        stat_y += 24
        combo_color = pa.GOLD if max_combo >= 8 else pa.ORANGE if max_combo >= 5 else pa.LIGHT_GRAY
        combo_str = f"最大连杀: {max_combo}"
        ct = stat_font.render(combo_str, False, combo_color)
        screen.blit(ct, (sw // 2 - ct.get_width() // 2, stat_y))
        cy += stat_panel_h + 10

        lb_count = min(len(leaderboard), 5)
        lb_panel_h = 32 + lb_count * 26 + 8
        pa.draw_panel(screen, px_l, cy, pw, lb_panel_h,
                      bg_color=(12, 8, 18), border_color=pa.DARK_PURPLE)
        _draw_text_center(screen, sm_font, "排 行 榜", pa.ORANGE, cy + 6)
        entry_y = cy + 34
        for i, s in enumerate(leaderboard[:5], 1):
            medal = ["①", "②", "③"][i - 1] if i <= 3 else f" {i}."
            color = pa.YELLOW if i <= 3 else pa.LIGHT_GRAY
            entry = f"{medal}  {s}"
            if s == score and i == next(
                (j for j, v in enumerate(leaderboard[:5], 1) if v == score), -1
            ):
                t = pygame.time.get_ticks()
                color = pa.GOLD if (t // 300) % 2 == 0 else pa.YELLOW
                entry += "  ← NEW"
            txt = rank_font.render(entry, False, color)
            screen.blit(txt, (sw // 2 - txt.get_width() // 2, entry_y))
            entry_y += 26
        cy += lb_panel_h + 16

        if (blink // 28) % 2 == 0:
            prompt = "点击屏幕再来一局" if IS_ANDROID else "按 回车 / J 再来一局"
            _draw_text_center(screen, sm_font, prompt, pa.WHITE, cy)
        cy += 28
        if not IS_ANDROID:
            _draw_text_center(screen, label_font,
                              "[ ESC 退出 ]", (55, 55, 75), cy)

        screen.blit(scanlines, (0, 0))
        pygame.display.flip()
        clock.tick(settings.FPS)


def fire_bullets(player: Player, bullets: list, kills: int = 0,
                 level: int = 1) -> None:
    by = player.rect.top
    cx = player.rect.centerx
    bt = player.bullet_type
    style = player.bullet_style
    if bt == "normal" and kills >= settings.DOUBLE_SHOT_UNLOCK:
        bt = "double"

    spd = 13
    w, h = (3, 18) if style == "laser" else (8, 14) if style == "plasma" else (5, 14) if style == "electric" else (4, 12)

    level_bonus = min(level - 1, 5)

    if bt == "fan10":
        count = 10 + level_bonus
        half_angle = 0.55 + level_bonus * 0.03
        for i in range(count):
            angle = -math.pi / 2 + (-half_angle + 2 * half_angle * i / max(1, count - 1))
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            bullets.append(Bullet(cx - w // 2, by, w, h, spd, style, vx=vx, vy=vy))
    elif bt == "fan7":
        count = 7 + level_bonus
        half_angle = 0.45 + level_bonus * 0.02
        for i in range(count):
            angle = -math.pi / 2 + (-half_angle + 2 * half_angle * i / max(1, count - 1))
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            bullets.append(Bullet(cx - w // 2, by, w, h, spd, style, vx=vx, vy=vy))
    elif bt == "fan5":
        count = 5 + level_bonus
        half_angle = 0.35 + level_bonus * 0.02
        for i in range(count):
            angle = -math.pi / 2 + (-half_angle + 2 * half_angle * i / max(1, count - 1))
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            bullets.append(Bullet(cx - w // 2, by, w, h, spd, style, vx=vx, vy=vy))
    elif bt == "triple":
        count = 3 + min(level_bonus, 3)
        half_angle = 0.2 + level_bonus * 0.015
        for i in range(count):
            angle = -math.pi / 2 + (-half_angle + 2 * half_angle * i / max(1, count - 1))
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            bullets.append(Bullet(cx - w // 2, by, w, h, spd, style, vx=vx, vy=vy))
    elif bt == "double":
        for ox in (-8, 4):
            bullets.append(Bullet(cx + ox - w // 2, by, w, h, spd, style))
        if level_bonus >= 2:
            for angle_off in [-0.15, 0.15]:
                angle = -math.pi / 2 + angle_off
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
                bullets.append(Bullet(cx - w // 2, by, w, h, spd, style, vx=vx, vy=vy))
    else:
        bullets.append(Bullet(cx - w // 2, by, w, h, spd, style))


def _boss_fire(boss: Boss, enemy_bullets: list, players: list[Player],
               lives_list: list[int], level: int) -> None:
    """Boss发射子弹 — 根据关卡使用不同弹幕模式"""
    alive = [(i, p) for i, p in enumerate(players) if lives_list[i] > 0]
    if not alive:
        return

    _, target = random.choice(alive)
    dx = target.rect.centerx - boss.rect.centerx
    dy = target.rect.centery - boss.rect.bottom
    base_angle = math.atan2(dy, dx)
    spd = settings.BOSS_BULLET_SPEED + level * 0.25
    phase = boss.attack_phase

    def _fan(count, spread, aimed=True):
        ang = base_angle if aimed else math.pi / 2
        for i in range(count):
            offset = (i - (count - 1) / 2) * (spread / max(1, count - 1))
            a = ang + offset
            enemy_bullets.append(EnemyBullet(
                boss.rect.centerx, boss.rect.bottom,
                vx=math.cos(a) * spd, vy=math.sin(a) * spd, is_boss=True))

    def _circle(count, speed_mult=1.0):
        for i in range(count):
            a = 2 * math.pi * i / count
            enemy_bullets.append(EnemyBullet(
                boss.rect.centerx, boss.rect.centery,
                vx=math.cos(a) * spd * speed_mult,
                vy=math.sin(a) * spd * speed_mult, is_boss=True))

    def _spiral(count, offset_angle=0):
        for i in range(count):
            a = offset_angle + (2 * math.pi * i / count)
            enemy_bullets.append(EnemyBullet(
                boss.rect.centerx, boss.rect.centery,
                vx=math.cos(a) * spd * 0.8,
                vy=math.sin(a) * spd * 0.8, is_boss=True))

    if level == 1:
        _fan(3 + phase % 2, 0.6)
    elif level == 2:
        if phase % 2 == 0:
            _fan(5, 0.8)
        else:
            _circle(8)
    elif level == 3:
        if phase % 3 == 0:
            _fan(7, 1.0)
        elif phase % 3 == 1:
            _circle(10)
        else:
            _fan(5, 0.5)
            for ox in [-30, 30]:
                enemy_bullets.append(EnemyBullet(
                    boss.rect.centerx + ox, boss.rect.bottom,
                    vx=0, vy=spd * 1.2, is_boss=True))
    elif level == 4:
        if phase % 3 == 0:
            _fan(9, 1.2)
        elif phase % 3 == 1:
            _circle(14)
        else:
            _spiral(10, boss.pattern_timer * 0.05)
    elif level == 5:
        if phase % 4 == 0:
            _fan(11, 1.4)
        elif phase % 4 == 1:
            _circle(16, 0.9)
            _circle(8, 1.3)
        elif phase % 4 == 2:
            _spiral(12, boss.pattern_timer * 0.08)
        else:
            _fan(7, 0.8)
            for ox in [-40, -20, 20, 40]:
                enemy_bullets.append(EnemyBullet(
                    boss.rect.centerx + ox, boss.rect.bottom,
                    vx=0, vy=spd * 1.1, is_boss=True))
    else:
        if phase % 4 == 0:
            _fan(13 + level, 1.6)
        elif phase % 4 == 1:
            _circle(18 + level, 0.85)
            _circle(10, 1.4)
        elif phase % 4 == 2:
            _spiral(14 + level, boss.pattern_timer * 0.1)
            _fan(5, 0.4)
        else:
            _circle(20 + level)
            for ox in [-50, -25, 0, 25, 50]:
                enemy_bullets.append(EnemyBullet(
                    boss.rect.centerx + ox, boss.rect.bottom,
                    vx=ox * 0.02, vy=spd * 1.3, is_boss=True))


def main() -> None:
    pygame.init()
    if not IS_ANDROID:
        try:
            pygame.key.stop_text_input()
        except AttributeError:
            pass
    flags = pygame.SCALED | pygame.FULLSCREEN if IS_ANDROID else 0
    screen = pygame.display.set_mode(
        (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), flags)
    pygame.display.set_caption(settings.WINDOW_TITLE + " [Pixel Edition]")

    font = get_font(settings.SCORE_FONT_SIZE)
    hud_font = get_font(20)
    clock = pygame.time.Clock()

    bg_gradient = pa.create_bg_gradient(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    scanlines = pa.create_scanlines(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
    stars = StarBackground(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

    render_surf = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))

    game_running = True

    while game_running:
        start, two_player = run_start_screen(screen, font, clock,
                                              bg_gradient, stars, scanlines)
        if not start:
            break

        pygame.event.clear()
        pygame.time.delay(80)

        players = [
            Player(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, 1, two_player),
        ]
        if two_player:
            players.append(Player(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, 2, two_player))
            players[0].rect.x = settings.SCREEN_WIDTH // 4 - 25
            players[1].rect.x = settings.SCREEN_WIDTH * 3 // 4 - 25

        for p in players:
            p.invincible = True
            p.invincible_timer = settings.INVINCIBILITY_FRAMES

        bullets: list[Bullet] = []
        enemy_bullets: list[EnemyBullet] = []
        enemies: list[Enemy] = []
        explosions: list[Explosion] = []
        missiles: list[tuple[Missile, int]] = []
        powerups: list[PowerUp] = []
        floating_texts: list[FloatingText] = []
        hit_sparks: list[HitSpark] = []
        boss: Boss | None = None

        score = 0
        kills = 0
        total_kills = 0
        level = 1
        lives_list = [settings.PLAYER_LIVES] * len(players)
        fire_cooldowns = [0] * len(players)
        missile_cooldowns = [0] * len(players)
        enemy_spawn_timer = 0
        formation_timer = 0
        keys_pressed: set[int] = set()

        combo_count = 0
        combo_timer = 0
        max_combo = 0
        shake = ScreenShake()

        boss_warning_timer = 0
        boss_warning_active = False
        level_clear_timer = 0

        touch: "TouchControls | None" = None
        if IS_ANDROID:
            touch = TouchControls(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

        SCN_W, SCN_A, SCN_S, SCN_D = 26, 4, 22, 7
        SCN_KP1, SCN_KP2 = 89, 90
        SCN_J, SCN_K = 13, 14
        SCN_LEFT, SCN_RIGHT, SCN_UP, SCN_DOWN = 80, 79, 82, 81

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    game_running = False
                elif event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION,
                                    pygame.FINGERUP):
                    if touch is not None and lives_list[0] > 0:
                        touch.handle_event(
                            event,
                            player_cx=float(players[0].rect.centerx),
                            player_cy=float(players[0].rect.centery),
                        )
                elif event.type == pygame.KEYDOWN:
                    scn = getattr(event, "scancode", -1)
                    keys_pressed.add(scn if scn >= 0 else event.key)
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    for i, p in enumerate(players):
                        if lives_list[i] <= 0:
                            continue
                        if p.player_id == 1:
                            fire_ok = (event.key == pygame.K_j or scn == SCN_J) and fire_cooldowns[i] <= 0
                            missile_ok = (event.key == pygame.K_k or scn == SCN_K) and missile_cooldowns[i] <= 0
                        else:
                            fire_ok = (event.key == pygame.K_KP1 or scn == SCN_KP1) and fire_cooldowns[i] <= 0
                            missile_ok = (event.key == pygame.K_KP2 or scn == SCN_KP2) and missile_cooldowns[i] <= 0
                        if fire_ok:
                            fire_bullets(p, bullets, kills, level)
                            fire_cooldowns[i] = settings.FIRE_COOLDOWN
                        if missile_ok:
                            m = Missile(p.rect.centerx, p.rect.top, settings.MISSILE_SPEED)
                            missiles.append((m, i))
                            missile_cooldowns[i] = settings.MISSILE_COOLDOWN
                elif event.type == pygame.KEYUP:
                    scn = getattr(event, "scancode", -1)
                    keys_pressed.discard(scn if scn >= 0 else event.key)

            if not running:
                break

            for i in range(len(fire_cooldowns)):
                if fire_cooldowns[i] > 0:
                    fire_cooldowns[i] -= 1
                if missile_cooldowns[i] > 0:
                    missile_cooldowns[i] -= 1

            if combo_timer > 0:
                combo_timer -= 1
                if combo_timer <= 0:
                    combo_count = 0

            shake.update()

            _kp = pygame.key.get_pressed()
            def _key(k, scn):
                return scn in keys_pressed or _kp[k]
            keys = type("Keys", (), {
                "__getitem__": lambda s, k: (
                    _key(pygame.K_LEFT, SCN_LEFT) if k == pygame.K_LEFT else
                    _key(pygame.K_RIGHT, SCN_RIGHT) if k == pygame.K_RIGHT else
                    _key(pygame.K_UP, SCN_UP) if k == pygame.K_UP else
                    _key(pygame.K_DOWN, SCN_DOWN) if k == pygame.K_DOWN else
                    _key(pygame.K_w, SCN_W) if k == pygame.K_w else
                    _key(pygame.K_a, SCN_A) if k == pygame.K_a else
                    _key(pygame.K_s, SCN_S) if k == pygame.K_s else
                    _key(pygame.K_d, SCN_D) if k == pygame.K_d else False
                )
            })()
            for i, p in enumerate(players):
                if lives_list[i] > 0:
                    if touch is not None and i == 0 and touch.target_x is not None:
                        p.update(touch_target=(touch.target_x, touch.target_y))
                    else:
                        p.update(keys)

            if touch is not None:
                if lives_list[0] > 0 and fire_cooldowns[0] <= 0:
                    fire_bullets(players[0], bullets, kills, level)
                    fire_cooldowns[0] = settings.FIRE_COOLDOWN
                if touch.consume_missile() and missile_cooldowns[0] <= 0:
                    m = Missile(players[0].rect.centerx, players[0].rect.top,
                                settings.MISSILE_SPEED)
                    missiles.append((m, 0))
                    missile_cooldowns[0] = settings.MISSILE_COOLDOWN
            else:
                for i, p in enumerate(players):
                    if lives_list[i] <= 0:
                        continue
                    if p.player_id == 1:
                        fire_held = _kp[pygame.K_j]
                        missile_held = _kp[pygame.K_k]
                    else:
                        fire_held = _kp[pygame.K_KP1]
                        missile_held = _kp[pygame.K_KP2]
                    if fire_held and fire_cooldowns[i] <= 0:
                        fire_bullets(p, bullets, kills, level)
                        fire_cooldowns[i] = settings.FIRE_COOLDOWN
                    if missile_held and missile_cooldowns[i] <= 0:
                        m = Missile(p.rect.centerx, p.rect.top, settings.MISSILE_SPEED)
                        missiles.append((m, i))
                        missile_cooldowns[i] = settings.MISSILE_COOLDOWN

            stars.update()

            if level_clear_timer > 0:
                level_clear_timer -= 1
                if level_clear_timer <= 0:
                    level += 1

            if boss_warning_active:
                boss_warning_timer -= 1
                if boss_warning_timer <= 0:
                    boss_warning_active = False
                    boss = Boss(settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT, level)
                    shake.trigger(6, 15)
            elif boss:
                boss.update()
                fire_interval = max(20, settings.BOSS_FIRE_INTERVAL - level * 3)
                if boss.should_fire(fire_interval):
                    boss.reset_fire_timer()
                    _boss_fire(boss, enemy_bullets, players, lives_list, level)
            elif level_clear_timer <= 0:
                if score >= level * settings.BOSS_SCORE_THRESHOLD:
                    boss_warning_active = True
                    boss_warning_timer = 120

            if not boss and not boss_warning_active and level_clear_timer <= 0:
                interval = get_spawn_interval(score + level * 5)
                enemy_spawn_timer += 1
                if enemy_spawn_timer >= interval:
                    enemies.append(spawn_enemy(settings.SCREEN_WIDTH))
                    enemy_spawn_timer = 0

                formation_timer += 1
                if formation_timer >= 400 + random.randint(0, 200):
                    enemies.extend(spawn_formation(settings.SCREEN_WIDTH))
                    formation_timer = 0

            for bullet in bullets[:]:
                bullet.update()
                if bullet.is_off_screen(settings.SCREEN_HEIGHT):
                    bullets.remove(bullet)

            for enemy in enemies[:]:
                enemy.update()
                if enemy.is_off_screen(settings.SCREEN_HEIGHT):
                    enemies.remove(enemy)
                if enemy.fire_timer >= settings.ENEMY_FIRE_INTERVAL:
                    enemy.fire_timer = 0
                    enemy_bullets.append(EnemyBullet(
                        enemy.rect.centerx, enemy.rect.bottom,
                        settings.ENEMY_BULLET_SPEED,
                    ))

            for eb in enemy_bullets[:]:
                eb.update()
                if eb.is_off_screen(settings.SCREEN_HEIGHT):
                    enemy_bullets.remove(eb)

            for pu in powerups[:]:
                pu.update()
                if pu.is_off_screen(settings.SCREEN_HEIGHT):
                    powerups.remove(pu)

            missiles_to_remove: list[int] = []
            for idx, (m, _) in enumerate(missiles):
                if m.update(settings.SCREEN_HEIGHT):
                    missiles_to_remove.append(idx)
            for idx in reversed(missiles_to_remove):
                m, _ = missiles.pop(idx)
                ex, ey = m.explosion_pos
                explosions.append(MissileExplosion(ex, ey, settings.MISSILE_RADIUS))
                shake.trigger(8, 18)
                r2 = settings.MISSILE_RADIUS ** 2
                for enemy in enemies[:]:
                    dx = enemy.rect.centerx - ex
                    dy = enemy.rect.centery - ey
                    if dx * dx + dy * dy <= r2:
                        enemies.remove(enemy)
                        combo_count += 1
                        combo_timer = settings.COMBO_WINDOW
                        max_combo = max(max_combo, combo_count)
                        multiplier = min(combo_count, settings.COMBO_MAX)
                        pts = enemy.points * multiplier
                        score += pts
                        kills += 1
                        total_kills += 1
                        explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery, 16))
                        _add_score_text(floating_texts, enemy.rect.centerx,
                                        enemy.rect.centery, pts, multiplier)
                        if random.random() < settings.POWERUP_DROP_CHANCE:
                            powerups.append(spawn_powerup(enemy.rect.centerx, enemy.rect.centery))
                for eb in enemy_bullets[:]:
                    dx = eb.rect.centerx - ex
                    dy = eb.rect.centery - ey
                    if dx * dx + dy * dy <= r2:
                        enemy_bullets.remove(eb)
                if boss:
                    dx = boss.rect.centerx - ex
                    dy = boss.rect.centery - ey
                    if dx * dx + dy * dy <= r2:
                        boss.take_damage(settings.MISSILE_BOSS_DAMAGE)
                        shake.trigger(6, 12)
                        for _ in range(5):
                            explosions.append(Explosion(
                                boss.rect.centerx + random.randint(-30, 30),
                                boss.rect.centery,
                                18,
                            ))

            for exp in explosions[:]:
                if exp.update():
                    explosions.remove(exp)

            for spark in hit_sparks[:]:
                if spark.update():
                    hit_sparks.remove(spark)

            for ft in floating_texts[:]:
                if ft.update():
                    floating_texts.remove(ft)

            bullets_to_remove: set[Bullet] = set()
            enemies_to_remove: set[Enemy] = set()
            if boss:
                for bullet in bullets:
                    if pygame.sprite.collide_rect(bullet, boss):
                        bullets_to_remove.add(bullet)
                        boss.take_damage(1)
                        hit_sparks.append(HitSpark(bullet.rect.centerx, bullet.rect.centery))
            else:
                for bullet in bullets:
                    for enemy in enemies:
                        if pygame.sprite.collide_rect(bullet, enemy):
                            bullets_to_remove.add(bullet)
                            enemies_to_remove.add(enemy)
                            explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
                            hit_sparks.append(HitSpark(bullet.rect.centerx, bullet.rect.centery))
                            if random.random() < settings.POWERUP_DROP_CHANCE:
                                powerups.append(spawn_powerup(enemy.rect.centerx, enemy.rect.centery))
                            break
            for bullet in bullets_to_remove:
                bullets.remove(bullet)
            for enemy in enemies_to_remove:
                enemies.remove(enemy)
                combo_count += 1
                combo_timer = settings.COMBO_WINDOW
                max_combo = max(max_combo, combo_count)
                multiplier = min(combo_count, settings.COMBO_MAX)
                pts = enemy.points * multiplier
                score += pts
                kills += 1
                total_kills += 1
                _add_score_text(floating_texts, enemy.rect.centerx,
                                enemy.rect.centery, pts, multiplier)

            if boss and boss.is_dead:
                bx, by = boss.rect.centerx, boss.rect.centery
                for _ in range(12):
                    explosions.append(Explosion(
                        bx + random.randint(-50, 50),
                        by + random.randint(-35, 35),
                        random.randint(18, 28),
                    ))
                shake.trigger(12, 25)
                score += boss.points
                floating_texts.append(FloatingText(
                    bx, by, f"BOSS +{boss.points}", pa.GOLD, 60, 22))
                boss = None
                level_clear_timer = 90

            for pu in powerups[:]:
                for i, p in enumerate(players):
                    if lives_list[i] <= 0:
                        continue
                    if pygame.sprite.collide_rect(p, pu):
                        if pu.ptype == "bullet":
                            levels = [
                                ("normal", "normal"), ("double", "normal"),
                                ("triple", "normal"), ("fan5", "normal"),
                                ("fan7", "normal"), ("fan7", "laser"),
                                ("fan10", "normal"), ("fan10", "laser"),
                                ("fan10", "plasma"), ("fan10", "electric"),
                            ]
                            cur = (p.bullet_type, p.bullet_style)
                            idx = next((j for j, L in enumerate(levels) if L == cur), 0)
                            nxt = levels[min(idx + 1, len(levels) - 1)]
                            if idx >= len(levels) - 1:
                                nxt = levels[6]
                            p.bullet_type, p.bullet_style = nxt
                            names = {"double": "双发!", "triple": "三连!",
                                     "fan5": "五连扇!", "fan7": "七连扇!",
                                     "fan10": "十连暴风!"}
                            label = names.get(nxt[0], "火力升级!")
                            if nxt[1] != "normal":
                                sn = {"laser": "激光", "plasma": "等离子", "electric": "雷电"}
                                label = sn.get(nxt[1], "") + "!" 
                            floating_texts.append(FloatingText(
                                p.rect.centerx, p.rect.top - 10,
                                label, pa.GREEN, 40, 18))
                        elif pu.ptype == "life":
                            lives_list[i] += 1
                            floating_texts.append(FloatingText(
                                p.rect.centerx, p.rect.top - 10,
                                "+1 HP", pa.RED, 40, 16))
                        elif pu.ptype == "morph":
                            forms = ["normal", "agile", "heavy"]
                            idx = forms.index(p.plane_form)
                            p.apply_form(forms[(idx + 1) % 3])
                            form_names = {"normal": "标准", "agile": "疾速", "heavy": "重甲"}
                            floating_texts.append(FloatingText(
                                p.rect.centerx, p.rect.top - 10,
                                form_names[p.plane_form], pa.ORANGE, 40, 16))
                        elif pu.ptype == "shield":
                            p.shield_timer = settings.SHIELD_DURATION
                            floating_texts.append(FloatingText(
                                p.rect.centerx, p.rect.top - 10,
                                "护盾!", pa.SHIELD_BLUE, 40, 16))
                        powerups.remove(pu)
                        break

            game_over = False
            for i, p in enumerate(players):
                if lives_list[i] > 0 and not p.invincible:
                    hit_taken = False
                    for eb in enemy_bullets[:]:
                        if pygame.sprite.collide_rect(p, eb):
                            enemy_bullets.remove(eb)
                            if p.shield_timer > 0:
                                p.shield_timer = 0
                                hit_sparks.append(HitSpark(
                                    eb.rect.centerx, eb.rect.centery, pa.SHIELD_BLUE))
                                floating_texts.append(FloatingText(
                                    p.rect.centerx, p.rect.top - 10,
                                    "护盾抵挡!", pa.SHIELD_BLUE, 35, 14))
                                shake.trigger(3, 6)
                            else:
                                lives_list[i] -= 1
                                shake.trigger(6, 12)
                                if lives_list[i] > 0:
                                    p.hit(settings.INVINCIBILITY_FRAMES)
                            hit_taken = True
                            break
                    if not hit_taken:
                        for enemy in enemies[:]:
                            if pygame.sprite.collide_rect(p, enemy):
                                enemies.remove(enemy)
                                explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
                                if p.shield_timer > 0:
                                    p.shield_timer = 0
                                    shake.trigger(3, 6)
                                else:
                                    lives_list[i] -= 1
                                    shake.trigger(6, 12)
                                    if lives_list[i] > 0:
                                        p.hit(settings.INVINCIBILITY_FRAMES)
                                hit_taken = True
                                break
                    if not hit_taken and boss and pygame.sprite.collide_rect(p, boss):
                        if p.shield_timer > 0:
                            p.shield_timer = 0
                            shake.trigger(3, 6)
                        else:
                            lives_list[i] -= 1
                            shake.trigger(6, 12)
                            if lives_list[i] > 0:
                                p.hit(settings.INVINCIBILITY_FRAMES)
            if all(l <= 0 for l in lives_list):
                game_over = True

            if game_over:
                leaderboard = add_to_leaderboard(score)
                if not run_game_over(screen, font, score, leaderboard, clock,
                                     bg_gradient, scanlines,
                                     total_kills, max_combo, level):
                    game_running = False
                break

            # ══════════════════════════════════════
            #  RENDER
            # ══════════════════════════════════════

            render_surf.blit(bg_gradient, (0, 0))

            tint_idx = (level - 1) % len(settings.LEVEL_TINTS)
            tint = settings.LEVEL_TINTS[tint_idx]
            tint_surf = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            tint_surf.fill((*tint, 35))
            render_surf.blit(tint_surf, (0, 0))

            stars.draw(render_surf)

            for exp in explosions:
                exp.draw(render_surf)
            for spark in hit_sparks:
                spark.draw(render_surf)
            for m, _ in missiles:
                m.draw(render_surf)
            for pu in powerups:
                pu.draw(render_surf)
            for i, p in enumerate(players):
                if lives_list[i] > 0:
                    p.draw(render_surf)
            for eb in enemy_bullets:
                eb.draw(render_surf)
            for enemy in enemies:
                enemy.draw(render_surf)
            if boss:
                boss.draw(render_surf)
            for bullet in bullets:
                bullet.draw(render_surf)
            for ft in floating_texts:
                ft.draw(render_surf)

            px = pa.PX

            _draw_text_shadow(render_surf, font,
                              f"SCORE {score}", pa.WHITE, 10, 8)
            _draw_text_shadow(render_surf, hud_font,
                              f"Lv.{level}", pa.CYAN, 12, 36)

            if combo_count >= 2:
                combo_color = pa.GOLD if combo_count >= 8 else pa.ORANGE if combo_count >= 5 else pa.YELLOW
                ticks = pygame.time.get_ticks()
                pulse = 1.0 + 0.1 * math.sin(ticks / 100.0)
                combo_text = f"COMBO x{combo_count}"
                combo_font = get_font(int(18 * pulse))
                _draw_text_shadow(render_surf, combo_font,
                                  combo_text, combo_color, 12, 58)

            if boss_warning_active:
                ticks = pygame.time.get_ticks()
                if (ticks // 100) % 2 == 0:
                    warn_font = get_font(36)
                    _draw_text_center(render_surf, warn_font,
                                      "⚠ WARNING ⚠", pa.RED,
                                      settings.SCREEN_HEIGHT // 2 - 40)
                flash_alpha = int(abs(math.sin(ticks / 80.0)) * 40)
                flash_surf = pygame.Surface(
                    (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surf.fill((255, 0, 0, flash_alpha))
                render_surf.blit(flash_surf, (0, 0))

            if boss:
                _draw_text_center(render_surf, font, "! BOSS !", pa.RED, 8)

            if level_clear_timer > 0:
                clear_font = get_font(32)
                alpha = min(255, level_clear_timer * 6)
                clear_text = f"LEVEL {level} CLEAR!"
                ct = clear_font.render(clear_text, False, pa.CYAN)
                ct.set_alpha(alpha)
                cx = settings.SCREEN_WIDTH // 2 - ct.get_width() // 2
                cy = settings.SCREEN_HEIGHT // 2 - 30
                shadow = clear_font.render(clear_text, False, (0, 0, 0))
                shadow.set_alpha(alpha)
                render_surf.blit(shadow, (cx + 2, cy + 2))
                render_surf.blit(ct, (cx, cy))

            for i, p in enumerate(players):
                lv = lives_list[i]
                color = pa.RED if p.player_id == 1 else pa.GREEN
                label_color = pa.LIGHT_BLUE if p.player_id == 1 else pa.LIGHT_GREEN
                y_off = 8 + i * 24
                label = f"P{p.player_id}"
                lbl_surf = hud_font.render(label, False, label_color)
                lbl_x = settings.SCREEN_WIDTH - settings.PLAYER_MAX_HP * (px * 5 + px) - lbl_surf.get_width() - 16
                render_surf.blit(lbl_surf, (lbl_x, y_off - 2))
                for j in range(settings.PLAYER_MAX_HP):
                    hx = lbl_x + lbl_surf.get_width() + 6 + j * (px * 5 + px)
                    if j < lv:
                        pa.draw_pixel_heart(render_surf, hx, y_off, color, px)
                    else:
                        pa.draw_pixel_heart(render_surf, hx, y_off, pa.DARK_GRAY, px)

            for i, p in enumerate(players):
                if lives_list[i] <= 0:
                    continue
                eff = "double" if (p.bullet_type == "normal" and kills >= settings.DOUBLE_SHOT_UNLOCK) else p.bullet_type
                tags = []
                bt_names = {"fan10": "十连", "fan7": "七连", "fan5": "五连",
                            "triple": "三发", "double": "双发"}
                if eff in bt_names:
                    tags.append(bt_names[eff])
                style_names = {"laser": "激光", "plasma": "等离子", "electric": "雷电"}
                if p.bullet_style != "normal":
                    tags.append(style_names.get(p.bullet_style, ""))
                if p.plane_form == "agile":
                    tags.append("疾")
                elif p.plane_form == "heavy":
                    tags.append("甲")
                if p.shield_timer > 0:
                    tags.append("盾")
                if tags:
                    tag_text = f"P{p.player_id}:{' '.join(tags)}"
                    _draw_text_shadow(render_surf, hud_font, tag_text,
                                      pa.GREEN, 10, settings.SCREEN_HEIGHT - 50 + i * 22)

            for i in range(len(players)):
                if lives_list[i] <= 0:
                    continue
                cd = missile_cooldowns[i]
                y_cd = settings.SCREEN_HEIGHT - 50 + i * 22
                if cd > 0:
                    ratio = 1 - cd / settings.MISSILE_COOLDOWN
                    bar_w = 60
                    bar_x = settings.SCREEN_WIDTH - bar_w - 10
                    pa.draw_pixel_bar(render_surf, bar_x, y_cd + 2, bar_w, px * 3,
                                      ratio, pa.ORANGE, (40, 20, 10), pa.PEACH)
                    _draw_text_shadow(render_surf, hud_font, "M",
                                      pa.ORANGE, bar_x - 18, y_cd - 2)
                else:
                    txt = hud_font.render("M:OK", False, pa.GREEN)
                    render_surf.blit(txt, (settings.SCREEN_WIDTH - txt.get_width() - 10, y_cd))

            if touch is not None:
                missile_ready = missile_cooldowns[0] <= 0 if lives_list[0] > 0 else False
                touch.draw(render_surf, hud_font, missile_ready)

            render_surf.blit(scanlines, (0, 0))

            shake_x, shake_y = shake.get_offset()
            screen.fill((0, 0, 0))
            screen.blit(render_surf, (shake_x, shake_y))

            pygame.display.flip()
            clock.tick(settings.FPS)

    pygame.quit()
    sys.exit()


def _add_score_text(floating_texts: list, x: int, y: int,
                    pts: int, multiplier: int) -> None:
    if multiplier >= 8:
        color = pa.GOLD
        size = 22
    elif multiplier >= 5:
        color = pa.CYAN
        size = 20
    elif multiplier >= 3:
        color = pa.ORANGE
        size = 18
    else:
        color = pa.YELLOW
        size = 16
    text = f"+{pts}"
    if multiplier > 1:
        text += f" x{multiplier}"
    floating_texts.append(FloatingText(x, y, text, color, 45, size))


if __name__ == "__main__":
    main()

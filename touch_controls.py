"""
触控控制模块 - 安卓移动端
触摸拖动控制飞机移动 + 自动射击 + 导弹按钮
"""
import math
import pygame


class TouchControls:
    """
    移动端触控方案:
    - 触摸并拖动: 飞机跟随手指移动(保持初始偏移，不会瞬移)
    - 自动射击: 玩家存活时持续开火
    - 导弹按钮: 右下角圆形按钮，点击发射导弹
    """

    def __init__(self, game_w: int, game_h: int):
        self.gw = game_w
        self.gh = game_h

        self.missile_x = game_w - 55
        self.missile_y = game_h - 65
        self.missile_r = 32

        self.move_finger: int | None = None
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.target_x: float | None = None
        self.target_y: float | None = None

        self.missile_tapped = False

        self._build_surfaces()

    def _build_surfaces(self) -> None:
        r = self.missile_r
        size = r * 2 + 6
        self.btn_normal = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.circle(self.btn_normal, (60, 160, 255, 45), (c, c), r)
        pygame.draw.circle(self.btn_normal, (80, 190, 255, 100), (c, c), r, 2)

        self.btn_active = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.btn_active, (80, 200, 255, 90), (c, c), r)
        pygame.draw.circle(self.btn_active, (130, 220, 255, 180), (c, c), r, 2)

        self.move_hint = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(self.move_hint, (255, 255, 255, 18), (60, 60), 55)
        pygame.draw.circle(self.move_hint, (255, 255, 255, 35), (60, 60), 55, 1)

    def begin_move(self, finger_id: int, finger_x: float, finger_y: float,
                   player_cx: float, player_cy: float) -> None:
        self.move_finger = finger_id
        self.offset_x = player_cx - finger_x
        self.offset_y = player_cy - finger_y
        self.target_x = player_cx
        self.target_y = player_cy

    def handle_event(self, event, player_cx: float = 0, player_cy: float = 0) -> bool:
        if event.type == pygame.FINGERDOWN:
            x = event.x * self.gw
            y = event.y * self.gh

            dx = x - self.missile_x
            dy = y - self.missile_y
            if dx * dx + dy * dy <= (self.missile_r * 1.6) ** 2:
                self.missile_tapped = True
                return True

            if self.move_finger is None:
                self.begin_move(event.finger_id, x, y, player_cx, player_cy)
                return True
            return False

        elif event.type == pygame.FINGERMOTION:
            if event.finger_id == self.move_finger:
                x = event.x * self.gw
                y = event.y * self.gh
                self.target_x = x + self.offset_x
                self.target_y = y + self.offset_y
                return True
            return False

        elif event.type == pygame.FINGERUP:
            if event.finger_id == self.move_finger:
                self.move_finger = None
                self.target_x = None
                self.target_y = None
                return True
            return False

        return False

    def consume_missile(self) -> bool:
        if self.missile_tapped:
            self.missile_tapped = False
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font,
             missile_ready: bool = True) -> None:
        if self.move_finger is not None and self.target_x is not None:
            mx = int(self.target_x - self.offset_x)
            my = int(self.target_y - self.offset_y)
            surface.blit(self.move_hint, (mx - 60, my - 60))

        btn = self.btn_normal if missile_ready else self.btn_active
        sz = btn.get_width()
        surface.blit(btn, (self.missile_x - sz // 2, self.missile_y - sz // 2))
        label = "导弹" if missile_ready else "CD"
        txt = font.render(label, False, (180, 220, 255))
        txt.set_alpha(160 if missile_ready else 80)
        surface.blit(txt, (self.missile_x - txt.get_width() // 2,
                           self.missile_y - txt.get_height() // 2))

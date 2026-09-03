import pygame
import math
from settings import *


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = PLAYER_SIZE
        self.speed = PLAYER_SPEED
        self.max_hp = PLAYER_MAX_HP
        self.hp = self.max_hp
        self.alive = True
        self.invincible_timer = 0
        self.xp = 0
        self.level = 1
        self.xp_to_next = XP_BASE
        self.total_kills = 0
        self.weapons = []
        self.armor = 0
        self.regen_rate = 0
        self.regen_timer = 0
        self.dash_timer = 0.0
        self.dash_cooldown = 0.0
        self.dash_dx = 0
        self.dash_dy = 0

    @property
    def rect(self):
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    def take_damage(self, amount):
        if self.invincible_timer > 0:
            return False
        actual = max(1, amount - self.armor)
        self.hp -= actual
        self.invincible_timer = PLAYER_INVINCIBLE_TIME
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return True

    def add_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(XP_BASE * (XP_GROWTH ** (self.level - 1)))
            leveled_up = True
        return leveled_up

    def start_dash(self, dx, dy):
        if self.dash_cooldown > 0 or self.dash_timer > 0:
            return False
        if dx == 0 and dy == 0:
            length = 1
        else:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
        self.dash_dx = dx
        self.dash_dy = dy
        self.dash_timer = DASH_DURATION
        self.dash_cooldown = DASH_COOLDOWN
        if DASH_INVINCIBLE:
            self.invincible_timer = max(self.invincible_timer, DASH_DURATION * 1000 + 50)
        return True

    def update(self, dt, keys):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt

        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.x += self.dash_dx * DASH_SPEED * dt
            self.y += self.dash_dy * DASH_SPEED * dt
        else:
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += 1

            if dx != 0 or dy != 0:
                length = math.sqrt(dx * dx + dy * dy)
                dx /= length
                dy /= length
                self.x += dx * self.speed * dt
                self.y += dy * self.speed * dt

        if self.invincible_timer > 0:
            self.invincible_timer -= dt * 1000

        if self.regen_rate > 0:
            self.regen_timer += dt
            if self.regen_timer >= 1.0:
                self.regen_timer -= 1.0
                self.hp = min(self.max_hp, self.hp + self.regen_rate)

    def draw(self, surface, camera_x, camera_y):
        # Render player to a temp surface to support opacity while dashing
        tmp = pygame.Surface((self.size + 4, self.size + 4), pygame.SRCALPHA)
        cx = self.size // 2 + 2
        cy = self.size // 2 + 2

        # Body
        pygame.draw.rect(
            tmp, CYAN,
            (cx - self.size // 2, cy - self.size // 2, self.size, self.size),
            border_radius=6,
        )
        # Inner highlight
        pygame.draw.rect(
            tmp, WHITE,
            (cx - self.size // 4, cy - self.size // 4, self.size // 2, self.size // 2),
            border_radius=4,
        )
        # Eyes
        eye_y = cy - 3
        pygame.draw.circle(tmp, BLACK, (int(cx - 5), int(eye_y)), 3)
        pygame.draw.circle(tmp, BLACK, (int(cx + 5), int(eye_y)), 3)
        pygame.draw.circle(tmp, WHITE, (int(cx - 4), int(eye_y - 1)), 1)
        pygame.draw.circle(tmp, WHITE, (int(cx + 6), int(eye_y - 1)), 1)

        # Reduce opacity to 75% while dashing
        if self.dash_timer > 0:
            tmp.set_alpha(190)

        surface.blit(tmp, (self.x - camera_x - 2, self.y - camera_y - 2))

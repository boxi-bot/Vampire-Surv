import pygame
import math
import random
from settings import *


ENEMY_TYPES = {
    "zombie": {
        "color": DARK_GREEN,
        "size": 22,
        "speed_mult": 1.0,
        "hp_mult": 1.0,
        "damage_mult": 1.0,
        "xp_mult": 1.0,
    },
    "bat": {
        "color": PURPLE,
        "size": 16,
        "speed_mult": 1.8,
        "hp_mult": 0.4,
        "damage_mult": 0.6,
        "xp_mult": 0.7,
    },
    "skeleton": {
        "color": LIGHT_GRAY,
        "size": 24,
        "speed_mult": 0.8,
        "hp_mult": 1.5,
        "damage_mult": 1.3,
        "xp_mult": 1.3,
    },
    "ghost": {
        "color": (150, 180, 255),
        "size": 20,
        "speed_mult": 1.2,
        "hp_mult": 0.8,
        "damage_mult": 0.9,
        "xp_mult": 1.1,
    },
    "brute": {
        "color": DARK_RED,
        "size": 34,
        "speed_mult": 0.5,
        "hp_mult": 3.0,
        "damage_mult": 2.0,
        "xp_mult": 2.5,
    },
}


class Enemy:
    def __init__(self, x, y, enemy_type, time_multiplier=1.0, diff=None):
        if diff is None:
            diff = {"hp_mult": 1.0, "dmg_mult": 1.0, "spd_mult": 1.0, "xp_mult": 1.0}
        info = ENEMY_TYPES.get(enemy_type, ENEMY_TYPES["zombie"])
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type
        self.size = info["size"]
        self.color = info["color"]
        self.speed = ENEMY_BASE_SPEED * info["speed_mult"] * diff["spd_mult"] * time_multiplier
        self.max_hp = int(ENEMY_BASE_HP * info["hp_mult"] * diff["hp_mult"] * time_multiplier)
        self.hp = self.max_hp
        self.damage = int(ENEMY_BASE_DAMAGE * info["damage_mult"] * diff["dmg_mult"] * max(1, time_multiplier * 0.5))
        self.xp_value = int(ENEMY_BASE_XP * info["xp_mult"] * diff["xp_mult"])
        self.alive = True
        self.hit_flash = 0

    @property
    def rect(self):
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2,
            self.size,
            self.size,
        )

    def take_damage(self, amount):
        self.hp -= amount
        self.hit_flash = 100
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def update(self, dt, player_x, player_y):
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx /= dist
            dy /= dist
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt

        if self.hit_flash > 0:
            self.hit_flash -= dt * 1000

    def draw(self, surface, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y

        color = WHITE if self.hit_flash > 0 else self.color

        # Body
        if self.enemy_type == "ghost":
            # Ghost: wavy bottom
            points = [
                (sx - self.size // 2, sy - self.size // 3),
                (sx + self.size // 2, sy - self.size // 3),
                (sx + self.size // 2, sy + self.size // 3),
                (sx + self.size // 4, sy + self.size // 5),
                (sx, sy + self.size // 3),
                (sx - self.size // 4, sy + self.size // 5),
            ]
            pygame.draw.polygon(surface, color, points)
        elif self.enemy_type == "bat":
            # Bat: diamond shape
            points = [
                (sx, sy - self.size // 2),
                (sx + self.size // 2, sy),
                (sx, sy + self.size // 2),
                (sx - self.size // 2, sy),
            ]
            pygame.draw.polygon(surface, color, points)
        elif self.enemy_type == "brute":
            # Brute: big rectangle
            pygame.draw.rect(
                surface, color,
                (sx - self.size // 2, sy - self.size // 2, self.size, self.size),
                border_radius=4,
            )
            # Angry eyes
            pygame.draw.rect(surface, RED, (sx - 8, sy - 6, 5, 3))
            pygame.draw.rect(surface, RED, (sx + 3, sy - 6, 5, 3))
        else:
            # Zombie/skeleton: circle
            pygame.draw.circle(surface, color, (int(sx), int(sy)), self.size // 2)
            # Eyes
            eye_color = RED if self.enemy_type == "zombie" else BLACK
            pygame.draw.circle(surface, eye_color, (int(sx - 4), int(sy - 3)), 2)
            pygame.draw.circle(surface, eye_color, (int(sx + 4), int(sy - 3)), 2)

        # HP bar for non-full-health enemies
        if self.hp < self.max_hp and self.enemy_type != "bat":
            bar_w = self.size + 6
            bar_h = 4
            bar_x = sx - bar_w // 2
            bar_y = sy - self.size // 2 - 8
            pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surface, RED, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))


def spawn_enemy(player_x, player_y, time_multiplier, diff=None):
    angle = random.uniform(0, 2 * math.pi)
    dist = ENEMY_SPAWN_DISTANCE + random.randint(200, 500)
    x = player_x + math.cos(angle) * dist
    y = player_y + math.sin(angle) * dist

    # Enemy type selection based on time
    type_weights = [
        ("zombie", 50),
        ("bat", max(0, 30 - time_multiplier * 2)),
        ("skeleton", min(30, time_multiplier * 5)),
        ("ghost", min(20, time_multiplier * 3)),
        ("brute", min(10, time_multiplier * 2)),
    ]
    total = sum(w for _, w in type_weights)
    roll = random.uniform(0, total)
    cumulative = 0
    chosen = "zombie"
    for etype, weight in type_weights:
        cumulative += weight
        if roll <= cumulative:
            chosen = etype
            break

    return Enemy(x, y, chosen, max(1.0, time_multiplier * 0.3 + 0.7), diff)

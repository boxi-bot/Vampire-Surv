import pygame
import math
from settings import *


class XPGem:
    def __init__(self, x, y, value):
        self.x = float(x)
        self.y = float(y)
        self.value = value
        self.alive = True
        self.size = max(3, min(8, value // 5 + 3))
        self.bob_offset = 0
        self.magnet_speed = 0

    def update(self, dt, player_x, player_y):
        self.bob_offset += dt * 3
        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < XP_MAGNET_RANGE:
            self.magnet_speed = min(self.magnet_speed + 800 * dt, XP_FLOAT_SPEED)
        if dist < XP_COLLECT_RANGE + self.size:
            return self.value

        if self.magnet_speed > 0 and dist > 0:
            dx /= dist
            dy /= dist
            self.x += dx * self.magnet_speed * dt
            self.y += dy * self.magnet_speed * dt

        return 0

    def draw(self, surface, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y + math.sin(self.bob_offset) * 2
        # Outer glow
        glow_size = self.size + 3
        glow_surf = pygame.Surface((glow_size * 4, glow_size * 4), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf, (50, 200, 50, 50),
            (glow_size * 2, glow_size * 2), glow_size * 2,
        )
        surface.blit(glow_surf, (sx - glow_size * 2, sy - glow_size * 2))
        # Gem
        pygame.draw.circle(surface, GREEN, (int(sx), int(sy)), self.size)
        pygame.draw.circle(surface, (180, 255, 180), (int(sx), int(sy)), max(1, self.size - 2))


class XPGemManager:
    def __init__(self):
        self.gems = []

    def spawn_gem(self, x, y, value):
        self.gems.append(XPGem(x, y, value))

    def update(self, dt, player_x, player_y):
        total_xp = 0
        for gem in self.gems:
            collected = gem.update(dt, player_x, player_y)
            if collected > 0:
                total_xp += collected
                gem.alive = False
        self.gems = [g for g in self.gems if g.alive]
        return total_xp

    def draw(self, surface, camera_x, camera_y):
        for gem in self.gems:
            gem.draw(surface, camera_x, camera_y)

import pygame
import math
import random
from settings import *


WEAPON_DEFS = {
    "wand": {
        "name": "Magic Wand",
        "color": CYAN,
        "damage": 10,
        "cooldown": 0.8,
        "speed": 400,
        "size": 6,
        "pierce": 0,
        "description": "Fires a bolt at the nearest enemy",
        "level_scale": 1.4,
    },
    "fire": {
        "name": "Ring Of Fire",
        "color": ORANGE,
        "damage": 8,
        "cooldown": 1.2,
        "speed": 0,
        "size": 60,
        "pierce": 999,
        "description": "Orbiting ring of fire that burns on contact",
        "level_scale": 1.3,
    },
    "axe": {
        "name": "Holy Axe",
        "color": YELLOW,
        "damage": 18,
        "cooldown": 1.5,
        "speed": 250,
        "size": 10,
        "pierce": 2,
        "description": "Heavy axe that hits multiple enemies",
        "level_scale": 1.5,
    },
    "knife": {
        "name": "Throwing Knife",
        "color": YELLOW,
        "damage": 6,
        "cooldown": 0.35,
        "speed": 550,
        "size": 4,
        "pierce": 0,
        "description": "Fast knife, high fire rate",
        "level_scale": 1.25,
    },
    "holy": {
        "name": "Holy Bible",
        "color": WHITE,
        "damage": 12,
        "cooldown": 3.0,
        "speed": 0,
        "size": 100,
        "pierce": 999,
        "description": "Orbiting shield that damages on contact",
        "level_scale": 1.35,
    },
    "wreck": {
        "name": "Wrecking Ball",
        "color": BROWN,
        "damage": 25,
        "cooldown": 6.0,
        "speed": 170,
        "size": 16,
        "pierce": 3,
        "fixed_dir": (0, -1),
        "above_bonus": 1.5,
        "description": "Slow heavy ball fired upward, +50% damage to enemies above you",
        "level_scale": 1.4,
    },
}


class Projectile:
    def __init__(self, x, y, dx, dy, weapon_def, level):
        self.x = float(x)
        self.y = float(y)
        self.dx = dx
        self.dy = dy
        self.speed = weapon_def["speed"]
        self.damage = int(weapon_def["damage"] * (weapon_def["level_scale"] ** (level - 1)))
        self.size = weapon_def["size"]
        self.pierce = weapon_def["pierce"]
        self.color = weapon_def["color"]
        self.above_bonus = weapon_def.get("above_bonus", 1.0)
        self.alive = True
        self.enemies_hit = set()
        self.lifetime = 3.0

    def update(self, dt):
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.size)
        # Glow
        glow_surf = pygame.Surface((self.size * 4, self.size * 4), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surf,
            (*self.color[:3], 60) if len(self.color) == 3 else self.color,
            (self.size * 2, self.size * 2),
            self.size * 2,
        )
        surface.blit(glow_surf, (sx - self.size * 2, sy - self.size * 2))


class Orbiter:
    def __init__(self, weapon_key, weapon_def, level):
        self.weapon_key = weapon_key
        self.damage = int(weapon_def["damage"] * (weapon_def["level_scale"] ** (level - 1)))
        self.radius = weapon_def["size"]
        self.color = weapon_def["color"]
        self.orbit_speed = 2.0
        self.angle = 0
        self.hit_cooldowns = {}
        self.frames = []
        self.anim_timer = 0.0
        self.frame_idx = 0
        if weapon_key == "fire":
            self._load_fire_frames()

    def _load_fire_frames(self):
        try:
            sheet = pygame.image.load(FIRE_SPRITE).convert_alpha()
        except Exception:
            return
        for r in range(FIRE_ROWS):
            for c in range(FIRE_COLS):
                rect = pygame.Rect(
                    c * FIRE_CELL, r * FIRE_CELL, FIRE_CELL, FIRE_CELL
                )
                frame = pygame.transform.scale(
                    sheet.subsurface(rect),
                    (FIRE_DISPLAY_SIZE, FIRE_DISPLAY_SIZE),
                )
                self.frames.append(frame)

    def update(self, dt, player_x, player_y):
        self.angle += self.orbit_speed * dt
        # Animate fire frames
        if self.frames:
            self.anim_timer += dt
            if self.anim_timer >= FIRE_ANIM_SPEED:
                self.anim_timer -= FIRE_ANIM_SPEED
                self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        # Clean expired cooldowns
        to_remove = [k for k, v in self.hit_cooldowns.items() if v <= 0]
        for k in to_remove:
            del self.hit_cooldowns[k]
        for k in self.hit_cooldowns:
            self.hit_cooldowns[k] -= dt

    def get_positions(self, player_x, player_y, count=3):
        positions = []
        for i in range(count):
            a = self.angle + (2 * math.pi / count) * i
            ox = player_x + math.cos(a) * self.radius
            oy = player_y + math.sin(a) * self.radius
            positions.append((ox, oy))
        return positions

    def draw(self, surface, camera_x, camera_y, player_x, player_y, count=3):
        for ox, oy in self.get_positions(player_x, player_y, count):
            sx = ox - camera_x
            sy = oy - camera_y
            if self.frames:
                frame = self.frames[self.frame_idx % len(self.frames)]
                surface.blit(
                    frame,
                    (int(sx) - FIRE_DISPLAY_SIZE // 2,
                     int(sy) - FIRE_DISPLAY_SIZE // 2),
                )
            else:
                pygame.draw.circle(surface, self.color, (int(sx), int(sy)), 8)
                pygame.draw.circle(surface, WHITE, (int(sx), int(sy)), 4)


class Weapon:
    def __init__(self, weapon_key):
        self.key = weapon_key
        self.defs = WEAPON_DEFS[weapon_key]
        self.level = 1
        self.cooldown_timer = 0
        self.orbiter = None

    @property
    def is_orbiter(self):
        return self.key in ("fire", "holy")

    def fire(self, player_x, player_y, enemies, projectiles):
        if self.is_orbiter:
            return []

        self.cooldown_timer -= 1.0 / FPS
        if self.cooldown_timer > 0:
            return []

        self.cooldown_timer = self.defs["cooldown"]

        # Fixed-direction weapons (e.g. Wrecking Ball fires straight up)
        fixed = self.defs.get("fixed_dir")
        if fixed is not None:
            dx, dy = fixed
            proj = Projectile(player_x, player_y, dx, dy, self.defs, self.level)
            projectiles.append(proj)
            return [proj]

        # Find nearest enemy
        nearest = None
        nearest_dist = float("inf")
        for e in enemies:
            if not e.alive:
                continue
            d = math.hypot(e.x - player_x, e.y - player_y)
            if d < nearest_dist:
                nearest_dist = d
                nearest = e

        if nearest is None:
            return []

        dx = nearest.x - player_x
        dy = nearest.y - player_y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist == 0:
            dx, dy = 1, 0
        else:
            dx /= dist
            dy /= dist

        proj = Projectile(player_x, player_y, dx, dy, self.defs, self.level)
        projectiles.append(proj)
        return [proj]

    def update_orbiter(self, dt, player_x, player_y, enemies):
        if not self.is_orbiter:
            return []

        if self.orbiter is None:
            self.orbiter = Orbiter(self.key, self.defs, self.level)
        else:
            self.orbiter.damage = int(
                self.defs["damage"] * (self.defs["level_scale"] ** (self.level - 1))
            )

        self.orbiter.update(dt, player_x, player_y)
        hit_enemies = []
        count = 3 + (self.level - 1)
        for ox, oy in self.orbiter.get_positions(player_x, player_y, count):
            for e in enemies:
                if not e.alive:
                    continue
                if e in self.orbiter.hit_cooldowns:
                    continue
                d = math.hypot(e.x - ox, e.y - oy)
                if d < e.size // 2 + 10:
                    e.take_damage(self.orbiter.damage)
                    self.orbiter.hit_cooldowns[id(e)] = 0.5
                    hit_enemies.append(e)
        return hit_enemies

    def draw_orbiter(self, surface, camera_x, camera_y, player_x, player_y):
        if self.orbiter:
            count = 3 + (self.level - 1)
            self.orbiter.draw(surface, camera_x, camera_y, player_x, player_y, count)


def get_random_weapon(exclude=None):
    exclude = exclude or []
    available = [k for k in WEAPON_DEFS if k not in exclude]
    if not available:
        available = list(WEAPON_DEFS.keys())
    return random.choice(available)

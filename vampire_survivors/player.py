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
        self.dash_level = 0
        self.quantum_dash = False
        self.dash_ended = False
        self.facing = "down"
        self.moving = False
        self.anim_timer = 0.0
        self.frame_idx = 0
        self.walk_frames = {"down": [], "left": [], "right": [], "up": []}
        self.idle_frames = {"down": [], "left": [], "right": [], "up": []}
        self.use_sprite = False
        self._load_sprites()

    def _load_sprites(self):
        try:
            walk = pygame.image.load(PLAYER_SPRITE_WALK).convert_alpha()
            idle = pygame.image.load(PLAYER_SPRITE_IDLE).convert_alpha()
        except Exception:
            return
        for r, name in enumerate(SPRITE_ROWS):
            for c in range(SPRITE_COLS):
                rect = pygame.Rect(
                    c * SPRITE_FRAME, r * SPRITE_FRAME,
                    SPRITE_FRAME, SPRITE_FRAME,
                )
                w = pygame.transform.scale(
                    walk.subsurface(rect), (PLAYER_SPRITE_SIZE, PLAYER_SPRITE_SIZE)
                )
                i = pygame.transform.scale(
                    idle.subsurface(rect), (PLAYER_SPRITE_SIZE, PLAYER_SPRITE_SIZE)
                )
                self.walk_frames[name].append(w)
                self.idle_frames[name].append(i)
        self.use_sprite = True

    def _set_facing(self, dx, dy):
        if abs(dx) > abs(dy):
            self.facing = "right" if dx > 0 else "left"
        elif dy != 0:
            self.facing = "down" if dy > 0 else "up"

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

    def dash_max_cooldown(self):
        return max(DASH_MIN_COOLDOWN, DASH_COOLDOWN - DASH_CD_REDUCTION * self.dash_level)

    def dash_duration(self):
        if self.dash_level >= 1:
            return DASH_DURATION * DASH_DISTANCE_MULT
        return DASH_DURATION

    def start_dash(self, dx, dy):
        if self.dash_cooldown > 0 or self.dash_timer > 0:
            return False
        if dx == 0 and dy == 0:
            dirs = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}
            dx, dy = dirs[self.facing]
        else:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
        self._set_facing(dx, dy)
        self.moving = True
        self.dash_dx = dx
        self.dash_dy = dy
        duration = self.dash_duration()
        self.dash_timer = duration
        self.dash_cooldown = self.dash_max_cooldown()
        if DASH_INVINCIBLE:
            self.invincible_timer = max(self.invincible_timer, duration * 1000 + 50)
        return True

    def update(self, dt, keys):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt

        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.x += self.dash_dx * DASH_SPEED * dt
            self.y += self.dash_dy * DASH_SPEED * dt
            self.moving = True
            if self.dash_timer <= 0:
                self.dash_timer = 0
                self.dash_ended = True
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
                self.moving = True
                self._set_facing(dx, dy)
                length = math.sqrt(dx * dx + dy * dy)
                dx /= length
                dy /= length
                self.x += dx * self.speed * dt
                self.y += dy * self.speed * dt
            else:
                self.moving = False

        # Animation timing
        speed = WALK_ANIM_SPEED if self.moving else IDLE_ANIM_SPEED
        self.anim_timer += dt
        if self.anim_timer >= speed:
            self.anim_timer -= speed
            self.frame_idx = (self.frame_idx + 1) % SPRITE_COLS

        if self.invincible_timer > 0:
            self.invincible_timer -= dt * 1000

        if self.regen_rate > 0:
            self.regen_timer += dt
            if self.regen_timer >= 1.0:
                self.regen_timer -= 1.0
                self.hp = min(self.max_hp, self.hp + self.regen_rate)

    def draw(self, surface, camera_x, camera_y):
        if not self.use_sprite:
            self._draw_fallback(surface, camera_x, camera_y)
            return

        frames = self.walk_frames if self.moving else self.idle_frames
        row = frames[self.facing]
        frame = row[self.frame_idx % len(row)] if row else None
        if frame is None:
            self._draw_fallback(surface, camera_x, camera_y)
            return

        img = frame
        if self.dash_timer > 0:
            img = frame.copy()
            img.set_alpha(190)

        surface.blit(
            img,
            (self.x - camera_x - PLAYER_SPRITE_SIZE // 2,
             self.y - camera_y - PLAYER_SPRITE_SIZE // 2),
        )

    def _draw_fallback(self, surface, camera_x, camera_y):
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

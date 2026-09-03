import pygame
import random
import math


class Particle:
    def __init__(self, x, y, color, vx, vy, lifetime, size):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 80 * dt  # slight gravity
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera_x, camera_y):
        sx = self.x - camera_x
        sy = self.y - camera_y
        alpha = max(0, self.lifetime / self.max_lifetime)
        size = max(1, int(self.size * alpha))
        color = tuple(min(255, int(c * alpha + 50)) for c in self.color[:3])
        pygame.draw.circle(surface, color, (int(sx), int(sy)), size)


class DamageNumber:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = str(text)
        self.color = color
        self.lifetime = 0.7
        self.max_lifetime = 0.7
        self.vy = -80
        self.alive = True

    def update(self, dt):
        self.y += self.vy * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera_x, camera_y, font):
        sx = self.x - camera_x
        sy = self.y - camera_y
        alpha = max(0, self.lifetime / self.max_lifetime)
        color = tuple(min(255, int(c * alpha + 100)) for c in self.color[:3])
        text_surf = font.render(self.text, True, color)
        text_rect = text_surf.get_rect(center=(int(sx), int(sy)))
        surface.blit(text_surf, text_rect)


class Ring:
    def __init__(self, x, y, max_radius, color, lifetime=0.4):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface, camera_x, camera_y):
        progress = 1.0 - max(0.0, self.lifetime / self.max_lifetime)
        radius = max(1, int(self.max_radius * (0.2 + 0.8 * progress)))
        alpha = int(220 * max(0.0, self.lifetime / self.max_lifetime))
        size = radius * 2 + 8
        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(tmp, self.color, (size // 2, size // 2), radius, 3)
        tmp.set_alpha(alpha)
        surface.blit(tmp, (self.x - camera_x - size // 2, self.y - camera_y - size // 2))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.damage_numbers = []
        self.rings = []
        self.enabled = True
        self.show_damage = True

    def spawn_hit(self, x, y, color, count=5):
        if not self.enabled:
            return
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(2, 4)
            self.particles.append(
                Particle(x, y, color, vx, vy, random.uniform(0.2, 0.5), size)
            )

    def spawn_death(self, x, y, color, count=12):
        if not self.enabled:
            return
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(80, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(2, 5)
            self.particles.append(
                Particle(x, y, color, vx, vy, random.uniform(0.3, 0.7), size)
            )

    def spawn_xp(self, x, y):
        if not self.enabled:
            return
        color = (100, 255, 100)
        for _ in range(4):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(20, 60)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            self.particles.append(
                Particle(x, y, color, vx, vy, random.uniform(0.2, 0.4), 2)
            )

    def add_damage_number(self, x, y, amount, color=None):
        if not self.show_damage:
            return        self.damage_numbers.append(
            DamageNumber(x, y, amount, color or (255, 255, 255))
        )

    def spawn_ring(self, x, y, max_radius, color):
        self.rings.append(Ring(x, y, max_radius, color))

    def update(self, dt):
        self.particles = [p for p in self.particles if p.alive]
        self.damage_numbers = [d for d in self.damage_numbers if d.alive]
        self.rings = [r for r in self.rings if r.alive]
        for p in self.particles:
            p.update(dt)
        for d in self.damage_numbers:
            d.update(dt)
        for r in self.rings:
            r.update(dt)

    def draw(self, surface, camera_x, camera_y, font=None):
        for p in self.particles:
            p.draw(surface, camera_x, camera_y)
        for r in self.rings:
            r.draw(surface, camera_x, camera_y)
        if font:
            for d in self.damage_numbers:
                d.draw(surface, camera_x, camera_y, font)

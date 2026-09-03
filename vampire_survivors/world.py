import pygame
import os
import random
from settings import (
    TEX_DIR, GROUND_TEXTURE, TILE_SIZE,
    PATH_H_SEGMENTS, PATH_V_SEGMENTS, PATH_JUNCTIONS,
    SCREEN_WIDTH, SCREEN_HEIGHT,
)


def _load_image(path, alpha=False):
    full = os.path.join(TEX_DIR, path)
    try:
        surf = pygame.image.load(full)
        return surf.convert_alpha() if alpha else surf.convert()
    except Exception:
        return None


class World:
    """Generates a random connected network of dirt paths on a varied dirt ground."""

    def __init__(self):
        self.ground = _load_image(GROUND_TEXTURE)
        self.h_segments = [img for img in (_load_image(p, alpha=True) for p in PATH_H_SEGMENTS) if img]
        self.v_segments = [img for img in (_load_image(p, alpha=True) for p in PATH_V_SEGMENTS) if img]
        self.junctions = [img for img in (_load_image(p, alpha=True) for p in PATH_JUNCTIONS) if img]

        self.path_tiles = {}  # (tx, ty) -> image (chosen once)
        self._generate_paths()

    def _generate_paths(self):
        """Create several long, winding road corridors that snake across the map."""
        grid = {}  # (tx, ty) -> present

        def carve_road(start, axis, points):
            """Carve one long winding road, recording every point cell it passes."""
            cx, cy = start
            points.append((cx, cy))
            steps = random.randint(50, 90)
            for _ in range(steps):
                run = random.randint(3, 10)
                for _ in range(run):
                    cx += axis[0]
                    cy += axis[1]
                    points.append((cx, cy))
                # Mostly keep going straight, occasionally turn or jink
                if random.random() < 0.18:
                    axis = (axis[1], axis[0])
                    if random.random() < 0.5:
                        axis = (-axis[0], -axis[1])
                elif random.random() < 0.15:
                    px, py = axis[1], axis[0]
                    if random.random() < 0.5:
                        px, py = -px, -py
                    cx += px
                    cy += py
                    points.append((cx, cy))

        # Build a few roads. One guaranteed to pass through/near the origin so
        # the player always starts on a road, plus others from map edges.
        road_starts = [
            (0, 0, random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])),
            (0, random.randint(-20, 20), random.choice([(1, 0), (0, 1)])),
            (random.randint(-20, 20), 0, random.choice([(1, 0), (0, 1)])),
            (0, random.randint(-20, 20), random.choice([(1, 0), (0, 1)])),
        ]

        for sx, sy, axis in road_starts:
            pts = []
            carve_road((sx, sy), axis, pts)
            # Connect consecutive points, filling h/v runs (and L-corners)
            for i in range(len(pts) - 1):
                ax, ay = pts[i]
                bx, by = pts[i + 1]
                stepx = 1 if bx > ax else (-1 if bx < ax else 0)
                stepy = 1 if by > ay else (-1 if by < ay else 0)
                if stepx == 0 and stepy == 0:
                    continue
                if ax != bx and ay != by:
                    # L-shape corner: fill horizontal then vertical
                    for x in range(ax, bx + stepx, stepx):
                        grid[(x, ay)] = True
                    for y in range(ay, by + stepy, stepy):
                        grid[(bx, y)] = True
                elif stepx != 0:
                    # Pure horizontal run
                    for x in range(ax, bx + stepx, stepx):
                        grid[(x, ay)] = True
                else:
                    # Pure vertical run
                    for y in range(ay, by + stepy, stepy):
                        grid[(ax, y)] = True

        # Determine connectivity direction per tile and assign its texture once
        for tx, ty in grid.keys():
            connections = set()
            if (tx + 1, ty) in grid:
                connections.add('E')
            if (tx - 1, ty) in grid:
                connections.add('W')
            if (tx, ty + 1) in grid:
                connections.add('S')
            if (tx, ty - 1) in grid:
                connections.add('N')
            has_h = 'E' in connections or 'W' in connections
            has_v = 'N' in connections or 'S' in connections
            if has_h and has_v:
                lst = self.junctions
            elif has_h:
                lst = self.h_segments
            elif has_v:
                lst = self.v_segments
            else:
                lst = self.junctions
            if lst:
                self.path_tiles[(tx, ty)] = random.choice(lst)

    def draw(self, surface, camera_x, camera_y):
        tw = TILE_SIZE
        # Ground
        if self.ground:
            sw, sh = self.ground.get_size()
            start_x = int(camera_x % sw)
            start_y = int(camera_y % sh)
            for gx in range(-start_x, SCREEN_WIDTH, sw):
                for gy in range(-start_y, SCREEN_HEIGHT, sh):
                    surface.blit(self.ground, (gx, gy))
        else:
            surface.fill((40, 40, 50))

        # Paths
        for (tx, ty), img in self.path_tiles.items():
            px = tx * tw
            py = ty * tw
            # Skip tiles not in view
            if px + tw < camera_x or px > camera_x + SCREEN_WIDTH:
                continue
            if py + tw < camera_y or py > camera_y + SCREEN_HEIGHT:
                continue
            sx = px - camera_x
            sy = py - camera_y
            surface.blit(img, (sx, sy))

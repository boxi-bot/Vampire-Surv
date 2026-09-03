import pygame
import sys
import random
import math
from settings import *
from player import Player
from enemy import Enemy, spawn_enemy
from weapons import Weapon, WEAPON_DEFS, get_random_weapon
from xp_system import XPGemManager
from particles import ParticleSystem
from ui import Camera, draw_hud, draw_upgrade_screen, draw_title_screen, draw_difficulty_screen, draw_game_over
from world import World


def generate_upgrade_choices(player):
    choices = []

    # New weapons
    owned_keys = [w.key for w in player.weapons]
    new_weapon_keys = [k for k in WEAPON_DEFS if k not in owned_keys]
    for key in new_weapon_keys[:2]:
        wdef = WEAPON_DEFS[key]
        choices.append({
            "type": "new_weapon",
            "weapon_key": key,
            "name": wdef["name"],
            "description": wdef["description"],
            "color": wdef["color"],
            "is_new": True,
            "current_level": 0,
            "new_level": 1,
        })

    # Upgrade existing weapons
    for weapon in player.weapons:
        if weapon.level < 8:
            wdef = weapon.defs
            choices.append({
                "type": "upgrade_weapon",
                "weapon_key": weapon.key,
                "name": f"{wdef['name']} Up",
                "description": f"Damage + level {weapon.level} -> {weapon.level + 1}",
                "color": wdef["color"],
                "is_new": False,
                "current_level": weapon.level,
                "new_level": weapon.level + 1,
            })

    # Stat upgrades
    stat_upgrades = [
        {
            "type": "max_hp",
            "name": "Max HP +20",
            "description": f"HP: {player.max_hp} -> {player.max_hp + 20}",
            "color": GREEN,
            "is_new": False,
            "current_level": 0,
            "new_level": 0,
        },
        {
            "type": "speed",
            "name": "Move Speed +10%",
            "description": f"Speed: {int(player.speed)} -> {int(player.speed * 1.1)}",
            "color": CYAN,
            "is_new": False,
            "current_level": 0,
            "new_level": 0,
        },
        {
            "type": "armor",
            "name": "Armor +1",
            "description": f"Armor: {player.armor} -> {player.armor + 1}",
            "color": GRAY,
            "is_new": False,
            "current_level": 0,
            "new_level": 0,
        },
        {
            "type": "regen",
            "name": "HP Regen +1/s",
            "description": f"Regen: {player.regen_rate}/s -> {player.regen_rate + 1}/s",
            "color": LIGHT_GRAY,
            "is_new": False,
            "current_level": 0,
            "new_level": 0,
        },
    ]
    choices.extend(random.sample(stat_upgrades, min(2, len(stat_upgrades))))

    random.shuffle(choices)
    return choices[:UPGRADE_CHOICES]


def apply_choice(player, choice):
    ctype = choice["type"]
    if ctype == "new_weapon":
        weapon = Weapon(choice["weapon_key"])
        player.weapons.append(weapon)
    elif ctype == "upgrade_weapon":
        for w in player.weapons:
            if w.key == choice["weapon_key"]:
                w.level += 1
                if w.is_orbiter and w.orbiter:
                    w.orbiter = None
                break
    elif ctype == "max_hp":
        player.max_hp += 20
        player.hp += 20
    elif ctype == "speed":
        player.speed *= 1.1
    elif ctype == "armor":
        player.armor += 1
    elif ctype == "regen":
        player.regen_rate += 1


def run_game():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    font_small = pygame.font.Font(None, 24)
    font_med = pygame.font.Font(None, 32)
    font_large = pygame.font.Font(None, 56)

    # ---- TITLE SCREEN ----
    state = "title"
    while state == "title":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = "difficulty"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    state = "difficulty"

        draw_title_screen(screen, font_large, font_med, font_small)
        pygame.display.flip()
        clock.tick(FPS)

    # ---- DIFFICULTY SCREEN ----
    difficulty_key = "normal"
    while state == "difficulty":
        hovered = draw_difficulty_screen(screen, font_large, font_med, font_small)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    difficulty_key = "easy"
                    state = "playing"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    difficulty_key = "normal"
                    state = "playing"
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    difficulty_key = "hard"
                    state = "playing"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hovered:
                    difficulty_key = hovered
                    state = "playing"

        clock.tick(FPS)

    diff = DIFFICULTIES[difficulty_key]

    # ---- GAME INIT ----
    world = World()
    player = Player(0, 0)
    player.weapons.append(Weapon("wand"))

    camera = Camera()
    enemies = []
    projectiles = []
    xp_manager = XPGemManager()
    particles = ParticleSystem()

    game_time = 0.0
    spawn_timer = 0
    state = "playing"
    upgrade_choices = []

    # ---- MAIN GAME LOOP ----
    while state == "playing":
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        game_time += dt

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    ddx, ddy = 0, 0
                    if keys[pygame.K_w] or keys[pygame.K_UP]:
                        ddy -= 1
                    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                        ddy += 1
                    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                        ddx -= 1
                    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                        ddx += 1
                    if player.start_dash(ddx, ddy):
                        particles.spawn_hit(player.x, player.y, CYAN, 8)

        # --- UPGRADE SCREEN ---
        if state == "playing" and upgrade_choices:
            hovered = draw_upgrade_screen(
                screen, player, upgrade_choices, font_med, font_small, font_large
            )
            pygame.display.flip()

            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_1, pygame.K_KP1) and len(upgrade_choices) > 0:
                            apply_choice(player, upgrade_choices[0])
                            upgrade_choices = []
                            waiting = False
                        elif event.key in (pygame.K_2, pygame.K_KP2) and len(upgrade_choices) > 1:
                            apply_choice(player, upgrade_choices[1])
                            upgrade_choices = []
                            waiting = False
                        elif event.key in (pygame.K_3, pygame.K_KP3) and len(upgrade_choices) > 2:
                            apply_choice(player, upgrade_choices[2])
                            upgrade_choices = []
                            waiting = False
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if 0 <= hovered < len(upgrade_choices):
                            apply_choice(player, upgrade_choices[hovered])
                            upgrade_choices = []
                            waiting = False

                hovered = draw_upgrade_screen(
                    screen, player, upgrade_choices, font_med, font_small, font_large
                )
                pygame.display.flip()
                clock.tick(30)

            continue

        # --- UPDATE ---
        keys = pygame.key.get_pressed()
        player.update(dt, keys)
        camera.update(player.x, player.y)

        # Difficulty scaling
        time_multiplier = 1.0 + game_time / 60.0

        # Spawn enemies
        spawn_interval = max(
            ENEMY_SPAWN_INTERVAL_MIN,
            ENEMY_SPAWN_INTERVAL_BASE * diff["spawn_mult"] - game_time * 10,
        )
        spawn_timer += dt * 1000
        if spawn_timer >= spawn_interval:
            spawn_timer -= spawn_interval
            count = 1 + int(game_time / 30)
            for _ in range(count):
                enemies.append(
                    spawn_enemy(player.x, player.y, time_multiplier, diff)
                )

        # Update enemies
        for e in enemies:
            e.update(dt, player.x, player.y)

        # Enemy-player collision
        for e in enemies:
            if not e.alive:
                continue
            if player.rect.colliderect(e.rect):
                if player.take_damage(e.damage):
                    particles.spawn_hit(
                        player.x, player.y, RED, 8
                    )
                    particles.add_damage_number(
                        player.x, player.y - 20, e.damage, RED
                    )
                    if not player.alive:
                        state = "dead"
                        break

        # Weapons fire
        alive_enemies = [e for e in enemies if e.alive]
        for weapon in player.weapons:
            if weapon.is_orbiter:
                hit = weapon.update_orbiter(dt, player.x, player.y, alive_enemies)
                for e in hit:
                    if not e.alive:
                        player.total_kills += 1
                        xp_manager.spawn_gem(e.x, e.y, e.xp_value)
                        particles.spawn_death(e.x, e.y, e.color, 10)
                        particles.add_damage_number(e.x, e.y - 15, weapon.orbiter.damage, YELLOW)
                    else:
                        particles.spawn_hit(e.x, e.y, e.color, 4)
                        particles.add_damage_number(
                            e.x, e.y - 15, weapon.orbiter.damage
                        )
            else:
                weapon.fire(player.x, player.y, alive_enemies, projectiles)

        # Update projectiles
        for p in projectiles:
            p.update(dt)
            if not p.alive:
                continue
            for e in alive_enemies:
                if not e.alive or id(e) in p.enemies_hit:
                    continue
                dist = math.hypot(p.x - e.x, p.y - e.y)
                if dist < p.size + e.size // 2:
                    killed = e.take_damage(p.damage)
                    p.enemies_hit.add(id(e))
                    particles.spawn_hit(e.x, e.y, e.color, 5)
                    particles.add_damage_number(e.x, e.y - 15, p.damage)
                    if killed:
                        player.total_kills += 1
                        xp_manager.spawn_gem(e.x, e.y, e.xp_value)
                        particles.spawn_death(e.x, e.y, e.color, 10)
                    if len(p.enemies_hit) > p.pierce:
                        p.alive = False
                        break

        projectiles = [p for p in projectiles if p.alive]

        # XP collection
        collected_xp = xp_manager.update(dt, player.x, player.y)
        if collected_xp > 0:
            particles.spawn_xp(player.x, player.y)
            if player.add_xp(collected_xp):
                upgrade_choices = generate_upgrade_choices(player)

        # Clean up dead enemies
        enemies = [e for e in enemies if e.alive]

        # Particles
        # Dash trail
        if player.dash_timer > 0:
            particles.spawn_hit(player.x, player.y, CYAN, 2)

        particles.update(dt)

        # --- DRAW ---
        screen.fill(DARK_BG)

        # Draw ground + paths
        world.draw(screen, camera.x, camera.y)

        # Draw XP gems
        xp_manager.draw(screen, camera.x, camera.y)

        # Draw projectiles
        for p in projectiles:
            p.draw(screen, camera.x, camera.y)

        # Draw orbiter effects
        for weapon in player.weapons:
            weapon.draw_orbiter(screen, camera.x, camera.y, player.x, player.y)

        # Draw enemies
        for e in enemies:
            e.draw(screen, camera.x, camera.y)

        # Draw player
        player.draw(screen, camera.x, camera.y)

        # Draw particles
        particles.draw(screen, camera.x, camera.y, font_small)

        # Draw HUD
        draw_hud(screen, player, game_time, font_small, font_med, font_large)

        pygame.display.flip()

    # ---- GAME OVER ----
    while state == "dead":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                state = "restart"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = "restart"

        screen.fill(DARK_BG)
        draw_game_over(screen, player, game_time, font_large, font_med, font_small)
        pygame.display.flip()
        clock.tick(FPS)

    if state == "restart":
        run_game()


if __name__ == "__main__":
    run_game()

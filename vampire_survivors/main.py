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
from ui import Camera, draw_hud, draw_upgrade_screen, draw_title_screen, draw_settings_screen, draw_difficulty_screen, draw_game_over
from world import World


def generate_upgrade_choices(player):
    choices = []

    # New weapons
    owned_keys = [w.key for w in player.weapons]
    new_weapon_keys = [k for k in WEAPON_DEFS if k not in owned_keys]
    for key in new_weapon_keys[:2]:
        wdef = WEAPON_DEFS[key]
        desc = wdef["description"]
        if key == "fire":
            desc += " Starts with 3 fireballs, +1 per level."
        elif key == "holy":
            desc += " Starts with 3 bibles, +1 per level."
        choices.append({
            "type": "new_weapon",
            "weapon_key": key,
            "name": wdef["name"],
            "description": desc,
            "color": wdef["color"],
            "is_new": True,
            "current_level": 0,
            "new_level": 1,
        })

    # Upgrade existing weapons
    for weapon in player.weapons:
        if weapon.level < 8:
            wdef = weapon.defs
            pct = round((wdef["level_scale"] - 1) * 100)
            desc = f"+{pct}% damage, Lv {weapon.level} -> {weapon.level + 1}"
            if weapon.key == "fire":
                desc += ", +1 fireball"
            elif weapon.key == "holy":
                desc += ", +1 bible"
            choices.append({
                "type": "upgrade_weapon",
                "weapon_key": weapon.key,
                "name": f"{wdef['name']} Up",
                "description": desc,
                "color": wdef["color"],
                "is_new": False,
                "current_level": weapon.level,
                "new_level": weapon.level + 1,
            })

    # Swift Dash (repeatable dash cooldown/distance upgrade)
    if player.dash_level < DASH_LEVEL_MAX:
        old_cd = player.dash_max_cooldown()
        new_cd = max(DASH_MIN_COOLDOWN, old_cd - DASH_CD_REDUCTION)
        desc = f"-0.5s dash cooldown ({old_cd:.1f}s -> {new_cd:.1f}s)"
        if player.dash_level == 0:
            desc += ", +50% dash distance"
        choices.append({
            "type": "dash",
            "weapon_key": None,
            "name": "Swift Dash",
            "description": desc,
            "color": CYAN,
            "is_new": False,
            "level_label": "Dash",
            "current_level": player.dash_level,
            "new_level": player.dash_level + 1,
        })

    # Quantum Dash (one-time ability)
    if not player.quantum_dash:
        qdmg = QUANTUM_BASE + QUANTUM_PER_LEVEL * player.level
        choices.append({
            "type": "quantum",
            "weapon_key": None,
            "name": "Quantum Dash",
            "description": f"Dash ends with a {QUANTUM_RADIUS}px purple blast for {qdmg} damage",
            "color": PURPLE,
            "is_new": True,
            "new_label": "NEW ABILITY",
            "current_level": 0,
            "new_level": 1,
        })

    # Stat upgrades
    stat_upgrades = [
        {
            "type": "max_hp",
            "name": "Max HP +20",
            "description": f"HP: {player.max_hp} -> {player.max_hp + 20}",
            "color": GREEN,
            "is_new": False,
            "level_label": "Max HP",
            "current_level": player.max_hp,
            "new_level": player.max_hp + 20,
        },
        {
            "type": "speed",
            "name": "Move Speed +10%",
            "description": f"Speed: {int(player.speed)} -> {int(player.speed * 1.1)}",
            "color": CYAN,
            "is_new": False,
            "level_label": "Speed",
            "current_level": int(player.speed),
            "new_level": int(player.speed * 1.1),
        },
        {
            "type": "armor",
            "name": "Armor +1",
            "description": f"Armor: {player.armor} -> {player.armor + 1}",
            "color": GRAY,
            "is_new": False,
            "level_label": "Armor",
            "current_level": player.armor,
            "new_level": player.armor + 1,
        },
        {
            "type": "regen",
            "name": "HP Regen +1/s",
            "description": f"Regen: {player.regen_rate}/s -> {player.regen_rate + 1}/s",
            "color": LIGHT_GRAY,
            "is_new": False,
            "level_label": "Regen",
            "current_level": player.regen_rate,
            "new_level": player.regen_rate + 1,
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
    elif ctype == "dash":
        player.dash_level = min(DASH_LEVEL_MAX, player.dash_level + 1)
    elif ctype == "quantum":
        player.quantum_dash = True


def run_game(game_settings=None):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    font_small = pygame.font.Font(None, 24)
    font_med = pygame.font.Font(None, 32)
    font_large = pygame.font.Font(None, 56)

    if game_settings is None:
        game_settings = {
            "fullscreen": False,
            "particles": True,
            "damage_numbers": True,
        }

    # Fixed-size canvas: everything is drawn here, then presented
    # to the display (scaled + letterboxed when fullscreen).
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def apply_display_mode():
        nonlocal screen
        if game_settings["fullscreen"]:
            screen = pygame.display.set_mode(
                (FULLSCREEN_W, FULLSCREEN_H), pygame.FULLSCREEN
            )
            s = min(FULLSCREEN_W / SCREEN_WIDTH, FULLSCREEN_H / SCREEN_HEIGHT)
            w, h = int(SCREEN_WIDTH * s), int(SCREEN_HEIGHT * s)
            VIEW.update({
                "scale": s,
                "ox": (FULLSCREEN_W - w) // 2,
                "oy": (FULLSCREEN_H - h) // 2,
                "w": w,
                "h": h,
            })
        else:
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            VIEW.update({
                "scale": 1.0, "ox": 0, "oy": 0,
                "w": SCREEN_WIDTH, "h": SCREEN_HEIGHT,
            })

    def present():
        if game_settings["fullscreen"]:
            screen.fill(BLACK)
            screen.blit(
                pygame.transform.scale(canvas, (VIEW["w"], VIEW["h"])),
                (VIEW["ox"], VIEW["oy"]),
            )
        else:
            screen.blit(canvas, (0, 0))
        pygame.display.flip()

    apply_display_mode()

    # ---- TITLE + SETTINGS MENU (loops until difficulty is chosen) ----
    state = "title"
    while state != "difficulty":
        while state == "title":
            hovered = draw_title_screen(canvas, font_large, font_med, font_small)
            present()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if hovered == "start":
                        state = "difficulty"
                    elif hovered == "settings":
                        state = "settings"

            clock.tick(FPS)

        # ---- SETTINGS SCREEN ----
        while state == "settings":
            hovered = draw_settings_screen(
                canvas, game_settings, font_large, font_med, font_small
            )
            present()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if hovered == "back":
                        state = "title"
                    elif hovered and hovered.startswith("toggle:"):
                        key = hovered.split(":", 1)[1]
                        game_settings[key] = not game_settings[key]
                        if key == "fullscreen":
                            apply_display_mode()

            clock.tick(FPS)

    # ---- DIFFICULTY SCREEN ----
    difficulty_key = "normal"
    while state == "difficulty":
        hovered = draw_difficulty_screen(canvas, font_large, font_med, font_small)
        present()

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
    particles.enabled = game_settings["particles"]
    particles.show_damage = game_settings["damage_numbers"]

    game_time = 0.0
    spawn_timer = 0
    state = "playing"
    upgrade_choices = []

    # ---- MAIN GAME LOOP ----
    while state == "playing":
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        game_time += dt

        # Keys (read before events so dash input can use them)
        keys = pygame.key.get_pressed()

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
                canvas, player, upgrade_choices, font_med, font_small, font_large
            )
            present()

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
                    canvas, player, upgrade_choices, font_med, font_small, font_large
                )
                present()
                clock.tick(30)

            continue

        # --- UPDATE ---
        player.update(dt, keys)
        camera.update(player.x, player.y)

        # Quantum Dash: splash damage at dash end position
        if player.dash_ended:
            player.dash_ended = False
            if player.quantum_dash:
                qdmg = QUANTUM_BASE + QUANTUM_PER_LEVEL * player.level
                particles.spawn_death(player.x, player.y, PURPLE, 20)
                particles.spawn_ring(player.x, player.y, QUANTUM_RADIUS, PURPLE)
                for e in enemies:
                    if not e.alive:
                        continue
                    if math.hypot(e.x - player.x, e.y - player.y) < QUANTUM_RADIUS + e.size // 2:
                        killed = e.take_damage(qdmg)
                        particles.add_damage_number(e.x, e.y - 15, qdmg, PURPLE)
                        if killed:
                            player.total_kills += 1
                            xp_manager.spawn_gem(e.x, e.y, e.xp_value)
                            particles.spawn_death(e.x, e.y, e.color, 10)

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
                    dmg = p.damage
                    if p.above_bonus != 1.0 and e.y < player.y:
                        dmg = int(p.damage * p.above_bonus)
                    killed = e.take_damage(dmg)
                    p.enemies_hit.add(id(e))
                    particles.spawn_hit(e.x, e.y, e.color, 5)
                    particles.add_damage_number(e.x, e.y - 15, dmg)
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
        canvas.fill(DARK_BG)

        # Draw ground + paths
        world.draw(canvas, camera.x, camera.y)

        # Draw XP gems
        xp_manager.draw(canvas, camera.x, camera.y)

        # Draw projectiles
        for p in projectiles:
            p.draw(canvas, camera.x, camera.y)

        # Draw orbiter effects
        for weapon in player.weapons:
            weapon.draw_orbiter(canvas, camera.x, camera.y, player.x, player.y)

        # Draw enemies
        for e in enemies:
            e.draw(canvas, camera.x, camera.y)

        # Draw player
        player.draw(canvas, camera.x, camera.y)

        # Draw particles
        particles.draw(canvas, camera.x, camera.y, font_small)

        # Draw HUD
        draw_hud(canvas, player, game_time, font_small, font_med, font_large)

        present()

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

        canvas.fill(DARK_BG)
        draw_game_over(canvas, player, game_time, font_large, font_med, font_small)
        present()
        clock.tick(FPS)

    if state == "restart":
        run_game(game_settings)
        return


if __name__ == "__main__":
    run_game()

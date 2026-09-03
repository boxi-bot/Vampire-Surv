import pygame
from settings import *


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x, target_y):
        self.x = target_x - SCREEN_WIDTH // 2
        self.y = target_y - SCREEN_HEIGHT // 2


def ui_mouse_pos():
    """Mouse position mapped into game-canvas coordinates (handles fullscreen scaling)."""
    mx, my = pygame.mouse.get_pos()
    s = VIEW["scale"]
    return ((mx - VIEW["ox"]) / s, (my - VIEW["oy"]) / s)


def draw_hud(surface, player, game_time, font_small, font_med, font_large):
    # HP bar
    bar_x, bar_y = 16, 16
    bar_w, bar_h = 200, 20
    pygame.draw.rect(surface, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    hp_ratio = max(0, player.hp / player.max_hp)
    hp_color = GREEN if hp_ratio > 0.5 else YELLOW if hp_ratio > 0.25 else RED
    pygame.draw.rect(
        surface, hp_color,
        (bar_x, bar_y, int(bar_w * hp_ratio), bar_h),
        border_radius=4,
    )
    hp_text = font_small.render(f"HP: {player.hp}/{player.max_hp}", True, WHITE)
    surface.blit(hp_text, (bar_x + 4, bar_y + 2))

    # XP bar
    xp_y = bar_y + bar_h + 6
    pygame.draw.rect(surface, DARK_GRAY, (bar_x, xp_y, bar_w, 12), border_radius=3)
    xp_ratio = player.xp / max(1, player.xp_to_next)
    pygame.draw.rect(
        surface, CYAN,
        (bar_x, xp_y, int(bar_w * xp_ratio), 12),
        border_radius=3,
    )

    # Level
    level_text = font_med.render(f"Lv. {player.level}", True, CYAN)
    surface.blit(level_text, (bar_x + bar_w + 10, bar_y - 2))

    # Timer
    minutes = int(game_time) // 60
    seconds = int(game_time) % 60
    timer_text = font_large.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
    timer_rect = timer_text.get_rect(center=(SCREEN_WIDTH // 2, 24))
    surface.blit(timer_text, timer_rect)

    # Kill count
    kill_text = font_small.render(f"Kills: {player.total_kills}", True, LIGHT_GRAY)
    surface.blit(kill_text, (SCREEN_WIDTH - kill_text.get_width() - 16, 16))

    # Weapon display
    wx = 16
    wy = SCREEN_HEIGHT - 60
    for i, weapon in enumerate(player.weapons):
        box_rect = (wx + i * 52, wy, 48, 48)
        pygame.draw.rect(surface, DARK_GRAY, box_rect, border_radius=6)
        pygame.draw.rect(surface, GRAY, box_rect, 2, border_radius=6)
        wtext = font_small.render(f"{weapon.level}", True, weapon.defs["color"])
        wname = font_small.render(weapon.key[:2].upper(), True, weapon.defs["color"])
        surface.blit(wname, (wx + i * 52 + 24 - wname.get_width() // 2, wy + 6))
        surface.blit(wtext, (wx + i * 52 + 24 - wtext.get_width() // 2, wy + 26))

    # Dash indicator
    dash_x = wx + len(player.weapons) * 52 + 12
    dash_rect = (dash_x, wy, 48, 48)
    if player.dash_cooldown > 0:
        ratio = 1.0 - player.dash_cooldown / player.dash_max_cooldown()
        pygame.draw.rect(surface, DARK_GRAY, dash_rect, border_radius=6)
        fill_h = int(48 * ratio)
        pygame.draw.rect(surface, CYAN, (dash_x, wy + 48 - fill_h, 48, fill_h), border_radius=6)
        pygame.draw.rect(surface, GRAY, dash_rect, 2, border_radius=6)
    elif player.dash_timer > 0:
        pygame.draw.rect(surface, CYAN, dash_rect, border_radius=6)
        pygame.draw.rect(surface, WHITE, dash_rect, 2, border_radius=6)
    else:
        pygame.draw.rect(surface, (30, 60, 60), dash_rect, border_radius=6)
        pygame.draw.rect(surface, CYAN, dash_rect, 2, border_radius=6)
    dash_label = font_small.render("DSH", True, CYAN)
    surface.blit(dash_label, (dash_x + 24 - dash_label.get_width() // 2, wy + 16))


def draw_upgrade_screen(surface, player, choices, font_med, font_small, font_large):
    # Dim background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    # Title
    title = font_large.render("LEVEL UP!", True, YELLOW)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
    surface.blit(title, title_rect)

    sub = font_small.render("Choose an upgrade:", True, LIGHT_GRAY)
    sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 165))
    surface.blit(sub, sub_rect)

    # Choice boxes
    box_w = 300
    box_h = 130
    total_w = len(choices) * box_w + (len(choices) - 1) * 20
    start_x = (SCREEN_WIDTH - total_w) // 2
    start_y = 220

    mouse_pos = ui_mouse_pos()
    hovered = -1

    for i, choice in enumerate(choices):
        bx = start_x + i * (box_w + 20)
        by = start_y
        rect = pygame.Rect(bx, by, box_w, box_h)
        is_hovered = rect.collidepoint(mouse_pos)
        if is_hovered:
            hovered = i

        bg_color = (60, 60, 80) if not is_hovered else (80, 80, 120)
        border_color = choice.get("color", CYAN) if is_hovered else GRAY

        # Glow effect for hovered card
        if is_hovered:
            glow_color = choice.get("color", (200, 200, 255))
            glow_surf = pygame.Surface((box_w + 20, box_h + 20), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surf, (*glow_color, 80),
                (10, 10, box_w, box_h), border_radius=14,
            )
            blur_surf = pygame.transform.smoothscale(
                pygame.transform.smoothscale(glow_surf, (40, 40)), (box_w + 20, box_h + 20)
            )
            surface.blit(blur_surf, (bx - 10, by - 10), special_flags=0)

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, 4, border_radius=10)

        # Name
        name_text = font_med.render(choice["name"], True, choice.get("color", WHITE))
        surface.blit(name_text, (bx + 12, by + 10))

        # Level
        if choice.get("is_new"):
            new_label = choice.get("new_label", "NEW WEAPON")
            level_text = font_small.render(new_label, True, GREEN)
        else:
            label = choice.get("level_label", "Level")
            level_text = font_small.render(f"{label} {choice['current_level']} -> {choice['new_level']}", True, YELLOW)
        surface.blit(level_text, (bx + 12, by + 40))

        # Description (wrapped)
        desc = choice["description"]
        max_desc_w = box_w - 24
        wrapped = []
        line = ""
        for word in desc.split(" "):
            test = line + (" " if line else "") + word
            if font_small.size(test)[0] <= max_desc_w:
                line = test
            else:
                wrapped.append(line)
                line = word
        if line:
            wrapped.append(line)

        dy = by + 64
        for line in wrapped:
            desc_text = font_small.render(line, True, LIGHT_GRAY)
            surface.blit(desc_text, (bx + 12, dy))
            dy += font_small.get_height()

    # Click instruction
    hint = font_small.render("Click a choice or press 1/2/3", True, GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, start_y + box_h + 40))
    surface.blit(hint, hint_rect)

    return hovered


def draw_button(surface, rect, label, font, color, hovered):
    bg = (60, 60, 80) if not hovered else (80, 80, 120)
    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.rect(surface, color if hovered else GRAY, rect, 3 if hovered else 2, border_radius=10)
    text = font.render(label, True, color if hovered else WHITE)
    surface.blit(text, text.get_rect(center=rect.center))


def draw_title_screen(surface, font_large, font_med, font_small):
    surface.fill(DARK_BG)

    # Title
    title = font_large.render("VAMPIRE SURVIVORS", True, RED)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
    surface.blit(title, title_rect)

    sub = font_med.render("Python Edition", True, ORANGE)
    sub_rect = sub.get_rect(center=(SCREEN_WIDTH // 2, 200))
    surface.blit(sub, sub_rect)

    # Instructions
    lines = [
        "WASD / Arrow Keys - Move",
        "Spacebar - Dash (7.5s cooldown, brief invincibility)",
        "Weapons fire automatically",
        "Collect green XP gems from enemies",
        "Level up to choose upgrades",
        "",
        "Survive as long as you can!",
    ]
    y = 280
    for line in lines:
        text = font_small.render(line, True, LIGHT_GRAY)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
        surface.blit(text, rect)
        y += 30

    # Buttons
    mouse_pos = ui_mouse_pos()
    hovered = None

    start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, 520, 280, 60)
    settings_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, 595, 280, 60)

    if start_rect.collidepoint(mouse_pos):
        hovered = "start"
    elif settings_rect.collidepoint(mouse_pos):
        hovered = "settings"

    draw_button(surface, start_rect, "START GAME", font_med, GREEN, hovered == "start")
    draw_button(surface, settings_rect, "SETTINGS", font_med, CYAN, hovered == "settings")

    return hovered


def draw_settings_screen(surface, game_settings, font_large, font_med, font_small):
    surface.fill(DARK_BG)

    title = font_large.render("SETTINGS", True, WHITE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 130))
    surface.blit(title, title_rect)

    mouse_pos = ui_mouse_pos()
    hovered = None

    options = [
        ("fullscreen", "Fullscreen"),
        ("particles", "Particles"),
        ("damage_numbers", "Damage Numbers"),
    ]
    start_y = 230
    row_h = 60
    gap = 15
    for i, (key, label) in enumerate(options):
        ry = start_y + i * (row_h + gap)
        rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, ry, 400, row_h)
        if rect.collidepoint(mouse_pos):
            hovered = f"toggle:{key}"
        state = "ON" if game_settings[key] else "OFF"
        color = GREEN if game_settings[key] else RED
        draw_button(surface, rect, f"{label}: {state}", font_med, color, hovered == f"toggle:{key}")

    back_rect = pygame.Rect(
        SCREEN_WIDTH // 2 - 140,
        start_y + len(options) * (row_h + gap) + 30, 280, 60,
    )
    if back_rect.collidepoint(mouse_pos):
        hovered = "back"
    draw_button(surface, back_rect, "BACK", font_med, YELLOW, hovered == "back")

    return hovered


def draw_difficulty_screen(surface, font_large, font_med, font_small):
    surface.fill(DARK_BG)

    title = font_large.render("SELECT DIFFICULTY", True, WHITE)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
    surface.blit(title, title_rect)

    keys = list(DIFFICULTIES.keys())
    box_w = 260
    box_h = 160
    gap = 30
    total_w = len(keys) * box_w + (len(keys) - 1) * gap
    start_x = (SCREEN_WIDTH - total_w) // 2
    start_y = 250

    mouse_pos = ui_mouse_pos()
    hovered_key = None

    for i, key in enumerate(keys):
        diff = DIFFICULTIES[key]
        bx = start_x + i * (box_w + gap)
        by = start_y
        rect = pygame.Rect(bx, by, box_w, box_h)
        is_hovered = rect.collidepoint(mouse_pos)
        if is_hovered:
            hovered_key = key

        bg_color = (40, 40, 55) if not is_hovered else (60, 60, 90)
        border_color = diff["color"] if is_hovered else GRAY

        pygame.draw.rect(surface, bg_color, rect, border_radius=10)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=10)

        label = font_large.render(diff["label"], True, diff["color"])
        surface.blit(label, (bx + box_w // 2 - label.get_width() // 2, by + 20))

        desc = font_small.render(diff["description"], True, LIGHT_GRAY)
        surface.blit(desc, (bx + box_w // 2 - desc.get_width() // 2, by + 70))

        stats_lines = [
            f"Enemy HP: {int(diff['hp_mult'] * 100)}%",
            f"Spawn Rate: {int((1 / diff['spawn_mult']) * 100)}%",
            f"Damage: {int(diff['dmg_mult'] * 100)}%",
        ]
        sy = by + 100
        for line in stats_lines:
            st = font_small.render(line, True, GRAY)
            surface.blit(st, (bx + box_w // 2 - st.get_width() // 2, sy))
            sy += 20

    hint = font_small.render("Click a difficulty or press 1 / 2 / 3", True, GRAY)
    hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, start_y + box_h + 40))
    surface.blit(hint, hint_rect)

    return hovered_key


def draw_game_over(surface, player, game_time, font_large, font_med, font_small):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    title = font_large.render("GAME OVER", True, RED)
    title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 200))
    surface.blit(title, title_rect)

    minutes = int(game_time) // 60
    seconds = int(game_time) % 60

    stats = [
        f"Survived: {minutes:02d}:{seconds:02d}",
        f"Level: {player.level}",
        f"Kills: {player.total_kills}",
    ]
    y = 300
    for line in stats:
        text = font_med.render(line, True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
        surface.blit(text, rect)
        y += 45

    pulse = abs((pygame.time.get_ticks() % 1500) - 750) / 750
    start_color = tuple(int(255 * (0.5 + 0.5 * pulse)) for _ in range(3))
    restart_text = font_med.render("CLICK TO RESTART", True, start_color)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
    surface.blit(restart_text, restart_rect)

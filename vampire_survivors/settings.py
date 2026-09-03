import pygame
import os

# Asset paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEX_DIR = os.path.join(ASSETS_DIR, "256x256")
GROUND_TEXTURE = "256_Stone Rubble 02.png"

# World tiles
TILE_SIZE = 256
PATH_H_SEGMENTS = ["256_Path Dirt Horizontal 01.png", "256_Path Dirt Horizontal 02.png",
                   "256_Path Dirt Horizontal 03.png", "256_Path Dirt Horizontal 04.png",
                   "256_Path Dirt Horizontal 05.png", "256_Path Dirt Horizontal 06.png",
                   "256_Path Dirt Horizontal 07.png", "256_Path Dirt Horizontal 08.png",
                   "256_Path Dirt Horizontal 09.png", "256_Path Dirt Horizontal 010.png"]
PATH_V_SEGMENTS = ["256_Path Dirt Vertical 01.png", "256_Path Dirt Vertical 02.png",
                   "256_Path Dirt Vertical 03.png", "256_Path Dirt Vertical 04.png",
                   "256_Path Dirt Vertical 05.png", "256_Path Dirt Vertical 06.png",
                   "256_Path Dirt Vertical 07.png", "256_Path Dirt Vertical 08.png",
                   "256_Path Dirt Vertical 09.png", "256_Path Dirt Vertical 010.png"]
PATH_JUNCTIONS = ["256_Path Dirt Junction 01.png", "256_Path Dirt Junction 02.png",
                  "256_Path Dirt Junction 03.png", "256_Path Dirt Junction 04.png",
                  "256_Path Dirt Junction 05.png", "256_Path Dirt Junction 06.png",
                  "256_Path Dirt Junction 07.png", "256_Path Dirt Junction 08.png"]

# Display
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
TITLE = "Vampire Survivors - Python Edition"

# Fullscreen display resolution
FULLSCREEN_W = 1920
FULLSCREEN_H = 1080

# View mapping: game canvas is always SCREEN_WIDTH x SCREEN_HEIGHT,
# letterboxed onto the display when fullscreen. Updated by apply_display_mode.
VIEW = {"scale": 1.0, "ox": 0, "oy": 0, "w": SCREEN_WIDTH, "h": SCREEN_HEIGHT}

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (50, 220, 50)
BLUE = (50, 120, 220)
YELLOW = (255, 220, 50)
ORANGE = (255, 160, 50)
BROWN = (160, 110, 60)
PURPLE = (180, 50, 220)
CYAN = (50, 220, 220)
DARK_GRAY = (40, 40, 50)
GRAY = (100, 100, 110)
LIGHT_GRAY = (180, 180, 190)
DARK_RED = (120, 20, 20)
DARK_GREEN = (20, 100, 20)
DARK_BG = (25, 25, 35)

# Player
PLAYER_SPEED = 250
PLAYER_MAX_HP = 100
PLAYER_SIZE = 28
PLAYER_INVINCIBLE_TIME = 500  # ms

# Ring of Fire sprite (2x2 grid of 1024px cells)
FIRE_SPRITE = os.path.join(ASSETS_DIR, "FireballAssets.png")
FIRE_COLS = 2
FIRE_ROWS = 2
FIRE_CELL = 1024
FIRE_DISPLAY_SIZE = 36
FIRE_ANIM_SPEED = 0.12  # seconds per frame
# Player sprite
PLAYER_SPRITE_WALK = os.path.join(ASSETS_DIR, "48x48", "Char_001.png")
PLAYER_SPRITE_IDLE = os.path.join(ASSETS_DIR, "48x48", "Char_001_Idle.png")
SPRITE_FRAME = 72  # cell size in the sheet
SPRITE_COLS = 4
SPRITE_ROWS = ["down", "left", "right", "up"]
PLAYER_SPRITE_SIZE = 48  # display size (hitbox stays PLAYER_SIZE)
WALK_ANIM_SPEED = 0.12  # seconds per frame
IDLE_ANIM_SPEED = 0.35  # seconds per frame

# Dash
DASH_SPEED = 800
DASH_DURATION = 0.12  # seconds
DASH_COOLDOWN = 7.5  # seconds
DASH_INVINCIBLE = True
DASH_CD_REDUCTION = 0.5  # cooldown reduction per Swift Dash level
DASH_LEVEL_MAX = 10
DASH_DISTANCE_MULT = 1.5  # dash distance multiplier from first Swift Dash level
DASH_MIN_COOLDOWN = 1.0  # cooldown floor

# Quantum Dash (splash damage at dash end)
QUANTUM_RADIUS = 100
QUANTUM_BASE = 15
QUANTUM_PER_LEVEL = 5

# Enemies
ENEMY_SPAWN_DISTANCE = 50
ENEMY_BASE_SPEED = 60
ENEMY_BASE_HP = 20
ENEMY_BASE_DAMAGE = 10
ENEMY_BASE_XP = 10
ENEMY_SPAWN_INTERVAL_BASE = 1500  # ms
ENEMY_SPAWN_INTERVAL_MIN = 300

# XP
XP_MAGNET_RANGE = 80
XP_COLLECT_RANGE = 20
XP_FLOAT_SPEED = 300

# Leveling
XP_BASE = 50
XP_GROWTH = 1.35

# Upgrade choices per level
UPGRADE_CHOICES = 3

# Difficulty presets: spawn_mult = faster spawns, hp_mult/dmg_mult/spd_mult = harder enemies
DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "color": GREEN,
        "spawn_mult": 1.0,
        "hp_mult": 0.7,
        "dmg_mult": 0.7,
        "spd_mult": 0.85,
        "xp_mult": 1.2,
        "description": "Enemies are weaker & slower",
    },
    "normal": {
        "label": "Normal",
        "color": YELLOW,
        "spawn_mult": 1.0,
        "hp_mult": 1.0,
        "dmg_mult": 1.0,
        "spd_mult": 1.0,
        "xp_mult": 1.0,
        "description": "The balanced experience",
    },
    "hard": {
        "label": "Hard",
        "color": RED,
        "spawn_mult": 0.6,
        "hp_mult": 1.5,
        "dmg_mult": 1.3,
        "spd_mult": 1.15,
        "xp_mult": 0.8,
        "description": "More enemies, much deadlier",
    },
}

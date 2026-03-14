import engine_main

import random
import math

import engine
import engine_io
import engine_draw
import engine_audio
import engine_save
from engine_nodes import Rectangle2DNode, CameraNode, Text2DNode
from engine_resources import FontResource, ToneSoundResource
from engine_math import Vector2
from engine_draw import Color


# =============================================================================
# Constants
# =============================================================================

# Physics (Y-down: +Y = down on screen)
GRAVITY = 0.35
JUMP_VEL = -5.0
GROUND_Y = 45
PLAYER_X = -30
PLAYER_SIZE = 10
DEATH_Y = 75

# Screen bounds (camera-relative)
SCREEN_MIN = -64
SCREEN_MAX = 64

# Speeds
BASE_SCROLL = 1.5
MAX_SCROLL = 3.5

# Ground
GROUND_SEG_W = 24
GROUND_SEG_H = 20
NUM_GROUND = 12

# Obstacles
NUM_OBSTACLES = 6
OBSTACLE_SPAWN_X = 80
OBSTACLE_HIDE_X = 200

# Particles
NUM_PARTICLES = 5

# Trail
NUM_TRAIL = 3

# Synthwave colors
COL_CYAN = Color(0.0, 1.0, 1.0)
COL_MAGENTA = Color(1.0, 0.0, 1.0)
COL_PINK = Color(1.0, 0.4, 0.7)
COL_PURPLE = Color(0.47, 0.0, 0.53)
COL_DARK_PURPLE = Color(0.15, 0.05, 0.25)
COL_VIOLET = Color(0.57, 0.33, 0.76)

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_DEAD = 2
STATE_RETRY = 3


# =============================================================================
# Engine Setup
# =============================================================================

engine.fps_limit(60)
camera = CameraNode()
font = FontResource("outrunner_outline.bmp")

# Save data
engine_save.set_location("save.data")

# Sound effects
snd_jump = ToneSoundResource()
snd_jump.frequency = 800
snd_death = ToneSoundResource()
snd_death.frequency = 200


# =============================================================================
# Create Nodes
# =============================================================================

# --- Player ---
player = Rectangle2DNode(color=COL_CYAN, width=PLAYER_SIZE, height=PLAYER_SIZE)
player.position = Vector2(PLAYER_X, GROUND_Y - PLAYER_SIZE / 2)
player.layer = 3

# --- Player trail ---
trail = []
for i in range(NUM_TRAIL):
    t = Rectangle2DNode(color=COL_CYAN, width=PLAYER_SIZE, height=PLAYER_SIZE, opacity=0.0)
    t.layer = 2
    trail.append(t)

# --- Ground segments ---
ground_segs = []
ground_is_gap = []
for i in range(NUM_GROUND):
    g = Rectangle2DNode(color=COL_PURPLE, width=GROUND_SEG_W, height=GROUND_SEG_H)
    g.position = Vector2(SCREEN_MIN + i * GROUND_SEG_W + GROUND_SEG_W / 2,
                         GROUND_Y + GROUND_SEG_H / 2)
    g.layer = 1
    ground_segs.append(g)
    ground_is_gap.append(False)

# --- Ground surface line ---
ground_line = Rectangle2DNode(color=COL_MAGENTA, width=300, height=1)
ground_line.position = Vector2(0, GROUND_Y)
ground_line.layer = 2

# --- Synthwave grid lines (below ground) ---
grid_lines = []
for i in range(4):
    y = GROUND_Y + GROUND_SEG_H + 2 + i * 8
    gl = Rectangle2DNode(color=COL_DARK_PURPLE, width=300, height=1,
                         opacity=0.35 - i * 0.07)
    gl.position = Vector2(0, y)
    gl.layer = 0
    grid_lines.append(gl)

# --- Obstacle pool ---
obstacles = []
ob_types = []
ob_active = []
for i in range(NUM_OBSTACLES):
    ob = Rectangle2DNode(width=8, height=8, opacity=0.0)
    ob.position = Vector2(OBSTACLE_HIDE_X, 0)
    ob.layer = 3
    obstacles.append(ob)
    ob_types.append("spike")
    ob_active.append(False)

# --- Background particles ---
particles = []
for i in range(NUM_PARTICLES):
    p = Rectangle2DNode(color=COL_DARK_PURPLE, width=2, height=2, opacity=0.3)
    p.position = Vector2(random.uniform(SCREEN_MIN, SCREEN_MAX),
                         random.uniform(-50, 30))
    p.layer = 0
    particles.append(p)

# --- Screen flash overlay ---
flash = Rectangle2DNode(color=COL_MAGENTA, width=128, height=128, opacity=0.0)
flash.layer = 6

# --- HUD text nodes ---
title_text = Text2DNode(font=font, text="GEODASH", position=Vector2(0, -20),
                        opacity=0.0, layer=7)
title_text.scale = Vector2(2.0, 2.0)

score_text = Text2DNode(font=font, text="0", position=Vector2(0, -55),
                        opacity=0.0, layer=7)

press_a_text = Text2DNode(font=font, text="PRESS A", position=Vector2(0, 10),
                          opacity=0.0, layer=7)

hi_text = Text2DNode(font=font, text="", position=Vector2(0, 0),
                     opacity=0.0, layer=7)


# =============================================================================
# Game State Variables
# =============================================================================

state = STATE_MENU
vel_y = 0.0
on_ground = True
scroll_speed = BASE_SCROLL
score = 0
hi_score = engine_save.load("hi", 0)
spawn_timer = 0
spawn_interval = 90
dead_timer = 0
menu_pulse = 0.0
gap_counter = 0
trail_history = []
snd_jump_timer = 0
snd_death_timer = 0


# =============================================================================
# Helper Functions
# =============================================================================

def reset_game():
    global vel_y, on_ground, scroll_speed, score, spawn_timer, spawn_interval
    global dead_timer, gap_counter, trail_history
    global snd_jump_timer, snd_death_timer

    vel_y = 0.0
    on_ground = True
    scroll_speed = BASE_SCROLL
    score = 0
    spawn_timer = 0
    spawn_interval = 90
    dead_timer = 0
    gap_counter = 0
    trail_history = []
    snd_jump_timer = 0
    snd_death_timer = 0

    # Stop any playing sounds
    engine_audio.stop(0)
    engine_audio.stop(1)

    # Reset player
    player.position = Vector2(PLAYER_X, GROUND_Y - PLAYER_SIZE / 2)
    player.rotation = 0.0
    player.opacity = 1.0

    # Reset ground
    for i in range(NUM_GROUND):
        ground_segs[i].position.x = (SCREEN_MIN + i * GROUND_SEG_W
                                     + GROUND_SEG_W / 2)
        ground_segs[i].opacity = 1.0
        ground_is_gap[i] = False

    # Reset obstacles
    for i in range(NUM_OBSTACLES):
        obstacles[i].position = Vector2(OBSTACLE_HIDE_X, 0)
        obstacles[i].opacity = 0.0
        ob_active[i] = False

    # Reset trail
    for t in trail:
        t.opacity = 0.0

    # Reset flash
    flash.opacity = 0.0


def spawn_obstacle():
    global spawn_timer
    for i in range(NUM_OBSTACLES):
        if not ob_active[i]:
            ob_active[i] = True
            if random.random() < 0.5:
                # Spike
                ob_types[i] = "spike"
                obstacles[i].width = 8
                obstacles[i].height = 8
                obstacles[i].color = COL_PINK
                obstacles[i].rotation = math.pi / 4
                obstacles[i].position = Vector2(OBSTACLE_SPAWN_X,
                                                GROUND_Y - 4)
            else:
                # Block
                ob_types[i] = "block"
                h = random.choice([10, 15, 20])
                obstacles[i].width = 10
                obstacles[i].height = h
                obstacles[i].color = COL_VIOLET
                obstacles[i].rotation = 0.0
                obstacles[i].position = Vector2(OBSTACLE_SPAWN_X,
                                                GROUND_Y - h / 2)
            obstacles[i].opacity = 1.0
            break
    spawn_timer = 0


def check_collision():
    px = player.position.x
    py = player.position.y
    pw = PLAYER_SIZE * 0.8
    ph = PLAYER_SIZE * 0.8

    for i in range(NUM_OBSTACLES):
        if not ob_active[i]:
            continue
        ox = obstacles[i].position.x
        oy = obstacles[i].position.y

        if ob_types[i] == "spike":
            ow = 8 * 0.7
            oh = 8 * 0.7
        else:
            ow = obstacles[i].width
            oh = obstacles[i].height

        if (abs(px - ox) < (pw + ow) / 2 and
                abs(py - oy) < (ph + oh) / 2):
            return True
    return False


def player_over_gap():
    px = player.position.x
    for i in range(NUM_GROUND):
        gx = ground_segs[i].position.x
        if abs(px - gx) < GROUND_SEG_W / 2 and ground_is_gap[i]:
            return True
    return False


def trigger_death():
    global state, dead_timer, snd_death_timer
    state = STATE_DEAD
    dead_timer = 0
    flash.opacity = 0.8
    engine_audio.stop(0)
    engine_audio.play(snd_death, 1, False)
    snd_death_timer = 30
    engine_io.rumble(0.5)


# =============================================================================
# Main Game Loop
# =============================================================================

while True:
    if engine.tick():

        # =============
        # STATE: MENU
        # =============
        if state == STATE_MENU:
            title_text.opacity = 1.0
            press_a_text.opacity = 1.0
            score_text.opacity = 0.0
            hi_text.opacity = 0.0

            # Show high score on menu if exists
            if hi_score > 0:
                hi_text.text = "BEST " + str(hi_score)
                hi_text.opacity = 1.0
                hi_text.position.y = 30

            # Pulsing player animation
            menu_pulse += 0.05
            player.opacity = 0.6 + 0.4 * math.sin(menu_pulse)
            player.position.y = (GROUND_Y - PLAYER_SIZE / 2
                                 + 3 * math.sin(menu_pulse * 1.5))

            if engine_io.A.is_just_pressed:
                state = STATE_PLAYING
                reset_game()
                title_text.opacity = 0.0
                press_a_text.opacity = 0.0
                hi_text.opacity = 0.0
                score_text.opacity = 1.0

        # ===============
        # STATE: PLAYING
        # ===============
        elif state == STATE_PLAYING:
            # Score
            score += 1
            display_score = score // 6
            score_text.text = str(display_score)

            # Difficulty scaling
            scroll_speed = min(BASE_SCROLL + display_score * 0.005, MAX_SCROLL)
            spawn_interval = max(45, 90 - display_score // 4)

            # --- Jump ---
            if engine_io.A.is_just_pressed and on_ground:
                vel_y = JUMP_VEL
                on_ground = False
                engine_audio.play(snd_jump, 0, False)
                snd_jump_timer = 8

            # --- Sound timers ---
            if snd_jump_timer > 0:
                snd_jump_timer -= 1
                if snd_jump_timer == 0:
                    engine_audio.stop(0)
            if snd_death_timer > 0:
                snd_death_timer -= 1
                if snd_death_timer == 0:
                    engine_audio.stop(1)

            # --- Gravity & position ---
            vel_y += GRAVITY
            player.position.y += vel_y

            # --- Ground collision (Y-down: ground at +45, player above = lower Y) ---
            over_gap = player_over_gap()
            if (not over_gap and
                    player.position.y >= GROUND_Y - PLAYER_SIZE / 2):
                player.position.y = GROUND_Y - PLAYER_SIZE / 2
                vel_y = 0.0
                if not on_ground:
                    # Snap rotation to nearest 90 degrees
                    snap = math.pi / 2
                    player.rotation = round(player.rotation / snap) * snap
                on_ground = True
            elif over_gap or player.position.y < GROUND_Y - PLAYER_SIZE / 2:
                on_ground = False

            # Rotate while airborne
            if not on_ground:
                player.rotation += 0.12

            # --- Trail ---
            trail_history.insert(0, (player.position.x, player.position.y,
                                     player.rotation))
            if len(trail_history) > 12:
                trail_history.pop()

            for i in range(NUM_TRAIL):
                idx = (i + 1) * 3
                if idx < len(trail_history):
                    tx, ty, tr = trail_history[idx]
                    trail[i].position = Vector2(tx, ty)
                    trail[i].rotation = tr
                    trail[i].opacity = 0.25 - i * 0.07
                else:
                    trail[i].opacity = 0.0

            # --- Scroll ground ---
            for i in range(NUM_GROUND):
                ground_segs[i].position.x -= scroll_speed
                if ground_segs[i].position.x < SCREEN_MIN - GROUND_SEG_W:
                    # Recycle to the rightmost position
                    rightmost_x = SCREEN_MIN
                    for g in ground_segs:
                        if g.position.x > rightmost_x:
                            rightmost_x = g.position.x
                    ground_segs[i].position.x = rightmost_x + GROUND_SEG_W

                    # Random gap generation (no gaps until score 50)
                    gap_counter += 1
                    if (display_score >= 50 and gap_counter >= 5 and
                            random.random() < 0.08 + display_score * 0.0005):
                        ground_is_gap[i] = True
                        ground_segs[i].opacity = 0.0
                        gap_counter = 0
                    else:
                        ground_is_gap[i] = False
                        ground_segs[i].opacity = 1.0

            # --- Scroll obstacles ---
            for i in range(NUM_OBSTACLES):
                if ob_active[i]:
                    obstacles[i].position.x -= scroll_speed
                    if obstacles[i].position.x < SCREEN_MIN - 20:
                        ob_active[i] = False
                        obstacles[i].opacity = 0.0
                        obstacles[i].position.x = OBSTACLE_HIDE_X

            # --- Spawn obstacles ---
            spawn_timer += 1
            if spawn_timer >= spawn_interval:
                spawn_obstacle()

            # --- Scroll particles (50% parallax) ---
            for p in particles:
                p.position.x -= scroll_speed * 0.5
                if p.position.x < SCREEN_MIN - 5:
                    p.position.x = SCREEN_MAX + 5
                    p.position.y = random.uniform(-50, 30)

            # --- Check collisions ---
            if check_collision():
                trigger_death()

            # --- Pit death ---
            if player.position.y > DEATH_Y:
                trigger_death()

        # =============
        # STATE: DEAD
        # =============
        elif state == STATE_DEAD:
            dead_timer += 1

            # Sound timer
            if snd_death_timer > 0:
                snd_death_timer -= 1
                if snd_death_timer == 0:
                    engine_audio.stop(1)

            # Flash fade-out
            if dead_timer < 10:
                flash.opacity = 0.8 * (1.0 - dead_timer / 10.0)
            else:
                flash.opacity = 0.0

            # Stop rumble
            if dead_timer == 15:
                engine_io.rumble(0.0)

            # Hide trail
            for t in trail:
                t.opacity = 0.0

            # Transition to retry after ~1 second
            if dead_timer >= 60:
                state = STATE_RETRY
                display_score = score // 6

                # Update high score
                if display_score > hi_score:
                    hi_score = display_score
                    engine_save.save("hi", hi_score)

                score_text.text = str(display_score)
                score_text.position.y = -10
                hi_text.text = "BEST " + str(hi_score)
                hi_text.opacity = 1.0
                hi_text.position.y = 10
                press_a_text.opacity = 1.0
                press_a_text.position.y = 30

        # ==============
        # STATE: RETRY
        # ==============
        elif state == STATE_RETRY:
            if engine_io.A.is_just_pressed:
                state = STATE_PLAYING
                reset_game()
                press_a_text.opacity = 0.0
                hi_text.opacity = 0.0
                score_text.opacity = 1.0
                score_text.position.y = -55
                press_a_text.position.y = 10

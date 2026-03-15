import engine_main

import random
import math

import engine
import engine_io
import engine_draw
import engine_audio
import engine_save
from engine_nodes import Rectangle2DNode, CameraNode, Text2DNode
from engine_resources import FontResource, ToneSoundResource, WaveSoundResource
from engine_math import Vector2
from engine_draw import Color


# =============================================================================
# Constants
# =============================================================================

# Physics (Y-down: +Y = down on screen)
GRAVITY = 0.70
JUMP_VEL = -10.0
GROUND_Y = 45
PLAYER_X = -30
PLAYER_SIZE = 20
DEATH_Y = 75

# Screen bounds (camera-relative)
SCREEN_MIN = -64
SCREEN_MAX = 64

# Speeds
BASE_SCROLL = 4.5
MAX_SCROLL = 7.0

# Ground
GROUND_SEG_W = 48
GROUND_SEG_H = 40
NUM_GROUND = 12

# Obstacles
NUM_OBSTACLES = 6
OBSTACLE_SPAWN_X = 80
OBSTACLE_HIDE_X = 200

# Particles
NUM_PARTICLES = 8
NUM_STARS = 12

# Death particles
NUM_DEATH_PARTICLES = 20

# Trail
NUM_TRAIL = 3

# Synthwave colors
COL_CYAN = Color(0.0, 1.0, 1.0)
COL_MAGENTA = Color(1.0, 0.0, 1.0)
COL_PINK = Color(1.0, 0.4, 0.7)
COL_PURPLE = Color(0.47, 0.0, 0.53)
COL_DARK_PURPLE = Color(0.15, 0.05, 0.25)
COL_VIOLET = Color(0.57, 0.33, 0.76)
COL_HOT_PINK = Color(1.0, 0.1, 0.5)
COL_SUNSET_ORANGE = Color(1.0, 0.3, 0.1)
COL_SUNSET_YELLOW = Color(1.0, 0.6, 0.1)
COL_DEEP_BLUE = Color(0.05, 0.0, 0.15)

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
hud_font = FontResource("/system/assets/font5x7.bmp")

# Save data
engine_save.set_location("save.data")

# Sound effects
snd_jump = ToneSoundResource()
snd_jump.frequency = 800
snd_death = ToneSoundResource()
snd_death.frequency = 200
snd_bgm = None


# =============================================================================
# Create Nodes
# =============================================================================

# --- Player ---
player = Rectangle2DNode(color=COL_CYAN, width=PLAYER_SIZE, height=PLAYER_SIZE, opacity=0.0)
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

# --- Sky gradient (horizon bands) ---
sky_bands = []
sky_colors = [COL_DEEP_BLUE, COL_DARK_PURPLE, COL_PURPLE, COL_HOT_PINK,
              COL_SUNSET_ORANGE, COL_SUNSET_YELLOW]
band_h = 16
for i, col in enumerate(sky_colors):
    b = Rectangle2DNode(color=col, width=300, height=band_h,
                        opacity=0.6 if i < 3 else 0.45)
    b.position = Vector2(0, -64 + i * band_h + band_h / 2)
    b.layer = 0
    sky_bands.append(b)

# --- Sun glow ---
SUN_START_Y = -50
SUN_END_Y = GROUND_Y - 10
sun = Rectangle2DNode(color=COL_SUNSET_YELLOW, width=30, height=16, opacity=0.5)
sun.position = Vector2(0, SUN_START_Y)
sun.layer = 0
sun_halo = Rectangle2DNode(color=COL_SUNSET_ORANGE, width=50, height=24, opacity=0.25)
sun_halo.position = Vector2(0, SUN_START_Y + 2)
sun_halo.layer = 0

# --- Synthwave grid lines (below ground, perspective spacing) ---
grid_lines = []
grid_y_offsets = [3, 8, 15, 24, 36]
for i, dy in enumerate(grid_y_offsets):
    y = GROUND_Y + dy
    gl = Rectangle2DNode(color=COL_MAGENTA, width=300, height=1,
                         opacity=0.5 - i * 0.08)
    gl.position = Vector2(0, y)
    gl.layer = 0
    grid_lines.append(gl)

# --- Horizon line glow ---
horizon_glow = Rectangle2DNode(color=COL_MAGENTA, width=300, height=2, opacity=0.3)
horizon_glow.position = Vector2(0, GROUND_Y + 1)
horizon_glow.layer = 0

# --- Obstacle pool ---
obstacles = []
ob_types = []
ob_active = []
for i in range(NUM_OBSTACLES):
    ob = Rectangle2DNode(width=16, height=16, opacity=0.0)
    ob.position = Vector2(OBSTACLE_HIDE_X, 0)
    ob.layer = 3
    obstacles.append(ob)
    ob_types.append("spike")
    ob_active.append(False)

# --- Background particles (neon streaks, parallax) ---
particles = []
particle_colors = [COL_CYAN, COL_PINK, COL_MAGENTA, COL_HOT_PINK]
for i in range(NUM_PARTICLES):
    col = particle_colors[i % len(particle_colors)]
    p = Rectangle2DNode(color=col, width=3, height=1, opacity=0.4)
    p.position = Vector2(random.uniform(SCREEN_MIN, SCREEN_MAX),
                         random.uniform(-60, 20))
    p.layer = 0
    particles.append(p)

# --- Stars (tiny dots in the sky) ---
stars = []
for i in range(NUM_STARS):
    s = Rectangle2DNode(color=COL_CYAN, width=1, height=1,
                        opacity=random.uniform(0.15, 0.5))
    s.position = Vector2(random.uniform(SCREEN_MIN, SCREEN_MAX),
                         random.uniform(-64, -10))
    s.layer = 0
    stars.append(s)

# --- Death explosion particles ---
death_particles = []
death_vels = []
for i in range(NUM_DEATH_PARTICLES):
    dp = Rectangle2DNode(color=COL_CYAN, width=4, height=4, opacity=0.0)
    dp.layer = 5
    death_particles.append(dp)
    death_vels.append((0.0, 0.0))

# --- Screen flash overlay ---
flash = Rectangle2DNode(color=COL_MAGENTA, width=128, height=128, opacity=0.0)
flash.layer = 6

# --- HUD text nodes ---
title_text = Text2DNode(font=font, text="GEODASH", position=Vector2(0, -20),
                        opacity=0.0, layer=7)
title_text.scale = Vector2(2.0, 2.0)

score_text = Text2DNode(font=hud_font, text="0", position=Vector2(0, -55),
                        opacity=0.0, layer=7, scale=Vector2(2.0, 2.0))

press_a_text = Text2DNode(font=hud_font, text="PRESS A", position=Vector2(0, 10),
                          opacity=0.0, layer=7, scale=Vector2(2.0, 2.0))

hi_text = Text2DNode(font=hud_font, text="", position=Vector2(0, 0),
                     opacity=0.0, layer=7, scale=Vector2(2.0, 2.0))


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
post_gap_cooldown = 0
falling_in_pit = False
trail_history = []
snd_jump_timer = 0
snd_death_timer = 0


# =============================================================================
# Helper Functions
# =============================================================================

def reset_game():
    global vel_y, on_ground, scroll_speed, score, spawn_timer, spawn_interval
    global dead_timer, gap_counter, post_gap_cooldown, falling_in_pit, trail_history
    global snd_jump_timer, snd_death_timer

    vel_y = 0.0
    on_ground = True
    scroll_speed = BASE_SCROLL
    score = 0
    spawn_timer = 0
    spawn_interval = 90
    dead_timer = 0
    gap_counter = 0
    post_gap_cooldown = 0
    falling_in_pit = False
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

    # Reset death particles
    for dp in death_particles:
        dp.opacity = 0.0

    # Reset sun
    sun.position.y = SUN_START_Y
    sun_halo.position.y = SUN_START_Y + 2


def gap_near_spawn():
    """Check if any gap is between the player and the spawn zone."""
    for i in range(NUM_GROUND):
        if ground_is_gap[i] and ground_segs[i].position.x > PLAYER_X - GROUND_SEG_W:
            return True
    return False


def obstacle_too_close():
    """Check if any active obstacle is still near the spawn zone."""
    for i in range(NUM_OBSTACLES):
        if ob_active[i] and obstacles[i].position.x > 20:
            return True
    return False


def spawn_obstacle():
    global spawn_timer
    # Don't spawn if too close to another obstacle, near a gap, or in post-gap cooldown
    if obstacle_too_close() or gap_near_spawn() or post_gap_cooldown > 0:
        return
    for i in range(NUM_OBSTACLES):
        if not ob_active[i]:
            ob_active[i] = True
            if random.random() < 0.5:
                # Spike
                ob_types[i] = "spike"
                obstacles[i].width = 16
                obstacles[i].height = 16
                obstacles[i].color = COL_PINK
                obstacles[i].rotation = math.pi / 4
                obstacles[i].position = Vector2(OBSTACLE_SPAWN_X,
                                                GROUND_Y - 8)
            else:
                # Block
                ob_types[i] = "block"
                h = random.choice([20, 30, 40])
                obstacles[i].width = 20
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
            ow = 16 * 0.7
            oh = 16 * 0.7
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
    global state, dead_timer, snd_death_timer, death_vels
    state = STATE_DEAD
    dead_timer = 0
    flash.opacity = 0.8

    # Spawn explosion particles in 3 layers (fast/medium/slow)
    px = player.position.x
    py = player.position.y
    for i in range(NUM_DEATH_PARTICLES):
        angle = random.uniform(0, 2 * math.pi)
        layer = i % 3
        if layer == 0:
            speed = random.uniform(3.0, 4.5)
            sz = 3
        elif layer == 1:
            speed = random.uniform(1.5, 2.5)
            sz = 4
        else:
            speed = random.uniform(0.5, 1.2)
            sz = 5
        death_vels[i] = (math.cos(angle) * speed, math.sin(angle) * speed)
        death_particles[i].position = Vector2(px, py)
        death_particles[i].width = sz
        death_particles[i].height = sz
        death_particles[i].opacity = 1.0
        col = random.choice([COL_CYAN, COL_PINK, COL_MAGENTA])
        death_particles[i].color = col
    player.opacity = 0.0

    engine_audio.stop(0)
    engine_audio.stop(2)
    engine_audio.play(snd_death, 1, False)
    snd_death_timer = 30
    engine_io.rumble(0.5)


# =============================================================================
# Main Game Loop
# =============================================================================

while True:
    if engine.tick():

        # --- Quit to launcher ---
        if engine_io.MENU.is_just_pressed:
            break

        # =============
        # STATE: MENU
        # =============
        if state == STATE_MENU:
            title_text.opacity = 1.0
            press_a_text.text = "Press A"
            press_a_text.opacity = 1.0
            hi_text.text = "To Start"
            hi_text.opacity = 1.0
            hi_text.position.y = 30
            score_text.opacity = 0.0

            # Pulsing player animation (subtle)
            menu_pulse += 0.05
            player.opacity = 0.15 + 0.15 * math.sin(menu_pulse)
            player.position.y = (GROUND_Y - PLAYER_SIZE / 2
                                 + 3 * math.sin(menu_pulse * 1.5))

            if engine_io.A.is_just_pressed:
                state = STATE_PLAYING
                reset_game()
                title_text.opacity = 0.0
                press_a_text.opacity = 0.0
                hi_text.opacity = 0.0
                score_text.opacity = 1.0
                snd_bgm = WaveSoundResource("bgm.wav")
                engine_audio.play(snd_bgm, 2, True)

        # ===============
        # STATE: PLAYING
        # ===============
        elif state == STATE_PLAYING:
            # Score
            score += 1
            display_score = score // 6
            score_text.text = str(display_score)

            # Difficulty scaling (step every 100 pts)
            speed_level = display_score // 100
            scroll_speed = min(BASE_SCROLL + speed_level * 0.5, MAX_SCROLL)
            spawn_interval = max(60, 90 - speed_level * 5)

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
            if over_gap:
                post_gap_cooldown = 45  # frames to land + jump again
                if player.position.y >= GROUND_Y and vel_y > 0:
                    falling_in_pit = True
            elif post_gap_cooldown > 0:
                post_gap_cooldown -= 1

            # Once falling into a pit, don't catch on the next ground segment
            if falling_in_pit:
                on_ground = False
            elif (not over_gap and
                    player.position.y >= GROUND_Y - PLAYER_SIZE / 2):
                player.position.y = GROUND_Y - PLAYER_SIZE / 2
                vel_y = 0.0
                if not on_ground:
                    player.rotation = 0.0
                on_ground = True
            elif player.position.y < GROUND_Y - PLAYER_SIZE / 2:
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

            # --- Sun descent ---
            sun_y = min(SUN_START_Y + display_score * 0.15, SUN_END_Y)
            sun.position.y = sun_y
            sun_halo.position.y = sun_y + 2

            # --- Scroll particles (neon streaks, 50% parallax) ---
            for p in particles:
                p.position.x -= scroll_speed * 0.5
                if p.position.x < SCREEN_MIN - 5:
                    p.position.x = SCREEN_MAX + 5
                    p.position.y = random.uniform(-60, 20)

            # --- Scroll stars (20% parallax, twinkle) ---
            for s in stars:
                s.position.x -= scroll_speed * 0.2
                if s.position.x < SCREEN_MIN - 2:
                    s.position.x = SCREEN_MAX + 2
                    s.position.y = random.uniform(-64, -10)
                # Twinkle
                s.opacity = random.uniform(0.1, 0.5)

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

            # Animate death particles
            for i in range(NUM_DEATH_PARTICLES):
                if death_particles[i].opacity > 0:
                    vx, vy = death_vels[i]
                    death_particles[i].position.x += vx
                    death_particles[i].position.y += vy
                    death_particles[i].opacity = max(0, 1.0 - dead_timer / 30.0)

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

                player.opacity = 0.15
                title_text.opacity = 1.0
                title_text.position.y = -40
                score_text.text = str(display_score)
                score_text.position.y = -15
                hi_text.text = "BEST " + str(hi_score)
                hi_text.opacity = 1.0
                hi_text.position.y = 10
                press_a_text.text = "Try Again?"
                press_a_text.opacity = 1.0
                press_a_text.position.y = 30

        # ==============
        # STATE: RETRY
        # ==============
        elif state == STATE_RETRY:
            if engine_io.A.is_just_pressed:
                state = STATE_PLAYING
                reset_game()
                title_text.opacity = 0.0
                press_a_text.opacity = 0.0
                hi_text.opacity = 0.0
                score_text.opacity = 1.0
                score_text.position.y = -55
                press_a_text.position.y = 10
                snd_bgm = WaveSoundResource("bgm.wav")
                engine_audio.play(snd_bgm, 2, True)

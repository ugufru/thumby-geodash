# GeoDash Development Guide

Engine API reference and patterns for Thumby Color game development.

## Coordinate System

- Camera sits at origin (0, 0)
- Screen shows **-64 to +64** on both axes (128x128 pixels)
- **Y-up**: positive Y = top of screen
- Node positions are relative to camera

## Core Engine Modules

### engine_main
Must be imported **first** — initializes the engine runtime.

### engine
- `engine.fps_limit(60)` — cap frame rate
- `engine.tick()` — advance one frame, returns `True` when a frame is ready
- `engine.root_dir()` — game's root directory path

### engine_draw
Color constants: `black`, `white`, `red`, `green`, `blue`, `yellow`

Custom colors via `Color(r, g, b)` where r/g/b are 0.0–1.0 floats.

Direct draw API (pixel coordinates 0–128, alternative to node rendering):
- `engine_draw.clear(0)` / `engine_draw.update()`
- `engine_draw.rect(color, x, y, w, h, filled, opacity)`
- `engine_draw.line(color, x1, y1, x2, y2, opacity)`
- `engine_draw.circle(color, x, y, radius, filled, opacity)`
- `engine_draw.text(font, text, color, x, y, scale_x, scale_y, opacity)`

### engine_io
- `engine_io.A.is_just_pressed` — true on the frame the button is first pressed
- `engine_io.A.is_pressed` — true while held
- Buttons: `A`, `B`, `LB`, `RB`, `UP`, `DOWN`, `LEFT`, `RIGHT`
- `engine_io.rumble(intensity)` — 0.0 to 1.0 (0.0 = off)

### engine_nodes
- `Rectangle2DNode(color, width, height, opacity, layer, outline)` — colored rectangle
- `Circle2DNode(color, radius, outline)` — colored circle
- `Sprite2DNode(texture, frame_count_x)` — sprite from texture
- `Text2DNode(font, text, position, opacity, layer, letter_spacing, scale)` — text display
- `CameraNode()` — required for node rendering
- `EmptyNode()` — invisible container for grouping

Common node properties:
- `.position` (Vector2), `.rotation` (radians), `.scale` (Vector2)
- `.opacity` (0.0–1.0), `.layer` (int, higher = on top)
- `.width`, `.height`, `.color`
- `.add_child(node)`, `.mark_destroy()`

### engine_resources
- `FontResource("font.bmp")` — load bitmap font
- `TextureResource("sprite.bmp")` — load sprite texture
- `ToneSoundResource()` — synthesized tone (`.frequency` property)
- `WaveSoundResource("file.wav")` — WAV playback
- `RTTTLSoundResource("file.rtttl")` — ringtone melody

### engine_audio
- `engine_audio.play(resource, channel, loop)` — play on channel 0–3
- `engine_audio.stop(channel)` — stop playback
- `engine_audio.set_volume(level)` — global volume

### engine_save
- `engine_save.set_location("save.data")` — set save file
- `engine_save.save(key, value)` — persist (str, int, float, Vector2, etc.)
- `engine_save.load(key, default)` — load with fallback
- `engine_save.delete(key)` — remove key
- Engine auto-creates `/Saves/GameName/` directory

### engine_math
- `Vector2(x, y)` — 2D vector with `.x`, `.y`
- `Vector3(x, y, z)` — 3D vector

## Game Loop Pattern

```python
import engine_main  # MUST be first

import engine
from engine_nodes import CameraNode

engine.fps_limit(60)
camera = CameraNode()

while True:
    if engine.tick():
        # Game logic runs here at 60fps
        pass
```

## Text Rendering

```python
from engine_resources import FontResource
from engine_nodes import Text2DNode
from engine_math import Vector2

font = FontResource("outrunner_outline.bmp")
label = Text2DNode(font=font, text="HELLO", position=Vector2(0, 50), layer=7)
label.scale = Vector2(1.5, 1.5)
label.opacity = 1.0
```

Font bitmaps are shared engine assets. `outrunner_outline.bmp` is the standard game font.

## Deployment

1. Connect Thumby Color via USB-C
2. Open Thonny — device filesystem appears in the file browser
3. Create `/Games/GeoDash/` on the device
4. Upload all game files: `main.py`, `manifest.ini`, `icon.bmp`, `outrunner_outline.bmp`
5. Reset device or navigate to game in launcher

### manifest.ini format
```ini
name = GeoDash
main = main.py
icon = icon.bmp
```

The launcher auto-discovers games in `/Games/` directories that contain a `manifest.ini` or `main.py`.

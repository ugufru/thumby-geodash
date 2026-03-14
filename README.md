# GeoDash - Thumby Color

A synthwave-themed Geometry Dash-style auto-scrolling platformer for the [Thumby Color](https://tinycircuits.com/products/thumby-color) handheld console.

## Gameplay

- **One-button controls**: Press **A** to jump
- Auto-scrolling platformer with procedurally generated obstacles
- Avoid spikes, blocks, and pit gaps
- Score increases with distance traveled
- Speed and difficulty ramp up over time
- High scores persist between plays

## File Structure

```
GeoDash/
├── main.py                  # Game code
├── manifest.ini             # Launcher metadata
├── icon.bmp                 # Launcher tile icon (38px tall)
└── outrunner_outline.bmp    # Font bitmap (from engine assets)
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ugufru/thumby-geodash.git
cd thumby-geodash
```

### 2. Deploy to Thumby Color

1. Connect Thumby Color via USB-C
2. Open [Thonny](https://thonny.org/) IDE and select the MicroPython interpreter for RP2350
3. In Thonny's file browser, navigate to the device filesystem
4. Create a `/Games/GeoDash/` folder on the device if it doesn't exist
5. Upload all project files (`main.py`, `manifest.ini`, `icon.bmp`, `outrunner_outline.bmp`) into `/Games/GeoDash/`
6. The game will appear in the Thumby Color launcher automatically

## Development

See [DEV_GUIDE.md](DEV_GUIDE.md) for engine API reference and development patterns.

## Device Specifications

- **Processor:** 150-300MHz Dual Core Raspberry Pi RP2350
- **Memory:** 520kB on-chip SRAM
- **Storage:** 16MiB Flash (1MiB firmware, 2MiB game scratch, 13MiB filesystem)
- **Display:** 0.85" 128x128px 16-bit Backlit Color TFT LCD
- **Battery:** 110mAh Rechargeable LiPo, ~2 Hours Gameplay
- **Audio:** 4kHz Magnetic Buzzer
- **Haptics:** Vibration Motor
- **Programming Language:** MicroPython

### Controls
- 4-way D-PAD
- 2 A/B Action Buttons
- 2 Shoulder Bumpers
- 1 Menu Button

## Resources

- [Thumby Color Home](https://color.thumby.us/home/)
- [Tiny Circuits Thumby Color](https://tinycircuits.com/products/thumby-color)
- [Getting Started with Thonny](https://color.thumby.us/pages/getting-started-with-thonny/getting-started-with-thonny/)
- [First Game Tutorial](https://color.thumby.us/pages/first-game/first-game/)
- [API Documentation](https://color.thumby.us/doc/landing.html)
- [Game Engine Examples](https://github.com/TinyCircuits/TinyCircuits-Tiny-Game-Engine/tree/main/filesystem/Games)

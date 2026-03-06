# Starship CLI Animation

A cinematic 2D terminal animation depicting a Starship launch sequence: liftoff, stage separation, booster return, and tower catch — all rendered in your terminal with ANSI colors and ASCII art.

## Quick Start

```bash
npm install
node src/index.js play
```

## Features

- **6 animated scenes**: Pre-launch, liftoff, ascent, stage separation, booster return, tower catch
- **Dynamic effects**: Animated flames, smoke particles, cold gas jets, screen shake, flash effects
- **Color support**: Truecolor (24-bit), 256-color, 16-color, and no-color modes with auto-detection
- **Cross-platform**: macOS, Linux, Windows PowerShell
- **Compatibility mode**: Reduced effects for limited terminals

## Usage

```bash
# Run the full animation
node src/index.js play

# Set custom frame rate
node src/index.js play --fps 15

# Compatibility mode (reduced effects, lower fps)
node src/index.js play --compat

# No colors
node src/index.js play --no-color

# Play a specific scene
node src/index.js play --scene separation

# Custom canvas size
node src/index.js play --size 100x40

# Loop the animation
node src/index.js play --loop

# Debug overlay (shows FPS, time, scene info)
node src/index.js play --debug
```

## Options

| Option | Description |
|--------|-------------|
| `--fps <n>` | Set frame rate (default: 20) |
| `--compat` | Enable compatibility mode |
| `--no-color` | Disable all colors |
| `--low-fps` | Use 10 FPS |
| `--scene <name>` | Play specific scene: `launchpad`, `liftoff`, `ascent`, `separation`, `return`, `catch`, `finale` |
| `--size <WxH>` | Set canvas size (e.g., `80x32`) |
| `--loop` | Loop the animation |
| `--debug` | Show debug overlay |

## Animation Scenes

| Time | Scene | Description |
|------|-------|-------------|
| 0-3s | Pre-Launch | Rocket on the pad, vapor venting, atmosphere building |
| 3-10s | Liftoff | Engine ignition, flame expansion, camera shake, ground smoke |
| 10-15s | Ascent | High-altitude climb, rocket shrinking, cloud layers |
| 15-19s | Separation | Stage split with flash, cold gas jets, debris, slow-motion feel |
| 19-26s | Booster Return | Camera cut to ground, booster descending toward tower |
| 26-31s | Tower Catch | Chopstick arms close, catch impact, vapor burst |
| 31-34s | Finale | Hero shot with "MISSION COMPLETE" |

## Architecture

```
src/
├── index.js              # CLI entry point
├── app.js                # Animation orchestrator
├── engine/
│   ├── screen.js         # Virtual screen buffer (2D char canvas)
│   ├── renderer.js       # ANSI string composition and output
│   ├── loop.js           # Fixed-timestep frame loop
│   ├── colors.js         # Color detection and ANSI formatting
│   ├── easing.js         # Animation easing functions
│   ├── noise.js          # Procedural noise for effects
│   └── timeline.js       # Scene timeline management
├── scene/
│   ├── background.js     # Starfield, sky gradient, clouds
│   ├── hud.js            # Telemetry overlay
│   ├── launchpad.js      # Scene 0: Pre-launch
│   ├── liftoff.js        # Scene 1: Ignition and liftoff
│   ├── ascent.js         # Scene 2: High-altitude climb
│   ├── separation.js     # Scene 3: Stage separation
│   ├── return.js         # Scene 4: Booster RTLS
│   └── catch.js          # Scene 5-6: Tower catch and finale
├── entity/
│   ├── starship.js       # Upper stage sprite
│   ├── booster.js        # Super Heavy booster sprite
│   ├── tower.js          # Launch/catch tower and ground
│   ├── chopsticks.js     # Catch arm mechanism
│   ├── flame.js          # Dynamic exhaust plume
│   ├── smoke.js          # Smoke particle system
│   └── particles.js      # Sparks, debris, cold gas particles
├── util/
│   ├── tty.js            # Terminal capability detection
│   ├── math.js           # Math helpers
│   ├── text.js           # Text alignment utilities
│   └── perf.js           # Performance monitoring
└── assets/
    ├── sprites.js        # ASCII sprite definitions
    └── palettes.js       # Color palettes
```

## Requirements

- Node.js 18+
- Terminal with at least 85x30 characters
- For best results: terminal with truecolor support (iTerm2, Windows Terminal, VS Code terminal)

## Dependencies

- `log-update` — Flicker-free frame replacement
- `ansi-escapes` — Terminal cursor and screen control
- `string-width` — Visual width calculation for alignment

#!/usr/bin/env node

/**
 * Starship CLI Animation - Entry Point
 *
 * Usage:
 *   node src/index.js play              # Run the animation
 *   node src/index.js play --fps 20     # Set frame rate
 *   node src/index.js play --compat     # Compatibility mode
 *   node src/index.js play --no-color   # No colors
 *   node src/index.js play --scene separation  # Play specific scene
 *   node src/index.js play --size 80x32        # Set canvas size
 *   node src/index.js play --loop       # Loop animation
 *   node src/index.js play --debug      # Show debug info
 */

import { run } from './app.js';

function parseArgs(args) {
  const config = {};
  let i = 0;

  // Skip 'play' command if present
  if (args[0] === 'play') i = 1;

  while (i < args.length) {
    const arg = args[i];

    switch (arg) {
      case '--fps':
        config.fps = parseInt(args[++i]) || 20;
        break;
      case '--compat':
        config.compatMode = true;
        break;
      case '--no-color':
        config.noColor = true;
        break;
      case '--scene':
        config.scene = args[++i];
        break;
      case '--size':
        config.size = args[++i];
        break;
      case '--loop':
        config.loop = true;
        break;
      case '--debug':
        config.debug = true;
        break;
      case '--low-fps':
        config.fps = 10;
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
        break;
      default:
        if (arg.startsWith('-')) {
          console.error(`Unknown option: ${arg}`);
          printHelp();
          process.exit(1);
        }
    }
    i++;
  }

  return config;
}

function printHelp() {
  console.log(`
Starship CLI Animation
======================

A cinematic 2D terminal animation of Starship launch,
stage separation, and tower catch.

Usage:
  node src/index.js play [options]

Options:
  --fps <n>         Set frame rate (default: 20)
  --compat          Enable compatibility mode (reduced effects)
  --no-color        Disable colors
  --low-fps         Use low frame rate (10 fps)
  --scene <name>    Play specific scene:
                      launchpad, liftoff, ascent,
                      separation, return, catch, finale
  --size <WxH>      Set canvas size (e.g., 80x32)
  --loop            Loop the animation
  --debug           Show debug overlay
  --help, -h        Show this help

Examples:
  node src/index.js play
  node src/index.js play --fps 15 --compat
  node src/index.js play --scene separation
  node src/index.js play --loop --debug
`);
}

// Main
const args = process.argv.slice(2);

if (args.length === 0 || args[0] === 'play') {
  const config = parseArgs(args);
  run(config).catch(err => {
    console.error('Error:', err.message);
    process.exit(1);
  });
} else if (args[0] === '--help' || args[0] === '-h') {
  printHelp();
} else {
  console.error(`Unknown command: ${args[0]}`);
  printHelp();
  process.exit(1);
}

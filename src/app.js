/**
 * Main application - orchestrates the animation engine.
 */

import { Screen } from './engine/screen.js';
import { Renderer } from './engine/renderer.js';
import { Loop } from './engine/loop.js';
import { Timeline, TOTAL_DURATION } from './engine/timeline.js';
import { setColorLevel, COLOR_NONE, COLOR_16, COLOR_256, COLOR_TRUE } from './engine/colors.js';
import { detectTerminalCapabilities, hideCursor, showCursor, setupCleanup, onResize } from './util/tty.js';
import { SmokeSystem } from './entity/smoke.js';
import { ParticleSystem } from './entity/particles.js';
import { renderLaunchpad } from './scene/launchpad.js';
import { renderLiftoff } from './scene/liftoff.js';
import { renderAscent } from './scene/ascent.js';
import { renderSeparation } from './scene/separation.js';
import { renderReturn } from './scene/return.js';
import { renderCatch, renderFinale } from './scene/catch.js';

// Default configuration
const DEFAULT_CONFIG = {
  fps: 20,
  logicalWidth: 80,
  logicalHeight: 32,
  minTerminalWidth: 85,
  minTerminalHeight: 30,
  colorMode: 'auto',
  cameraShake: true,
  particles: 'high',
  compatMode: false,
  loop: false,
  debug: false,
  scene: null, // play specific scene only
};

export async function run(userConfig = {}) {
  const config = { ...DEFAULT_CONFIG, ...userConfig };

  // Detect terminal capabilities
  const caps = detectTerminalCapabilities();

  // Apply compat mode adjustments
  if (config.compatMode || caps.compatMode) {
    config.fps = Math.min(config.fps, 15);
    config.particles = 'low';
  }

  // Color mode override
  if (config.colorMode === 'none' || config.noColor) {
    setColorLevel(COLOR_NONE);
  } else if (config.colorMode === '16') {
    setColorLevel(COLOR_16);
  } else if (config.colorMode === '256') {
    setColorLevel(COLOR_256);
  } else if (config.colorMode === 'truecolor') {
    setColorLevel(COLOR_TRUE);
  }
  // 'auto' uses detected level

  // Parse size override
  let logicalWidth = config.logicalWidth;
  let logicalHeight = config.logicalHeight;
  if (config.size) {
    const parts = config.size.split('x');
    if (parts.length === 2) {
      logicalWidth = parseInt(parts[0]) || logicalWidth;
      logicalHeight = parseInt(parts[1]) || logicalHeight;
    }
  }

  // Check terminal size
  if (caps.isTTY) {
    if (caps.width < config.minTerminalWidth || caps.height < config.minTerminalHeight) {
      console.error(
        `Terminal too small: ${caps.width}x${caps.height}. ` +
        `Minimum required: ${config.minTerminalWidth}x${config.minTerminalHeight}. ` +
        `Please resize your terminal window.`
      );
      process.exit(1);
    }
  }

  // Fit logical canvas within terminal
  logicalWidth = Math.min(logicalWidth, caps.width - 2);
  logicalHeight = Math.min(logicalHeight, caps.height - 2);

  // Create engine components
  const screen = new Screen(logicalWidth, logicalHeight);
  const renderer = new Renderer(screen);
  const timeline = new Timeline();
  const smoke = new SmokeSystem(config.particles === 'low' ? 80 : (config.particles === 'medium' ? 150 : 200));
  const particles = new ParticleSystem(config.particles === 'low' ? 50 : (config.particles === 'medium' ? 100 : 150));

  // Shared state across scenes
  const state = {
    rocketCX: Math.floor(logicalWidth / 2),
    groundY: logicalHeight - 4,
    towerX: Math.floor(logicalWidth / 2) - 12,
    towerHeight: logicalHeight - 8,
  };

  // Scene start time offset (for --scene mode)
  let timeOffset = 0;
  if (config.scene) {
    const sceneStarts = {
      launchpad: 0, liftoff: 3, ascent: 10,
      separation: 15, return: 19, catch: 26, finale: 31,
    };
    timeOffset = sceneStarts[config.scene] || 0;
  }

  // Hide cursor and setup cleanup
  hideCursor();

  const cleanup = () => {
    loop.stop();
    showCursor();
    renderer.cleanup();
    process.stdout.write('\x1b[0m\n');
  };
  setupCleanup(cleanup);

  // Handle resize
  let tooSmall = false;
  onResize((w, h) => {
    if (w < config.minTerminalWidth || h < config.minTerminalHeight) {
      tooSmall = true;
    } else {
      tooSmall = false;
    }
  });

  // The update function called each frame
  const update = (elapsed, dt) => {
    if (tooSmall) return; // skip update when too small

    const globalTime = elapsed + timeOffset;
    timeline.update(globalTime);

    // Stop when finished (unless looping)
    if (timeline.finished) {
      if (config.loop) {
        // Reset for loop
        loop.startTime = Date.now();
        smoke.clear();
        particles.clear();
        timeline.update(0);
        return;
      }
      // Hold the final frame for a moment, then exit
      setTimeout(() => {
        cleanup();
        process.exit(0);
      }, 2000);
      loop.stop();
      return;
    }

    // Update particle systems
    smoke.update(dt);
    particles.update(dt);

    // Clear screen buffer
    screen.clear();
    screen.cameraX = 0;
    screen.cameraY = 0;

    // Render current scene
    const sceneId = timeline.getSceneId();
    const lt = timeline.sceneLocalTime;
    const sp = timeline.sceneProgress;

    switch (sceneId) {
      case 'launchpad':
        renderLaunchpad(screen, globalTime, lt, sp, state);
        break;
      case 'liftoff':
        renderLiftoff(screen, globalTime, lt, sp, state, smoke, particles);
        break;
      case 'ascent':
        renderAscent(screen, globalTime, lt, sp, state, smoke, particles);
        break;
      case 'separation':
        renderSeparation(screen, globalTime, lt, sp, state, smoke, particles);
        break;
      case 'return':
        renderReturn(screen, globalTime, lt, sp, state, smoke, particles);
        break;
      case 'catch':
        renderCatch(screen, globalTime, lt, sp, state, smoke, particles);
        break;
      case 'finale':
        renderFinale(screen, globalTime, lt, sp, state, smoke, particles);
        break;
    }

    // Debug overlay
    if (config.debug) {
      const dbg = `FPS:${config.fps} T:${globalTime.toFixed(1)} S:${sceneId} P:${sp.toFixed(2)}`;
      screen.drawText(0, logicalHeight - 1, dbg, [255, 255, 0], null, 11);
    }
  };

  // The render function called each frame
  const render = () => {
    if (tooSmall) {
      process.stdout.write('\x1b[2J\x1b[H');
      process.stdout.write('Terminal too small. Please resize.\n');
      return;
    }
    renderer.render();
  };

  // Start the animation loop
  const loop = new Loop(config.fps, update, render);
  loop.start();
}

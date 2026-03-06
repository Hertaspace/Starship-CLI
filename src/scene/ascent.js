/**
 * Scene 2: High-altitude ascent - rocket shrinks, smoke trail, telemetry visible.
 */

import { drawBackground, drawClouds } from './background.js';
import { drawFlame } from '../entity/flame.js';
import { drawHUD } from './hud.js';
import { ROCKET_MID, ROCKET_SMALL } from '../assets/sprites.js';
import { ROCKET } from '../assets/palettes.js';
import { noise1D } from '../engine/noise.js';
import { easeInOutQuad, mapRange } from '../engine/easing.js';

/**
 * Render the ascent scene.
 */
export function renderAscent(screen, t, localT, progress, state, smoke, particles) {
  const { width, height } = screen;

  // Reset camera
  screen.cameraX = 0;
  screen.cameraY = 0;

  // Background - deeper space as we climb
  drawBackground(screen, t, progress * 20);

  // Clouds at mid-screen, scrolling down
  drawClouds(screen, t, height * 0.6 + progress * 10, progress * 15);

  // Rocket gets smaller as it ascends
  const scale = 1 - progress * 0.7; // 1 -> 0.3
  const useSmall = progress > 0.5;
  const sprite = useSmall ? ROCKET_SMALL : ROCKET_MID;
  const spriteWidth = sprite[0].length;

  // Rocket position: centered, moving slightly upward
  const rocketCX = Math.floor(width / 2);
  const rocketX = rocketCX - Math.floor(spriteWidth / 2);
  const rocketY = Math.floor(height * 0.3 + (1 - progress) * height * 0.2);
  const rocketBottomY = rocketY + sprite.length;

  const colorMap = (col, row, ch) => {
    if (ch === ':') return { fg: ROCKET.heatshield };
    if (ch === 'S') return { fg: ROCKET.dark };
    if (ch === '/' || ch === '\\') return { fg: ROCKET.silver };
    return { fg: ROCKET.white };
  };
  screen.drawSprite(rocketX, rocketY, sprite, colorMap, 5);

  // Flame (getting smaller)
  const flameLength = Math.max(2, Math.floor(6 * (1 - progress * 0.5) + noise1D(t * 5) * 1.5));
  const flameWidth = useSmall ? 2 : 4;
  drawFlame(screen, rocketCX, rocketBottomY, flameLength, flameWidth, t);

  // Smoke trail below
  if (localT % 0.2 < 0.06) {
    smoke.emit(rocketCX, rocketBottomY + flameLength, 2, {
      dxRange: [-1, 1],
      dyRange: [0.5, 2],
      life: 4,
    });
  }
  smoke.draw(screen);
  particles.draw(screen);

  // HUD
  const altitude = 5000 + Math.floor(progress * 60000);
  const velocity = 800 + Math.floor(progress * 2200);
  drawHUD(screen, t, 'ascent', {
    altitude,
    velocity,
    status: 'NOMINAL',
    prop: 'PROP NOMINAL',
  });

  // Store state for separation
  state.ascentRocketCX = rocketCX;
  state.ascentRocketY = rocketY;
}

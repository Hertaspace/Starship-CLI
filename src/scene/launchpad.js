/**
 * Scene 0: Pre-launch - rocket on the pad, atmosphere building.
 */

import { drawBackground } from './background.js';
import { drawGround, drawTower, drawLaunchPad } from '../entity/tower.js';
import { drawHUD } from './hud.js';
import { ROCKET_FULL } from '../assets/sprites.js';
import { ROCKET, TOWER as TOWER_PAL } from '../assets/palettes.js';
import { noise1D } from '../engine/noise.js';

/**
 * Render the launchpad scene.
 * @param {Screen} screen
 * @param {number} t - global time
 * @param {number} localT - time within this scene (0..3)
 * @param {number} progress - scene progress (0..1)
 * @param {object} state - shared animation state
 */
export function renderLaunchpad(screen, t, localT, progress, state) {
  const { width, height } = screen;
  const groundY = height - 4;

  // Background
  drawBackground(screen, t);

  // Ground
  drawGround(screen, groundY);

  // Tower (left of rocket)
  const towerX = Math.floor(width / 2) - 12;
  const towerHeight = groundY - 4;
  drawTower(screen, towerX, groundY, towerHeight);

  // Launch pad
  const rocketCX = Math.floor(width / 2);
  drawLaunchPad(screen, rocketCX, groundY);

  // Draw rocket (full stack)
  const sprite = ROCKET_FULL;
  const spriteWidth = sprite[0].length;
  const rocketX = rocketCX - Math.floor(spriteWidth / 2);
  const rocketBottomY = groundY - 2;
  const rocketTopY = rocketBottomY - sprite.length;

  const colorMap = (col, row, ch) => {
    if (ch === ':') return { fg: ROCKET.heatshield };
    if (ch === 'S') return { fg: ROCKET.dark };
    if (ch === '/' || ch === '\\') return { fg: ROCKET.silver };
    if (ch === '_') return { fg: ROCKET.gray };
    if (ch === '=') return { fg: ROCKET.gray };
    return { fg: ROCKET.white };
  };

  screen.drawSprite(rocketX, rocketTopY, sprite, colorMap, 5);

  // Subtle vapor venting near the base
  for (let i = 0; i < 3; i++) {
    const vx = rocketCX + Math.floor((noise1D(t * 3 + i) - 0.5) * 8);
    const vy = rocketBottomY - Math.floor(Math.random() * 2);
    if (Math.random() < 0.4 + progress * 0.3) {
      screen.setPixel(vx, vy, '.', [100, 105, 115], null, 3);
    }
  }

  // Dim lights on ground
  for (let i = 0; i < 5; i++) {
    const lx = rocketCX + Math.floor((i - 2) * 6);
    screen.setPixel(lx, groundY, '*', [80, 70, 40], null, 3);
  }

  // Store state for scene transitions
  state.rocketCX = rocketCX;
  state.groundY = groundY;
  state.towerX = towerX;
  state.towerHeight = towerHeight;
  state.rocketTopY = rocketTopY;
  state.rocketBottomY = rocketBottomY;

  // HUD
  drawHUD(screen, t, 'launchpad', { status: 'NOMINAL', prop: 'PROP LOADED' });
}

/**
 * Launch / catch tower entity.
 */

import { TOWER } from '../assets/palettes.js';
import { GROUND } from '../assets/palettes.js';

/**
 * Draw the launch tower structure.
 * @param {Screen} screen
 * @param {number} x - left edge x position
 * @param {number} groundY - ground level y
 * @param {number} height - tower height in rows
 * @param {number} zIndex
 */
export function drawTower(screen, x, groundY, height, zIndex = 4) {
  const towerWidth = 6;
  const topY = groundY - height;

  for (let row = 0; row < height; row++) {
    const y = topY + row;
    const isStrut = row % 2 === 0;

    // Left pillar
    screen.setPixel(x, y, '|', TOWER.main, null, zIndex);
    // Right pillar
    screen.setPixel(x + towerWidth - 1, y, '|', TOWER.main, null, zIndex);

    // Cross struts
    if (isStrut) {
      for (let i = 1; i < towerWidth - 1; i++) {
        screen.setPixel(x + i, y, '=', TOWER.dark, null, zIndex);
      }
    }
  }

  // Base
  for (let i = -1; i <= towerWidth; i++) {
    screen.setPixel(x + i, groundY, '=', TOWER.accent, null, zIndex);
  }

  return {
    topY,
    centerX: x + towerWidth / 2,
    width: towerWidth,
  };
}

/**
 * Draw the ground / landscape.
 */
export function drawGround(screen, groundY, zIndex = 1) {
  const width = screen.width;
  for (let x = 0; x < width; x++) {
    // Ground line
    screen.setPixel(x, groundY, '_', GROUND.light, null, zIndex);

    // Below ground fill
    for (let y = groundY + 1; y < screen.height; y++) {
      screen.setPixel(x, y, ' ', null, GROUND.dark, zIndex);
    }
  }
}

/**
 * Draw the launch pad under the rocket.
 */
export function drawLaunchPad(screen, cx, groundY, width = 16, zIndex = 3) {
  const halfW = Math.floor(width / 2);
  for (let dx = -halfW; dx <= halfW; dx++) {
    screen.setPixel(cx + dx, groundY, '#', TOWER.dark, null, zIndex);
    screen.setPixel(cx + dx, groundY - 1, '=', TOWER.accent, null, zIndex);
  }
}

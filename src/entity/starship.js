/**
 * Starship upper stage entity.
 */

import { STARSHIP_CLOSE, STARSHIP_MID, STARSHIP_FAR, STARSHIP_TINY } from '../assets/sprites.js';
import { ROCKET } from '../assets/palettes.js';
import { lerpColor } from '../engine/colors.js';

/**
 * Get the appropriate sprite for the given scale.
 */
function getSprite(scale) {
  if (scale >= 0.8) return STARSHIP_CLOSE;
  if (scale >= 0.5) return STARSHIP_MID;
  if (scale >= 0.2) return STARSHIP_FAR;
  return STARSHIP_TINY;
}

/**
 * Color mapping for starship sprite.
 */
function colorMap(col, row, ch) {
  if (ch === '/') return { fg: ROCKET.silver };
  if (ch === '\\') return { fg: ROCKET.silver };
  if (ch === 'S') return { fg: ROCKET.dark };
  if (ch === '|') return { fg: ROCKET.white };
  if (ch === '_') return { fg: ROCKET.gray };
  return { fg: ROCKET.white };
}

/**
 * Draw the Starship upper stage.
 * @param {Screen} screen
 * @param {number} x - center x position
 * @param {number} y - top y position
 * @param {number} scale - visual scale (1 = close, 0 = far)
 * @param {number} zIndex
 */
export function drawStarship(screen, x, y, scale = 1, zIndex = 5) {
  const sprite = getSprite(scale);
  const spriteWidth = sprite[0].length;
  const drawX = Math.round(x - spriteWidth / 2);
  screen.drawSprite(drawX, Math.round(y), sprite, colorMap, zIndex);
  return {
    width: spriteWidth,
    height: sprite.length,
    bottomY: Math.round(y) + sprite.length,
  };
}

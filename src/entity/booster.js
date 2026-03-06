/**
 * Super Heavy Booster entity.
 */

import { BOOSTER_CLOSE, BOOSTER_MID, BOOSTER_FAR, BOOSTER_TINY, GRID_FINS } from '../assets/sprites.js';
import { ROCKET } from '../assets/palettes.js';

function getSprite(scale) {
  if (scale >= 0.8) return BOOSTER_CLOSE;
  if (scale >= 0.5) return BOOSTER_MID;
  if (scale >= 0.2) return BOOSTER_FAR;
  return BOOSTER_TINY;
}

function colorMap(col, row, ch) {
  if (ch === ':') return { fg: ROCKET.heatshield };
  if (ch === '/') return { fg: ROCKET.silver };
  if (ch === '\\') return { fg: ROCKET.silver };
  if (ch === '|') return { fg: ROCKET.white };
  if (ch === '_') return { fg: ROCKET.gray };
  if (ch === '=') return { fg: ROCKET.gray };
  return { fg: ROCKET.white };
}

/**
 * Draw the Super Heavy Booster.
 */
export function drawBooster(screen, x, y, scale = 1, zIndex = 5) {
  const sprite = getSprite(scale);
  const spriteWidth = sprite[0].length;
  const drawX = Math.round(x - spriteWidth / 2);
  screen.drawSprite(drawX, Math.round(y), sprite, colorMap, zIndex);
  return {
    width: spriteWidth,
    height: sprite.length,
    bottomY: Math.round(y) + sprite.length,
    topY: Math.round(y),
  };
}

/**
 * Draw grid fins on the booster (for return phase).
 */
export function drawGridFins(screen, x, y, zIndex = 5) {
  const sprite = GRID_FINS;
  const spriteWidth = sprite[0].length;
  const drawX = Math.round(x - spriteWidth / 2);
  screen.drawSprite(drawX, Math.round(y), sprite, colorMap, zIndex);
}

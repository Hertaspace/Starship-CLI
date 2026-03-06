/**
 * "Chopstick" catch arms entity.
 */

import { TOWER } from '../assets/palettes.js';

/**
 * Draw the chopstick arms at a given opening angle.
 * @param {Screen} screen
 * @param {number} cx - center x (tower center)
 * @param {number} y - y position of the arms
 * @param {number} openness - 0 = closed/caught, 1 = fully open
 * @param {number} zIndex
 */
export function drawChopsticks(screen, cx, y, openness = 1, zIndex = 6) {
  const maxSpread = 8;
  const spread = Math.round(openness * maxSpread);

  // Left arm: goes from center-left outward
  // Right arm: goes from center-right outward
  const armLength = 4 + Math.round(openness * 3);

  for (let i = 0; i < armLength; i++) {
    const ratio = i / armLength;
    const offsetX = Math.round(ratio * spread);
    const offsetY = Math.round(ratio * 1.5); // slight downward angle

    // Left arm
    screen.setPixel(cx - 1 - offsetX, y + offsetY, '\\', TOWER.accent, null, zIndex);
    // Right arm
    screen.setPixel(cx + 1 + offsetX, y + offsetY, '/', TOWER.accent, null, zIndex);
  }

  // Arm tips
  if (spread > 0) {
    const tipOffsetX = spread;
    const tipOffsetY = Math.round(1.5);
    screen.setPixel(cx - 1 - tipOffsetX, y + tipOffsetY + 1, '<', TOWER.light, null, zIndex);
    screen.setPixel(cx + 1 + tipOffsetX, y + tipOffsetY + 1, '>', TOWER.light, null, zIndex);
  }

  // When caught (openness near 0), draw the grip
  if (openness < 0.15) {
    screen.setPixel(cx - 1, y, '[', TOWER.accent, null, zIndex);
    screen.setPixel(cx + 1, y, ']', TOWER.accent, null, zIndex);
    screen.setPixel(cx - 1, y + 1, '[', TOWER.accent, null, zIndex);
    screen.setPixel(cx + 1, y + 1, ']', TOWER.accent, null, zIndex);
  }
}

/**
 * Flame / exhaust plume entity with dynamic shape and color.
 */

import { FLAME_LAUNCH, FLAME_LAND } from '../assets/palettes.js';
import { lerpColor } from '../engine/colors.js';
import { noise1D } from '../engine/noise.js';
import { randFloat, pick } from '../engine/noise.js';

const FLAME_CHARS = ['#', '*', '.', ',', '~', '^'];
const CORE_CHARS = ['#', '@', '%'];
const EDGE_CHARS = ['.', ',', '~', '*', "'"];

/**
 * Draw a launch flame (large, expansive) below a rocket.
 * @param {Screen} screen
 * @param {number} cx - center x of the flame base
 * @param {number} topY - y position of the flame top (base of rocket)
 * @param {number} length - flame length in rows
 * @param {number} baseWidth - width at the top
 * @param {number} t - time for animation
 * @param {object} palette - flame color palette
 * @param {number} zIndex
 */
export function drawFlame(screen, cx, topY, length, baseWidth, t, palette = FLAME_LAUNCH, zIndex = 3) {
  if (length <= 0) return;

  const halfBase = Math.floor(baseWidth / 2);

  for (let row = 0; row < length; row++) {
    const progress = row / length; // 0 at top, 1 at tip
    // Width narrows toward the tip with noise
    const noiseVal = noise1D(t * 8 + row * 0.5) * 2;
    const widthAtRow = Math.max(1, Math.floor(halfBase * (1 - progress * 0.7) + noiseVal));

    for (let dx = -widthAtRow; dx <= widthAtRow; dx++) {
      const x = cx + dx;
      const y = topY + row;
      const distFromCenter = Math.abs(dx) / (widthAtRow + 1);

      // Pick character based on position
      let ch;
      if (distFromCenter < 0.3) {
        ch = pick(CORE_CHARS);
      } else if (distFromCenter < 0.7) {
        ch = pick(FLAME_CHARS);
      } else {
        ch = pick(EDGE_CHARS);
      }

      // Randomly skip some edge cells for organic look
      if (distFromCenter > 0.6 && Math.random() < 0.3) continue;

      // Color based on distance from center and depth
      let color;
      if (distFromCenter < 0.2 && progress < 0.3) {
        color = palette.core;
      } else if (distFromCenter < 0.4) {
        color = lerpColor(palette.inner, palette.mid, progress);
      } else if (distFromCenter < 0.7) {
        color = lerpColor(palette.mid, palette.outer, progress);
      } else {
        color = lerpColor(palette.outer, palette.edge, progress);
      }

      // Flicker: slight color variation
      if (Math.random() < 0.15) {
        color = lerpColor(color, palette.core, 0.2);
      }

      screen.setPixel(x, y, ch, color, null, zIndex);
    }
  }

  // Add some sparks/embers below the main flame
  const sparkCount = Math.floor(length * 0.4);
  for (let i = 0; i < sparkCount; i++) {
    const sx = cx + Math.floor((Math.random() - 0.5) * baseWidth * 1.2);
    const sy = topY + length + Math.floor(Math.random() * 3);
    if (Math.random() < 0.5) {
      screen.setPixel(sx, sy, pick(['.', ',', '*', "'"]), palette.tip || palette.edge, null, zIndex - 1);
    }
  }
}

/**
 * Draw a landing flame (shorter, more focused).
 */
export function drawLandingFlame(screen, cx, topY, length, baseWidth, t, zIndex = 3) {
  drawFlame(screen, cx, topY, length, Math.max(2, baseWidth - 2), t, FLAME_LAND, zIndex);
}

/**
 * Draw exhaust spread (billowing effect at ground level).
 */
export function drawExhaustSpread(screen, cx, groundY, width, t, zIndex = 2) {
  const halfW = Math.floor(width / 2);
  for (let dx = -halfW; dx <= halfW; dx++) {
    const dist = Math.abs(dx) / halfW;
    const noiseVal = noise1D(t * 5 + dx * 0.3);

    // The exhaust spreads outward
    if (Math.random() < (1 - dist * 0.7) * 0.6) {
      const ch = dist < 0.3 ? '#' : (dist < 0.6 ? '*' : (Math.random() < 0.5 ? '.' : ','));
      const color = lerpColor(FLAME_LAUNCH.mid, FLAME_LAUNCH.edge, dist);
      const y = groundY + Math.floor(noiseVal * 1.5);
      screen.setPixel(cx + dx, y, ch, color, null, zIndex);
    }

    // Smoke above exhaust
    if (Math.random() < 0.3 * (1 - dist)) {
      const smokeY = groundY - 1 - Math.floor(Math.random() * 2);
      screen.setPixel(cx + dx, smokeY, pick(['.', '~', ',']), [120, 110, 100], null, zIndex - 1);
    }
  }
}

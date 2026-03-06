/**
 * Background rendering - starfield, sky gradient, clouds.
 * Shared across all scenes.
 */

import { SKY, STARS } from '../assets/palettes.js';
import { lerpColor } from '../engine/colors.js';
import { noise2D } from '../engine/noise.js';

// Pre-generate star positions (fixed layout)
let stars = null;

function generateStars(width, height) {
  if (stars && stars.w === width && stars.h === height) return stars.data;
  const data = [];
  const count = Math.floor(width * height * 0.02); // 2% density
  for (let i = 0; i < count; i++) {
    data.push({
      x: Math.floor(Math.random() * width),
      y: Math.floor(Math.random() * Math.floor(height * 0.7)), // stars in upper 70%
      brightness: Math.random(),
      twinkleSpeed: 1 + Math.random() * 3,
    });
  }
  stars = { w: width, h: height, data };
  return data;
}

/**
 * Draw the sky background with gradient.
 * @param {number} scrollY - vertical camera offset for parallax
 */
export function drawBackground(screen, t, scrollY = 0) {
  const { width, height } = screen;

  // Sky gradient (top to bottom)
  for (let y = 0; y < height; y++) {
    const ratio = y / height;
    let color;
    if (ratio < 0.3) {
      color = lerpColor(SKY.top, SKY.mid, ratio / 0.3);
    } else if (ratio < 0.7) {
      color = lerpColor(SKY.mid, SKY.bottom, (ratio - 0.3) / 0.4);
    } else {
      color = lerpColor(SKY.bottom, SKY.dawn, (ratio - 0.7) / 0.3);
    }

    for (let x = 0; x < width; x++) {
      screen.setPixel(x, y, ' ', null, color, 0);
    }
  }

  // Stars with twinkling
  const starData = generateStars(width, height);
  for (const star of starData) {
    const sy = star.y + Math.floor(scrollY * 0.1); // slow parallax
    if (sy < 0 || sy >= height) continue;

    // Twinkle effect
    const twinkle = Math.sin(t * star.twinkleSpeed + star.x * 0.1) * 0.5 + 0.5;
    const visible = twinkle > 0.3;
    if (!visible) continue;

    let color;
    if (star.brightness > 0.8) {
      color = STARS.bright;
    } else if (star.brightness > 0.4) {
      color = STARS.dim;
    } else {
      color = STARS.faint;
    }

    const ch = star.brightness > 0.85 ? '*' : (star.brightness > 0.5 ? '.' : ',');
    screen.setPixel(star.x, sy, ch, color, null, 1);
  }
}

/**
 * Draw thin wispy clouds.
 */
export function drawClouds(screen, t, baseY, scrollY = 0) {
  const { width } = screen;
  for (let x = 0; x < width; x++) {
    const cloudNoise = noise2D(x * 0.08 + t * 0.2, baseY * 0.1 + scrollY * 0.05);
    if (cloudNoise > 0.6) {
      const y = Math.round(baseY + scrollY * 0.3);
      if (y >= 0 && y < screen.height) {
        const intensity = (cloudNoise - 0.6) / 0.4;
        const ch = intensity > 0.5 ? '~' : '.';
        const color = lerpColor([40, 40, 60], [80, 80, 100], intensity);
        screen.setPixel(x, y, ch, color, null, 1);
      }
    }
  }
}

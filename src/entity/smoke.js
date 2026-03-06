/**
 * Smoke / vapor particle system.
 * Particles spawn, drift, expand, and fade out.
 */

import { SMOKE } from '../assets/palettes.js';
import { lerpColor } from '../engine/colors.js';
import { randFloat, randInt } from '../engine/noise.js';

const SMOKE_CHARS_DENSE = ['#', '%', '@'];
const SMOKE_CHARS_MID = ['*', '~', '#'];
const SMOKE_CHARS_LIGHT = ['.', ',', "'", '~'];

export class SmokeSystem {
  constructor(maxParticles = 200) {
    this.particles = [];
    this.maxParticles = maxParticles;
  }

  /**
   * Emit smoke particles from a position.
   * @param {number} x - emit x
   * @param {number} y - emit y
   * @param {number} count - number of particles
   * @param {object} opts - { dxRange, dyRange, life, spread }
   */
  emit(x, y, count, opts = {}) {
    const {
      dxRange = [-2, 2],
      dyRange = [-1, 0],
      life = 3,
      spread = 'wide',
    } = opts;

    for (let i = 0; i < count; i++) {
      if (this.particles.length >= this.maxParticles) break;

      this.particles.push({
        x: x + randFloat(-1, 1),
        y: y + randFloat(-0.5, 0.5),
        vx: randFloat(dxRange[0], dxRange[1]),
        vy: randFloat(dyRange[0], dyRange[1]),
        life,
        maxLife: life,
        age: 0,
        spread,
      });
    }
  }

  /**
   * Update all particles by dt seconds.
   */
  update(dt) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.age += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;

      // Slow down horizontal drift
      p.vx *= 0.98;
      // Slight upward drift for smoke
      p.vy -= 0.1 * dt;

      if (p.age >= p.life) {
        this.particles.splice(i, 1);
      }
    }
  }

  /**
   * Draw all smoke particles to the screen.
   */
  draw(screen, zIndex = 2) {
    for (const p of this.particles) {
      const lifeRatio = p.age / p.maxLife; // 0 = fresh, 1 = dying

      // Character density decreases with age
      let ch;
      if (lifeRatio < 0.3) {
        ch = SMOKE_CHARS_DENSE[randInt(0, SMOKE_CHARS_DENSE.length - 1)];
      } else if (lifeRatio < 0.6) {
        ch = SMOKE_CHARS_MID[randInt(0, SMOKE_CHARS_MID.length - 1)];
      } else {
        ch = SMOKE_CHARS_LIGHT[randInt(0, SMOKE_CHARS_LIGHT.length - 1)];
      }

      // Color fades from bright to dark
      let color;
      if (lifeRatio < 0.3) {
        color = lerpColor(SMOKE.bright, SMOKE.mid, lifeRatio / 0.3);
      } else if (lifeRatio < 0.7) {
        color = lerpColor(SMOKE.mid, SMOKE.dark, (lifeRatio - 0.3) / 0.4);
      } else {
        color = lerpColor(SMOKE.dark, SMOKE.faint, (lifeRatio - 0.7) / 0.3);
      }

      // Skip very faded particles randomly
      if (lifeRatio > 0.8 && Math.random() < 0.4) continue;

      const px = Math.round(p.x);
      const py = Math.round(p.y);
      screen.setPixel(px, py, ch, color, null, zIndex);
    }
  }

  /**
   * Clear all particles.
   */
  clear() {
    this.particles.length = 0;
  }
}

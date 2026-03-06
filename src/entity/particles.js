/**
 * General particle system for sparks, debris, cold gas, and vapor effects.
 */

import { lerpColor } from '../engine/colors.js';
import { randFloat, randInt, pick } from '../engine/noise.js';
import { COLDGAS, FLAME_LAUNCH } from '../assets/palettes.js';

const SPARK_CHARS = ['*', '.', ',', "'", '`'];
const DEBRIS_CHARS = ['*', '#', '+', 'x'];
const GAS_CHARS = ['.', '~', ',', "'"];

export class ParticleSystem {
  constructor(maxParticles = 150) {
    this.particles = [];
    this.maxParticles = maxParticles;
  }

  /**
   * Emit spark particles (fire embers).
   */
  emitSparks(x, y, count, opts = {}) {
    const { speed = 3, life = 1.5, color = FLAME_LAUNCH.outer } = opts;
    for (let i = 0; i < count; i++) {
      if (this.particles.length >= this.maxParticles) break;
      const angle = randFloat(0, Math.PI * 2);
      const spd = randFloat(speed * 0.3, speed);
      this.particles.push({
        x, y,
        vx: Math.cos(angle) * spd,
        vy: Math.sin(angle) * spd,
        life: randFloat(life * 0.5, life),
        maxLife: life,
        age: 0,
        type: 'spark',
        color,
      });
    }
  }

  /**
   * Emit cold gas / separation jet particles.
   */
  emitColdGas(x, y, count, direction = 'both') {
    for (let i = 0; i < count; i++) {
      if (this.particles.length >= this.maxParticles) break;
      let vx;
      if (direction === 'left') vx = randFloat(-4, -1);
      else if (direction === 'right') vx = randFloat(1, 4);
      else vx = randFloat(-3, 3);

      this.particles.push({
        x: x + randFloat(-1, 1),
        y: y + randFloat(-0.5, 0.5),
        vx,
        vy: randFloat(-1, 1),
        life: randFloat(0.5, 1.5),
        maxLife: 1.5,
        age: 0,
        type: 'gas',
        color: COLDGAS.bright,
      });
    }
  }

  /**
   * Emit debris particles (separation event).
   */
  emitDebris(x, y, count) {
    for (let i = 0; i < count; i++) {
      if (this.particles.length >= this.maxParticles) break;
      this.particles.push({
        x: x + randFloat(-2, 2),
        y: y + randFloat(-1, 1),
        vx: randFloat(-5, 5),
        vy: randFloat(-3, 2),
        life: randFloat(1, 3),
        maxLife: 3,
        age: 0,
        type: 'debris',
        color: [180, 180, 180],
      });
    }
  }

  /**
   * Emit vapor / steam particles.
   */
  emitVapor(x, y, count) {
    for (let i = 0; i < count; i++) {
      if (this.particles.length >= this.maxParticles) break;
      this.particles.push({
        x: x + randFloat(-1, 1),
        y,
        vx: randFloat(-0.5, 0.5),
        vy: randFloat(-1.5, -0.3),
        life: randFloat(1, 2.5),
        maxLife: 2.5,
        age: 0,
        type: 'vapor',
        color: [160, 170, 180],
      });
    }
  }

  update(dt) {
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      p.age += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;

      // Gravity for sparks and debris
      if (p.type === 'spark' || p.type === 'debris') {
        p.vy += 2 * dt;
      }
      // Upward drift for gas and vapor
      if (p.type === 'gas' || p.type === 'vapor') {
        p.vy -= 0.5 * dt;
        p.vx *= 0.97;
      }

      if (p.age >= p.life) {
        this.particles.splice(i, 1);
      }
    }
  }

  draw(screen, zIndex = 2) {
    for (const p of this.particles) {
      const lifeRatio = p.age / p.maxLife;

      // Skip dying particles randomly
      if (lifeRatio > 0.7 && Math.random() < 0.3) continue;

      let ch;
      switch (p.type) {
        case 'spark':
          ch = pick(SPARK_CHARS);
          break;
        case 'debris':
          ch = pick(DEBRIS_CHARS);
          break;
        case 'gas':
        case 'vapor':
          ch = pick(GAS_CHARS);
          break;
        default:
          ch = '.';
      }

      // Fade color
      const fadedColor = lerpColor(p.color, [30, 30, 30], lifeRatio * 0.7);

      const px = Math.round(p.x);
      const py = Math.round(p.y);
      screen.setPixel(px, py, ch, fadedColor, null, zIndex);
    }
  }

  clear() {
    this.particles.length = 0;
  }
}

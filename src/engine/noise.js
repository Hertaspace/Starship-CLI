/**
 * Simple noise and randomness utilities for visual effects.
 */

// Seeded pseudo-random for reproducible effects
let seed = 42;

export function setSeed(s) {
  seed = s;
}

export function seededRandom() {
  seed = (seed * 16807 + 0) % 2147483647;
  return (seed - 1) / 2147483646;
}

/**
 * Simple 1D value noise.
 */
export function noise1D(x) {
  const i = Math.floor(x);
  const f = x - i;
  const smooth = f * f * (3 - 2 * f); // smoothstep
  const a = hash1D(i);
  const b = hash1D(i + 1);
  return a + (b - a) * smooth;
}

function hash1D(n) {
  let x = Math.sin(n * 127.1) * 43758.5453;
  return x - Math.floor(x);
}

/**
 * Simple 2D value noise.
 */
export function noise2D(x, y) {
  const ix = Math.floor(x);
  const iy = Math.floor(y);
  const fx = x - ix;
  const fy = y - iy;
  const sx = fx * fx * (3 - 2 * fx);
  const sy = fy * fy * (3 - 2 * fy);

  const a = hash2D(ix, iy);
  const b = hash2D(ix + 1, iy);
  const c = hash2D(ix, iy + 1);
  const d = hash2D(ix + 1, iy + 1);

  return a + (b - a) * sx + (c - a) * sy + (a - b - c + d) * sx * sy;
}

function hash2D(x, y) {
  let n = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
  return n - Math.floor(n);
}

/**
 * Fractional Brownian Motion (fBm) - layered noise for natural-looking effects.
 */
export function fbm(x, octaves = 4, lacunarity = 2.0, gain = 0.5) {
  let value = 0;
  let amplitude = 1;
  let frequency = 1;
  let maxVal = 0;
  for (let i = 0; i < octaves; i++) {
    value += amplitude * noise1D(x * frequency);
    maxVal += amplitude;
    amplitude *= gain;
    frequency *= lacunarity;
  }
  return value / maxVal;
}

/**
 * Random integer in range [min, max] inclusive.
 */
export function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Random float in range [min, max).
 */
export function randFloat(min, max) {
  return Math.random() * (max - min) + min;
}

/**
 * Random pick from array.
 */
export function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

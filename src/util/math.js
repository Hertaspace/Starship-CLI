/**
 * Math utilities for animation calculations.
 */

export function lerp(a, b, t) {
  return a + (b - a) * t;
}

export function clamp(val, min, max) {
  return Math.max(min, Math.min(max, val));
}

export function distance(x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  return Math.sqrt(dx * dx + dy * dy);
}

export function wrap(val, min, max) {
  const range = max - min;
  return ((val - min) % range + range) % range + min;
}

export function oscillate(t, frequency = 1, amplitude = 1) {
  return Math.sin(t * frequency * Math.PI * 2) * amplitude;
}

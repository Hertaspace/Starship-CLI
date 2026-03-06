/**
 * Easing functions for smooth animation transitions.
 * All functions take t in [0, 1] and return a value in [0, 1].
 */

export function linear(t) {
  return t;
}

export function easeInQuad(t) {
  return t * t;
}

export function easeOutQuad(t) {
  return t * (2 - t);
}

export function easeInOutQuad(t) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
}

export function easeInCubic(t) {
  return t * t * t;
}

export function easeOutCubic(t) {
  const t1 = t - 1;
  return t1 * t1 * t1 + 1;
}

export function easeInOutCubic(t) {
  return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

export function easeOutElastic(t) {
  if (t === 0 || t === 1) return t;
  return Math.pow(2, -10 * t) * Math.sin((t - 0.075) * (2 * Math.PI) / 0.3) + 1;
}

export function easeOutBounce(t) {
  if (t < 1 / 2.75) return 7.5625 * t * t;
  if (t < 2 / 2.75) { t -= 1.5 / 2.75; return 7.5625 * t * t + 0.75; }
  if (t < 2.5 / 2.75) { t -= 2.25 / 2.75; return 7.5625 * t * t + 0.9375; }
  t -= 2.625 / 2.75;
  return 7.5625 * t * t + 0.984375;
}

/**
 * Clamp a value between min and max.
 */
export function clamp(val, min = 0, max = 1) {
  return Math.max(min, Math.min(max, val));
}

/**
 * Map a value from one range to another.
 */
export function mapRange(val, inMin, inMax, outMin, outMax) {
  return outMin + (outMax - outMin) * clamp((val - inMin) / (inMax - inMin));
}

/**
 * Smoothstep interpolation.
 */
export function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0));
  return t * t * (3 - 2 * t);
}

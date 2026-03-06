/**
 * Color palettes for the animation.
 * All colors are [R, G, B] arrays.
 */

// Night sky gradient (top to bottom)
export const SKY = {
  top:    [5, 5, 20],
  mid:    [10, 10, 40],
  bottom: [20, 15, 50],
  dawn:   [40, 20, 60],
  horizon:[60, 30, 45],
};

// Stars
export const STARS = {
  bright: [255, 255, 255],
  dim:    [120, 120, 160],
  faint:  [60, 60, 90],
};

// Ground / landscape
export const GROUND = {
  dark:   [20, 15, 10],
  mid:    [40, 30, 20],
  light:  [60, 45, 30],
};

// Tower / structure
export const TOWER = {
  main:    [70, 80, 100],
  dark:    [40, 45, 60],
  light:   [100, 110, 130],
  accent:  [150, 160, 180],
};

// Rocket body
export const ROCKET = {
  white:   [220, 225, 230],
  silver:  [180, 185, 195],
  gray:    [120, 125, 135],
  dark:    [50, 55, 65],
  black:   [30, 30, 40],
  heatshield: [40, 35, 30],
};

// Flame - launch (hot, expansive)
export const FLAME_LAUNCH = {
  core:   [255, 255, 240],
  inner:  [255, 240, 150],
  mid:    [255, 180, 50],
  outer:  [255, 100, 20],
  edge:   [200, 50, 10],
  tip:    [120, 30, 10],
};

// Flame - landing (cooler, more focused)
export const FLAME_LAND = {
  core:   [255, 250, 230],
  inner:  [255, 220, 160],
  mid:    [240, 160, 80],
  outer:  [200, 100, 40],
  edge:   [150, 60, 20],
};

// Smoke
export const SMOKE = {
  bright: [200, 195, 185],
  mid:    [140, 135, 130],
  dark:   [80, 75, 70],
  faint:  [50, 48, 45],
};

// UI elements
export const UI = {
  text:    [0, 200, 100],
  dim:     [0, 120, 60],
  label:   [100, 180, 220],
  warn:    [255, 200, 50],
  success: [50, 255, 100],
};

// Exhaust / cold gas
export const COLDGAS = {
  bright: [200, 220, 255],
  mid:    [140, 160, 200],
  dim:    [80, 90, 120],
};

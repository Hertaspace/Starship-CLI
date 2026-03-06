/**
 * Color capability detection and ANSI color formatting.
 * Supports truecolor (24-bit), 256-color, 16-color, and no-color modes.
 */

// Color levels
export const COLOR_NONE = 0;
export const COLOR_16 = 1;
export const COLOR_256 = 2;
export const COLOR_TRUE = 3;

let currentColorLevel = null;

/**
 * Detect the terminal's color capability level.
 */
export function detectColorLevel() {
  if (currentColorLevel !== null) return currentColorLevel;

  // Check for explicit no-color
  if (process.env.NO_COLOR !== undefined || process.argv.includes('--no-color')) {
    currentColorLevel = COLOR_NONE;
    return currentColorLevel;
  }

  // Not a TTY
  if (!process.stdout.isTTY) {
    currentColorLevel = COLOR_NONE;
    return currentColorLevel;
  }

  const colorterm = (process.env.COLORTERM || '').toLowerCase();
  const term = (process.env.TERM || '').toLowerCase();
  const isWin = process.platform === 'win32';

  // Truecolor detection
  if (colorterm === 'truecolor' || colorterm === '24bit') {
    currentColorLevel = COLOR_TRUE;
    return currentColorLevel;
  }

  // Modern terminals
  if (term.includes('256color') || term.includes('xterm')) {
    currentColorLevel = COLOR_256;
    // Many xterm-256color terminals actually support truecolor
    if (process.env.TERM_PROGRAM === 'iTerm.app' ||
        process.env.TERM_PROGRAM === 'Hyper' ||
        process.env.WT_SESSION || // Windows Terminal
        process.env.TERM_PROGRAM === 'vscode') {
      currentColorLevel = COLOR_TRUE;
    }
    return currentColorLevel;
  }

  // Windows with modern terminal
  if (isWin) {
    if (process.env.WT_SESSION) {
      currentColorLevel = COLOR_TRUE;
    } else {
      // PowerShell / CMD - conservative
      currentColorLevel = COLOR_256;
    }
    return currentColorLevel;
  }

  // Fallback
  currentColorLevel = COLOR_16;
  return currentColorLevel;
}

/**
 * Override the detected color level (for --compat, --no-color, etc.)
 */
export function setColorLevel(level) {
  currentColorLevel = level;
}

/**
 * Format an RGB foreground color to ANSI escape.
 */
export function fg(r, g, b) {
  const level = detectColorLevel();
  if (level === COLOR_NONE) return '';
  if (level === COLOR_TRUE) return `\x1b[38;2;${r};${g};${b}m`;
  if (level === COLOR_256) return `\x1b[38;5;${rgbTo256(r, g, b)}m`;
  return `\x1b[${rgbTo16Fg(r, g, b)}m`;
}

/**
 * Format an RGB background color to ANSI escape.
 */
export function bg(r, g, b) {
  const level = detectColorLevel();
  if (level === COLOR_NONE) return '';
  if (level === COLOR_TRUE) return `\x1b[48;2;${r};${g};${b}m`;
  if (level === COLOR_256) return `\x1b[48;5;${rgbTo256(r, g, b)}m`;
  return `\x1b[${rgbTo16Bg(r, g, b)}m`;
}

export const RESET = '\x1b[0m';

/**
 * Build a complete ANSI style string for a cell.
 */
export function styleCell(fgColor, bgColor) {
  const level = detectColorLevel();
  if (level === COLOR_NONE) return '';
  let s = '';
  if (fgColor) s += fg(...fgColor);
  if (bgColor) s += bg(...bgColor);
  return s;
}

// --- Color space conversions ---

function rgbTo256(r, g, b) {
  // Check grayscale ramp first
  if (r === g && g === b) {
    if (r < 8) return 16;
    if (r > 248) return 231;
    return Math.round((r - 8) / 247 * 24) + 232;
  }
  // 6x6x6 color cube
  const ri = Math.round(r / 255 * 5);
  const gi = Math.round(g / 255 * 5);
  const bi = Math.round(b / 255 * 5);
  return 16 + 36 * ri + 6 * gi + bi;
}

// Basic 16-color mapping (approximate)
const ANSI_16_TABLE = [
  { rgb: [0, 0, 0], fg: 30, bg: 40 },       // black
  { rgb: [170, 0, 0], fg: 31, bg: 41 },      // red
  { rgb: [0, 170, 0], fg: 32, bg: 42 },      // green
  { rgb: [170, 85, 0], fg: 33, bg: 43 },     // yellow
  { rgb: [0, 0, 170], fg: 34, bg: 44 },      // blue
  { rgb: [170, 0, 170], fg: 35, bg: 45 },    // magenta
  { rgb: [0, 170, 170], fg: 36, bg: 46 },    // cyan
  { rgb: [170, 170, 170], fg: 37, bg: 47 },  // white
  { rgb: [85, 85, 85], fg: 90, bg: 100 },    // bright black
  { rgb: [255, 85, 85], fg: 91, bg: 101 },   // bright red
  { rgb: [85, 255, 85], fg: 92, bg: 102 },   // bright green
  { rgb: [255, 255, 85], fg: 93, bg: 103 },  // bright yellow
  { rgb: [85, 85, 255], fg: 94, bg: 104 },   // bright blue
  { rgb: [255, 85, 255], fg: 95, bg: 105 },  // bright magenta
  { rgb: [85, 255, 255], fg: 96, bg: 106 },  // bright cyan
  { rgb: [255, 255, 255], fg: 97, bg: 107 }, // bright white
];

function closestAnsi16(r, g, b) {
  let minDist = Infinity;
  let best = ANSI_16_TABLE[0];
  for (const entry of ANSI_16_TABLE) {
    const dr = r - entry.rgb[0];
    const dg = g - entry.rgb[1];
    const db = b - entry.rgb[2];
    const dist = dr * dr + dg * dg + db * db;
    if (dist < minDist) {
      minDist = dist;
      best = entry;
    }
  }
  return best;
}

function rgbTo16Fg(r, g, b) {
  return closestAnsi16(r, g, b).fg;
}

function rgbTo16Bg(r, g, b) {
  return closestAnsi16(r, g, b).bg;
}

/**
 * Linearly interpolate between two RGB colors.
 */
export function lerpColor(c1, c2, t) {
  t = Math.max(0, Math.min(1, t));
  return [
    Math.round(c1[0] + (c2[0] - c1[0]) * t),
    Math.round(c1[1] + (c2[1] - c1[1]) * t),
    Math.round(c1[2] + (c2[2] - c1[2]) * t),
  ];
}

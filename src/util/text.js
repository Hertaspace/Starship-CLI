/**
 * Text alignment and width utilities.
 */

import stringWidth from 'string-width';

/**
 * Get the visual width of a string, ignoring ANSI codes.
 */
export function visWidth(str) {
  return stringWidth(str);
}

/**
 * Center a text string within a given width.
 */
export function centerText(text, width) {
  const tw = visWidth(text);
  const pad = Math.max(0, Math.floor((width - tw) / 2));
  return ' '.repeat(pad) + text;
}

/**
 * Right-align text within a given width.
 */
export function rightAlign(text, width) {
  const tw = visWidth(text);
  const pad = Math.max(0, width - tw);
  return ' '.repeat(pad) + text;
}

/**
 * Pad or truncate text to exact visual width.
 */
export function fitWidth(text, width) {
  const tw = visWidth(text);
  if (tw >= width) return text.slice(0, width);
  return text + ' '.repeat(width - tw);
}

/**
 * Format a number with leading zeros.
 */
export function padNum(n, digits = 2) {
  return String(Math.floor(n)).padStart(digits, '0');
}

/**
 * Format time as MM:SS.f
 */
export function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${padNum(m)}:${padNum(s)}.${Math.floor((s % 1) * 10)}`;
}

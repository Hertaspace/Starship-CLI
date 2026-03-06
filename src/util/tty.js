/**
 * Terminal capability detection and platform-specific handling.
 */

import ansiEscapes from 'ansi-escapes';

/**
 * Detect comprehensive terminal capabilities.
 */
export function detectTerminalCapabilities() {
  const isWin = process.platform === 'win32';
  const shell = detectShell();
  const isTTY = !!process.stdout.isTTY;
  const width = process.stdout.columns || 80;
  const height = process.stdout.rows || 24;

  // Color level detection
  let colorLevel = 3; // default truecolor
  if (!isTTY || process.env.NO_COLOR !== undefined) {
    colorLevel = 0;
  } else if (process.env.COLORTERM === 'truecolor' || process.env.COLORTERM === '24bit') {
    colorLevel = 3;
  } else if (process.env.WT_SESSION) {
    colorLevel = 3; // Windows Terminal
  } else if (isWin && shell === 'powershell') {
    colorLevel = 2; // conservative for PowerShell
  } else if ((process.env.TERM || '').includes('256color')) {
    colorLevel = 2;
  } else if (isWin) {
    colorLevel = 1;
  }

  const isPowerShell = isWin && (shell === 'powershell' || shell === 'pwsh');

  return {
    isTTY,
    width,
    height,
    platform: process.platform,
    shell,
    colorLevel,
    unicodeSafe: !isPowerShell,
    isPowerShell,
    compatMode: isPowerShell && colorLevel < 3,
  };
}

function detectShell() {
  const parentEnv = process.env.PSModulePath;
  if (parentEnv) return 'powershell';
  const shell = process.env.SHELL || '';
  if (shell.includes('zsh')) return 'zsh';
  if (shell.includes('bash')) return 'bash';
  if (process.env.ComSpec) return 'cmd';
  return 'unknown';
}

/**
 * Hide the terminal cursor.
 */
export function hideCursor() {
  process.stdout.write(ansiEscapes.cursorHide);
}

/**
 * Show the terminal cursor.
 */
export function showCursor() {
  process.stdout.write(ansiEscapes.cursorShow);
}

/**
 * Clear the terminal screen.
 */
export function clearScreen() {
  process.stdout.write(ansiEscapes.clearScreen);
}

/**
 * Move cursor to position.
 */
export function moveCursor(x, y) {
  process.stdout.write(ansiEscapes.cursorTo(x, y));
}

/**
 * Setup graceful cleanup on exit signals.
 */
export function setupCleanup(cleanupFn) {
  const handler = () => {
    cleanupFn();
    process.exit(0);
  };
  process.on('SIGINT', handler);
  process.on('SIGTERM', handler);
  process.on('exit', () => {
    showCursor();
    process.stdout.write('\x1b[0m');
  });
}

/**
 * Listen for terminal resize events.
 */
export function onResize(callback) {
  process.stdout.on('resize', () => {
    const width = process.stdout.columns || 80;
    const height = process.stdout.rows || 24;
    callback(width, height);
  });
}

/**
 * Renderer - composes the screen buffer into an ANSI string and outputs to terminal.
 * Uses log-update for flicker-free frame replacement.
 */

import logUpdate from 'log-update';
import { RESET, styleCell, detectColorLevel, COLOR_NONE } from './colors.js';

export class Renderer {
  constructor(screen) {
    this.screen = screen;
  }

  /**
   * Render the screen buffer to a single ANSI string and output it.
   */
  render() {
    const { width, height, buffer } = this.screen;
    const noColor = detectColorLevel() === COLOR_NONE;
    const lines = [];

    for (let y = 0; y < height; y++) {
      let line = '';
      let lastFg = null;
      let lastBg = null;
      let styleActive = false;

      for (let x = 0; x < width; x++) {
        const cell = buffer[y][x];

        if (noColor) {
          line += cell.char;
          continue;
        }

        const fgSame = cell.fg === lastFg || (cell.fg && lastFg && cell.fg[0] === lastFg[0] && cell.fg[1] === lastFg[1] && cell.fg[2] === lastFg[2]);
        const bgSame = cell.bg === lastBg || (cell.bg && lastBg && cell.bg[0] === lastBg[0] && cell.bg[1] === lastBg[1] && cell.bg[2] === lastBg[2]);

        if (!fgSame || !bgSame) {
          if (styleActive && !cell.fg && !cell.bg) {
            line += RESET;
            styleActive = false;
          } else if (cell.fg || cell.bg) {
            line += RESET + styleCell(cell.fg, cell.bg);
            styleActive = true;
          }
          lastFg = cell.fg;
          lastBg = cell.bg;
        }

        line += cell.char;
      }

      if (styleActive) {
        line += RESET;
      }

      lines.push(line);
    }

    logUpdate(lines.join('\n'));
  }

  /**
   * Final cleanup of renderer output.
   */
  cleanup() {
    logUpdate.clear();
  }
}

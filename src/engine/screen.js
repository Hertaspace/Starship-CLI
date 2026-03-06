/**
 * Virtual screen buffer - 2D character canvas with per-cell styling.
 * Each cell stores: char, fg (foreground), bg (background), zIndex.
 */

export class Cell {
  constructor() {
    this.char = ' ';
    this.fg = null;
    this.bg = null;
    this.zIndex = 0;
  }

  reset() {
    this.char = ' ';
    this.fg = null;
    this.bg = null;
    this.zIndex = 0;
  }

  copyFrom(other) {
    this.char = other.char;
    this.fg = other.fg;
    this.bg = other.bg;
    this.zIndex = other.zIndex;
  }

  equals(other) {
    return this.char === other.char &&
           this.fg === other.fg &&
           this.bg === other.bg;
  }
}

export class Screen {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.buffer = [];
    for (let y = 0; y < height; y++) {
      const row = [];
      for (let x = 0; x < width; x++) {
        row.push(new Cell());
      }
      this.buffer.push(row);
    }
    // Camera offset for shake/pan effects
    this.cameraX = 0;
    this.cameraY = 0;
  }

  clear() {
    for (let y = 0; y < this.height; y++) {
      for (let x = 0; x < this.width; x++) {
        this.buffer[y][x].reset();
      }
    }
  }

  inBounds(x, y) {
    return x >= 0 && x < this.width && y >= 0 && y < this.height;
  }

  /**
   * Set a single pixel (character cell) with style.
   * Respects zIndex - only overwrites if new zIndex >= existing.
   */
  setPixel(x, y, char, fg = null, bg = null, zIndex = 0) {
    const px = Math.round(x + this.cameraX);
    const py = Math.round(y + this.cameraY);
    if (!this.inBounds(px, py)) return;
    const cell = this.buffer[py][px];
    if (zIndex >= cell.zIndex) {
      cell.char = char;
      cell.fg = fg;
      cell.bg = bg;
      cell.zIndex = zIndex;
    }
  }

  /**
   * Draw a text string horizontally starting at (x, y).
   */
  drawText(x, y, text, fg = null, bg = null, zIndex = 0) {
    for (let i = 0; i < text.length; i++) {
      this.setPixel(x + i, y, text[i], fg, bg, zIndex);
    }
  }

  /**
   * Draw a multi-line sprite (array of strings) at position.
   * Optional colorMap: function(localX, localY, char) => { fg, bg }
   */
  drawSprite(x, y, lines, colorMap = null, zIndex = 0) {
    for (let row = 0; row < lines.length; row++) {
      const line = lines[row];
      for (let col = 0; col < line.length; col++) {
        const ch = line[col];
        if (ch === ' ' && (!colorMap || !colorMap(col, row, ch)?.bg)) continue;
        let fg = null, bg = null;
        if (colorMap) {
          const c = colorMap(col, row, ch);
          if (c) { fg = c.fg; bg = c.bg; }
        }
        this.setPixel(x + col, y + row, ch, fg, bg, zIndex);
      }
    }
  }

  /**
   * Fill a rectangular area with a character and style.
   */
  fillRect(x, y, w, h, char = ' ', fg = null, bg = null, zIndex = 0) {
    for (let row = 0; row < h; row++) {
      for (let col = 0; col < w; col++) {
        this.setPixel(x + col, y + row, char, fg, bg, zIndex);
      }
    }
  }

  /**
   * Get a cell at position (without camera offset).
   */
  getCell(x, y) {
    if (!this.inBounds(x, y)) return null;
    return this.buffer[y][x];
  }
}

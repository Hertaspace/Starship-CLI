/**
 * Fixed-timestep game loop with frame rate control.
 */

export class Loop {
  constructor(fps, updateFn, renderFn) {
    this.fps = fps;
    this.frameDuration = 1000 / fps;
    this.updateFn = updateFn;
    this.renderFn = renderFn;
    this.running = false;
    this.startTime = 0;
    this.frameCount = 0;
    this.timer = null;
  }

  start() {
    this.running = true;
    this.startTime = Date.now();
    this.frameCount = 0;
    this._tick();
  }

  stop() {
    this.running = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  _tick() {
    if (!this.running) return;

    const now = Date.now();
    const elapsed = (now - this.startTime) / 1000; // seconds

    this.updateFn(elapsed, 1 / this.fps);
    this.renderFn();
    this.frameCount++;

    if (!this.running) return;

    // Schedule next frame, compensating for processing time
    const frameEnd = Date.now();
    const processingTime = frameEnd - now;
    const delay = Math.max(1, this.frameDuration - processingTime);

    this.timer = setTimeout(() => this._tick(), delay);
  }

  getElapsed() {
    return (Date.now() - this.startTime) / 1000;
  }
}

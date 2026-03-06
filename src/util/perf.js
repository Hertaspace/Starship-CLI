/**
 * Simple performance monitoring.
 */

export class PerfMonitor {
  constructor() {
    this.frameTimes = [];
    this.maxSamples = 60;
  }

  startFrame() {
    this._frameStart = Date.now();
  }

  endFrame() {
    if (this._frameStart) {
      const dt = Date.now() - this._frameStart;
      this.frameTimes.push(dt);
      if (this.frameTimes.length > this.maxSamples) {
        this.frameTimes.shift();
      }
    }
  }

  getAvgFrameTime() {
    if (this.frameTimes.length === 0) return 0;
    const sum = this.frameTimes.reduce((a, b) => a + b, 0);
    return sum / this.frameTimes.length;
  }

  getFPS() {
    const avg = this.getAvgFrameTime();
    return avg > 0 ? Math.round(1000 / avg) : 0;
  }
}

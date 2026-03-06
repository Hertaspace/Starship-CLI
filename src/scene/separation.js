/**
 * Scene 3: Stage separation - the showpiece moment.
 * Slow-motion feel, cold gas jets, debris, two stages diverging.
 */

import { drawBackground } from './background.js';
import { drawFlame } from '../entity/flame.js';
import { drawStarship } from '../entity/starship.js';
import { drawBooster } from '../entity/booster.js';
import { drawHUD } from './hud.js';
import { FLAME_LAUNCH, FLAME_LAND, COLDGAS } from '../assets/palettes.js';
import { noise1D } from '../engine/noise.js';
import { easeOutCubic, easeInOutQuad, smoothstep } from '../engine/easing.js';

/**
 * Render the separation scene.
 */
export function renderSeparation(screen, t, localT, progress, state, smoke, particles) {
  const { width, height } = screen;

  // Flash effect at separation moment
  if (progress < 0.08) {
    const flashIntensity = 1 - progress / 0.08;
    const flashColor = [
      Math.floor(255 * flashIntensity * 0.3),
      Math.floor(255 * flashIntensity * 0.3),
      Math.floor(255 * flashIntensity * 0.4),
    ];
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        screen.setPixel(x, y, ' ', null, flashColor, 0);
      }
    }
  } else {
    drawBackground(screen, t, 30);
  }

  // Camera shake at separation
  const shakeDecay = Math.max(0, 1 - progress * 3);
  screen.cameraX = Math.round((noise1D(t * 20) - 0.5) * shakeDecay * 2);
  screen.cameraY = Math.round((noise1D(t * 18 + 50) - 0.5) * shakeDecay);

  const cx = Math.floor(width / 2);

  // Separation gap increases with time
  const gapProgress = easeOutCubic(Math.min(1, progress * 2));
  const gap = Math.floor(gapProgress * 12);

  // Starship (upper stage) - drifts upward and slightly right
  const shipX = cx + Math.floor(gapProgress * 4);
  const shipY = Math.floor(height * 0.25 - gapProgress * 5);
  const shipInfo = drawStarship(screen, shipX, shipY, 0.8, 5);

  // Upper stage engine ignition (after a brief delay)
  if (progress > 0.3) {
    const shipFlameProgress = (progress - 0.3) / 0.7;
    const flameLen = Math.floor(2 + shipFlameProgress * 5 + noise1D(t * 7) * 1);
    drawFlame(screen, shipX, shipInfo.bottomY, flameLen, 3, t, FLAME_LAUNCH, 4);
  }

  // Booster - drifts downward and slightly left
  const boosterX = cx - Math.floor(gapProgress * 3);
  const boosterY = Math.floor(height * 0.25 + gap + shipInfo.height);
  const boosterInfo = drawBooster(screen, boosterX, boosterY, 0.8, 5);

  // Cold gas jets at the separation interface
  if (progress < 0.5) {
    const jetIntensity = Math.floor(8 * (1 - progress * 2));
    const separationY = Math.floor((shipInfo.bottomY + boosterInfo.topY) / 2);
    particles.emitColdGas(cx, separationY, jetIntensity, 'both');

    // Debris
    if (progress < 0.2 && Math.random() < 0.4) {
      particles.emitDebris(cx, separationY, 3);
    }
  }

  // Booster flip maneuver (later in scene)
  if (progress > 0.6) {
    const flipProgress = (progress - 0.6) / 0.4;
    // Show brief RCS firing
    if (flipProgress < 0.5) {
      const rcsY = boosterY + 1;
      screen.setPixel(boosterX - 4, rcsY, '~', COLDGAS.bright, null, 4);
      screen.setPixel(boosterX + 4, rcsY, '~', COLDGAS.bright, null, 4);
    }
  }

  // Draw particles
  smoke.draw(screen);
  particles.draw(screen);

  // HUD
  const altitude = 65000 + Math.floor(progress * 5000);
  const velocity = 3000 - Math.floor(progress * 500);
  drawHUD(screen, t, 'separation', {
    altitude,
    velocity,
    status: progress < 0.15 ? 'STAGE SEP' : 'NOMINAL',
    prop: 'BOOSTER SEP CONF',
  });

  state.separationProgress = progress;
}

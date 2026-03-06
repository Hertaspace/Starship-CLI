/**
 * Scene 4: Booster return to launch site (RTLS).
 * Camera cuts back to ground view. Booster descends toward the tower.
 */

import { drawBackground } from './background.js';
import { drawGround, drawTower } from '../entity/tower.js';
import { drawBooster, drawGridFins } from '../entity/booster.js';
import { drawLandingFlame } from '../entity/flame.js';
import { drawChopsticks } from '../entity/chopsticks.js';
import { drawHUD } from './hud.js';
import { ROCKET } from '../assets/palettes.js';
import { noise1D } from '../engine/noise.js';
import { easeInOutQuad, easeOutQuad, mapRange } from '../engine/easing.js';

/**
 * Render the booster return scene.
 */
export function renderReturn(screen, t, localT, progress, state, smoke, particles) {
  const { width, height } = screen;
  const groundY = height - 4;

  // Gentle camera
  screen.cameraX = 0;
  screen.cameraY = 0;

  // Background
  drawBackground(screen, t);

  // Ground and tower
  drawGround(screen, groundY);
  const towerX = Math.floor(width / 2) - 12;
  const towerHeight = groundY - 4;
  const towerInfo = drawTower(screen, towerX, groundY, towerHeight);

  // Chopsticks on tower - arms open, waiting
  const chopY = towerInfo.topY + 3;
  const openness = 0.7 + noise1D(t * 0.5) * 0.05;
  drawChopsticks(screen, towerInfo.centerX, chopY, openness, 6);

  // Booster descending
  // Starts small/far, gets bigger as it approaches
  const descentProgress = easeOutQuad(progress);
  const scale = 0.2 + descentProgress * 0.6; // 0.2 -> 0.8

  // Booster starts high and to the right, arcs toward tower
  const targetX = towerInfo.centerX;
  const startX = width * 0.75;
  const boosterX = Math.floor(startX + (targetX - startX) * descentProgress);

  const startY = -5;
  const targetY = chopY - 2;
  const boosterY = Math.floor(startY + (targetY - startY) * descentProgress);

  const boosterInfo = drawBooster(screen, boosterX, boosterY, scale, 5);

  // Grid fins visible during descent
  if (scale > 0.4) {
    drawGridFins(screen, boosterX, boosterInfo.topY - 1, 5);
  }

  // Landing burn flame (underneath)
  if (progress > 0.2) {
    const burnProgress = (progress - 0.2) / 0.8;
    const flameLen = Math.max(1, Math.floor(3 + burnProgress * 4 + noise1D(t * 6) * 1.5));
    const flameWidth = Math.max(2, Math.floor(3 * scale));
    drawLandingFlame(screen, boosterX, boosterInfo.bottomY, flameLen, flameWidth, t, 4);
  }

  // Slight micro-adjustments (RCS puffs)
  if (progress > 0.5 && Math.random() < 0.15) {
    const side = Math.random() < 0.5 ? -3 : 3;
    screen.setPixel(boosterX + side, boosterInfo.topY + 1, '~', [180, 200, 240], null, 4);
  }

  // Alignment guide line (subtle)
  if (progress > 0.4 && progress < 0.9) {
    const guideX = targetX;
    for (let y = boosterInfo.bottomY + 5; y < groundY - 2; y += 3) {
      screen.setPixel(guideX, y, ':', [40, 60, 40], null, 1);
    }
  }

  // Smoke from landing burn
  if (progress > 0.3 && Math.random() < 0.3) {
    smoke.emit(boosterX, boosterInfo.bottomY + 4, 1, {
      dxRange: [-2, 2],
      dyRange: [0.5, 1.5],
      life: 2,
    });
  }
  smoke.draw(screen);
  particles.draw(screen);

  // HUD
  const altitude = Math.max(0, Math.floor(50000 * (1 - descentProgress)));
  const velocity = Math.max(0, Math.floor(500 * (1 - descentProgress)));
  drawHUD(screen, t, 'return', {
    altitude,
    velocity,
    status: 'RTLS',
    prop: 'LANDING BURN',
  });

  // Pass state for catch scene
  state.catchTowerX = towerX;
  state.catchTowerInfo = towerInfo;
  state.catchChopY = chopY;
  state.catchGroundY = groundY;
  state.catchTowerHeight = towerHeight;
}

/**
 * Scene 5: Tower catch - the climactic moment.
 * Booster descends into the chopstick arms, catch, hold, hero shot.
 */

import { drawBackground } from './background.js';
import { drawGround, drawTower } from '../entity/tower.js';
import { drawBooster } from '../entity/booster.js';
import { drawLandingFlame } from '../entity/flame.js';
import { drawChopsticks } from '../entity/chopsticks.js';
import { drawHUD } from './hud.js';
import { UI } from '../assets/palettes.js';
import { noise1D } from '../engine/noise.js';
import { easeOutCubic, easeOutElastic, smoothstep } from '../engine/easing.js';

/**
 * Render the catch scene.
 */
export function renderCatch(screen, t, localT, progress, state, smoke, particles) {
  const { width, height } = screen;
  const groundY = state.catchGroundY || height - 4;

  // Background
  drawBackground(screen, t);

  // Ground
  drawGround(screen, groundY);

  // Tower
  const towerX = state.catchTowerX || Math.floor(width / 2) - 12;
  const towerHeight = state.catchTowerHeight || groundY - 4;
  const towerInfo = drawTower(screen, towerX, groundY, towerHeight);

  const catchMoment = 0.5; // when the catch happens (50% through scene)
  const isCaught = progress >= catchMoment;

  // Booster final descent
  const targetX = towerInfo.centerX;
  const chopY = state.catchChopY || towerInfo.topY + 3;

  let boosterY;
  let boosterX = targetX;
  if (!isCaught) {
    // Descending to catch point
    const preProgress = progress / catchMoment;
    const descentEase = easeOutCubic(preProgress);
    boosterY = Math.floor(chopY - 15 + descentEase * 15);
    // Very slight lateral adjustment
    boosterX = targetX + Math.round((noise1D(t * 3) - 0.5) * (1 - preProgress) * 2);
  } else {
    // Caught - locked in position
    boosterY = chopY;
    boosterX = targetX;
  }

  // Draw booster
  const boosterInfo = drawBooster(screen, boosterX, boosterY, 0.8, 5);

  // Chopstick arms
  let armOpenness;
  if (!isCaught) {
    // Arms open, waiting
    armOpenness = 0.6 + noise1D(t) * 0.05;
  } else {
    // Arms closing after catch
    const closeProgress = Math.min(1, (progress - catchMoment) / 0.2);
    armOpenness = Math.max(0, 0.6 * (1 - easeOutCubic(closeProgress)));
  }
  drawChopsticks(screen, towerInfo.centerX, chopY, armOpenness, 6);

  // Landing flame (cuts off at catch)
  if (!isCaught) {
    const flameLen = Math.max(1, Math.floor(4 + noise1D(t * 7) * 2 - progress * 3));
    drawLandingFlame(screen, boosterX, boosterInfo.bottomY, flameLen, 3, t, 4);
  } else if (progress < catchMoment + 0.1) {
    // Brief residual flame
    const fadeProgress = (progress - catchMoment) / 0.1;
    const flameLen = Math.max(0, Math.floor(3 * (1 - fadeProgress)));
    if (flameLen > 0) {
      drawLandingFlame(screen, boosterX, boosterInfo.bottomY, flameLen, 2, t, 4);
    }
  }

  // Catch impact effects
  if (isCaught && progress < catchMoment + 0.15) {
    const impactProgress = (progress - catchMoment) / 0.15;

    // Screen shake
    const shakeDecay = Math.max(0, 1 - impactProgress * 2);
    screen.cameraX = Math.round((noise1D(t * 25) - 0.5) * shakeDecay * 2);
    screen.cameraY = Math.round((noise1D(t * 22 + 30) - 0.5) * shakeDecay);

    // Flash
    if (impactProgress < 0.2) {
      const flashBright = Math.floor(40 * (1 - impactProgress / 0.2));
      for (let y = chopY - 3; y < chopY + 5; y++) {
        for (let x = targetX - 6; x < targetX + 6; x++) {
          const cell = screen.getCell(x, y);
          if (cell) {
            cell.fg = [
              Math.min(255, (cell.fg ? cell.fg[0] : 0) + flashBright),
              Math.min(255, (cell.fg ? cell.fg[1] : 0) + flashBright),
              Math.min(255, (cell.fg ? cell.fg[2] : 0) + flashBright),
            ];
          }
        }
      }
    }

    // Vapor / steam burst
    if (impactProgress < 0.5) {
      smoke.emit(targetX, chopY + 2, 3, {
        dxRange: [-3, 3],
        dyRange: [-1, 1],
        life: 2,
      });
      particles.emitVapor(targetX, chopY + 3, 2);
    }
  } else {
    screen.cameraX = 0;
    screen.cameraY = 0;
  }

  smoke.draw(screen);
  particles.draw(screen);

  // HUD
  const statusText = isCaught ? 'CATCH SUCCESS' : 'FINAL APPROACH';
  drawHUD(screen, t, isCaught ? 'finale' : 'catch', {
    altitude: isCaught ? 0 : Math.max(0, Math.floor(500 * (1 - progress / catchMoment))),
    velocity: isCaught ? 0 : Math.max(0, Math.floor(50 * (1 - progress / catchMoment))),
    status: statusText,
    prop: isCaught ? 'MISSION SUCCESS' : 'LANDING BURN',
  });
}

/**
 * Render the finale / hero shot.
 */
export function renderFinale(screen, t, localT, progress, state, smoke, particles) {
  // Reuse catch scene with progress=1 (fully caught, static)
  renderCatch(screen, t, localT, 1.0, state, smoke, particles);

  // Add "MISSION COMPLETE" text
  const { width, height } = screen;
  const msg = '* MISSION COMPLETE *';
  const msgX = Math.floor(width / 2 - msg.length / 2);
  const msgY = 2;

  // Blinking effect
  if (Math.floor(t * 2) % 2 === 0) {
    screen.drawText(msgX, msgY, msg, UI.success, null, 10);
  }
}

/**
 * Scene 1: Ignition and liftoff - rocket lifts off the pad with dramatic flame.
 */

import { drawBackground } from './background.js';
import { drawGround, drawTower, drawLaunchPad } from '../entity/tower.js';
import { drawFlame, drawExhaustSpread } from '../entity/flame.js';
import { drawHUD } from './hud.js';
import { ROCKET_FULL, ROCKET_MID } from '../assets/sprites.js';
import { ROCKET } from '../assets/palettes.js';
import { noise1D } from '../engine/noise.js';
import { easeInCubic, easeOutQuad, mapRange } from '../engine/easing.js';

/**
 * Render the liftoff scene.
 */
export function renderLiftoff(screen, t, localT, progress, state, smoke, particles) {
  const { width, height } = screen;
  const groundY = height - 4;

  // Camera shake during liftoff
  const shakeIntensity = progress < 0.3 ? progress / 0.3 * 2 : Math.max(0, 2 - progress * 1.5);
  screen.cameraX = Math.round((noise1D(t * 15) - 0.5) * shakeIntensity);
  screen.cameraY = Math.round((noise1D(t * 12 + 100) - 0.5) * shakeIntensity * 0.5);

  // Rocket rises with easing
  const riseProgress = easeInCubic(Math.min(1, progress));
  const rocketRise = riseProgress * (height + 10); // pixels to rise
  const cameraFollow = Math.max(0, riseProgress * height * 0.3); // camera follows up

  const scrollY = cameraFollow;

  // Background with parallax
  drawBackground(screen, t, scrollY);

  // Ground and tower scroll down as rocket rises
  const effectiveGroundY = groundY + Math.floor(scrollY);

  if (effectiveGroundY < height + 5) {
    drawGround(screen, Math.min(effectiveGroundY, height - 1));

    // Tower
    const towerX = state.towerX || Math.floor(width / 2) - 12;
    const towerHeight = state.towerHeight || (groundY - 4);
    if (effectiveGroundY - towerHeight < height) {
      drawTower(screen, towerX, Math.min(effectiveGroundY, height - 1), towerHeight);
    }

    // Launch pad
    drawLaunchPad(screen, state.rocketCX || Math.floor(width / 2), Math.min(effectiveGroundY, height - 1));
  }

  // Rocket position
  const rocketCX = state.rocketCX || Math.floor(width / 2);

  // Choose sprite based on how far it's risen
  const useSmallSprite = progress > 0.7;
  const sprite = useSmallSprite ? ROCKET_MID : ROCKET_FULL;
  const spriteWidth = sprite[0].length;
  const rocketX = rocketCX - Math.floor(spriteWidth / 2);

  // Rocket base position (starts at groundY - 2, rises up)
  const baseRocketBottomY = (state.rocketBottomY || groundY - 2);
  const rocketBottomY = baseRocketBottomY - Math.floor(rocketRise) + Math.floor(scrollY);
  const rocketTopY = rocketBottomY - sprite.length;

  // Only draw rocket if visible
  if (rocketTopY < height && rocketBottomY > -5) {
    const colorMap = (col, row, ch) => {
      if (ch === ':') return { fg: ROCKET.heatshield };
      if (ch === 'S') return { fg: ROCKET.dark };
      if (ch === '/' || ch === '\\') return { fg: ROCKET.silver };
      if (ch === '_') return { fg: ROCKET.gray };
      return { fg: ROCKET.white };
    };
    screen.drawSprite(rocketX, rocketTopY, sprite, colorMap, 5);

    // Flame below rocket
    const flameLength = Math.floor(4 + progress * 10 + noise1D(t * 6) * 2);
    const flameWidth = useSmallSprite ? 4 : 6;
    drawFlame(screen, rocketCX, rocketBottomY, flameLength, flameWidth, t);
  }

  // Ground-level exhaust spread (early liftoff)
  if (progress < 0.4 && effectiveGroundY < height) {
    const spreadWidth = Math.floor(10 + progress * 30);
    drawExhaustSpread(screen, rocketCX, Math.min(effectiveGroundY, height - 2), spreadWidth, t);
  }

  // Emit smoke from launch pad
  if (progress < 0.5) {
    const smokeRate = progress < 0.2 ? 5 : 2;
    smoke.emit(rocketCX, Math.min(effectiveGroundY - 1, height - 3), smokeRate, {
      dxRange: [-4, 4],
      dyRange: [-1, 0.5],
      life: 3,
    });
  }

  // Update and draw smoke (with camera offset)
  smoke.draw(screen);

  // Spark particles near flame
  if (Math.random() < 0.3) {
    particles.emitSparks(rocketCX, rocketBottomY + 3, 2, { speed: 4, life: 1 });
  }
  particles.draw(screen);

  // HUD
  const altitude = Math.floor(riseProgress * 5000);
  const velocity = Math.floor(riseProgress * 800);
  drawHUD(screen, t, 'liftoff', {
    altitude,
    velocity,
    status: 'NOMINAL',
    prop: 'PROP NOMINAL',
  });

  // Store state
  state.scrollY = scrollY;
  state.rocketRise = rocketRise;
}

/**
 * HUD / telemetry overlay.
 */

import { UI } from '../assets/palettes.js';
import { formatTime } from '../util/text.js';

/**
 * Draw the telemetry HUD.
 */
export function drawHUD(screen, t, sceneId, extra = {}) {
  const { width } = screen;
  const zIndex = 10;

  // Time code (top-left)
  const timeStr = `T+${formatTime(t)}`;
  screen.drawText(1, 0, timeStr, UI.dim, null, zIndex);

  // Mission phase (top-right)
  const phaseLabels = {
    launchpad: 'PRE-LAUNCH',
    liftoff: 'LIFTOFF',
    ascent: 'STAGE 1 ASCENT',
    separation: 'STAGE SEP',
    return: 'BOOSTER RTLS',
    catch: 'TOWER CATCH',
    finale: 'CATCH SUCCESS',
  };
  const phase = phaseLabels[sceneId] || '';
  screen.drawText(width - phase.length - 1, 0, phase, UI.label, null, zIndex);

  // Telemetry data (bottom-left area)
  if (extra.altitude !== undefined) {
    const altStr = `ALT  ${String(Math.floor(extra.altitude)).padStart(6)} m`;
    screen.drawText(1, screen.height - 3, altStr, UI.dim, null, zIndex);
  }
  if (extra.velocity !== undefined) {
    const velStr = `VEL  ${String(Math.floor(extra.velocity)).padStart(6)} m/s`;
    screen.drawText(1, screen.height - 2, velStr, UI.dim, null, zIndex);
  }

  // Status indicator (bottom-right)
  if (extra.status) {
    const statusColor = extra.status === 'NOMINAL' ? UI.text :
                        extra.status === 'CATCH SUCCESS' ? UI.success :
                        UI.warn;
    screen.drawText(width - extra.status.length - 1, screen.height - 2, extra.status, statusColor, null, zIndex);
  }

  // Prop status
  if (extra.prop) {
    screen.drawText(width - extra.prop.length - 1, screen.height - 3, extra.prop, UI.dim, null, zIndex);
  }
}

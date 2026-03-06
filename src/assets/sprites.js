/**
 * ASCII sprite definitions for all visual elements.
 * Each sprite is an array of strings (rows).
 */

// ─── Starship (upper stage) ───

export const STARSHIP_CLOSE = [
  '    /\\    ',
  '   /  \\   ',
  '  /    \\  ',
  '  |    |  ',
  '  | SS |  ',
  '  |    |  ',
  '  |    |  ',
  '  |    |  ',
  '  |____|  ',
];

export const STARSHIP_MID = [
  '  /\\  ',
  ' /  \\ ',
  ' |  | ',
  ' |SS| ',
  ' |  | ',
  ' |__| ',
];

export const STARSHIP_FAR = [
  ' /\\ ',
  ' || ',
  ' || ',
  ' \\/ ',
];

export const STARSHIP_TINY = [
  ' | ',
  ' | ',
];

// ─── Super Heavy Booster ───

export const BOOSTER_CLOSE = [
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |_/\\_|  ',
  ' /|    |\\ ',
  '/ |____| \\',
];

export const BOOSTER_MID = [
  ' |::| ',
  ' |::| ',
  ' |::| ',
  ' |::| ',
  ' |::| ',
  ' |/\\| ',
  '/|__|\\',
];

export const BOOSTER_FAR = [
  ' || ',
  ' || ',
  ' || ',
  ' /\\ ',
];

export const BOOSTER_TINY = [
  ' | ',
  ' V ',
];

// ─── Full rocket (stacked) ───

export const ROCKET_FULL = [
  '    /\\    ',
  '   /  \\   ',
  '  /    \\  ',
  '  |    |  ',
  '  | SS |  ',
  '  |    |  ',
  '  |    |  ',
  '  |____|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |::::|  ',
  '  |_/\\_|  ',
  ' /|    |\\ ',
  '/ |____| \\',
];

export const ROCKET_MID = [
  '  /\\  ',
  ' /  \\ ',
  ' |  | ',
  ' |SS| ',
  ' |  | ',
  ' |__| ',
  ' |::| ',
  ' |::| ',
  ' |::| ',
  ' |::| ',
  ' |/\\| ',
  '/|__|\\',
];

export const ROCKET_SMALL = [
  ' /\\ ',
  ' || ',
  ' || ',
  ' || ',
  ' || ',
  ' || ',
  ' /\\ ',
];

// ─── Launch Tower ───

export const TOWER_STRUCTURE = [
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  ' |  | ',
  ' |==| ',
  '=|==|=',
  '/|  |\\',
  '/|__|\\',
];

// ─── Chopstick Arms ───

export const CHOPSTICKS_OPEN = [
  '\\      /',
  ' \\    / ',
];

export const CHOPSTICKS_CLOSING = [
  ' \\    / ',
  '  \\  /  ',
];

export const CHOPSTICKS_CAUGHT = [
  '  \\  /  ',
  '  |==|  ',
];

// ─── Ground / Pad ───

export const LAUNCH_PAD = [
  '################',
  '================',
];

// ─── Grid fins (on booster) ───

export const GRID_FINS = [
  '=|  |=',
];

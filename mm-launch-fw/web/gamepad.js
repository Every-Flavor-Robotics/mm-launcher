// Gamepad aiming: pure mapping from a standard-layout gamepad to aim rates and
// operator actions. No DOM, no timers: the panel polls navigator.getGamepads()
// and feeds this; test/host/test_gamepad.mjs tests it under node.
//
// Standard mapping (https://w3c.github.io/gamepad/#remapping):
//   axes  0 LX, 1 LY, 2 RX, 3 RY        (up is negative Y)
//   buttons 0 A, 1 B, 2 X, 3 Y, 4 LB, 5 RB
//
// Controls:
//   left stick   pan / tilt at up to `maxRate` deg/s (cubic expo for fine aim)
//   right stick  the same at `fineScale` of the rate
//   Y            center (pan 0, tilt 0)
//   B            stop (always, whatever else is held)
//   A            fire one shot, ONLY while LB (the deadman) is held and the
//                board reports state 4 (at speed). The firmware re-checks
//                everything; this only decides whether to ask.
// Spin-up is deliberately not on the pad: it stays a panel button.
//
// Conventions match the firmware: pan + is counter-clockwise seen from above,
// so pushing the stick right turns the turret right (pan decreasing); tilt +
// is muzzle up, so pushing the stick up raises it.

export const BTN = { A: 0, B: 1, X: 2, Y: 3, LB: 4, RB: 5 };
export const AT_SPEED = 4;

export const DEFAULTS = Object.freeze({
  deadzone: 0.15,
  expo: 0.6,       // 0 = linear, 1 = pure cubic
  maxRate: 90,     // deg/s at full stick
  fineScale: 0.25, // right stick
  panMin: -90, panMax: 90,
  tiltMin: 0, tiltMax: 45,
  maxDt: 0.1,      // s; a background tab must not jump the turret on return
});

/// Deadzone + expo, output in [-1, 1].
export function shape(x, deadzone = DEFAULTS.deadzone, expo = DEFAULTS.expo) {
  if (!Number.isFinite(x)) return 0;
  const a = Math.abs(x);
  if (a <= deadzone) return 0;
  const n = Math.min(1, (a - deadzone) / (1 - deadzone));
  return Math.sign(x) * (expo * n * n * n + (1 - expo) * n);
}

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

/// Integrate one poll. `axes` is the gamepad axes array, `dt` seconds.
/// Returns { pan, tilt, moved }.
export function stepAim(aim, axes, dt, cfg = DEFAULTS) {
  const t = clamp(Number.isFinite(dt) ? dt : 0, 0, cfg.maxDt);
  const ax = i => (axes && axes.length > i ? axes[i] : 0);
  const sx = shape(ax(0), cfg.deadzone, cfg.expo) + cfg.fineScale * shape(ax(2), cfg.deadzone, cfg.expo);
  const sy = shape(ax(1), cfg.deadzone, cfg.expo) + cfg.fineScale * shape(ax(3), cfg.deadzone, cfg.expo);
  const pan = clamp(aim.pan - sx * cfg.maxRate * t, cfg.panMin, cfg.panMax);
  const tilt = clamp(aim.tilt - sy * cfg.maxRate * t, cfg.tiltMin, cfg.tiltMax);
  return { pan, tilt, moved: pan !== aim.pan || tilt !== aim.tilt };
}

/// Button states as booleans (a pad reports {pressed, value} objects).
export function pressedList(buttons) {
  return Array.from(buttons || [], b => !!(b && (b.pressed || b.value > 0.5)));
}

/// Indices that went from up to down since the last poll.
export function edges(prev, cur) {
  const out = [];
  for (let i = 0; i < cur.length; i++) if (cur[i] && !prev[i]) out.push(i);
  return out;
}

/// What to do this poll. `held` is the current pressed list, `pressed` the
/// new presses (edges), `state` the board state code (telemetry `state`).
/// Returns a list of 'stop' | 'center' | 'fire' | 'fire_refused'.
export function decide(pressed, held, state) {
  const acts = [];
  if (pressed.includes(BTN.B)) return ['stop']; // stop wins, nothing else this poll
  if (pressed.includes(BTN.Y)) acts.push('center');
  if (pressed.includes(BTN.A)) acts.push(held[BTN.LB] && state === AT_SPEED ? 'fire' : 'fire_refused');
  return acts;
}

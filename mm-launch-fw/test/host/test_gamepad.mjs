// Node tests for web/gamepad.js (run by `make -C test/host`).
import { shape, stepAim, edges, decide, pressedList, BTN, DEFAULTS } from '../../web/gamepad.js';

let failures = 0;
const check = (cond, what) => { if (!cond) { console.log('FAIL', what); failures++; } };
const near = (a, b, tol = 1e-6) => Math.abs(a - b) <= tol;

// shape: deadzone, saturation, sign, NaN
check(shape(0.1) === 0, 'inside deadzone is 0');
check(shape(-0.15) === 0, 'deadzone edge is 0');
check(near(shape(1), 1) && near(shape(-1), -1), 'full stick is +/-1');
check(shape(0.5) > 0 && shape(0.5) < 0.5, 'expo makes half stick gentler than linear');
check(shape(NaN) === 0, 'NaN axis is 0');
check(near(shape(1.4), 1), 'over-range clamps');

// stepAim sign conventions: stick right -> pan decreases (turn right, CW from above)
let a = stepAim({ pan: 0, tilt: 10 }, [1, 0, 0, 0], 0.1);
check(near(a.pan, -DEFAULTS.maxRate * 0.1) && a.tilt === 10 && a.moved, 'right stick pans right');
// stick up (negative Y) -> tilt increases (muzzle up)
a = stepAim({ pan: 0, tilt: 10 }, [0, -1, 0, 0], 0.1);
check(near(a.tilt, 10 + DEFAULTS.maxRate * 0.1), 'stick up raises tilt');
// fine stick at a quarter rate
a = stepAim({ pan: 0, tilt: 10 }, [0, 0, 1, 0], 0.1);
check(near(a.pan, -DEFAULTS.maxRate * 0.1 * DEFAULTS.fineScale), 'right stick is fine aim');
// limits
a = stepAim({ pan: 89, tilt: 44 }, [-1, -1, 0, 0], 0.1);
check(a.pan === 90 && a.tilt === 45, 'clamped at pan +90 / tilt 45');
a = stepAim({ pan: -89, tilt: 1 }, [1, 1, 0, 0], 0.1);
check(a.pan === -90 && a.tilt === 0, 'clamped at pan -90 / tilt 0');
// a long dt (background tab) is capped
a = stepAim({ pan: 0, tilt: 0 }, [1, 0, 0, 0], 5);
check(near(a.pan, -DEFAULTS.maxRate * DEFAULTS.maxDt), 'dt capped');
// centred sticks: no move, no send
a = stepAim({ pan: 12, tilt: 7 }, [0.05, -0.1, 0, 0], 0.016);
check(!a.moved && a.pan === 12 && a.tilt === 7, 'idle sticks do not move');
// missing axes
a = stepAim({ pan: 0, tilt: 0 }, [], 0.1);
check(!a.moved, 'no axes, no move');

// buttons
const held = pressedList([{ pressed: true }, null, { value: 0.9 }, { pressed: false }]);
check(held[0] && !held[1] && held[2] && !held[3], 'pressedList');
check(JSON.stringify(edges([false, true, false], [true, true, true])) === '[0,2]', 'edges');

// fire needs the deadman (LB) AND the board at speed (state 4)
const h = (...b) => { const x = Array(8).fill(false); b.forEach(i => (x[i] = true)); return x; };
check(JSON.stringify(decide([BTN.A], h(BTN.A, BTN.LB), 4)) === '["fire"]', 'A + LB at speed fires');
check(JSON.stringify(decide([BTN.A], h(BTN.A), 4)) === '["fire_refused"]', 'A without deadman refused');
check(JSON.stringify(decide([BTN.A], h(BTN.A, BTN.LB), 3)) === '["fire_refused"]', 'A while spinning up refused');
check(JSON.stringify(decide([BTN.A], h(BTN.A, BTN.LB), 6)) === '["fire_refused"]', 'A in fault refused');
// stop always wins
check(JSON.stringify(decide([BTN.B, BTN.A], h(BTN.A, BTN.B, BTN.LB), 4)) === '["stop"]', 'B beats A');
check(JSON.stringify(decide([BTN.Y], h(BTN.Y), 0)) === '["center"]', 'Y centers');
check(decide([], h(BTN.LB), 4).length === 0, 'holding the deadman alone does nothing');

console.log(`${failures ? 'FAIL' : 'PASS'}: gamepad (${failures} failures)`);
process.exit(failures ? 1 : 0);

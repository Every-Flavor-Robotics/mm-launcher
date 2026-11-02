// Headless test and screenshots for the v3 assembly_guide.html over the Chrome DevTools Protocol (no puppeteer).
//   node test_guide.mjs [--shots DIR]
// Ported from the v2 guide's test. Exits non-zero if any check fails. Prints console errors and uncaught exceptions.
// With --shots it writes the v2 set of 8 views plus screenshots/steps/<n>_<id>.png: every step caught mid-fly-in in
// "Follow parts" mode, to look over for parts coming from the wrong side, hidden parts and empty steps.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL_ = 'file://' + path.join(HERE, 'assembly_guide.html');
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const port = 9334;
const proc = spawn(CHROME, ['--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', `--remote-debugging-port=${port}`,
  '--user-data-dir=/tmp/mmguide3-chrome-cdp', '--no-first-run', '--hide-scrollbars', '--window-size=1600,1000', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let i = 0; i < 50; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json(); if (targets.length) break; } catch {} await sleep(200); }
const ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise(r => (ws.onopen = r));
let id = 0; const pending = new Map(); const logs = [];
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') logs.push('EXCEPTION ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
  if (m.method === 'Runtime.consoleAPICalled' && ['error', 'warning'].includes(m.params.type)) logs.push(m.params.type + ' ' + m.params.args.map(a => a.value ?? a.description).join(' '));
};
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async expr => { const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result.exceptionDetails) throw new Error(expr + ' -> ' + JSON.stringify(r.result.exceptionDetails.exception?.description)); return r.result.result.value; };
const shot = async name => { if (!SHOTS) return; const s = await send('Page.captureScreenshot', { format: 'png' }); const f = path.join(SHOTS, name); fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, Buffer.from(s.result.data, 'base64')); };
const waitStill = async (ms = 8000) => { const t = Date.now(); while (Date.now() - t < ms) { if (!(await ev('guide.flying()'))) return; await sleep(100); } };
await send('Runtime.enable'); await send('Page.enable');
await send('Page.navigate', { url: URL_ });
for (let i = 0; i < 150; i++) { await sleep(200); if (await ev("document.body && document.body.dataset.ready === '1'")) break; }
await sleep(1800);   // ax-three's intro dolly
const results = []; const check = (name, ok, info = '') => results.push([ok ? 'PASS' : 'FAIL', name, info]);
const cur = () => ev("document.querySelector('.g-step[aria-current] .id')?.textContent");
const idx = sid => ev(`guide.STEPS.findIndex(s => s.id === ${JSON.stringify(sid)})`);
const visible = () => ev("Object.entries(guide.OBJ).filter(([n,o]) => o.node.visible).map(([n]) => n)");
const modeOf = n => ev(`guide.OBJ[${JSON.stringify(n)}].mode`);
const offMM = n => ev(`guide.OBJ[${JSON.stringify(n)}].node.position.distanceTo(guide.OBJ[${JSON.stringify(n)}].basePos)`);
const camPos = () => ev("guide.camera.position.toArray().map(x => +x.toFixed(2))");
const green = n => ev(`guide.OBJ[${JSON.stringify(n)}].meshes[0].material.color.getHexString()`);
const deg = j => ev(`guide.PIV.${j}.rotation.${j === 'PIV_tilt' ? 'x' : 'y'} * 180 / Math.PI`);
// world displacement of an object from its resting place, in the design frame (+X right, +Y front, +Z up), as a unit vector
const worldOff = n => ev(`(() => { const o = guide.OBJ[${JSON.stringify(n)}]; const p = o.node.position.clone();
  const a = o.node.getWorldPosition(new THREE_V()); o.node.position.copy(o.basePos).add(o.shift); o.node.updateMatrixWorld(true);
  const b = o.node.getWorldPosition(new THREE_V()); o.node.position.copy(p); o.node.updateMatrixWorld(true);
  const d = a.sub(b); const L = d.length(); return { mm: L, d: L ? [d.x / L, -d.z / L, d.y / L] : [0, 0, 0] }; })()`);
await ev("window.THREE_V = guide.camera.position.constructor");
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const N = await ev('guide.STEPS.length');

check('loaded', await ev("document.body.dataset.ready === '1'"), await ev("Object.keys(guide.OBJ).length + ' objects'"));
check('25 steps listed', (await ev("document.querySelectorAll('.g-step').length")) === 25 && N === 25, String(N));
check('74 machine objects in the GLB', (await ev('Object.keys(guide.OBJ).length')) === 74);
check('every step maps clean', (await ev("guide.STEPS.filter(s => s.status !== 'clean').map(s => s.id).join(',')")) === '');
check('header: cadcheck 0 fails, 69 warns; 25 printed parts, 11 screws + 3 nuts',
  await ev("(t => t.includes('cadcheck 0 fails, 69 warns') && t.includes('25 printed parts · 11 screws + 3 nuts'))(document.querySelector('#meta').textContent)"),
  await ev("document.querySelector('#meta').textContent"));
check('starts at step 0 with nothing placed', (await cur()) === '0' && (await visible()).length === 0);
const liftFirst = () => ev("(w => !!w && w.classList.contains('critical') && /base only/.test(w.textContent) && /line \\d+/.test(w.textContent))(document.querySelector('#detail .g-warn'))");
check('step 0: "lift by the base only" is the first warning, a caution with its line ref', await liftFirst());
check('stationary camera is the default', !(await ev('guide.state.follow')) && (await ev("document.querySelector('#follow').getAttribute('aria-pressed')")) === 'false');
const cam0 = await camPos();

// navigation
await ev("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true}))");
check('ArrowRight -> step 1', (await cur()) === '1', await ev('location.hash'));
await ev("document.querySelector('#next').click()"); check('Next -> 1a', (await cur()) === '1a');
await ev("document.querySelector('#prev').click()"); check('Prev -> 1', (await cur()) === '1');
await ev("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowLeft', bubbles: true}))"); check('ArrowLeft -> 0', (await cur()) === '0');
await sleep(1500);
check('step 0 shows nothing after 1 flies out', (await visible()).length === 0);

// every step: something new or merged in green, every green part drawn, each moving part flying in along its rule
const dirBad = [], empty = [], hidden = [], still = [];
for (let i = 1; i < N; i++) {
  await ev(`guide.go(${i - 1})`); await waitStill();
  await ev(`guide.go(${i})`); await sleep(120); await ev('guide.pauseFlight()');
  const st = await ev(`(s => ({ id: s.id, focus: s.focus_objects, explode: s.explode, pin: s.pose_in }))(guide.STEPS[${i}])`);
  if (!st.focus.length) empty.push(st.id);
  for (const n of st.focus) {
    if (!(await ev(`guide.OBJ[${JSON.stringify(n)}].node.visible`))) hidden.push(`${st.id}:${n}`);
    const r = st.explode[n]; if (!Array.isArray(r) || !r.some(Boolean)) continue;
    const w = await worldOff(n);
    if (w.mm < 5) { still.push(`${st.id}:${n} ${w.mm.toFixed(1)}`); continue; }
    // expected world direction: the rule, turned by the parent joints at their pose (pose_in tilt counter-rotation included)
    const exp = await ev(`(() => { const o = guide.OBJ[${JSON.stringify(n)}]; const v = guide.STEPS[${i}]._off[${JSON.stringify(n)}].clone();
      v.applyQuaternion(o.node.parent.getWorldQuaternion(o.node.quaternion.clone())).normalize(); return [v.x, -v.z, v.y]; })()`);
    if (dot(w.d, exp) < 0.98) dirBad.push(`${st.id}:${n} got ${w.d.map(x => x.toFixed(2))} want ${exp.map(x => x.toFixed(2))}`);
  }
  await ev('guide.resumeFlight()');
}
await waitStill();
check('no empty step: every step from 1 on shows parts in green', empty.length === 0, empty.join(', '));
check('no hidden parts: every green part is drawn while it flies in', hidden.length === 0, hidden.slice(0, 8).join(', '));
check('every part with a fly-in rule is moving at 120 ms', still.length === 0, still.slice(0, 8).join(', '));
check('every fly-in follows its step rule in the world', dirBad.length === 0, dirBad.slice(0, 6).join(' | '));

// fly-ins against the insertion paths in ASSEMBLY.md / checks.json, in world terms
const flyAt = async (sid, n, ms = 150) => { await ev(`guide.go(${(await idx(sid)) - 1})`); await waitStill(); await ev(`guide.go(${await idx(sid)})`); await sleep(ms); const w = await worldOff(n); await waitStill(); return w; };
const ax = { '+X': [1, 0, 0], '-X': [-1, 0, 0], '+Y': [0, 1, 0], '-Y': [0, -1, 0], '+Z': [0, 0, 1], '-Z': [0, 0, -1] };
for (const [sid, n, from, why] of [
  ['1', 'BUY_dewalt_adapter', '-Z', 'up into the deck fences'],
  ['1b', 'PRT_pan_servo_mount', '-Z', 'pressed up onto the deck posts'],
  ['2b', 'PRT_hub_gear', '-Z', 'pushed up through the deck hole'],
  ['6b', 'PRT_encoder_cap', '-X', 'into the rear counterbore'],
  ['6c/6d', 'PRT_journal_plate', '+X', 'pressed -X onto its pegs'],
  ['6f', 'PRT_flywheel', '+X', 'onto the D-shaft from +X'],
  ['8', 'BUY_servo_tilt', '+Z', 'dropped -Z into the post pocket'],
  ['9', 'PRT_beam', '+Z', 'down onto the posts'],
  ['10b', 'BUY_servo_feeder', '-Z', 'up into the closed lobe pocket'],
  ['11', 'PRT_feeder_crown', '+Z', 'lowered onto the beam'],
  ['11a', 'BUY_bus_junction', '-Z', 'pushed up the hub-gear bore'],
  ['12', 'BUY_buck_12v', '-X', 'slid +X under its hook rails'],
  ['13', 'PRT_base_floor', '-Z', 'pushed up into the shell'],
  ['16', 'BUY_battery', '+X', 'onto the rail from +X']]) {
  const w = await flyAt(sid, n);
  check(`${sid}: ${n} comes from ${from} (${why})`, dot(w.d, ax[from]) > 0.98, w.d.map(x => x.toFixed(2)).join(', '));
}
{ const w = await flyAt('6g', 'PRT_launcher_cover');
  check('6g: wheel-side cover comes from front-below (insert_dirs (0, 0.71, -0.71), the way out)', dot(w.d, [0, 0.7071, -0.7071]) > 0.98, w.d.map(x => x.toFixed(2)).join(', ')); }
{ const w = await flyAt('6e', 'PRT_nip_cover');
  check('6e: nip cover slides on along the dovetail (0, -0.32, 0.95)', dot(w.d, [0, -0.3185, 0.9479]) > 0.98, w.d.map(x => x.toFixed(2)).join(', ')); }

// step 7: the pod comes straight down nose-up 20, then levels
await ev(`guide.go(${await idx('6g')})`); await waitStill();
await ev(`guide.go(${await idx('7')})`); await sleep(250);
const t7 = await deg('PIV_tilt'), w7 = await worldOff('PRT_nacelle');
const s7 = await worldOff('FST_motor_0');
check("7: the pod's own screws come in with it (no screw delay on a merge)", Math.abs(s7.mm - w7.mm) < 1 && dot(s7.d, w7.d) > 0.999, `${s7.mm.toFixed(1)} vs ${w7.mm.toFixed(1)} mm`);
check('7: pod held nose-up 20 while it drops in', Math.abs(t7 - 20) < 1, t7.toFixed(1));
check('7: pod comes straight down in the world (from +Z)', dot(w7.d, [0, 0, 1]) > 0.99, w7.d.map(x => x.toFixed(2)).join(', '));
await waitStill(); await sleep(2000);
check('7: pod levelled to tilt 0 once in', Math.abs(await deg('PIV_tilt')) < 0.5, (await deg('PIV_tilt')).toFixed(2));

// step 15: the jar drops in at +30 and twists to 0
await ev(`guide.go(${await idx('14')})`); await waitStill();
await ev(`guide.go(${await idx('15')})`); await sleep(250);
const j15 = await deg('PIV_jar'), w15 = await worldOff('BUY_jar');
check('15: jar held at +30 while it drops in', Math.abs(j15 - 30) < 1, j15.toFixed(1));
check('15: jar comes from +Z', dot(w15.d, [0, 0, 1]) > 0.99, w15.d.map(x => x.toFixed(2)).join(', '));
check('15: "lift by the base only" caution shown', await liftFirst());
await waitStill(); await sleep(2000);
check('15: jar twisted to 0 once in', Math.abs(await deg('PIV_jar')) < 0.5, (await deg('PIV_jar')).toFixed(2));
await ev(`guide.go(${await idx('14')})`); await waitStill();
check('14: "lift by the base only" caution shown', await ev("[...document.querySelectorAll('#detail .g-warn.critical')].some(w => /never the machine by the jar/.test(w.textContent))"));
check('14: Seats and Release lines shown', await ev("!!document.querySelector('#detail .g-seats') && !!document.querySelector('#detail .g-release')"));
await ev(`guide.go(${await idx('9')})`);
check('9: Seats and Release shown, with the joint kind', await ev("!!document.querySelector('#detail .g-seats') && /Release/.test(document.querySelector('#detail .g-release').textContent) && /Joint: snap/.test(document.querySelector('#detail').textContent)"));
check('every warning cites its line', await ev("guide.STEPS.every(s => s.warnings.every(w => /line \\d+/.test(w.source)))"));
{ // every step's ASSEMBLY.md Seats and Release lines are drawn in its detail panel
  const miss = [];
  for (let i = 0; i < N; i++) {
    await ev(`guide.go(${i})`);
    const r = await ev(`(s => ({ id: s.id, seats: !!s.seats, rel: !!s.release, ds: !!document.querySelector('#detail .g-seats'), dr: !!document.querySelector('#detail .g-release') }))(guide.STEPS[${i}])`);
    if (r.seats !== r.ds || r.rel !== r.dr) miss.push(r.id);
  }
  const both = await ev("guide.STEPS.filter(s => s.seats && s.release).map(s => s.id).join(',')");
  check('every step shows the Seats and Release lines ASSEMBLY.md gives it', miss.length === 0, (miss.join(',') || 'both on ' + both)); }
// no bench isolation: step 6e (pod bench) keeps the base, posts and turntable in view, in place
await ev(`guide.go(${await idx('6c/6d')})`); await waitStill();
await ev("document.querySelector('#next').click()");            // 6c/6d -> 6e, adjacent: fly-in
await sleep(150);
const mid = await offMM('PRT_nip_cover');
check('6e: nip cover starts its fly-in away from its place', mid > 15, mid.toFixed(1) + ' mm');
check('6e: the fly-in is still running at 150 ms', await ev('guide.flying()'));
await waitStill();
const end = await offMM('PRT_nip_cover');
check('6e: nip cover lands in place', end < 0.01, end.toFixed(3) + ' mm');
const vis = await visible();
check('6e: bench step shown in place, nothing isolated', ['PRT_base_shell', 'PRT_turntable', 'PRT_nacelle', 'PRT_nip_cover'].every(n => vis.includes(n)), vis.length + ' visible');
check('6e: later parts hidden (flywheel, beam, jar)', !vis.includes('PRT_flywheel') && !vis.includes('PRT_beam') && !vis.includes('BUY_jar'));
check('6e: step parts green and opaque', (await modeOf('PRT_nip_cover')) === 'focus' && (await green('PRT_nip_cover')) === '0f9a66');
check('6e: earlier parts translucent', (await modeOf('PRT_base_shell')) === 'context' && (await ev("guide.OBJ.PRT_base_shell.meshes[0].material.opacity")) < 0.3);
check('stationary: camera did not move on step changes', JSON.stringify(await camPos()) === JSON.stringify(cam0));

// screws fly along their axis, after the parts
await ev(`guide.go(${await idx('2b')})`); await waitStill(); await ev(`guide.go(${await idx('6a')})`);
await sleep(80);
const scr = await ev("(() => { const o = guide.OBJ.FST_motor_0; const d = o.node.position.clone().sub(o.basePos).normalize(); return [d.x, d.y, d.z].map(x => +x.toFixed(2)); })()");
check('6a: motor screw flies along its axis (+X, the reverse of into -X)', scr[0] > 0.99, JSON.stringify(scr));
await waitStill();

// back flies out, then hides
await ev(`guide.go(${await idx('6g')})`); await waitStill();
await ev("document.querySelector('#prev').click()");             // 6g -> 6f
let seenOut = 0;
for (let k = 0; k < 20 && !seenOut; k++) { await sleep(50); if (await ev('guide.OBJ.PRT_launcher_cover.node.visible')) { const d = await offMM('PRT_launcher_cover'); if (d > 2) seenOut = d; } }
check('back 6g -> 6f: wheel-side cover drawn while it flies out', seenOut > 2, seenOut.toFixed(1) + ' mm');
await waitStill(); await sleep(150);
check('back: wheel-side cover hidden once out', !(await ev('guide.OBJ.PRT_launcher_cover.node.visible')));

// ghost the rest
await ev(`guide.go(${await idx('7')})`); await waitStill();
await ev("document.querySelector('#ghost').click()");
check('ghost the rest: later parts faint', (await modeOf('BUY_jar')) === 'ghost' && (await ev("guide.OBJ.BUY_jar.node.visible")));
await ev("document.querySelector('#ghost').click()");
check('ghost off: later parts hidden again', !(await ev("guide.OBJ.BUY_jar.node.visible")));

// hold apart does not fight the fly-in
await ev(`guide.go(${await idx('9')})`);
await ev("{ const e = document.querySelector('#explode'); e.value = 50; e.dispatchEvent(new Event('input')) }");
await waitStill(); await sleep(200);
const held = await offMM('PRT_beam'), dist9 = await ev(`guide.STEPS[${await idx('9')}]._dist`);
check('hold apart 50: beam rests at half its fly-in offset', Math.abs(held - dist9 * 0.5) < 0.5, `${held.toFixed(1)} of ${dist9.toFixed(1)} mm`);
check('hold apart leaves earlier parts in place', (await offMM('PRT_turntable')) < 1e-6);
await ev("{ const e = document.querySelector('#explode'); e.value = 0; e.dispatchEvent(new Event('input')) }"); await sleep(400);
check('hold apart 0: beam back in place', (await offMM('PRT_beam')) < 0.01);

// follow mode
await ev(`guide.go(${await idx('6e')})`); await waitStill();
await ev("document.querySelector('#follow').click()"); await sleep(1500);
const camF = await camPos();
check('follow on: camera eases in to the step', JSON.stringify(camF) !== JSON.stringify(cam0) && (await ev('guide.camera.position.distanceTo(guide.controls.target)')) < (await ev('guide.MAIN.pos.distanceTo(guide.MAIN.tgt)')), camF.join(','));
await ev(`guide.go(${await idx('10b')})`); await sleep(1500);
check('follow: camera follows to the next step', JSON.stringify(await camPos()) !== JSON.stringify(camF));
await ev("document.querySelector('#follow').click()"); await sleep(1500);
check('follow off: camera eases back to the main view', (await ev('guide.camera.position.distanceTo(guide.MAIN.pos)')) < 1);

// selection
await ev(`guide.go(${await idx('16')})`); await waitStill();
await ev("guide.select(['PRT_journal_plate'])"); await sleep(100);
check('select a part: it turns green', (await green('PRT_journal_plate')) === '0f9a66' && (await modeOf('PRT_journal_plate')) === 'focus');
check('select: the panel shows it with a go-to-step button', await ev("!!document.querySelector('.g-sel #selGo')"));
await ev("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))");
check('Escape clears the selection', !(await ev('guide.state.select')) && (await green('PRT_journal_plate')) !== '0f9a66');
await ev(`guide.go(${await idx('6e')})`); await waitStill();
await ev("document.querySelector('.g-part').click()"); await sleep(100);
check('highlight list row selects its part', (await ev('JSON.stringify(guide.state.select)')) === '["PRT_nip_wheel"]' && (await ev("document.querySelector('.g-part').classList.contains('on')")));
await ev('guide.select(null)');

// motion
await ev(`guide.go(${await idx('16')})`); await waitStill();
await ev("{ const e = document.querySelector('#pan'); e.value = 45; e.dispatchEvent(new Event('input')) }");
await ev("{ const e = document.querySelector('#tilt'); e.value = 30; e.dispatchEvent(new Event('input')) }");
await sleep(2500);
const rot = await ev("[guide.PIV.PIV_pan.rotation.y, guide.PIV.PIV_pan_pinion.rotation.y, guide.PIV.PIV_tilt.rotation.x].map(r => r * 180 / Math.PI)");
check('pan 45 turns PIV_pan', Math.abs(rot[0] - 45) < 1, rot[0].toFixed(2));
check('pan pinion counter-turns (ratio -1)', Math.abs(rot[1] + 45) < 1, rot[1].toFixed(2));
check('tilt 30 turns PIV_tilt', Math.abs(rot[2] - 30) < 1, rot[2].toFixed(2));
const fw0 = await ev("guide.PIV.PIV_flywheel.rotation.x");
await ev("document.querySelector('#spin').click()"); await sleep(700);
check('spin turns the flywheel', Math.abs((await ev("guide.PIV.PIV_flywheel.rotation.x")) - fw0) > 0.5);
await ev("document.querySelector('#spin').click()");
await ev("document.querySelector('#feed').click()");
let fd = [0, 0];
for (let k = 0; k < 30; k++) { await sleep(100); const r = await ev("[guide.PIV.PIV_feeder.rotation.y, guide.PIV.PIV_feeder_pinion.rotation.y].map(r => r * 180 / Math.PI)"); if (Math.abs(r[0]) > Math.abs(fd[0])) fd = r; }
check('feeder index swings the disc toward 60', Math.abs(fd[0]) > 45, fd.map(x => x.toFixed(1)).join(' / '));
check('feeder pinion follows at -1.467', Math.abs(fd[1] / fd[0] + 1.4667) < 0.02);
await ev("document.querySelector('#feed').click()");
await ev("document.querySelector('#home').click()"); await sleep(1500);

// lightbox
await ev(`guide.go(${await idx('8')})`);
await ev("document.querySelector('.g-fig').click()");
check('render thumbnail opens a lightbox', await ev("!!document.querySelector('.ax-lightbox img')"));
await ev("document.querySelector('.ax-lightbox').click()");
await ev(`guide.go(${await idx('9')})`);
check('9: attempt-1 design section shown with its hotfix note', await ev("[...document.querySelectorAll('.g-fig figcaption')].some(f => /attempt-1\\/sec_beam_hook/.test(f.textContent) && /hotfix/.test(f.textContent))"));

// overview + isolate
await ev("document.querySelector('[data-tab=overview]').click()"); await sleep(300);
check('overview lists parts', (await ev("document.querySelectorAll('#side [data-iso]').length")) > 40);
check('overview shows every machine object, opaque', (await visible()).length === 74 && (await modeOf('PRT_base_shell')) === 'normal');
check('overview tiles: 25 parts, 8 plates, 14 metal fasteners', await ev("(t => /Machine parts\\s*25/i.test(t) && /Plates\\s*8/i.test(t) && /Metal fasteners\\s*14/i.test(t) && /11 screws \\+ 3 nuts/.test(t))(document.querySelector('.g-tiles').innerText.replace(/\\n/g, ' '))"),
  await ev("document.querySelector('.g-tiles').innerText.replace(/\\n/g, ' ')"));
await ev("[...document.querySelectorAll('#side [data-iso]')].find(b => b.dataset.key === 'flywheel').click()"); await sleep(200);
check('isolate flywheel shows just it, in green', JSON.stringify(await visible()) === '["PRT_flywheel"]' && (await green('PRT_flywheel')) === '0f9a66');
await ev("document.querySelector('tr[data-plate=\"2-pod-feeder-terracotta\"]').click()"); await sleep(200);
check('isolate plate 2 shows its 5 parts', (await visible()).length === 5);
await ev("document.querySelector('tr[data-plate=\"0a-fit-coupons-grey\"]').click()"); await sleep(200);
check('isolate plate 0a shows only the real tilt horn adapter (coupons are not in the model)', JSON.stringify(await visible()) === '["PRT_tilt_horn_adapter"]', JSON.stringify(await visible()));
await ev("document.querySelector('#showall').click()");
await ev("document.querySelector('[data-tab=steps]').click()");
check('back to steps keeps the step', (await cur()) === '9');

// every step, both directions
for (let i = 0; i < N; i++) await ev(`guide.go(${i})`);
for (let i = N - 1; i >= 0; i--) await ev(`guide.go(${i})`);
await sleep(1500);
check('walk all 25 steps forward and back: no exceptions', !logs.some(l => l.startsWith('EXCEPTION')));

// screenshots
if (SHOTS) {
  const reset = async () => { await ev("guide.select(null)"); if (await ev('guide.state.follow')) await ev("document.querySelector('#follow').click()");
    await ev("document.querySelector('#home').click()"); await sleep(1600); };
  const at = async (sid, extra = '') => { await ev(`guide.go(${await idx(sid)})`); await waitStill(); await sleep(400); if (extra) await ev(extra); };
  await reset();
  await at('0'); await shot('0_start_lift_warning.png');
  await at('1a'); await shot('1_stationary_early_1a.png');
  await at('6e'); await shot('2_stationary_mid_6e.png');
  await at('11'); await shot('3_stationary_late_11.png');
  await ev("document.querySelector('#follow').click()"); await at('6e'); await sleep(1200); await shot('4_follow_mid_6e.png');
  await reset();
  await at('16'); await ev("guide.select(['BUY_servo_tilt'])"); await sleep(500); await shot('5_selected_part_green_step16.png');
  await reset();
  await ev("document.querySelector('[data-tab=overview]').click()"); await sleep(1600); await shot('6_overview.png');
  await ev("document.querySelector('[data-tab=steps]').click()"); await sleep(1600);
  await at('8'); await ev("document.querySelector('#next').click()");          // 8 -> 9: the beam flies in
  for (let k = 0; k < 40; k++) { await sleep(30); const f = await ev('guide.OBJ.PRT_beam.fly'); if (f > 0.3 && f < 0.7) break; }
  await ev('guide.pauseFlight()'); await sleep(600);                 // hold the flight while frames render
  const f = await ev('guide.OBJ.PRT_beam.fly');
  await shot('7_mid_fly_in_step9_beam.png');
  await ev('guide.resumeFlight()'); await waitStill();
  console.log('mid-fly-in frame grabbed at fly =', (+f).toFixed(2), '(1 = at the offset, 0 = in place)');
  await at('16'); await ev("{ const p = document.querySelector('#pan'); p.value = 45; p.dispatchEvent(new Event('input')); const t = document.querySelector('#tilt'); t.value = 30; t.dispatchEvent(new Event('input')) }");
  await sleep(2500); await shot('8_final_step16_pan45_tilt30.png');
  await at('14'); await shot('9_jar_bench_step14_warnings.png');
  // every step mid-fly-in, camera following: hold the parts at their offset until the camera has framed them
  await reset(); await ev("document.querySelector('#follow').click()");
  for (let i = 1; i < N; i++) {
    await ev(`guide.go(${i - 1})`); await waitStill();
    await ev(`guide.go(${i})`); await ev('guide.pauseFlight()'); await sleep(1300);
    await ev('guide.resumeFlight()');
    const lead = await ev(`guide.STEPS[${i}].focus_objects.find(n => !n.startsWith('FST_') && !n.startsWith('CAB_')) || guide.STEPS[${i}].focus_objects[0]`);
    for (let k = 0; k < 60; k++) { await sleep(15); const fl = await ev(`guide.OBJ[${JSON.stringify(lead)}].fly`); if (fl < 0.55) break; }
    await ev('guide.pauseFlight()'); await sleep(500);
    const sid = await ev(`guide.STEPS[${i}].id`);
    await shot(`steps/${String(i).padStart(2, '0')}_${sid.replace('/', '-')}_midflight.png`);
    await ev('guide.resumeFlight()');
  }
  await waitStill();
}

for (const r of results) console.log(r.join('  '));
console.log(`${results.filter(r => r[0] === 'PASS').length}/${results.length} passed`);
console.log('console errors/warnings/exceptions:', logs.length ? logs : 'none');
ws.close(); proc.kill();
process.exit(results.some(r => r[0] === 'FAIL') ? 1 : 0);

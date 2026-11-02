// Headless test and screenshots for assembly_guide.html over the Chrome DevTools Protocol (no puppeteer).
//   node test_guide.mjs [--shots DIR]
// Exits non-zero if any check fails. Prints console errors and uncaught exceptions.
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const URL_ = 'file://' + path.join(HERE, 'assembly_guide.html');
const SHOTS = process.argv.includes('--shots') ? process.argv[process.argv.indexOf('--shots') + 1] : null;
const port = 9333;
const proc = spawn(CHROME, ['--headless=new', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', `--remote-debugging-port=${port}`,
  '--user-data-dir=/tmp/mmguide-chrome-cdp', '--no-first-run', '--hide-scrollbars', '--window-size=1600,1000', 'about:blank'], { stdio: 'ignore' });
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
const shot = async name => { if (!SHOTS) return; const s = await send('Page.captureScreenshot', { format: 'png' }); fs.mkdirSync(SHOTS, { recursive: true }); fs.writeFileSync(path.join(SHOTS, name), Buffer.from(s.result.data, 'base64')); };
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

check('loaded', await ev("document.body.dataset.ready === '1'"), await ev("Object.keys(guide.OBJ).length + ' objects'"));
check('33 steps listed', (await ev("document.querySelectorAll('.g-step').length")) === 33);
check('starts at step 0 with nothing placed', (await cur()) === '0' && (await visible()).length === 0);
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

// no bench isolation: step 6e (pod bench) keeps the base, posts and turntable in view, in place
await ev(`guide.go(${await idx('6d')})`); await waitStill();
await ev("document.querySelector('#next').click()");            // 6d -> 6e, adjacent: fly-in
await sleep(150);
const mid = await offMM('PRT_nip_cover');
check('6e: nip cover starts its fly-in away from its place', mid > 15, mid.toFixed(1) + ' mm');
check('6e: the fly-in is still running at 150 ms', await ev('guide.flying()'));
await waitStill();
const end = await offMM('PRT_nip_cover');
check('6e: nip cover lands in place (0.8-1.4 s)', end < 0.01, end.toFixed(3) + ' mm');
const vis = await visible();
check('6e: bench step shown in place, nothing isolated', ['PRT_base_shell', 'PRT_turntable', 'PRT_post_L', 'PRT_nacelle', 'PRT_nip_cover'].every(n => vis.includes(n)), vis.length + ' visible');
check('6e: later parts hidden (flywheel, beam, jar)', !vis.includes('PRT_flywheel') && !vis.includes('PRT_beam') && !vis.includes('BUY_jar'));
check('6e: step parts green and opaque', (await modeOf('PRT_nip_cover')) === 'focus' && (await green('PRT_nip_cover')) === '0f9a66');
check('6e: earlier parts translucent', (await modeOf('PRT_base_shell')) === 'context' && (await ev("guide.OBJ.PRT_base_shell.meshes[0].material.opacity")) < 0.3);
check('stationary: camera did not move on step changes', JSON.stringify(await camPos()) === JSON.stringify(cam0));

// screws fly along their axis, after the parts
await ev(`guide.go(${await idx('6f')})`); await ev(`guide.go(${await idx('6g')})`);
await sleep(80);
const scr = await ev("(() => { const o = guide.OBJ.FST_cover_0; const d = o.node.position.clone().sub(o.basePos).normalize(); return [d.x, d.y, d.z].map(x => +x.toFixed(2)); })()");
check('6g: cover screw flies along its axis (+X, the reverse of into -X)', scr[0] > 0.99, JSON.stringify(scr));
await waitStill();

// back flies out, then hides
await ev("document.querySelector('#prev').click()");             // 6g -> 6f
let seenOut = 0;
for (let k = 0; k < 20 && !seenOut; k++) { await sleep(50); if (await ev('guide.OBJ.PRT_launcher_cover.node.visible')) { const d = await offMM('PRT_launcher_cover'); if (d > 2) seenOut = d; } }
check('back 6g -> 6f: wheel-side cover drawn while it flies out', seenOut > 2, seenOut.toFixed(1) + ' mm');
await waitStill(); await sleep(150);
check('back: wheel-side cover hidden once out', !(await ev('guide.OBJ.PRT_launcher_cover.node.visible')));

// merge step: the pod flies down into the posts
await ev(`guide.go(${await idx('6g')})`); await waitStill();
await ev(`guide.go(${await idx('7')})`); await sleep(150);
check('7: the pod drops into the U-slots (comes from above)', (await ev("guide.OBJ.PRT_nacelle.node.position.y - guide.OBJ.PRT_nacelle.basePos.y")) > 10);
await waitStill();

// ghost the rest
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
check('hold apart leaves earlier parts in place', (await offMM('PRT_post_L')) < 1e-6);
await ev("{ const e = document.querySelector('#explode'); e.value = 0; e.dispatchEvent(new Event('input')) }"); await sleep(400);
check('hold apart 0: beam back in place', (await offMM('PRT_beam')) < 0.01);

// follow mode
await ev(`guide.go(${await idx('6e')})`); await waitStill();
await ev("document.querySelector('#follow').click()"); await sleep(1500);
const camF = await camPos();
check('follow on: camera eases in to the step', JSON.stringify(camF) !== JSON.stringify(cam0) && (await ev('guide.camera.position.distanceTo(guide.controls.target)')) < (await ev('guide.MAIN.pos.distanceTo(guide.MAIN.tgt)')), camF.join(','));
await ev(`guide.go(${await idx('10a')})`); await sleep(1500);
check('follow: camera follows to the next step', JSON.stringify(await camPos()) !== JSON.stringify(camF));
await ev("document.querySelector('#follow').click()"); await sleep(1500);
check('follow off: camera eases back to the main view', (await ev('guide.camera.position.distanceTo(guide.MAIN.pos)')) < 1);

// selection
await ev(`guide.go(${await idx('15')})`); await waitStill();
await ev("guide.select(['PRT_post_R_cover'])"); await sleep(100);
check('select a part: it turns green', (await green('PRT_post_R_cover')) === '0f9a66' && (await modeOf('PRT_post_R_cover')) === 'focus');
check('select: the panel shows it with a go-to-step button', await ev("!!document.querySelector('.g-sel #selGo')"));
await ev("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}))");
check('Escape clears the selection', !(await ev('guide.state.select')) && (await green('PRT_post_R_cover')) !== '0f9a66');
await ev(`guide.go(${await idx('6e')})`); await waitStill();
await ev("document.querySelector('.g-part').click()"); await sleep(100);
check('highlight list row selects its part', (await ev('JSON.stringify(guide.state.select)')) === '["PRT_nip_wheel"]' && (await ev("document.querySelector('.g-part').classList.contains('on')")));
await ev('guide.select(null)');

// motion
await ev(`guide.go(${await idx('15')})`); await waitStill();
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

// 11a: prop, removed cover, servo slide
await ev(`guide.go(${await idx('11')})`); await waitStill();
await ev("document.querySelector('#next').click()"); await sleep(2600);
check('11a.0 sets tilt 45', Math.abs((await ev("guide.PIV.PIV_tilt.rotation.x * 180 / Math.PI")) - 45) < 1);
check('11a.0: prop flies in and is green', await ev("guide.OBJ.TOOL_tilt45_prop.node.visible") && (await offMM('TOOL_tilt45_prop')) < 0.01 && (await modeOf('TOOL_tilt45_prop')) === 'focus');
check('11a.0: post cover taken off, parked faint (not vanished)', (await modeOf('PRT_post_R_cover')) === 'ghost' && (await offMM('PRT_post_R_cover')) > 20);
check('11a.0: tilt servo slid +X 10', Math.abs((await ev("guide.OBJ.BUY_servo_tilt.node.position.x - guide.OBJ.BUY_servo_tilt.basePos.x")) - 10) < 0.05);
await ev(`guide.go(${await idx('11a.1 to 11a.9')})`); await waitStill();
await ev("document.querySelector('#next').click()"); await sleep(2600);
check('11a.10: cover flies back in, prop flies out, servo home', await ev("guide.OBJ.PRT_post_R_cover.node.visible && !guide.OBJ.TOOL_tilt45_prop.node.visible && guide.OBJ.BUY_servo_tilt.node.position.distanceTo(guide.OBJ.BUY_servo_tilt.basePos) < 0.05") && (await offMM('PRT_post_R_cover')) < 0.01);

// lightbox
await ev(`guide.go(${await idx('8')})`);
await ev("document.querySelector('.g-fig').click()");
check('render thumbnail opens a lightbox', await ev("!!document.querySelector('.ax-lightbox img')"));
await ev("document.querySelector('.ax-lightbox').click()");

// overview + isolate
await ev("document.querySelector('[data-tab=overview]').click()"); await sleep(300);
check('overview lists parts', (await ev("document.querySelectorAll('#side [data-iso]').length")) > 50);
check('overview shows every machine object, opaque', (await visible()).length === 178 && (await modeOf('PRT_base_shell')) === 'normal');
await ev("[...document.querySelectorAll('#side [data-iso]')].find(b => b.dataset.key === 'flywheel').click()"); await sleep(200);
check('isolate flywheel shows just it, in green', JSON.stringify(await visible()) === '["PRT_flywheel"]' && (await green('PRT_flywheel')) === '0f9a66');
await ev("document.querySelector('tr[data-plate=\"3-feeder-jar-terracotta\"]').click()"); await sleep(200);
check('isolate plate 3 shows its 5 parts', (await visible()).length === 5);
await ev("document.querySelector('#showall').click()");
await ev("document.querySelector('[data-tab=steps]').click()");
check('back to steps keeps the step', (await cur()) === '8');

// every step, both directions
const n = await ev("guide.STEPS.length");
for (let i = 0; i < n; i++) await ev(`guide.go(${i})`);
for (let i = n - 1; i >= 0; i--) await ev(`guide.go(${i})`);
await sleep(1500);
check('walk all 33 steps forward and back: no exceptions', !logs.some(l => l.startsWith('EXCEPTION')));

// screenshots
if (SHOTS) {
  const reset = async () => { await ev("guide.select(null)"); if (await ev('guide.state.follow')) await ev("document.querySelector('#follow').click()");
    await ev("document.querySelector('#home').click()"); await sleep(1600); };
  const at = async (sid, extra = '') => { await ev(`guide.go(${await idx(sid)})`); await waitStill(); await sleep(400); if (extra) await ev(extra); };
  await reset();
  await at('2a'); await shot('1_stationary_early_2a.png');
  await at('6e'); await shot('2_stationary_mid_6e.png');
  await at('11'); await shot('3_stationary_late_11.png');
  await ev("document.querySelector('#follow').click()"); await at('6e'); await sleep(1200); await shot('4_follow_mid_6e.png');
  await reset();
  await at('15'); await ev("guide.select(['BUY_servo_tilt'])"); await sleep(500); await shot('5_selected_part_green_step15.png');
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
  await at('15'); await ev("{ const p = document.querySelector('#pan'); p.value = 45; p.dispatchEvent(new Event('input')); const t = document.querySelector('#tilt'); t.value = 30; t.dispatchEvent(new Event('input')) }");
  await sleep(2500); await shot('8_final_step15_pan45_tilt30.png');
}

for (const r of results) console.log(r.join('  '));
console.log(`${results.filter(r => r[0] === 'PASS').length}/${results.length} passed`);
console.log('console errors/warnings/exceptions:', logs.length ? logs : 'none');
ws.close(); proc.kill();
process.exit(results.some(r => r[0] === 'FAIL') ? 1 : 0);

// Assembly guide app. Runs inside the page's module script after axScene (ax-three.js) and the three imports.
// Frames: the design is +X right, +Y front, +Z up (mm); the GLB is Y-up, so design (x, y, z) is three (x, z, -y).
//
// Display model (v2, after user feedback): nothing is isolated or hidden by bench views. Every part placed so far stays
// at its final place in the machine; bench sub-assemblies are built in place. On each step the step's parts fly in from
// their explode offset (screws along their axis); going back flies them out. The step's parts are green and opaque,
// every other placed part is translucent, later parts are hidden (or faint with "Ghost the rest"). Two camera modes:
// stationary (the main view, untouched on step change) and "Follow parts" (eases to frame each step's parts).

const D = JSON.parse(document.getElementById('guide-data').textContent);
const STEPS = D.steps, PARTS = D.parts;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const b2t = a => new THREE.Vector3(a[0], a[2], -a[1]);
const rad = THREE.MathUtils.degToRad;

// URL hash: #step=6e&hold=60&pan=45&tilt=30&ghost=1&follow=1&select=PRT_flywheel&tab=overview&isolate=PRT_flywheel&snap=1
const H = Object.fromEntries(location.hash.slice(1).split('&').filter(Boolean)
  .map(kv => { const i = kv.indexOf('='); return [decodeURIComponent(kv.slice(0, i)), decodeURIComponent(kv.slice(i + 1))]; }));
const SNAP = H.snap === '1' || reduced;          // no animation: screenshots and reduced motion

const state = { tab: 'steps', step: 0, ghost: false, hold: 0, follow: false, select: null, isolate: null, isolateKey: null };
const target = { pan: 0, tilt: 0 }, actual = { pan: 0, tilt: 0, feed: 0, fw: 0 };
let spin = false, feeding = false, feedClock = 0, feedSign = 1, feedTarget = 0;

// Focus green: the style guide's series green s3 (#0f9a66 dark). Status "good" green is reserved for state.
const GREEN = new THREE.Color(tok('s3'));
const CONTEXT_OPACITY = 0.24, CONTEXT_OPACITY_FOLLOW = 0.13, GHOST_OPACITY = 0.07;   // follow: close up, so fainter context
const FLY_S = 1.0, FLY_OUT_S = 0.7, SCREW_DELAY_S = 0.4;

const objFirst = {}, mergeAt = {};
STEPS.forEach((s, i) => { s.new_objects.forEach(n => (objFirst[n] = i)); if (s.merge) mergeAt[s.merge] = i; });

// What each object is at step i: 'in' (placed, at its final place), 'removed' (taken off at this step: parked at its
// offset, faint), or absent. Bench parts are placed from their own step on, in place.
function placedSet(i) {
  const st = STEPS[i], out = new Set();
  for (const [n, k] of Object.entries(objFirst)) if (k <= i) out.add(n);
  st.extra_objects.forEach(n => out.add(n));
  st.hide_objects.forEach(n => out.delete(n));
  return out;
}
const removedSet = i => new Set(STEPS[i].hide_objects);
const focusSet = i => { const p = placedSet(i); return new Set(STEPS[i].focus_objects.filter(n => p.has(n))); };

// ── header meta ──
{
  const m = D.meta;
  $('#meta').innerHTML = [`model ${esc(m.model)}`, `cadcheck ${esc(m.cadcheck)}`, `${STEPS.length} steps`,
    `${m.objects} objects`, `GLB ${m.glb_mb} MB`, `<span class="ax-status" id="loadState">Loading model</span>`]
    .map(s => `<span>${s}</span>`).join('');
}

// ── scene ──
const view = $('#view');
const v = axScene(view, { units: 'mm', floor: 260, camera: [520, 430, 560], target: [0, 190, 0], autoRotate: false, triad: false });
v.camera.layers.enable(2);            // layer 2 = ghosts: drawn, never picked (ax-three's raycaster sees layer 0 only)
v.camera.near = 2; v.camera.updateProjectionMatrix();

// Design-frame axis gizmo in the viewport corner. ax-three's floor triad labels three.js axes (Y up there) and sits in
// the middle of close-up views, so the axes are drawn in screen space instead, still labelled with units.
const gizmo = (() => {
  const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
  svg.setAttribute('class', 'g-gizmo'); svg.setAttribute('viewBox', '0 0 130 120'); svg.setAttribute('aria-label', 'Axes');
  const axes = [['X, mm', [1, 0, 0], 's2'], ['Y front, mm', [0, 1, 0], 's3'], ['Z, mm', [0, 0, 1], 's1']].map(([t, d, c]) => {
    const g = document.createElementNS(NS, 'g'), l = document.createElementNS(NS, 'line'), x = document.createElementNS(NS, 'text');
    l.setAttribute('stroke', tok(c)); l.setAttribute('stroke-width', 2.5); l.setAttribute('x1', 65); l.setAttribute('y1', 62);
    x.textContent = t; x.setAttribute('class', 'g-gz-t');
    g.append(l, x); svg.appendChild(g);
    return { g, l, x, d: b2t(d) };
  });
  view.appendChild(svg);
  const q = new THREE.Quaternion(), p = new THREE.Vector3();
  return () => {
    q.copy(v.camera.quaternion).invert();
    axes.map(a => { p.copy(a.d).applyQuaternion(q); return { a, x: p.x, y: p.y, z: p.z }; })
      .sort((m, n) => m.z - n.z).forEach(({ a, x, y }) => {
        a.l.setAttribute('x2', 65 + x * 34); a.l.setAttribute('y2', 62 - y * 34);
        a.x.setAttribute('x', 65 + x * 44); a.x.setAttribute('y', 62 - y * 44 + 3);
        a.x.setAttribute('text-anchor', x < -0.2 ? 'end' : x > 0.2 ? 'start' : 'middle');
        svg.appendChild(a.g);
      });
  };
})();
// fill light from below: several steps are looked at from under the deck
{ const fill = new THREE.DirectionalLight(0xffffff, 0.7); fill.position.set(-200, -300, 150); v.scene.add(fill); }

const OBJ = {}, PIV = {};
const ink = new THREE.Color(tok('ink'));
let ready = false;

function tipHTML(n) {
  const p = PARTS[n] || {};
  const st = p.step ? `step ${esc(p.step)}` : (n.startsWith('TOOL_') ? 'tool for step 11a' : '');
  let d = '';
  if (p.kind === 'PRT') d = `printed · ${esc(p.stl)} · plate ${esc(p.plate)} · colour ${p.colour}`;
  else if (p.kind === 'BUY') d = `purchased${p.mass_g ? ` · ${p.mass_g} g` : ''}`;
  else if (p.kind === 'FST') d = esc(p.spec);
  else if (p.kind === 'CAB') d = `cable${p.lead ? ` · lead ${p.lead} mm` : ''}${p.path ? ` · routed ${p.path} mm` : ''}`;
  else if (p.kind === 'TOOL') d = `printed tool · ${esc(p.stl)}`;
  return `<b>${esc(n)}</b><br>${d}${st ? `<br><span style="color:var(--ax-muted)">${st}</span>` : ''}<br><span style="color:var(--ax-muted)">click to select</span>`;
}

function onPick(n) {
  if (state.tab === 'overview') { isolate([n], n); return; }
  select(state.select && state.select.length === 1 && state.select[0] === n ? null : [n]);
}

async function loadModel() {
  const b64 = document.getElementById('glb').textContent.trim();
  const buf = await (await fetch('data:application/octet-stream;base64,' + b64)).arrayBuffer();
  const url = URL.createObjectURL(new Blob([buf], { type: 'model/gltf-binary' }));
  const holder = await v.load(url);
  URL.revokeObjectURL(url);
  holder.traverse(o => {
    if (o.name.startsWith('PIV_')) { PIV[o.name] = o; return; }
    if (!PARTS[o.name] || OBJ[o.name]) return;
    const meshes = [];
    o.traverse(m => m.isMesh && meshes.push(m));
    meshes.forEach(m => {
      m.material = m.material.clone();
      m.userData.base = { color: m.material.color.clone(), opacity: m.material.opacity, transparent: m.material.transparent };
      m.userData.edges = m.children.find(c => c.isLineSegments);
      v.pickable(m, () => tipHTML(o.name), () => onPick(o.name));
    });
    OBJ[o.name] = { name: o.name, node: o, meshes, basePos: o.position.clone(), mode: null,
                    fly: 0, anim: null, off: new THREE.Vector3(), shift: new THREE.Vector3(), shiftTo: new THREE.Vector3() };
  });
  holder.updateMatrixWorld(true);
  for (const o of Object.values(OBJ)) o.boxHome = new THREE.Box3().setFromObject(o.node);
  // fly-in vectors per step, in each object's parent frame (home pose: parent frames are unrotated, so the design
  // directions apply directly, and the offsets then turn with pan and tilt)
  STEPS.forEach(st => {
    const box = new THREE.Box3();
    st.focus_objects.forEach(n => OBJ[n] && box.union(OBJ[n].boxHome));
    const size = box.isEmpty() ? 80 : box.getSize(new THREE.Vector3()).length();
    st._dist = THREE.MathUtils.clamp(size * 0.55, 40, 150);
    st._off = {};
    for (const n of st.focus_objects) {
      const r = st.explode[n];
      st._off[n] = Array.isArray(r) ? b2t(r).multiplyScalar(st._dist) : new THREE.Vector3(0, st._dist, 0);
    }
  });
  const missing = STEPS.flatMap(s => s.focus_objects.concat(s.new_objects)).filter(n => !OBJ[n]);
  if (missing.length) console.warn('GUIDE: steps name objects not in the GLB', [...new Set(missing)]);
  ready = true;
}

// the offset an object flies along: from the step that places it (or the step being shown, for a merge)
function offFor(n, i) {
  if (STEPS[i]._off[n]) return STEPS[i]._off[n];
  const k = objFirst[n] ?? STEPS.findIndex(s => s._off[n]);
  return (k >= 0 && STEPS[k]._off[n]) || new THREE.Vector3(0, 60, 0);
}

// ── looks: focus (green, opaque) / normal / context (translucent) / ghost / hidden ──
function setMode(o, mode) {
  if (o.mode === mode) return;
  o.mode = mode;
  o.node.visible = mode !== 'hidden';
  for (const m of o.meshes) {
    const b = m.userData.base, see = mode === 'context' || mode === 'ghost';
    m.layers.set(mode === 'ghost' ? 2 : 0);
    m.material.color.copy(mode === 'focus' ? GREEN : b.color);
    m.material.transparent = see || b.transparent;
    m.material.opacity = mode === 'ghost' ? Math.min(GHOST_OPACITY, b.opacity * 0.4)
      : mode === 'context' ? Math.min(state.follow ? CONTEXT_OPACITY_FOLLOW : CONTEXT_OPACITY, b.opacity) : b.opacity;
    m.material.depthWrite = !see && !b.transparent;
    m.material.emissive?.set(0x000000);
    m.material.needsUpdate = true;
    const e = m.userData.edges;
    if (e) {
      e.material.color.copy(ink);
      e.material.opacity = mode === 'ghost' ? 0.05 : mode === 'context' ? (state.follow ? 0.13 : 0.22) : 0.55;
      e.material.depthWrite = !see;
    }
  }
}

function applyLooks() {
  if (!ready) return;
  const sel = new Set(state.select || []);
  if (state.tab === 'overview') {
    const iso = state.isolate ? new Set(state.isolate) : null;
    for (const [n, o] of Object.entries(OBJ)) {
      const machine = !n.startsWith('TOOL_');
      let mode = !machine ? 'hidden' : !iso ? 'normal' : iso.has(n) ? 'focus' : state.ghost ? 'ghost' : 'hidden';
      setMode(o, mode);
    }
    $('#empty').classList.remove('on');
    return;
  }
  const i = state.step, placed = placedSet(i), focus = focusSet(i), removed = removedSet(i);
  const anyFocus = focus.size > 0 || sel.size > 0;
  for (const [n, o] of Object.entries(OBJ)) {
    let mode;
    if (focus.has(n) || (sel.has(n) && placed.has(n))) mode = 'focus';
    else if (placed.has(n)) mode = anyFocus ? 'context' : 'normal';
    else if (removed.has(n)) mode = 'ghost';
    else if (o.anim && o.anim.hideAtEnd) mode = o.mode === 'hidden' ? 'context' : o.mode;   // flying out: keep drawn
    else mode = state.ghost && !n.startsWith('TOOL_') ? 'ghost' : 'hidden';
    setMode(o, mode);
  }
  const empty = placed.size === 0;
  $('#empty').classList.toggle('on', empty && !state.ghost);
  $('#empty').textContent = empty ? 'Nothing is placed yet. Press Next step, or turn on "Ghost the rest" to see the finished machine.' : '';
}

// ── fly-in / fly-out ──
const easeIO = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
function animate(o, from, to, { delay = 0, dur = FLY_S, hideAtEnd = false } = {}) {
  if (SNAP) { o.fly = to; o.anim = null; if (hideAtEnd) o.hiddenByAnim = true; return; }
  o.fly = from;
  o.anim = { from, to, t0: performance.now() + delay * 1000, dur: dur * 1000, hideAtEnd };
}
function stepAnimations(now) {
  let ended = false;
  for (const o of Object.values(OBJ)) {
    const a = o.anim; if (!a) continue;
    const t = Math.max(0, Math.min(1, (now - a.t0) / a.dur));
    o.fly = a.from + (a.to - a.from) * easeIO(t);
    if (t >= 1) { o.anim = null; if (a.hideAtEnd) ended = true; }
  }
  if (ended) applyLooks();
}
const flying = () => Object.values(OBJ).some(o => o.anim);
// freeze the fly-in clock (debug and screenshots: a frame grabbed mid-flight)
let pausedAt = null;
function pauseFlight() { pausedAt = performance.now(); }
function resumeFlight() { const d = performance.now() - pausedAt; for (const o of Object.values(OBJ)) if (o.anim) o.anim.t0 += d; pausedAt = null; }

// transition from step p to step i
function transition(p, i) {
  const adjacent = Math.abs(i - p) === 1, forward = i > p;
  const placedP = placedSet(p), placedI = placedSet(i), remP = removedSet(p), remI = removedSet(i);
  const focusI = focusSet(i);
  for (const [n, o] of Object.entries(OBJ)) {
    const wasIn = placedP.has(n), wasRem = remP.has(n), isIn = placedI.has(n), isRem = remI.has(n);
    if (focusI.has(n) && (forward || !adjacent)) {             // the step's parts arrive
      o.off.copy(offFor(n, i));
      animate(o, 1, 0, { delay: n.startsWith('FST_') ? SCREW_DELAY_S : 0 });
    } else if (isRem) {                                          // taken off at this step: park at its offset, faint
      o.off.copy(offFor(n, objFirst[n] ?? i));
      if (wasIn && adjacent) animate(o, o.fly, 1, { dur: FLY_OUT_S }); else { o.fly = 1; o.anim = null; }
    } else if (isIn) {                                           // stays (or comes back) in place
      if (wasRem && adjacent) animate(o, o.fly, 0); else if (!o.anim || o.anim.to !== 0) { o.fly = 0; o.anim = null; }
    } else if ((wasIn || wasRem) && adjacent) {                  // leaves: fly out, then hide
      if (!wasRem) o.off.copy(offFor(n, p));
      animate(o, o.fly, 1, { dur: FLY_OUT_S, hideAtEnd: true });
    } else { o.fly = 0; o.anim = null; }
    // servo slid out at 11a: ease the shift
    o.shiftTo.set(0, 0, 0);
  }
  const sh = STEPS[i].shift;
  if (sh) for (const n of sh.objects) OBJ[n]?.shiftTo.copy(b2t(sh.mm));
  if (SNAP) for (const o of Object.values(OBJ)) o.shift.copy(o.shiftTo);
}

function placeObjects(dt = 0) {
  const focus = state.tab === 'steps' ? focusSet(state.step) : new Set();
  const k = Math.min(1, dt * 4);
  for (const [n, o] of Object.entries(OBJ)) {
    o.shift.lerp(o.shiftTo, k);
    const f = focus.has(n) ? Math.max(o.fly, state.hold) : o.fly;      // "hold apart" never pulls a part in mid-flight
    o.node.position.copy(o.basePos).add(o.shift).addScaledVector(o.off, state.tab === 'steps' ? f : 0);
  }
}

// ── joints ──
const AX = { X: ['x', 1], Y: ['z', -1], Z: ['y', 1] };
function setJoint(name, degVal) {
  const p = PIV[name]; if (!p) return;
  const [k, s] = AX[p.userData.joint_axis || 'Z'];
  p.rotation[k] = s * rad(degVal);
}
function poseJoints() {
  const ang = { PIV_pan: actual.pan, PIV_tilt: actual.tilt, PIV_feeder: actual.feed };
  setJoint('PIV_pan', actual.pan); setJoint('PIV_tilt', actual.tilt); setJoint('PIV_feeder', actual.feed);
  if (PIV.PIV_flywheel) PIV.PIV_flywheel.rotation.x = actual.fw;
  for (const [n, p] of Object.entries(PIV)) {
    const c = p.userData.couple_to;
    if (c && ang[c] !== undefined) setJoint(n, (p.userData.couple_ratio ?? 1) * ang[c]);
  }
}

// ── camera ──
let cam = null, MAIN = null;
const T0 = performance.now();
const MAIN_DIR = [1, 1.3, 0.75];
function fitPose(box, viewDir, margin = 1.35, minR = 75) {
  const center = box.getCenter(new THREE.Vector3());
  const r = Math.max(box.getSize(new THREE.Vector3()).length() / 2, minR);
  const vf = rad(v.camera.fov), hf = 2 * Math.atan(Math.tan(vf / 2) * v.camera.aspect);
  const dist = r / Math.sin(Math.min(vf, hf) / 2) * margin;
  const dir = viewDir ? b2t(viewDir).normalize() : v.camera.position.clone().sub(v.controls.target).normalize();
  return { pos: center.clone().addScaledVector(dir, dist), tgt: center };
}
function easeCamera(to, instant) {
  cam = { fromPos: v.camera.position.clone(), fromTgt: v.controls.target.clone(), to, t: 0, dur: instant || SNAP ? 0 : 0.9 };
}
function mainView() {
  const box = new THREE.Box3();
  Object.values(OBJ).forEach(o => !o.name.startsWith('TOOL_') && box.union(o.boxHome));
  return fitPose(box, MAIN_DIR, 0.9);
}
// box of the parts at their final place plus where they fly in from
function arrivalBox(names) {
  const box = new THREE.Box3(), q = new THREE.Quaternion();
  for (const n of names) {
    const o = OBJ[n]; if (!o) continue;
    const saved = o.node.position.clone();
    o.node.position.copy(o.basePos).add(o.shiftTo); o.node.updateMatrixWorld(true);
    const b = new THREE.Box3().setFromObject(o.node);
    box.union(b);
    o.node.parent.getWorldQuaternion(q);
    const off = (STEPS[state.step]._off[n] || o.off).clone().applyQuaternion(q);
    box.union(b.clone().translate(off.multiplyScalar(Math.max(0.6, state.hold))));
    o.node.position.copy(saved);
  }
  return box;
}
function followFrame(instant) {
  if (!ready) return;
  // settle the step's pose first, so the frame is where the parts will be
  const save = { pan: actual.pan, tilt: actual.tilt };
  actual.pan = target.pan; actual.tilt = target.tilt; poseJoints(); v.scene.updateMatrixWorld(true);
  let names = state.tab === 'overview' ? (state.isolate || []) : [...(state.select?.length ? state.select : focusSet(state.step))];
  if (!names.length) names = [...placedSet(state.step)];
  const box = arrivalBox(names);
  actual.pan = save.pan; actual.tilt = save.tilt; poseJoints();
  if (box.isEmpty()) { easeCamera(MAIN, instant); return; }
  const dir = state.tab === 'steps' && !state.select?.length ? STEPS[state.step].view : null;
  easeCamera(fitPose(box, dir), instant);
}
v.controls.addEventListener('start', () => { if (cam && performance.now() - T0 > 1500) cam = null; });
function stepCamera(dt) {
  if (!cam) return;
  cam.t = cam.dur ? Math.min(1, cam.t + dt / cam.dur) : 1;
  const k = easeIO(cam.t);
  v.camera.position.lerpVectors(cam.fromPos, cam.to.pos, k);
  v.controls.target.lerpVectors(cam.fromTgt, cam.to.tgt, k);
  // ax-three dollies the camera in for its first 1.2 s; keep re-applying our pose until that is over
  if (cam.t >= 1 && performance.now() - T0 > 1600) cam = null;
}

// ── per-frame ──
const grid = v.scene.children.find(o => o.type === 'GridHelper');
v.onFrame(dt => {
  if (grid) grid.visible = v.camera.position.y > 0;   // seen from under the floor the grid cuts across the parts
  gizmo();
  if (!ready) return;
  const k = Math.min(1, dt * 4);
  actual.pan += (target.pan - actual.pan) * k;
  actual.tilt += (target.tilt - actual.tilt) * k;
  if (spin) actual.fw += dt * Math.PI * 2 * 1.5;
  if (feeding) {
    feedClock += dt;
    if (feedClock > 1.8) { feedClock = 0; feedSign = -feedSign; }
    feedTarget = feedClock < 0.7 ? 60 * feedSign : 0;
  } else feedTarget = 0;
  const pf = actual.feed;
  actual.feed += (feedTarget - actual.feed) * Math.min(1, dt * 7);
  if (Math.round(pf) !== Math.round(actual.feed)) $('#feedOut').textContent = Math.round(actual.feed);
  poseJoints();
  stepAnimations(pausedAt ?? performance.now());
  placeObjects(dt);
  stepCamera(dt);
  // a faint green breathing on the focused parts
  const t = performance.now() / 1000, pulse = reduced ? 0.04 : 0.03 + 0.03 * Math.sin(t * 3.2);
  for (const o of Object.values(OBJ)) {
    if (o.mode !== 'focus') continue;
    for (const m of o.meshes) {
      m.material.emissive?.copy(GREEN).multiplyScalar(pulse);
      const e = m.userData.edges; if (e) { e.material.color.copy(ink); e.material.opacity = 0.6; }
    }
  }
});

// ── UI: step list ──
function renderStepList() {
  let html = '', group = null;
  STEPS.forEach((s, i) => {
    if (s.group !== group) { group = s.group; html += `<div class="ax-label g-group">${esc(group)}</div>`; }
    const tags = [];
    if (s.bench) tags.push(`<span class="g-tag">Bench · ${esc(s.bench)}</span>`);
    if (s.merge) tags.push(`<span class="g-tag">Joins ${esc(s.merge)}</span>`);
    if (s.status === 'flagged') tags.push(`<span class="ax-status warning">Flagged</span>`);
    html += `<button class="g-step" data-i="${i}"><span class="id">${esc(s.id)}</span><span class="tt">${esc(s.title)}</span>` +
            (tags.length ? `<span class="tags">${tags.join('')}</span>` : '') + `</button>`;
  });
  $('#side').innerHTML = html;
  $('#side').querySelectorAll('.g-step').forEach(b => (b.onclick = () => go(+b.dataset.i)));
}

function groupNames(names) {
  // fasteners collapse to one row per spec; everything else one row each
  const rows = [], fst = {};
  for (const n of names) {
    const p = PARTS[n] || {};
    if (p.kind === 'FST') (fst[p.spec || 'fastener'] ??= []).push(n);
    else rows.push({ label: n, sub: p.kind === 'PRT' ? `plate ${(p.plate || '').split('-')[0]} · ${p.colour}` : (p.kind || '').toLowerCase(), names: [n] });
  }
  for (const [spec, ns] of Object.entries(fst))
    rows.push({ label: `${ns.length} x ${spec}`, sub: ns.length > 1 ? ns[0].replace(/_?\d+$/, '_*') : ns[0], names: ns });
  return rows;
}

function selectedHTML() {
  if (!state.select?.length) return '';
  const n = state.select[0], k = objFirst[n];
  const label = state.select.length > 1 ? `${state.select.length} x ${esc(PARTS[n]?.spec || n)}` : esc(n);
  return `<div class="g-sel"><div class="ax-label">Selected</div><div class="g-sel-name"><span class="g-sw g-green"></span>${label}</div>` +
    `<div class="g-sub">${tipHTML(n).split('<br>').slice(1, -1).join(' · ')}</div><div class="g-sel-btns">` +
    (k !== undefined && k !== state.step ? `<button class="ax-btn" id="selGo">Go to step ${esc(STEPS[k].id)}</button>` : '') +
    `<button class="ax-btn" id="selClear">Clear selection</button></div></div>`;
}

function renderDetail() {
  const s = STEPS[state.step];
  const parts = [selectedHTML()];
  parts.push(`<div class="ax-label">Step ${esc(s.id)} · ${esc(s.group)}</div><h2 class="g-title">${esc(s.title)}</h2>`);
  if (s.bench) {
    const at = mergeAt[s.bench] !== undefined ? STEPS[mergeAt[s.bench]].id : '?';
    parts.push(`<div class="g-sub">Bench sub-assembly <b>${esc(s.bench)}</b>: built off the machine and shown here where it ends up. It joins the machine at step ${esc(at)}.</div>`);
  } else if (s.merge) parts.push(`<div class="g-sub">The <b>${esc(s.merge)}</b> bench sub-assembly joins the machine here.</div>`);
  if (s.hide_objects.length) parts.push(`<div class="g-sub">Taken off for this step and shown faint where it was put aside: ${groupNames(s.hide_objects).map(r => esc(r.label)).join(', ')}.</div>`);
  if (s.warnings.length) parts.push(`<div class="g-sec">` + s.warnings.map(w =>
    `<div class="g-warn ${w.level}"><span class="ax-status ${w.level}">${w.level === 'critical' ? 'Caution' : 'Warning'}</span>` +
    `<p>${esc(w.text)}</p><div class="src">${esc(w.source)}</div></div>`).join('') + `</div>`);
  if (s.tools.length) parts.push(`<div class="g-sec"><span class="ax-label">Tools</span><ul class="g-tools">${s.tools.map(t => `<li>${t}</li>`).join('')}</ul></div>`);
  if (s.fasteners.length) {
    const fc = s.fastener_check;
    parts.push(`<div class="g-sec"><span class="ax-label">Fasteners</span><table><tbody>` +
      s.fasteners.map(f => `<tr><td class="num">${f.qty ?? ''}</td><td>${f.qty ? f.spec : f.text}</td></tr>`).join('') +
      `</tbody></table><div class="g-check"><span class="ax-status ${fc.state === 'good' ? 'good' : fc.state === 'warning' ? 'warning' : ''}">${esc(fc.text)}</span></div></div>`);
  }
  for (const f of s.fields) parts.push(`<div class="g-sec"><span class="ax-label">${esc(f.label)}</span>${f.html}</div>`);
  for (const p of s.paragraphs) parts.push(`<p class="g-sub">${p}</p>`);
  const newRows = groupNames(s.focus_objects);
  if (newRows.length) parts.push(`<div class="g-sec"><span class="ax-label">In green in the view (${s.focus_objects.length}) · click one to select it</span><div class="g-parts">` +
    newRows.map((r, i) => `<button class="g-part" data-r="${i}"><span><span class="g-sw g-green"></span>${esc(r.label)}</span><span>${esc(r.sub)}</span></button>`).join('') + `</div></div>`);
  for (const r of s.renders) {
    const src = D.thumbs[r.key]; if (!src) continue;
    parts.push(`<div class="g-sec"><span class="ax-label">${r.scope === 'section' ? 'Section render' : 'Render'}</span>` +
      `<figure class="g-fig" data-key="${esc(r.key)}" data-ref="${esc(r.ref)}"><img src="${src}" alt="${esc(r.key)}"><figcaption>${esc(r.ref)}</figcaption></figure></div>`);
  }
  const ao = s.assembly_order.map(a => `${a.label}${a.bench ? ` (bench ${a.bench})` : ''}${a.merge ? ` (merges ${a.merge})` : ''}`).join(', ');
  parts.push(`<div class="g-sec"><span class="ax-label">Model mapping</span><ul class="g-map">` +
    `<li><span class="ax-status ${s.status === 'clean' ? 'good' : 'warning'}">${s.status === 'clean' ? 'Mapped' : 'Flagged'}</span> ` +
    `${ao ? `checks.json assembly_order ${esc(ao)}` : 'no assembly_order entry: nothing new is placed in this step'}; ${s.new_objects.length} new objects</li>` +
    s.flags.map(f => `<li><span class="ax-status warning">Flag</span> ${esc(f)}</li>`).join('') +
    s.notes.map(f => `<li>${esc(f)}</li>`).join('') + `</ul></div>`);
  const keep = $('#detail').scrollTop, sameStep = $('#detail').dataset.step === String(state.step);
  $('#detail').innerHTML = parts.join('');
  $('#detail').dataset.step = state.step;
  $('#detail').scrollTop = sameStep ? keep : 0;
  $('#detail').querySelectorAll('.g-part').forEach(b => {
    const r = newRows[+b.dataset.r];
    b.classList.toggle('on', !!state.select && r.names.every(n => state.select.includes(n)) && state.select.length === r.names.length);
    b.onclick = () => select(b.classList.contains('on') ? null : r.names);
  });
  $('#detail').querySelectorAll('.g-fig').forEach(f => (f.onclick = () => lightbox(D.thumbs[f.dataset.key], f.dataset.ref)));
  $('#selGo') && ($('#selGo').onclick = () => { const k = objFirst[state.select[0]]; go(k); });
  $('#selClear') && ($('#selClear').onclick = () => select(null));
}

function lightbox(src, cap) {
  const lb = document.createElement('div');
  lb.className = 'ax-lightbox';
  lb.innerHTML = `<figure><img src="${src}" alt=""><figcaption><b>Render</b> ${esc(cap)}</figcaption></figure>`;
  lb.onclick = () => { lb.classList.add('closing'); setTimeout(() => lb.remove(), 180); };
  document.body.appendChild(lb);
}

function renderBadge() {
  const s = STEPS[state.step];
  const sq = (c, t) => `<span style="--c:${c}">${t}</span>`;
  if (state.tab === 'overview') {
    $('#badge').innerHTML = `<div class="t">Finished machine</div><div class="ax-label">${state.isolate ? `Isolated: ${esc(state.isolateKey)}` : 'All parts · click one in the list to isolate it'}</div>`;
    $('#legend').innerHTML = sq('#d1ccc2', 'PLA A warm grey') + sq('#c4532b', 'PLA B terracotta') + (state.isolate ? sq('var(--g-green)', 'Isolated') : '');
    return;
  }
  const where = s.bench ? `Bench sub-assembly: ${esc(s.bench)}, shown in place` : s.merge ? `${esc(s.merge)} sub-assembly joins the machine` : 'On the machine';
  $('#badge').innerHTML = `<div class="t"><b>${esc(s.id)}</b>${esc(s.title)}</div><div class="ax-label">${where}${s.pose.tilt ? ` · pod at tilt ${s.pose.tilt}°` : ''} · ${state.follow ? 'following parts' : 'stationary camera'}</div>`;
  $('#legend').innerHTML = sq('var(--g-green)', state.select?.length ? 'This step / selected' : 'This step') +
    sq('rgba(209, 204, 194, 0.3)', 'Placed earlier') + (state.ghost ? sq('rgba(209, 204, 194, 0.08)', 'Later') : '');
}

// ── overview tab ──
function renderOverview() {
  const m = D.meta, tot = m.totals, c = m.counts;
  const prt = Object.entries(PARTS).filter(([, p]) => p.kind === 'PRT');
  let side = `<button class="ax-btn g-showall" id="showall">Show all parts</button>`;
  side += `<div class="ax-label g-group">Printed, by plate</div>`;
  for (const p of D.plates) {
    side += `<div class="g-sub" style="margin:8px 0 2px"><span class="g-sw" style="background:${p.colour === 'B' ? '#c4532b' : '#d1ccc2'}"></span>${esc(p.name)} · ${p.printer}</div><div class="g-parts">`;
    for (const it of p.items) side += `<button class="g-part" data-iso="${esc(it.objects.join(','))}" data-key="${esc(it.stl)}" ${it.objects.length ? '' : 'disabled title="not in the assembly model"'}><span>${esc(it.stl)}${it.qty > 1 ? ` x ${it.qty}` : ''}</span><span>${it.objects.length ? `${it.infill} %` : 'tool, not in model'}</span></button>`;
    side += `</div>`;
  }
  const kindList = (kind, title) => {
    const rows = groupNames(Object.keys(PARTS).filter(n => PARTS[n].kind === kind).sort());
    return `<div class="ax-label g-group">${title}</div><div class="g-parts">` + rows.map(r =>
      `<button class="g-part" data-iso="${esc(r.names.join(','))}" data-key="${esc(r.label)}"><span>${esc(r.label)}</span><span>${esc(PARTS[r.names[0]].step ? 'step ' + PARTS[r.names[0]].step : '')}</span></button>`).join('') + `</div>`;
  };
  side += kindList('BUY', 'Purchased') + kindList('FST', 'Fasteners, by size') + kindList('CAB', 'Cables');
  $('#side').innerHTML = side;
  const tile = (label, val, unit, sub) => `<div class="ax-tile"><div class="ax-label">${label}</div><div class="ax-value">${val}${unit ? `<small>${unit}</small>` : ''}</div>${sub ? `<div class="ax-sub">${sub}</div>` : ''}</div>`;
  let det = `<div class="ax-label">Print plan · PRINT_PLAN.md</div><h2 class="g-title">Parts and plates</h2>`;
  det += `<div class="g-tiles">` +
    tile('Machine parts', prt.length, '', '37 prints: the nip leaf twice') +
    tile('Plates', D.plates.length, '', 'H2D 4 · P1S 5') +
    tile('Print time', tot.h.toFixed(1), 'h', 'about 15 h on both printers') +
    tile('Filament', Math.round(tot.g), 'g', `A ${Math.round(tot.g_A)} g · B ${Math.round(tot.g_B)} g`) +
    tile('Purchased', c.BUY || 0, '', 'in the model') +
    tile('Fasteners', c.FST || 0, '', 'in the model, plus 4 drilled to fit') + `</div>`;
  det += `<p class="g-sub" style="margin-top:8px">Times and grams are estimates from the geometry. No slicer was run.</p>`;
  det += `<div class="g-sec"><span class="ax-label">Plates</span><table><thead><tr><th>Plate</th><th>Printer</th><th class="num">h</th><th class="num">g</th></tr></thead><tbody>` +
    D.plates.map(p => `<tr class="clk" data-plate="${esc(p.name)}"><td><span class="g-sw" style="background:${p.colour === 'B' ? '#c4532b' : '#d1ccc2'}"></span>${esc(p.name)}</td><td>${p.printer}</td><td class="num">${p.h?.toFixed(1) ?? ''}</td><td class="num">${p.g ? Math.round(p.g) : ''}</td></tr>`).join('') +
    `</tbody></table><div class="g-sub" style="margin-top:4px">Click a plate to isolate its parts. Colour A warm grey: structure and drivetrain. Colour B terracotta: the candy path and touch points.</div></div>`;
  det += `<div class="g-sec"><span class="ax-label">Measure before printing · MEASURE_FIRST.md</span><table><thead><tr><th>Item</th><th>Measure</th><th>Before</th></tr></thead><tbody>` +
    D.measure.map(r => `<tr><td class="num">${r.item}</td><td>${esc(r.what)}</td><td>${esc(r.before)}</td></tr>`).join('') + `</tbody></table></div>`;
  det += `<div class="g-sec"><span class="ax-label">Step mapping</span><p class="g-sub">${STEPS.filter(s => s.status === 'clean').length} of ${STEPS.length} steps map cleanly onto checks.json assembly_order; ` +
    `${STEPS.filter(s => s.status !== 'clean').length} flagged: ${STEPS.filter(s => s.status !== 'clean').map(s => esc(s.id)).join(', ') || 'none'}.</p></div>`;
  $('#detail').innerHTML = det;
  $('#detail').dataset.step = '';
  $('#showall').onclick = () => isolate(null);
  document.querySelectorAll('[data-iso]').forEach(b => (b.onclick = () => isolate(b.dataset.iso.split(',').filter(Boolean), b.dataset.key)));
  document.querySelectorAll('tr[data-plate]').forEach(tr => (tr.onclick = () => {
    const p = D.plates.find(x => x.name === tr.dataset.plate);
    isolate(p.items.flatMap(it => it.objects), p.name);
  }));
  markIsolated();
}

function markIsolated() {
  document.querySelectorAll('[data-iso], tr[data-plate]').forEach(b =>
    b.classList.toggle('on', !!state.isolateKey && (b.dataset.key === state.isolateKey || b.dataset.plate === state.isolateKey)));
}

function isolate(names, key) {
  state.isolate = names && names.length ? names : null;
  state.isolateKey = state.isolate ? (key || names[0]) : null;
  applyLooks(); renderBadge(); markIsolated();
  if (state.follow) followFrame(); else if (!state.isolate) easeCamera(MAIN);
  else followFrame();            // isolating one part in the overview always frames it: it may be a 6 mm screw
}

function select(names) {
  state.select = names && names.length ? names : null;
  applyLooks(); renderBadge();
  if (state.tab === 'steps') renderDetail();
  if (state.follow) followFrame();
}

// ── navigation ──
function go(i) {
  const p = state.step;
  state.step = Math.max(0, Math.min(STEPS.length - 1, i));
  const s = STEPS[state.step];
  target.pan = s.pose.pan; target.tilt = s.pose.tilt;
  setSlider('pan', target.pan); setSlider('tilt', target.tilt);
  if (SNAP) { actual.pan = target.pan; actual.tilt = target.tilt; }
  if (state.tab !== 'steps') return;
  if (state.select && !state.select.every(n => placedSet(state.step).has(n))) state.select = null;
  document.querySelectorAll('.g-step').forEach(b => {
    const on = +b.dataset.i === state.step;
    if (on) { b.setAttribute('aria-current', 'step'); b.scrollIntoView({ block: 'nearest' }); } else b.removeAttribute('aria-current');
  });
  axSet($('#stepNo'), state.step + 1, { digits: 0 });
  $('#prev').disabled = state.step === 0;
  $('#next').disabled = state.step === STEPS.length - 1;
  renderDetail(); renderBadge();
  if (ready) {
    transition(p, state.step);
    applyLooks();
    placeObjects();
    if (state.follow) followFrame();
  }
  if (!SNAP && ready) history.replaceState(null, '', '#step=' + encodeURIComponent(s.id));
}

function setTab(tab) {
  state.tab = tab;
  document.body.dataset.tab = tab;
  document.querySelectorAll('.g-tabs .ax-btn').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === tab));
  if (tab === 'overview') {
    renderOverview(); renderBadge(); applyLooks(); placeObjects();
    target.pan = 0; target.tilt = 0; setSlider('pan', 0); setSlider('tilt', 0);
    if (!state.isolate) easeCamera(MAIN);
  } else {
    renderStepList();
    if (state.isolate) { state.isolate = null; state.isolateKey = null; }
    go(state.step);
    if (!state.follow) easeCamera(MAIN);
  }
}

function setSlider(id, val) {
  const el = $('#' + id); el.value = val;
  const out = $('#' + id + 'Out');
  if (+out.textContent !== Math.round(val)) axSet(out, Math.round(val), { digits: 0 });
}

function setFollow(on) {
  state.follow = on;
  $('#follow').setAttribute('aria-pressed', on);
  for (const o of Object.values(OBJ)) o.mode = null;    // context opacity depends on the mode
  applyLooks(); renderBadge();
  if (on) followFrame(); else easeCamera(MAIN);
}

// ── controls ──
$('#prev').onclick = () => go(state.step - 1);
$('#next').onclick = () => go(state.step + 1);
$('#explode').oninput = e => { state.hold = e.target.value / 100; $('#explodeOut').textContent = e.target.value; };
$('#pan').oninput = e => { target.pan = +e.target.value; $('#panOut').textContent = e.target.value; };
$('#tilt').oninput = e => { target.tilt = +e.target.value; $('#tiltOut').textContent = e.target.value; };
const toggle = (id, fn) => { const b = $('#' + id); b.onclick = () => { const on = b.getAttribute('aria-pressed') !== 'true'; b.setAttribute('aria-pressed', on); fn(on); }; };
toggle('ghost', on => { state.ghost = on; applyLooks(); renderBadge(); });
toggle('spin', on => (spin = on));
toggle('feed', on => { feeding = on; feedClock = 0; });
$('#follow').onclick = () => setFollow($('#follow').getAttribute('aria-pressed') !== 'true');
$('#mainview').onclick = () => { if (state.follow) setFollow(false); else easeCamera(MAIN); };
$('#home').onclick = () => { target.pan = 0; target.tilt = 0; setSlider('pan', 0); setSlider('tilt', 0); };
document.querySelectorAll('.g-tabs .ax-btn').forEach(b => (b.onclick = () => setTab(b.dataset.tab)));
document.addEventListener('keydown', e => {
  if (e.target.matches?.('input, textarea, select') || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'Escape' && state.select) { select(null); return; }
  if (state.tab !== 'steps') return;
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === 'PageDown') { go(state.step + 1); e.preventDefault(); }
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'PageUp') { go(state.step - 1); e.preventDefault(); }
});

// ── start ──
$('#stepOf').textContent = `/ ${STEPS.length}`;
const startIdx = (() => {
  if (H.i !== undefined) return +H.i;
  const k = STEPS.findIndex(s => s.id === H.step);
  return k >= 0 ? k : 0;
})();
state.step = startIdx;
state.ghost = H.ghost === '1';
$('#ghost').setAttribute('aria-pressed', state.ghost);
renderStepList();
go(startIdx);
axBusy(view, true, 'Loading model');
loadModel().then(() => {
  axBusy(view, false);
  const ls = $('#loadState'); ls.className = 'ax-status good'; ls.textContent = 'Model loaded';
  MAIN = mainView();
  easeCamera(MAIN, true);
  const hold = H.hold ?? H.explode;
  if (hold) { state.hold = +hold / 100; $('#explode').value = hold; $('#explodeOut').textContent = hold; }
  if (H.spin === '1') $('#spin').click();
  if (H.select) state.select = H.select.split(',');
  if (H.tab === 'overview') {
    setTab('overview');
    if (H.isolate) isolate(H.isolate.split(','), H.isolate);
  } else {
    setTab('steps');
    state.step = startIdx;
    transition(startIdx > 0 ? startIdx - 1 : 0, startIdx);   // play the opening step's fly-in
    applyLooks(); renderDetail(); renderBadge();
  }
  if (H.pan !== undefined) { target.pan = +H.pan; setSlider('pan', target.pan); }
  if (H.tilt !== undefined) { target.tilt = +H.tilt; setSlider('tilt', target.tilt); }
  if (SNAP) { actual.pan = target.pan; actual.tilt = target.tilt; poseJoints(); placeObjects(); }
  if (H.follow === '1') setFollow(true);
  document.body.dataset.ready = '1';
  console.log('GUIDE_READY', Object.keys(OBJ).length, 'objects');
}).catch(err => {
  axBusy(view, false);
  const ls = $('#loadState'); ls.className = 'ax-status critical'; ls.textContent = 'Model failed to load';
  $('#empty').classList.add('on'); $('#empty').textContent = 'The 3D model failed to load: ' + err.message + '. three.js loads from cdn.jsdelivr.net, so the page needs a network connection.';
  console.error('GUIDE_FAIL', err);
});

// handle for debugging from the console (and the headless test): guide.state, guide.OBJ, guide.PIV ...
window.guide = { state, target, actual, OBJ, PIV, STEPS, go, select, placedSet, focusSet, flying, setFollow, pauseFlight, resumeFlight, get MAIN() { return MAIN; }, camera: v.camera, controls: v.controls };

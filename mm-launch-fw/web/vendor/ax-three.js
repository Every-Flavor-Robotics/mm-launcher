// alex-style three.js viewport. ES module; needs this import map in the page:
//
//   <script type="importmap">{ "imports": {
//     "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
//     "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/" } }</script>
//
//   import { axScene } from './ax-three.js';
//   const v = axScene(document.getElementById('view'), { units: 'mm' });
//   const part = v.solid(new THREE.BoxGeometry(40, 10, 10));      // styled mesh with ink edges
//   v.pickable(part, () => `J2 · shoulder<br>${angle.toFixed(1)}°`); // hover glow + tooltip
//   const gripper = await v.load('assets/robotiq_base.stl', { size: 60 }); // spinner while loading
//   v.onFrame(dt => { ... });
//
// Look: flat dark solids, thin ink edges like a CAD drawing, dashed floor grid,
// a labeled XYZ triad, terracotta glow on whatever the mouse is over.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const tok = v => getComputedStyle(document.documentElement).getPropertyValue('--ax-' + v).trim();
const col = v => new THREE.Color(tok(v));

export function axScene(container, { units = 'mm', floor = 400, camera: camPos = [320, 260, 320], target = [0, 80, 0], autoRotate = true, triad = true } = {}) {
  container.style.position ||= 'relative';
  container.classList.add('ax-viewport');

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  const labels = new CSS2DRenderer();
  Object.assign(labels.domElement.style, { position: 'absolute', inset: '0', pointerEvents: 'none' });
  container.appendChild(labels.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 1, 20000);
  camera.position.set(...camPos);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(...target);
  controls.enableDamping = true;
  controls.autoRotate = autoRotate;
  controls.autoRotateSpeed = 0.6;
  // Stop idling the moment someone touches it; resume after 6 s alone
  let idle;
  controls.addEventListener('start', () => { controls.autoRotate = false; clearTimeout(idle); });
  controls.addEventListener('end', () => { idle = setTimeout(() => (controls.autoRotate = autoRotate), 6000); });

  scene.add(new THREE.HemisphereLight(0xffffff, 0x202020, 1.6));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(300, 500, 200);
  scene.add(key);

  // Floor: dashed-looking grid in the chart grid color, with a brighter centre cross
  const grid = new THREE.GridHelper(floor * 2, 24, col('axis'), col('grid'));
  grid.material.transparent = true; grid.material.opacity = 0.9;
  scene.add(grid);

  if (triad) {
    // Triad sits in the floor corner nearest the camera's left, clear of the model
    const L = floor * 0.18;
    const toCam = new THREE.Vector3(camPos[0], 0, camPos[2]).normalize();
    const left = new THREE.Vector3(-toCam.z, 0, toCam.x);
    const corner = toCam.clone().multiplyScalar(floor * 0.55).add(left.multiplyScalar(floor * 0.45)).setY(0.5);
    [['X', [1, 0, 0], 's2'], ['Y', [0, 1, 0], 's3'], ['Z', [0, 0, 1], 's1']].forEach(([name, d, c]) => {
      const dir = new THREE.Vector3(...d);
      scene.add(new THREE.ArrowHelper(dir, corner, L, col(c), 8, 5));
      const tag = document.createElement('div');
      tag.className = 'ax-3d-label';
      tag.textContent = `${name}, ${units}`;
      const o = new CSS2DObject(tag);
      o.position.copy(dir.multiplyScalar(L + 14)).add(corner);
      scene.add(o);
    });
  }

  // ── Styled solids ──
  const edgeMat = () => new THREE.LineBasicMaterial({ color: col('ink'), transparent: true, opacity: 0.55 });
  function solid(geometry, { color = 'panel', edges = 20, metal = 0.2 } = {}) {
    const base = tok(color) ? col(color) : new THREE.Color(color);
    if (color === 'panel') base.offsetHSL(0, 0, 0.12);
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: base, roughness: 0.6, metalness: metal, flatShading: true }));
    const lines = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, edges), edgeMat());
    mesh.add(lines);
    mesh.userData.edges = lines;
    return mesh;
  }

  // ── Hover picking ──
  const pickables = [];
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
  let hovered = null, mouseEv = null;
  let tip = document.querySelector('.ax-tip');
  if (!tip) { tip = document.createElement('div'); tip.className = 'ax-tip'; document.body.appendChild(tip); }

  function pickable(mesh, info, onClick) {
    mesh.userData.info = info; mesh.userData.onClick = onClick;
    pickables.push(mesh);
    return mesh;
  }
  function setHover(m) {
    if (hovered === m) return;
    if (hovered) {
      hovered.material.emissive?.set(0x000000);
      hovered.userData.edges && (hovered.userData.edges.material.color = col('ink'), hovered.userData.edges.material.opacity = 0.55);
    }
    hovered = m;
    renderer.domElement.style.cursor = m ? 'pointer' : '';
    if (m) {
      m.material.emissive?.copy(col('accent')).multiplyScalar(0.35);
      m.userData.edges && (m.userData.edges.material.color = col('accent'), m.userData.edges.material.opacity = 1);
    } else tip.style.display = 'none';
  }
  renderer.domElement.addEventListener('pointermove', e => (mouseEv = e));
  renderer.domElement.addEventListener('pointerleave', () => { mouseEv = null; setHover(null); });
  renderer.domElement.addEventListener('click', () => hovered?.userData.onClick?.(hovered));

  function updateHover() {
    if (!mouseEv) return;
    const r = renderer.domElement.getBoundingClientRect();
    mouse.set(((mouseEv.clientX - r.left) / r.width) * 2 - 1, -((mouseEv.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(pickables, false)[0];
    setHover(hit ? hit.object : null);
    if (hovered) {
      const info = hovered.userData.info;
      tip.innerHTML = typeof info === 'function' ? info() : info;
      tip.style.display = 'block';
      tip.style.left = mouseEv.clientX + 14 + 'px'; tip.style.top = mouseEv.clientY + 14 + 'px';
    }
  }

  // ── Loading models (STL or GLB/GLTF) with the house spinner ──
  async function load(url, { size, color, parent = scene } = {}) {
    window.axBusy?.(container, true, 'Loading model');
    try {
      let obj;
      if (/\.stl$/i.test(url)) {
        const { STLLoader } = await import('three/addons/loaders/STLLoader.js');
        const geo = await new STLLoader().loadAsync(url);
        geo.computeVertexNormals();
        obj = solid(geo, { color, edges: 35 });
      } else {
        const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
        obj = (await new GLTFLoader().loadAsync(url)).scene;
        obj.traverse(m => { if (m.isMesh) m.add(new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry, 35), edgeMat())); });
      }
      // Wrap in a group so callers can rotate and place it about its own center
      const holder = new THREE.Group();
      if (size) { // scale so the largest dimension equals `size`, and center it
        const box = new THREE.Box3().setFromObject(obj), s = box.getSize(new THREE.Vector3());
        const k = size / Math.max(s.x, s.y, s.z);
        obj.scale.setScalar(k);
        obj.position.sub(box.getCenter(new THREE.Vector3()).multiplyScalar(k));
      }
      holder.add(obj);
      parent.add(holder);
      return holder;
    } finally {
      window.axBusy?.(container, false);
    }
  }

  // ── Loop ──
  const frameFns = [];
  const clock = new THREE.Clock();
  function resize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h, false); labels.setSize(w, h);
    renderer.domElement.style.width = '100%'; renderer.domElement.style.height = '100%';
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(container);
  resize();

  // Intro: dolly in from further out
  const end = camera.position.clone(), start = end.clone().multiplyScalar(1.6);
  let intro = matchMedia('(prefers-reduced-motion: reduce)').matches ? 1 : 0;
  renderer.setAnimationLoop(() => {
    const dt = clock.getDelta();
    if (intro < 1) { intro = Math.min(1, intro + dt / 1.2); camera.position.lerpVectors(start, end, 1 - Math.pow(1 - intro, 3)); }
    frameFns.forEach(f => f(dt));
    controls.update();
    updateHover();
    renderer.render(scene, camera);
    labels.render(scene, camera);
  });

  return { THREE, scene, camera, renderer, controls, solid, pickable, load, onFrame: f => frameFns.push(f), label(obj, text) {
    const d = document.createElement('div'); d.className = 'ax-3d-label'; d.textContent = text;
    const o = new CSS2DObject(d); obj.add(o); return o;
  } };
}

/* Viewer 3D hasil eksperimen — IF3170 FrontierFolly.
 * Jalankan dari root repo: python3 -m http.server 8123, lalu buka /visualizer/.
 */
import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { DATA } from './data.js';

const { packages, truck } = DATA;
const [TW, TL, TH] = truck.dimensions;
const CAP = truck.max_capacity;
const IDS = Object.keys(packages).sort();
const MAXV = Math.max(...IDS.map((id) => packages[id].value));
const MAXW = Math.max(...IDS.map((id) => packages[id].weight));

const ALGOS = [
  { id: 'random_restart',  label: 'Hill Climbing — Random Restart',  base: '../output/hill_climbing/random_restart' },
  { id: 'steepest_ascent', label: 'Hill Climbing — Steepest Ascent', base: '../output/hill_climbing/steepest_ascent' },
  { id: 'stochastic',      label: 'Hill Climbing — Stochastic',      base: '../output/hill_climbing/stochastic' },
  { id: 'sideways_move',   label: 'Hill Climbing — Sideways Move',   base: '../output/hill_climbing/sideways_move' },
  { id: 'sa',              label: 'Simulated Annealing',             base: '../output/simulated_annealing' },
  { id: 'bonus',           label: 'Bonus — Objective Urgency',       base: '../output/hill_climbing/bonus_alt_objective/steepest' },
];
const RUNS = [1, 2, 3];
const CHECK_LABELS = { orientation: 'orientasi', bounds: 'batas', collision: 'tabrakan', weight: 'berat', support: 'support', fragile: 'fragile' };
const REDUCE_MOTION = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
const COMPACT_DEFAULT_OUTSIDE = window.innerWidth >= 960;

const qs = new URLSearchParams(location.search);
const qsT = qs.has('t') ? Number(qs.get('t')) : 1;
const qsColor = qs.get('color');
const ui = {
  algo: ALGOS.some((a) => a.id === qs.get('algo')) ? qs.get('algo') : 'random_restart',
  run: RUNS.includes(Number(qs.get('run'))) ? Number(qs.get('run')) : 2,
  t: Number.isFinite(qsT) ? Math.min(1, Math.max(0, qsT)) : 1,
  colorMode: ['value', 'weight', 'fragile'].includes(qsColor) ? qsColor : 'value',
  labels: true,
  outside: COMPACT_DEFAULT_OUTSIDE,
};

const $ = (id) => document.getElementById(id);
const dom = {
  algo: $('algo'), runSeg: $('runSeg'), runLabel: $('runLabel'), runPath: $('runPath'),
  colorSeg: $('colorSeg'), legend: $('legend'), legendMin: $('legendMin'), legendMax: $('legendMax'),
  stValue: $('stValue'), stScore: $('stScore'), stWeight: $('stWeight'), stCount: $('stCount'),
  weightBar: $('weightBar'), stExtras: $('stExtras'), stChecks: $('stChecks'),
  t: $('t'), tLabel: $('tLabel'), btnInitial: $('btnInitial'), btnFinal: $('btnFinal'),
  play: $('play'), playLabel: $('playLabel'),
  chkLabels: $('chkLabels'), chkOutside: $('chkOutside'), resetCam: $('resetCam'),
  banner: $('banner'), tooltip: $('tooltip'), stage: $('stage'),
  pinned: $('pinned'), pinnedDot: $('pinnedDot'), pinnedTitle: $('pinnedTitle'),
  pinnedTag: $('pinnedTag'), pinnedBody: $('pinnedBody'), pinnedClose: $('pinnedClose'),
};

const runButtons = [...dom.runSeg.querySelectorAll('button')];
const colorButtons = [...dom.colorSeg.querySelectorAll('button')];

let pendingSelect = qs.get('select');

const fmt = (n, d = 2) => new Intl.NumberFormat('id-ID', { maximumFractionDigits: d }).format(n);
const lerp = (a, b, t) => a + (b - a) * t;

const ico = (paths, strokeWidth = 1.9) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
const ICONS = {
  seed: ico('<path d="M4 9h16M4 15h16M10 3 8 21M16 3l-2 18"/>'),
  clock: ico('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'),
  repeat: ico('<path d="m17 2 4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>'),
  alert: ico('<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>'),
  refresh: ico('<path d="M21 12a9 9 0 1 1-2.6-6.4"/><path d="M21 3v6h-6"/>'),
  arrowRight: ico('<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>'),
  flag: ico('<path d="M4 22V4"/><path d="M4 4h14l-2.5 4L18 12H4"/>'),
  target: ico('<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3.5"/>'),
  check: ico('<path d="M20 6 9 17l-5-5"/>', 2.4),
};

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.domElement.setAttribute('role', 'img');
renderer.domElement.setAttribute('aria-label', 'Visualisasi 3D penempatan paket di dalam truk');
dom.stage.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
camera.up.set(0, 0, 1); // dunia memakai z sebagai sumbu atas (sesuai data)
const DESKTOP_CAM = new THREE.Vector3(21, -26, 18);
const MOBILE_CAM = new THREE.Vector3(18, -22, 13.5);
const CAM_HOME = DESKTOP_CAM.clone();
camera.position.copy(CAM_HOME);
const TARGET = new THREE.Vector3(TW / 2, TL / 2, TH / 2 - 0.5);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(TARGET);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 4;
controls.maxDistance = 170;
controls.maxPolarAngle = Math.PI * 0.52;

scene.add(new THREE.HemisphereLight(0xffffff, 0xc9d6e6, 1.15));
scene.add(new THREE.AmbientLight(0xffffff, 0.3));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.35);
keyLight.position.set(20, -8, 26);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0xa9c7ff, 0.55);
rimLight.position.set(-16, 22, 12);
scene.add(rimLight);

const truckGroup = new THREE.Group();
{
  const ox = 0.02;
  const x0 = -ox;
  const x1 = TW + ox;
  const y0 = -ox;
  const y1 = TL + ox;
  const z1 = TH + ox;
  const pts = [
    [x0, y0, 0], [x0, y0, z1],
    [x1, y0, 0], [x1, y0, z1],
    [x1, y1, 0], [x1, y1, z1],
    [x0, y1, 0], [x0, y1, z1],
    [x0, y0, z1], [x1, y0, z1],
    [x1, y0, z1], [x1, y1, z1],
    [x1, y1, z1], [x0, y1, z1],
    [x0, y1, z1], [x0, y0, z1],
  ].map(([x, y, z]) => new THREE.Vector3(x, y, z));
  const frameGeo = new THREE.BufferGeometry().setFromPoints(pts);
  const edges = new THREE.LineSegments(
    frameGeo,
    new THREE.LineBasicMaterial({ color: 0x1d4ed8, transparent: true, opacity: 0.55 }),
  );
  truckGroup.add(edges);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(TW, TL),
    new THREE.MeshBasicMaterial({ color: 0xdbe8ff, transparent: true, opacity: 0.7, side: THREE.DoubleSide }),
  );
  floor.position.set(TW / 2, TL / 2, 0.01);
  truckGroup.add(floor);

  const grid = new THREE.GridHelper(48, 48, 0xd2dce8, 0xe4eaf2);
  grid.rotation.x = Math.PI / 2;
  grid.position.set(TW / 2, TL / 2, -0.002);
  truckGroup.add(grid);
}
scene.add(truckGroup);

const boxGroup = new THREE.Group();
const outsideGroup = new THREE.Group();
scene.add(boxGroup, outsideGroup);
const pickables = [];

const UNIT_GEO = new THREE.BoxGeometry(1, 1, 1);
const UNIT_EDGES = new THREE.EdgesGeometry(UNIT_GEO);
const EDGE_MAT = new THREE.LineBasicMaterial({ color: 0x0b1b2b, transparent: true, opacity: 0.24 });
const SELECT_HELPER = new THREE.BoxHelper(new THREE.Mesh(UNIT_GEO), 0x0866ff);
SELECT_HELPER.material.depthTest = false;
SELECT_HELPER.material.transparent = true;
SELECT_HELPER.material.opacity = 0.9;
SELECT_HELPER.renderOrder = 30;
SELECT_HELPER.visible = false;
scene.add(SELECT_HELPER);
const C_LOW = new THREE.Color('#7fb2ff');
const C_HIGH = new THREE.Color('#0747c9');
const C_FRAG = new THREE.Color('#e5484d');
const C_FRAG_NORMAL = new THREE.Color('#9cc3ff');
const C_OUT = new THREE.Color('#afc0d6');

function colorFor(id) {
  const p = packages[id];
  if (ui.colorMode === 'fragile') return (p.is_fragile ? C_FRAG : C_FRAG_NORMAL).clone();
  const tc = ui.colorMode === 'weight'
    ? (MAXW ? p.weight / MAXW : 0)
    : (MAXV ? p.value / MAXV : 0);
  return C_LOW.clone().lerp(C_HIGH, tc);
}

const labelTex = new Map();
function textureFor(id) {
  if (labelTex.has(id)) return labelTex.get(id);
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 112;
  const ctx = c.getContext('2d');
  const x = 16;
  const y = 14;
  const w = 224;
  const h = 84;
  const r = 26;

  ctx.save();
  ctx.shadowColor = 'rgba(15, 27, 38, 0.18)';
  ctx.shadowBlur = 10;
  ctx.shadowOffsetY = 3;
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.96)';
  ctx.fill();
  ctx.restore();

  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.strokeStyle = 'rgba(11, 27, 43, 0.14)';
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.font = '700 44px Inter, system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#0b1b2b';
  ctx.fillText(id, packages[id].is_fragile ? 106 : 128, y + h / 2 + 2);

  // penanda fragile: bentuk, bukan hanya warna
  if (packages[id].is_fragile) {
    ctx.beginPath();
    ctx.arc(196, y + h / 2, 16, 0, Math.PI * 2);
    ctx.fillStyle = '#e5484d';
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.roundRect(194.25, y + h / 2 - 16, 3.5, 17, 1.75);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(196, y + h / 2 + 9, 2.4, 0, Math.PI * 2);
    ctx.fill();
  }

  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  labelTex.set(id, t);
  return t;
}

function makeBox(id, { outside = false } = {}) {
  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({
    roughness: 0.48,
    metalness: 0.04,
    transparent: true,
    opacity: outside ? 0.55 : 1,
  });
  mat.color.copy(colorFor(id));
  if (outside) mat.color.lerp(C_OUT, 0.55);

  const mesh = new THREE.Mesh(UNIT_GEO, mat);
  mesh.userData.pkgId = id;
  mesh.add(new THREE.LineSegments(UNIT_EDGES, EDGE_MAT));
  group.add(mesh);

  const label = new THREE.Sprite(new THREE.SpriteMaterial({
    map: textureFor(id),
    depthTest: false,
    transparent: true,
    opacity: outside ? 0.85 : 1,
  }));
  label.scale.set(1.6, 0.7, 1);
  label.renderOrder = 20;
  group.add(label);

  group.userData = { id, mesh, mat, label, outside };
  pickables.push(mesh);
  return group;
}

function sizeOf(id, ori) {
  const d = packages[id].dimensions;
  return [d[ori[0]], d[ori[1]], d[ori[2]]];
}

let runData = null; // { base, initial, final, result }
let boxes = [];     // { id, group, a, b } — a/b = { pos, size } | null
let outsideBoxes = [];
let playState = null;
let selectedId = null;

function norm(saved) {
  return {
    inside: saved.inside || {},
    outside: saved.outside || [],
    value: saved.value ?? null,
    score: saved.score ?? saved.value ?? null,
  };
}

async function getJson(url, required = true) {
  const res = await fetch(url);
  if (!res.ok) {
    if (required) throw new Error(`HTTP ${res.status} — ${url}`);
    return null;
  }
  return res.json();
}

async function loadRun(algoId, run) {
  ui.algo = algoId;
  ui.run = run;
  dom.algo.value = algoId;
  setRunUI();

  const algo = ALGOS.find((a) => a.id === algoId);
  const base = `${algo.base}/run${run}`;
  hideBanner();
  let initial;
  let final;
  let result;
  try {
    [initial, final, result] = await Promise.all([
      getJson(`${base}/initialState.json`),
      getJson(`${base}/finalState.json`),
      getJson(`${base}/result.json`, false),
    ]);
  } catch (err) {
    showBanner(`Gagal memuat <code>${base}</code>.<br>Jalankan lewat server lokal dari root repo, contoh:<br>`
      + '<code>cd IF3170_G32_FrontierFolly && python3 -m http.server 8123</code>, lalu buka <code>http://localhost:8123/visualizer/</code>.');
    return;
  }
  stopPlay();
  clearSelection();
  runData = { base, initial: norm(initial), final: norm(final), result };
  buildScene();
  updatePanel();

  if (pendingSelect) {
    const id = pendingSelect;
    pendingSelect = null;
    if (runData.initial.inside[id] || runData.final.inside[id]) selectPackage(id);
  }
  syncUrl();
}

function clearGroup(group) {
  for (const root of [...group.children]) {
    root.traverse((o) => {
      if ((o.isMesh || o.isSprite) && o.material && o.material !== EDGE_MAT) o.material.dispose();
    });
    group.remove(root);
  }
}

function buildScene() {
  clearGroup(boxGroup);
  clearGroup(outsideGroup);
  boxes = [];
  outsideBoxes = [];
  pickables.length = 0;

  const ini = runData.initial.inside;
  const fin = runData.final.inside;

  for (const id of IDS) {
    const a = ini[id] ? { pos: [...ini[id].position], size: sizeOf(id, ini[id].orientation) } : null;
    const b = fin[id] ? { pos: [...fin[id].position], size: sizeOf(id, fin[id].orientation) } : null;
    if (!a && !b) continue;
    const group = makeBox(id);
    boxGroup.add(group);
    boxes.push({ id, group, a, b });
  }

  // paket di luar truk: susun sebagai kolom di samping
  let y = 0.4;
  let xRight = -1.4;
  let colW = 0;
  for (const id of IDS) {
    if (ini[id] || fin[id]) continue;
    const size = sizeOf(id, [0, 1, 2]);
    if (y + size[1] > TL) {
      xRight -= colW + 0.8;
      y = 0.4;
      colW = 0;
    }
    const group = makeBox(id, { outside: true });
    group.userData.mesh.scale.set(size[0], size[1], size[2]);
    group.position.set(xRight - size[0] / 2, y + size[1] / 2, size[2] / 2);
    y += size[1] + 0.45;
    colW = Math.max(colW, size[0]);
    outsideGroup.add(group);
    outsideBoxes.push(group);
  }

  applyColorMode();
  applyOutside();
  layout(ui.t);
}

function layout(t) {
  for (const { group, a, b } of boxes) {
    const { mesh, mat, label } = group.userData;
    let pos;
    let size;
    let op;
    let lift = 0;

    if (a && b) {
      pos = [lerp(a.pos[0], b.pos[0], t), lerp(a.pos[1], b.pos[1], t), lerp(a.pos[2], b.pos[2], t)];
      size = [lerp(a.size[0], b.size[0], t), lerp(a.size[1], b.size[1], t), lerp(a.size[2], b.size[2], t)];
      op = 1;
    } else if (a) { // hanya ada di state awal → memudar naik
      pos = a.pos;
      size = a.size;
      op = 1 - t;
      lift = t * 1.5;
    } else {        // hanya ada di state akhir → memudar turun
      pos = b.pos;
      size = b.size;
      op = t;
      lift = (1 - t) * 1.5;
    }

    mesh.scale.set(size[0], size[1], size[2]);
    group.position.set(
      pos[0] + size[0] / 2,
      pos[1] + size[1] / 2,
      pos[2] + size[2] / 2 + lift,
    );
    mat.opacity = op;
    group.visible = op > 0.02;
    label.visible = ui.labels && group.visible;
  }
  updateSelectionHelper();
}

function updateSelectionHelper() {
  if (!selectedId) {
    SELECT_HELPER.visible = false;
    return;
  }
  const entry = boxes.find((b) => b.id === selectedId);
  const group = entry ? entry.group : outsideBoxes.find((g) => g.userData.id === selectedId);
  if (!group || !group.visible) {
    SELECT_HELPER.visible = false;
    return;
  }
  // matrixWorld induk harus segar, terutama saat deep-link sebelum render pertama
  group.updateWorldMatrix(true, true);
  SELECT_HELPER.setFromObject(group.userData.mesh);
  SELECT_HELPER.visible = true;
}

function applyColorMode() {
  for (const { id, group } of boxes) group.userData.mat.color.copy(colorFor(id));
  for (const group of outsideBoxes) {
    group.userData.mat.color.copy(colorFor(group.userData.id)).lerp(C_OUT, 0.55);
    group.userData.mat.opacity = 0.55;
  }
  refreshEmissive();
}

function applyOutside() {
  outsideGroup.visible = ui.outside;
  updateSelectionHelper();
}

function setT(t, syncSlider = true) {
  ui.t = Math.min(1, Math.max(0, t));
  if (syncSlider) dom.t.value = String(ui.t);
  dom.t.style.setProperty('--fill', `${(ui.t * 100).toFixed(1)}%`);
  layout(ui.t);
  dom.tLabel.textContent = ui.t <= 0.001 ? 'awal' : ui.t >= 0.999 ? 'akhir' : `${Math.round(ui.t * 100)}%`;
}

function setPlayUI() {
  const playing = !!playState;
  dom.play.classList.toggle('playing', playing);
  dom.playLabel.textContent = playing ? 'Stop' : 'Putar morph';
}

function stopPlay() {
  playState = null;
  setPlayUI();
}

dom.play.addEventListener('click', () => {
  if (playState) {
    stopPlay();
    return;
  }
  const from = ui.t >= 0.999 ? 0 : ui.t;
  if (REDUCE_MOTION) {
    setT(1);
    return;
  }
  playState = { start: performance.now(), from, dur: 500 + 1500 * (1 - from) };
  setPlayUI();
});

function statsOf(st) {
  let value = 0;
  let weight = 0;
  let count = 0;
  for (const id of Object.keys(st.inside)) {
    value += packages[id].value;
    weight += packages[id].weight;
    count += 1;
  }
  return { value, weight, count };
}

/* port dari src/constraint.py — memastikan state di JSON tetap memenuhi constraint */
function fullState(saved) {
  const s = {};
  for (const id of IDS) s[id] = { position: null, orientation: [0, 1, 2] };
  for (const [id, v] of Object.entries(saved.inside)) {
    s[id] = { position: [...v.position], orientation: [...v.orientation] };
  }
  return s;
}

function dimsOf(state, id) {
  const d = packages[id].dimensions;
  const o = state[id].orientation;
  return [d[o[0]], d[o[1]], d[o[2]]];
}

function contact(pa, da, pb, db) {
  return pa[2] + da[2] === pb[2]
    && pa[0] < pb[0] + db[0] && pb[0] < pa[0] + da[0]
    && pa[1] < pb[1] + db[1] && pb[1] < pa[1] + da[1];
}

function checkState(state) {
  const res = { orientation: true, bounds: true, collision: true, weight: true, support: true, fragile: true };

  for (const id of IDS) {
    const o = state[id].orientation;
    if ([...o].sort().join(',') !== '0,1,2') res.orientation = false;
  }

  for (const id of IDS) {
    const p = state[id].position;
    if (!p) continue;
    const d = dimsOf(state, id);
    for (let k = 0; k < 3; k += 1) {
      if (p[k] < 0 || p[k] + d[k] > truck.dimensions[k]) res.bounds = false;
    }
  }

  for (let i = 0; i < IDS.length; i += 1) {
    const A = IDS[i];
    const pa = state[A].position;
    if (!pa) continue;
    const da = dimsOf(state, A);
    for (let j = i + 1; j < IDS.length; j += 1) {
      const B = IDS[j];
      const pb = state[B].position;
      if (!pb) continue;
      const db = dimsOf(state, B);
      let coll = true;
      for (let k = 0; k < 3; k += 1) {
        if (pa[k] + da[k] <= pb[k] || pb[k] + db[k] <= pa[k]) { coll = false; break; }
      }
      if (coll) res.collision = false;
    }
  }

  let weight = 0;
  for (const id of IDS) if (state[id].position) weight += packages[id].weight;
  if (weight > CAP) res.weight = false;

  for (const A of IDS) {
    const pa = state[A].position;
    if (!pa || pa[2] === 0) continue;
    const da = dimsOf(state, A);
    let supported = false;
    for (const B of IDS) {
      if (A === B) continue;
      const pb = state[B].position;
      if (!pb) continue;
      if (contact(pb, dimsOf(state, B), pa, da)) { supported = true; break; }
    }
    if (!supported) { res.support = false; break; }
  }

  for (const A of IDS) {
    const pa = state[A].position;
    if (!pa || !packages[A].is_fragile) continue;
    const da = dimsOf(state, A);
    for (const B of IDS) {
      if (A === B) continue;
      const pb = state[B].position;
      if (!pb) continue;
      if (contact(pa, da, pb, dimsOf(state, B))) { res.fragile = false; break; } // fragile menjadi penopang
    }
  }

  return res;
}

function setRunUI() {
  for (const b of runButtons) {
    const active = Number(b.dataset.run) === ui.run;
    b.classList.toggle('active', active);
    b.setAttribute('aria-pressed', String(active));
  }
  dom.runLabel.textContent = `run ${ui.run}`;
}

function setColorUI() {
  for (const b of colorButtons) {
    const active = b.dataset.mode === ui.colorMode;
    b.classList.toggle('active', active);
    b.setAttribute('aria-pressed', String(active));
  }
}

function updateLegend() {
  if (ui.colorMode === 'fragile') {
    dom.legend.style.background = 'linear-gradient(90deg,#9cc3ff 0 50%,#e5484d 50% 100%)';
    dom.legendMin.textContent = 'normal';
    dom.legendMax.textContent = 'fragile';
  } else if (ui.colorMode === 'weight') {
    dom.legend.style.background = 'linear-gradient(90deg,#8fbbff,#0747c9)';
    dom.legendMin.textContent = 'ringan';
    dom.legendMax.textContent = `berat · maks ${MAXW}`;
  } else {
    dom.legend.style.background = 'linear-gradient(90deg,#8fbbff,#0747c9)';
    dom.legendMin.textContent = 'value rendah';
    dom.legendMax.textContent = `value tinggi · ${MAXV}`;
  }
}

function chip(iconName, text) {
  return `<span class="chip">${ICONS[iconName] ?? ''}${text}</span>`;
}

function updatePanel() {
  const { initial, final, result, base } = runData;
  dom.runPath.textContent = base.replace('../', '');
  dom.runLabel.textContent = `run ${ui.run}`;

  const si = statsOf(initial);
  const sf = statsOf(final);
  dom.stValue.innerHTML = `${fmt(si.value, 0)}<span class="arrow">→</span><b>${fmt(sf.value, 0)}</b>`;
  dom.stScore.innerHTML = `${fmt(initial.score ?? si.value)}<span class="arrow">→</span><b>${fmt(final.score ?? sf.value)}</b>`;
  dom.stWeight.innerHTML = `${fmt(si.weight, 0)}<span class="arrow">→</span><b>${fmt(sf.weight, 0)} / ${CAP}</b>`;
  dom.stCount.innerHTML = `${si.count}<span class="arrow">→</span><b>${sf.count} / ${IDS.length}</b>`;
  dom.weightBar.style.width = `${Math.min(100, (sf.weight / CAP) * 100)}%`;

  const chips = [];
  if (result?.seed != null) chips.push(chip('seed', `seed ${result.seed}`));
  if (result?.duration != null) chips.push(chip('clock', `${fmt(result.duration, 3)} s`));
  if (result?.iterations != null) chips.push(chip('repeat', `${result.iterations} iterasi`));
  if (result?.stuck != null) chips.push(chip('alert', `stuck ${result.stuck}`));
  if (result?.restarts != null) chips.push(chip('refresh', `${result.restarts} restart`));
  if (result?.sideways_moves != null) chips.push(chip('arrowRight', `${result.sideways_moves} sideways`));
  if (result?.stopped_by) chips.push(chip('flag', `stop: ${result.stopped_by}`));
  if (result?.objective === 'urgency') chips.push(chip('target', 'objective: urgency'));
  dom.stExtras.innerHTML = chips.join('');

  const badI = Object.entries(checkState(fullState(initial))).filter(([, v]) => !v).map(([k]) => CHECK_LABELS[k]);
  const badF = Object.entries(checkState(fullState(final))).filter(([, v]) => !v).map(([k]) => CHECK_LABELS[k]);
  const pill = (label, bad) => (bad.length
    ? `<span class="status-pill bad">${ICONS.alert}${label}: ${bad.join(', ')}</span>`
    : `<span class="status-pill ok">${ICONS.check}${label} valid</span>`);
  dom.stChecks.innerHTML = pill('awal', badI) + pill('akhir', badF);

  updateLegend();
  dom.chkLabels.checked = ui.labels;
  dom.chkOutside.checked = ui.outside;
}

function refreshEmissive() {
  for (const { id, group } of boxes) {
    const m = group.userData.mat;
    m.emissive.setHex(0x000000);
    if (id === selectedId) m.emissive.copy(m.color).multiplyScalar(0.22);
    else if (group.userData.mesh === hovered) m.emissive.copy(m.color).multiplyScalar(0.14);
  }
  for (const group of outsideBoxes) {
    const m = group.userData.mat;
    m.emissive.setHex(0x000000);
    if (group.userData.id === selectedId) m.emissive.copy(m.color).multiplyScalar(0.18);
    else if (group.userData.mesh === hovered) m.emissive.copy(m.color).multiplyScalar(0.12);
  }
}

function renderPinned() {
  if (!selectedId || !runData) return;
  const id = selectedId;
  const p = packages[id];
  const inI = runData.initial.inside[id] || null;
  const inF = runData.final.inside[id] || null;
  const status = inI && inF
    ? 'Termuat (awal & akhir)'
    : inI
      ? 'Keluar saat state akhir'
      : 'Masuk saat state akhir';
  const posEntry = inF || inI;
  const pos = posEntry ? `(${posEntry.position.join(', ')})` : '–';

  dom.pinnedDot.style.background = colorFor(id).getStyle();
  dom.pinnedTitle.textContent = `Paket ${id}`;
  dom.pinnedTag.classList.toggle('hidden', !p.is_fragile);
  dom.pinnedBody.innerHTML = `
    <div class="pin-row"><span>Dimensi (w × l × h)</span><b>${p.dimensions.join(' × ')}</b></div>
    <div class="pin-row"><span>Value</span><b>${p.value}</b></div>
    <div class="pin-row"><span>Berat</span><b>${p.weight}</b></div>
    <div class="pin-row"><span>Eta (urgency)</span><b>${p.eta}</b></div>
    <div class="pin-row"><span>Status</span><b>${status}</b></div>
    <div class="pin-row"><span>Posisi ${inF ? 'akhir' : 'awal'}</span><b>${pos}</b></div>`;
}

function selectPackage(id) {
  selectedId = selectedId === id ? null : id;
  if (!selectedId) {
    dom.pinned.classList.add('hidden');
  } else {
    renderPinned();
    dom.pinned.classList.remove('hidden');
  }
  refreshEmissive();
  updateSelectionHelper();
  syncUrl();
}

function clearSelection() {
  selectedId = null;
  dom.pinned.classList.add('hidden');
  refreshEmissive();
  updateSelectionHelper();
}

dom.pinnedClose.addEventListener('click', () => {
  clearSelection();
  syncUrl();
});
window.addEventListener('keydown', (ev) => {
  if (ev.key === 'Escape') {
    clearSelection();
    syncUrl();
  }
});

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let hovered = null;
let downPos = null;

const isVisible = (obj) => {
  let o = obj;
  while (o) {
    if (!o.visible) return false;
    o = o.parent;
  }
  return true;
};

function hitTest(ev) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  return raycaster.intersectObjects(pickables, false)
    .find((h) => isVisible(h.object) && h.object.material.opacity > 0.3)?.object ?? null;
}

function setHover(mesh, ev) {
  if (hovered !== mesh) {
    hovered = mesh;
    refreshEmissive();
  }
  renderer.domElement.style.cursor = hovered ? 'pointer' : '';

  if (!mesh) {
    dom.tooltip.classList.add('hidden');
    return;
  }

  const id = mesh.userData.pkgId;
  const p = packages[id];
  const inI = !!runData?.initial.inside[id];
  const inF = !!runData?.final.inside[id];
  const status = inI && inF
    ? 'Termuat pada state awal & akhir'
    : inI
      ? 'Keluar saat state akhir'
      : 'Masuk saat state akhir';
  const near = ui.t < 0.5 ? (inI ? runData.initial.inside[id] : null) : (inF ? runData.final.inside[id] : null);
  const posTxt = near ? `(${near.position.join(', ')})` : '–';

  dom.tooltip.innerHTML = `
    <div class="tt-head">
      <span class="dot" style="background:${colorFor(id).getStyle()}" aria-hidden="true"></span>
      <strong>Paket ${id}</strong>
      ${p.is_fragile ? '<span class="tag">Fragile</span>' : ''}
    </div>
    <div class="tt-row">Dimensi <b>${p.dimensions.join(' × ')}</b></div>
    <div class="tt-row">Value <b>${p.value}</b> · Berat <b>${p.weight}</b> · Eta <b>${p.eta}</b></div>
    <div class="tt-row">${status}</div>
    <div class="tt-row">Posisi (${ui.t < 0.5 ? 'awal' : 'akhir'}) <b>${posTxt}</b></div>`;
  dom.tooltip.classList.remove('hidden');

  const stageRect = dom.stage.getBoundingClientRect();
  let px = ev.clientX - stageRect.left + 14;
  let py = ev.clientY - stageRect.top + 14;
  const tw = dom.tooltip.offsetWidth;
  const th = dom.tooltip.offsetHeight;
  if (px + tw > stageRect.width - 8) px = ev.clientX - stageRect.left - tw - 14;
  if (py + th > stageRect.height - 8) py = ev.clientY - stageRect.top - th - 14;
  dom.tooltip.style.left = `${px}px`;
  dom.tooltip.style.top = `${py}px`;
}

renderer.domElement.addEventListener('pointermove', (ev) => setHover(hitTest(ev), ev));
renderer.domElement.addEventListener('pointerleave', () => setHover(null));
renderer.domElement.addEventListener('pointerdown', (ev) => {
  downPos = { x: ev.clientX, y: ev.clientY };
});
renderer.domElement.addEventListener('click', (ev) => {
  if (downPos && Math.hypot(ev.clientX - downPos.x, ev.clientY - downPos.y) > 5) return;
  const hit = hitTest(ev);
  if (hit) selectPackage(hit.userData.pkgId);
  else {
    clearSelection();
    syncUrl();
  }
});

function showBanner(html) {
  dom.banner.innerHTML = html;
  dom.banner.classList.remove('hidden');
}

function hideBanner() {
  dom.banner.classList.add('hidden');
}

function syncUrl() {
  const q = new URLSearchParams({ algo: ui.algo, run: String(ui.run) });
  if (ui.t < 0.999) q.set('t', ui.t.toFixed(3));
  if (ui.colorMode !== 'value') q.set('color', ui.colorMode);
  if (selectedId) q.set('select', selectedId);
  history.replaceState(null, '', `?${q}`);
}

for (const a of ALGOS) dom.algo.add(new Option(a.label, a.id));
dom.algo.value = ui.algo;

dom.algo.addEventListener('change', () => loadRun(dom.algo.value, ui.run));

for (const b of runButtons) {
  b.addEventListener('click', () => {
    const run = Number(b.dataset.run);
    if (run !== ui.run) loadRun(ui.algo, run);
  });
}

for (const b of colorButtons) {
  b.addEventListener('click', () => {
    ui.colorMode = b.dataset.mode;
    setColorUI();
    applyColorMode();
    updateLegend();
    if (selectedId) renderPinned();
    syncUrl();
  });
}

dom.t.addEventListener('input', () => {
  stopPlay();
  setT(Number(dom.t.value));
});
dom.t.addEventListener('change', syncUrl);
dom.btnInitial.addEventListener('click', () => { stopPlay(); setT(0); syncUrl(); });
dom.btnFinal.addEventListener('click', () => { stopPlay(); setT(1); syncUrl(); });
dom.chkLabels.addEventListener('change', () => {
  ui.labels = dom.chkLabels.checked;
  layout(ui.t);
});
dom.chkOutside.addEventListener('change', () => {
  ui.outside = dom.chkOutside.checked;
  applyOutside();
});
dom.resetCam.addEventListener('click', () => {
  camera.position.copy(CAM_HOME);
  controls.target.copy(TARGET);
  controls.update();
});

document.addEventListener('dragover', (ev) => ev.preventDefault());
document.addEventListener('drop', async (ev) => {
  ev.preventDefault();
  const file = ev.dataTransfer?.files?.[0];
  if (!file) return;
  try {
    const saved = JSON.parse(await file.text());
    if (!saved.inside) throw new Error('bukan berkas state (tidak ada key "inside")');
    stopPlay();
    clearSelection();
    runData = { base: file.name, initial: norm(saved), final: norm(saved), result: null };
    buildScene();
    updatePanel();
    hideBanner();
  } catch (err) {
    showBanner(`File tidak bisa dibaca: ${err.message}`);
  }
});

let compactView = null;

function applyViewportMode() {
  const compact = window.innerWidth < 960;
  if (compact === compactView) return;
  compactView = compact;
  if (compact) {
    CAM_HOME.copy(MOBILE_CAM);
    TARGET.set(4.6, 9.8, 1.2);
  } else {
    CAM_HOME.copy(DESKTOP_CAM);
    TARGET.set(TW / 2, TL / 2, TH / 2 - 0.5);
  }
  camera.position.copy(CAM_HOME);
  controls.target.copy(TARGET);
  controls.update();
}

function resize() {
  const w = dom.stage.clientWidth;
  const h = dom.stage.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  applyViewportMode();
}
window.addEventListener('resize', resize);

function animate(now) {
  if (playState) {
    const k = Math.min(1, (now - playState.start) / playState.dur);
    const e = k < 0.5 ? 2 * k * k : 1 - ((-2 * k + 2) ** 2) / 2; // easeInOutQuad
    setT(playState.from + (1 - playState.from) * e);
    if (k >= 1) stopPlay();
  }
  controls.update();
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);

resize();
setRunUI();
setColorUI();
updateLegend();
setT(ui.t);
loadRun(ui.algo, ui.run);

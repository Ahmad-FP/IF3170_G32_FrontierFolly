/* Truck Packing 3D Visualizer — IF3170 FrontierFolly
 * Visualisasi state awal/akhir + animasi morph untuk 4 varian Hill Climbing,
 * Simulated Annealing, dan bonus objective urgency.
 *
 * Jalankan dari root repo:
 *   python3 -m http.server 8123
 * lalu buka http://localhost:8123/visualizer/
 */
import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';
import { DATA } from './data.js';

/* ------------------------------- data ------------------------------- */
const { packages, truck } = DATA;
const [TW, TL, TH] = truck.dimensions; // 10 x 20 x 5
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

const qs = new URLSearchParams(location.search);
const qsT = qs.has('t') ? Number(qs.get('t')) : 1;
const ui = {
  algo: ALGOS.some((a) => a.id === qs.get('algo')) ? qs.get('algo') : 'random_restart',
  run: RUNS.includes(Number(qs.get('run'))) ? Number(qs.get('run')) : 2,
  t: Number.isFinite(qsT) ? Math.min(1, Math.max(0, qsT)) : 1,
  colorMode: 'value',
  labels: true,
  outside: true,
};

const $ = (id) => document.getElementById(id);
const dom = {
  algo: $('algo'), run: $('run'), colorMode: $('colorMode'), legend: $('legend'),
  legendMin: $('legendMin'), legendMax: $('legendMax'), runPath: $('runPath'),
  stValue: $('stValue'), stScore: $('stScore'), stWeight: $('stWeight'), stCount: $('stCount'),
  stExtras: $('stExtras'), stChecks: $('stChecks'),
  t: $('t'), tLabel: $('tLabel'), btnInitial: $('btnInitial'), btnFinal: $('btnFinal'), play: $('play'),
  chkLabels: $('chkLabels'), chkOutside: $('chkOutside'), resetCam: $('resetCam'),
  banner: $('banner'), tooltip: $('tooltip'), stage: $('stage'),
};

const fmt = (n, d = 2) => new Intl.NumberFormat('id-ID', { maximumFractionDigits: d }).format(n);
const lerp = (a, b, t) => a + (b - a) * t;

/* ------------------------------- three ------------------------------- */
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
dom.stage.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
camera.up.set(0, 0, 1); // dunia memakai z sebagai sumbu atas (sesuai data)
const CAM_HOME = new THREE.Vector3(20, -24, 17);
camera.position.copy(CAM_HOME);
const TARGET = new THREE.Vector3(TW / 2, TL / 2, TH / 2 - 0.6);

const controls = new OrbitControls(camera, renderer.domElement);
controls.target.copy(TARGET);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 4;
controls.maxDistance = 170;
controls.maxPolarAngle = Math.PI * 0.52;

scene.add(new THREE.HemisphereLight(0xdbe6ff, 0x0a0e16, 1.1));
scene.add(new THREE.AmbientLight(0x93a4c8, 0.35));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.7);
keyLight.position.set(22, -10, 28);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x7aa2f7, 0.6);
rimLight.position.set(-16, 22, 12);
scene.add(rimLight);

/* kerangka truk + lantai + grid */
const truckGroup = new THREE.Group();
{
  const geo = new THREE.BoxGeometry(TW, TL, TH);
  const edges = new THREE.LineSegments(
    new THREE.EdgesGeometry(geo),
    new THREE.LineBasicMaterial({ color: 0x93a9ff, transparent: true, opacity: 0.8 }),
  );
  edges.position.set(TW / 2, TL / 2, TH / 2);
  truckGroup.add(edges);

  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(TW, TL),
    new THREE.MeshBasicMaterial({ color: 0x7aa2f7, transparent: true, opacity: 0.07, side: THREE.DoubleSide }),
  );
  floor.position.set(TW / 2, TL / 2, 0.01);
  truckGroup.add(floor);

  const grid = new THREE.GridHelper(48, 48, 0x2b3550, 0x1a2236);
  grid.rotation.x = Math.PI / 2;
  grid.position.set(TW / 2, TL / 2, -0.002);
  truckGroup.add(grid);
}
scene.add(truckGroup);

const boxGroup = new THREE.Group();
const outsideGroup = new THREE.Group();
scene.add(boxGroup, outsideGroup);
const pickables = [];

/* geometri & material yang dipakai bersama */
const UNIT_GEO = new THREE.BoxGeometry(1, 1, 1);
const UNIT_EDGES = new THREE.EdgesGeometry(UNIT_GEO);
const EDGE_MAT = new THREE.LineBasicMaterial({ color: 0x0b1220, transparent: true, opacity: 0.4 });
const C_LOW = new THREE.Color('#4dabf7');
const C_HIGH = new THREE.Color('#f59e0b');
const C_FRAG = new THREE.Color('#ff6b6b');
const C_OUT = new THREE.Color('#55617d');

function colorFor(id) {
  const p = packages[id];
  if (ui.colorMode === 'fragile') return (p.is_fragile ? C_FRAG : C_LOW).clone();
  const tc = ui.colorMode === 'weight'
    ? (MAXW ? p.weight / MAXW : 0)
    : (MAXV ? p.value / MAXV : 0);
  return C_LOW.clone().lerp(C_HIGH, tc);
}

/* label id paket */
const labelTex = new Map();
function textureFor(id) {
  if (labelTex.has(id)) return labelTex.get(id);
  const c = document.createElement('canvas');
  c.width = 256;
  c.height = 128;
  const ctx = c.getContext('2d');
  ctx.font = '700 64px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.lineWidth = 10;
  ctx.strokeStyle = 'rgba(6, 10, 18, 0.85)';
  ctx.strokeText(id, 128, 68);
  ctx.fillStyle = '#fff';
  ctx.fillText(id, 128, 68);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  labelTex.set(id, t);
  return t;
}

function makeBox(id, { outside = false } = {}) {
  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({
    roughness: 0.5,
    metalness: 0.08,
    transparent: true,
    opacity: outside ? 0.5 : 1,
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
    opacity: 0.95,
  }));
  label.scale.set(1.6, 0.8, 1);
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

/* ------------------------------ runtime ------------------------------ */
let runData = null; // { base, initial, final, result }
let boxes = [];     // { id, group, a, b } — a/b = { pos, size } | null
let outsideBoxes = [];
let playState = null;

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
  runData = { base, initial: norm(initial), final: norm(final), result };
  buildScene();
  updatePanel();
  syncUrl();
}

/* --------------------------- scene building --------------------------- */
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

  // kotak yang ikut bermorph (ada di state awal dan/atau akhir)
  for (const id of IDS) {
    const a = ini[id] ? { pos: [...ini[id].position], size: sizeOf(id, ini[id].orientation) } : null;
    const b = fin[id] ? { pos: [...fin[id].position], size: sizeOf(id, fin[id].orientation) } : null;
    if (!a && !b) continue;
    const group = makeBox(id);
    boxGroup.add(group);
    boxes.push({ id, group, a, b });
  }

  // paket yang tidak termuat pada awal DAN akhir → deretan di samping truk
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

/* posisikan semua kotak untuk parameter morph t ∈ [0,1] */
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
}

function applyColorMode() {
  for (const { id, group } of boxes) group.userData.mat.color.copy(colorFor(id));
  for (const group of outsideBoxes) {
    group.userData.mat.color.copy(colorFor(group.userData.id)).lerp(C_OUT, 0.55);
    group.userData.mat.opacity = 0.5;
  }
}

function applyOutside() {
  outsideGroup.visible = ui.outside;
}

function setT(t, syncSlider = true) {
  ui.t = Math.min(1, Math.max(0, t));
  if (syncSlider) dom.t.value = String(ui.t);
  layout(ui.t);
  dom.tLabel.textContent = ui.t <= 0.001 ? 'awal' : ui.t >= 0.999 ? 'akhir' : `${Math.round(ui.t * 100)}%`;
}

/* animasi putar otomatis */
function stopPlay() {
  playState = null;
  dom.play.textContent = '▶ Putar morph';
}

dom.play.addEventListener('click', () => {
  if (playState) {
    stopPlay();
    return;
  }
  ui.t = ui.t >= 0.999 ? 0 : ui.t;
  playState = { start: performance.now(), from: ui.t, dur: 500 + 1500 * (1 - ui.t) };
  dom.play.textContent = '⏸ Stop';
});

/* ------------------------------- stats ------------------------------- */
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

function updateLegend() {
  if (ui.colorMode === 'fragile') {
    dom.legend.style.background = 'linear-gradient(90deg,#4dabf7 0 50%,#ff6b6b 50% 100%)';
    dom.legendMin.textContent = 'normal';
    dom.legendMax.textContent = 'fragile';
  } else if (ui.colorMode === 'weight') {
    dom.legend.style.background = 'linear-gradient(90deg,#4dabf7,#f59e0b)';
    dom.legendMin.textContent = 'ringan';
    dom.legendMax.textContent = `berat · maks ${MAXW}`;
  } else {
    dom.legend.style.background = 'linear-gradient(90deg,#4dabf7,#f59e0b)';
    dom.legendMin.textContent = 'value rendah';
    dom.legendMax.textContent = `value tinggi · ${MAXV}`;
  }
}

function updatePanel() {
  const { initial, final, result, base } = runData;
  dom.runPath.textContent = base.replace('../', '');

  const si = statsOf(initial);
  const sf = statsOf(final);
  dom.stValue.innerHTML = `${fmt(si.value, 0)} <span class="arrow">→</span> <b>${fmt(sf.value, 0)}</b>`;
  dom.stScore.innerHTML = `${fmt(initial.score ?? si.value)} <span class="arrow">→</span> <b>${fmt(final.score ?? sf.value)}</b>`;
  dom.stWeight.innerHTML = `${fmt(si.weight, 0)} <span class="arrow">→</span> <b>${fmt(sf.weight, 0)} / ${CAP}</b>`;
  dom.stCount.innerHTML = `${si.count} <span class="arrow">→</span> <b>${sf.count} / ${IDS.length}</b>`;

  const chips = [];
  if (result?.seed != null) chips.push(`seed ${result.seed}`);
  if (result?.duration != null) chips.push(`⏱ ${fmt(result.duration, 3)} s`);
  if (result?.iterations != null) chips.push(`${result.iterations} iterasi`);
  if (result?.stuck != null) chips.push(`stuck ${result.stuck}`);
  if (result?.restarts != null) chips.push(`${result.restarts} restart`);
  if (result?.sideways_moves != null) chips.push(`${result.sideways_moves} sideways`);
  if (result?.stopped_by) chips.push(`stop: ${result.stopped_by}`);
  if (result?.objective === 'urgency') chips.push('objective: urgency');
  dom.stExtras.innerHTML = chips.map((c) => `<span class="chip">${c}</span>`).join('');

  const badI = Object.entries(checkState(fullState(initial))).filter(([, v]) => !v).map(([k]) => CHECK_LABELS[k]);
  const badF = Object.entries(checkState(fullState(final))).filter(([, v]) => !v).map(([k]) => CHECK_LABELS[k]);
  dom.stChecks.innerHTML = [
    `<span class="chip ${badI.length ? 'bad' : 'ok'}">awal: ${badI.length ? `✗ ${badI.join(', ')}` : '✓ valid'}</span>`,
    `<span class="chip ${badF.length ? 'bad' : 'ok'}">akhir: ${badF.length ? `✗ ${badF.join(', ')}` : '✓ valid'}</span>`,
  ].join('');

  updateLegend();

  // tampilkan posisi kotak sesuai state terdekat dari slider
  dom.chkLabels.checked = ui.labels;
  dom.chkOutside.checked = ui.outside;
}

/* ------------------------------ tooltip ------------------------------ */
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let hovered = null;

function setHover(mesh, ev) {
  if (hovered !== mesh) {
    if (hovered) hovered.material.emissive.setHex(0x000000);
    hovered = mesh;
    if (hovered) hovered.material.emissive.copy(hovered.material.color).multiplyScalar(0.35);
    renderer.domElement.style.cursor = hovered ? 'pointer' : '';
  }
  if (!mesh) {
    dom.tooltip.classList.add('hidden');
    return;
  }

  const id = mesh.userData.pkgId;
  const p = packages[id];
  const inI = !!runData?.initial.inside[id];
  const inF = !!runData?.final.inside[id];
  const status = inI && inF
    ? 'termuat pada state awal & akhir'
    : inI
      ? 'keluar saat state akhir'
      : 'masuk saat state akhir';
  const near = ui.t < 0.5 ? (inI ? runData.initial.inside[id] : null) : (inF ? runData.final.inside[id] : null);
  const posTxt = near ? `(${near.position.join(', ')})` : '–';

  dom.tooltip.innerHTML = `<b>Paket ${id}</b>${p.is_fragile ? ' · <span class="frag">fragile</span>' : ''}
    <div class="rowline">dimensi ${p.dimensions.join(' × ')} · value <b>${p.value}</b> · berat ${p.weight} · η ${p.eta}</div>
    <div class="rowline">${status}</div>
    <div class="rowline">posisi (state ${ui.t < 0.5 ? 'awal' : 'akhir'}): ${posTxt}</div>`;
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

renderer.domElement.addEventListener('pointermove', (ev) => {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(pickables, false)
    .find((h) => h.object.parent.visible && h.object.material.opacity > 0.3);
  setHover(hit ? hit.object : null, ev);
});

renderer.domElement.addEventListener('pointerleave', () => setHover(null));

/* ------------------------------ banner ------------------------------ */
function showBanner(html) {
  dom.banner.innerHTML = html;
  dom.banner.classList.remove('hidden');
}

function hideBanner() {
  dom.banner.classList.add('hidden');
}

function syncUrl() {
  const q = new URLSearchParams({ algo: ui.algo, run: String(ui.run) });
  history.replaceState(null, '', `?${q}`);
}

/* ------------------------------- events ------------------------------- */
for (const a of ALGOS) dom.algo.add(new Option(a.label, a.id));
for (const r of RUNS) dom.run.add(new Option(`run ${r} (seed ${r})`, String(r)));
dom.algo.value = ui.algo;
dom.run.value = String(ui.run);

dom.algo.addEventListener('change', () => loadRun(dom.algo.value, ui.run));
dom.run.addEventListener('change', () => loadRun(ui.algo, Number(dom.run.value)));
dom.colorMode.addEventListener('change', () => {
  ui.colorMode = dom.colorMode.value;
  applyColorMode();
  updateLegend();
});
dom.t.addEventListener('input', () => {
  stopPlay();
  setT(Number(dom.t.value));
});
dom.btnInitial.addEventListener('click', () => { stopPlay(); setT(0); });
dom.btnFinal.addEventListener('click', () => { stopPlay(); setT(1); });
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

/* drag & drop satu berkas state */
document.addEventListener('dragover', (ev) => ev.preventDefault());
document.addEventListener('drop', async (ev) => {
  ev.preventDefault();
  const file = ev.dataTransfer?.files?.[0];
  if (!file) return;
  try {
    const saved = JSON.parse(await file.text());
    if (!saved.inside) throw new Error('bukan berkas state (tidak ada key "inside")');
    stopPlay();
    runData = { base: file.name, initial: norm(saved), final: norm(saved), result: null };
    buildScene();
    updatePanel();
    hideBanner();
  } catch (err) {
    showBanner(`File tidak bisa dibaca: ${err.message}`);
  }
});

/* ------------------------------- resize ------------------------------- */
function resize() {
  const w = dom.stage.clientWidth;
  const h = dom.stage.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);

/* ------------------------------- loop ------------------------------- */
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

/* ------------------------------- init ------------------------------- */
resize();
updateLegend();
setT(ui.t);
loadRun(ui.algo, ui.run);

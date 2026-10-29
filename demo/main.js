// 画面试验 v1：废弃屋子、窗外阳光、灰尘光柱、人物走路、越肩镜头。
// 目的是看网页（尤其手机）上实际能做出什么画面、卡不卡。和比赛作品无关。
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import characterB64 from './assets/character-glb.js';

const VERSION = 'v1';
const hud = document.getElementById('hud');
const msg = document.getElementById('msg');
window.addEventListener('error', (e) => { msg.style.display = 'flex'; msg.textContent = '出错了：' + e.message; });

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x05070a);
scene.fog = new THREE.FogExp2(0x2a2620, 0.09);
const camera = new THREE.PerspectiveCamera(55, 1, 0.05, 60);

// ---------- procedural textures (no image files needed) ----------
function noiseTexture(base, spread, planks = false, repeat = 1) {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  g.fillStyle = base;
  g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 9000; i++) {
    const v = (Math.random() - 0.5) * spread;
    g.fillStyle = v > 0 ? `rgba(255,240,220,${v})` : `rgba(0,0,0,${-v})`;
    g.fillRect(Math.random() * 256, Math.random() * 256, 1 + Math.random() * 3, 1 + Math.random() * 3);
  }
  if (planks) {
    g.fillStyle = 'rgba(0,0,0,0.45)';
    for (let x = 0; x < 256; x += 32) g.fillRect(x, 0, 2, 256);
    for (let i = 0; i < 40; i++) {
      g.fillStyle = `rgba(0,0,0,${0.05 + Math.random() * 0.1})`;
      g.fillRect(Math.floor(Math.random() * 8) * 32, Math.random() * 256, 32, 1);
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat, repeat);
  return t;
}
const mat = {
  floor: new THREE.MeshStandardMaterial({ map: noiseTexture('#5a3d24', 0.35, true, 3), roughness: 0.85 }),
  wall: new THREE.MeshStandardMaterial({ map: noiseTexture('#8c8e80', 0.3, false, 2), roughness: 0.95 }),
  wood: new THREE.MeshStandardMaterial({ map: noiseTexture('#4d3018', 0.4, true, 1), roughness: 0.8 }),
  pale: new THREE.MeshStandardMaterial({ map: noiseTexture('#806040', 0.4, true, 1), roughness: 0.75 }),
  leaf: new THREE.MeshStandardMaterial({ color: 0x2f5a1a, roughness: 0.6, side: THREE.DoubleSide }),
  jug: new THREE.MeshStandardMaterial({ color: 0x8a4a2c, roughness: 0.35 }),
};

function box(w, h, d, x, y, z, m, ry = 0, rx = 0) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  mesh.position.set(x, y, z);
  mesh.rotation.set(rx, ry, 0);
  mesh.castShadow = mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}

// ---------- the room (y is up; the window is on the far wall at z = -3) ----------
const W = 6, D = 6, H = 3, T = 0.2;
const win = { x0: -0.4, x1: 1.2, y0: 1.0, y1: 2.3 };
const bz = -D / 2;
box(W, T, D, 0, -T / 2, 0, mat.floor);
box(W, T, D, 0, H + T / 2, 0, mat.wall);
box(T, H, D, -W / 2, H / 2, 0, mat.wall);
box(T, H, D, W / 2, H / 2, 0, mat.wall);
box(W, H, T, 0, H / 2, D / 2, mat.wall);
box(win.x0 + W / 2, H, T, (-W / 2 + win.x0) / 2, H / 2, bz, mat.wall);
box(W / 2 - win.x1, H, T, (W / 2 + win.x1) / 2, H / 2, bz, mat.wall);
box(win.x1 - win.x0, win.y0, T, (win.x0 + win.x1) / 2, win.y0 / 2, bz, mat.wall);
box(win.x1 - win.x0, H - win.y1, T, (win.x0 + win.x1) / 2, (H + win.y1) / 2, bz, mat.wall);
const midX = (win.x0 + win.x1) / 2, midY = (win.y0 + win.y1) / 2;
box(0.06, win.y1 - win.y0, 0.1, midX, midY, bz, mat.wood);
box(win.x1 - win.x0, 0.06, 0.1, midX, midY, bz, mat.wood);

// bright sky behind the window
const sky = new THREE.Mesh(new THREE.PlaneGeometry(14, 8),
  new THREE.MeshBasicMaterial({ color: 0xcfe3ff, toneMapped: false, fog: false }));
sky.position.set(1, 2, bz - 2.5);
scene.add(sky);

// props
box(1.4, 0.06, 0.8, -1.7, 0.78, -1.6, mat.wood);
for (const dx of [-0.62, 0.62]) for (const dz of [-0.32, 0.32]) box(0.06, 0.75, 0.06, -1.7 + dx, 0.375, -1.6 + dz, mat.wood);
const jug = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.25, 20), mat.jug);
jug.position.set(-1.4, 0.94, -1.5); jug.castShadow = true; scene.add(jug);
box(0.6, 0.6, 0.6, 2.0, 0.3, -2.2, mat.pale, 0.1);
box(0.6, 0.6, 0.6, 2.05, 0.9, -2.15, mat.pale, -0.15);
box(0.6, 0.6, 0.6, 1.3, 0.3, -2.4, mat.pale, 0.4);
for (let i = 0; i < 5; i++) box(0.18, 2.2, 0.03, -2.6 + i * 0.22, 1.05, bz + 0.25, mat.pale, 0, 0.21);
for (let i = 0; i < 6; i++) box(0.15, 0.025, 1.1, Math.random() * 3 - 1.5, 0.013, Math.random() * 2 - 1, mat.pale, Math.random() * Math.PI);
const leafGeo = new THREE.PlaneGeometry(0.12, 0.12);
for (let i = 0; i < 160; i++) {
  const l = new THREE.Mesh(leafGeo, mat.leaf);
  l.position.set(win.x0 - 0.3 + Math.random() * (win.x1 - win.x0 + 0.6), Math.random() * 0.15, bz + 0.1 + Math.random() * 0.6);
  l.rotation.set(Math.random() * 6, Math.random() * 6, Math.random() * 6);
  l.receiveShadow = true;
  scene.add(l);
}

// ---------- light ----------
const sunDir = new THREE.Vector3(0.35, -0.55, 1.0).normalize(); // direction the light travels
const sun = new THREE.DirectionalLight(0xffd29a, 6.0);
sun.position.copy(new THREE.Vector3(0.5, 0, 0).addScaledVector(sunDir, -12));
sun.target.position.set(0.5, 0, 0);
sun.castShadow = true;
Object.assign(sun.shadow.camera, { left: -5, right: 5, top: 5, bottom: -5, near: 1, far: 30 });
sun.shadow.bias = -0.0005;
sun.shadow.normalBias = 0.02;
scene.add(sun, sun.target);
scene.add(new THREE.HemisphereLight(0x9fb4d0, 0x3a2a1a, 0.35));
const bounce = new THREE.PointLight(0xffb070, 3.0, 6, 1.5); // warm light bouncing off the sunlit floor
bounce.position.set(1.2, 0.4, 0.2);
scene.add(bounce);

// ---------- light shafts: one soft beam per window pane, plus floating dust ----------
function beam(x0, x1, y0, y1) {
  const hit = (x, y) => { const t = y / -sunDir.y; return [x + sunDir.x * t, 0.02, bz + sunDir.z * t]; };
  const top = [[x0, y1, bz], [x1, y1, bz], [x1, y0, bz], [x0, y0, bz]];
  const bot = top.map(([x, y]) => hit(x, y));
  const pos = [], fade = [];
  for (let i = 0; i < 4; i++) {
    const j = (i + 1) % 4;
    pos.push(...top[i], ...top[j], ...bot[j], ...top[i], ...bot[j], ...bot[i]);
    fade.push(1, 1, 0, 1, 0, 0);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('fade', new THREE.Float32BufferAttribute(fade, 1));
  return new THREE.Mesh(g, beamMat);
}
const beamMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
  uniforms: { strength: { value: 0.10 } },
  vertexShader: 'attribute float fade; varying float vF; void main(){ vF = fade; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
  fragmentShader: 'uniform float strength; varying float vF; void main(){ gl_FragColor = vec4(vec3(1.0,0.85,0.6) * strength * (0.25 + 0.75*vF), 1.0); }',
});
const gap = 0.03;
for (const [a, b] of [[win.x0, midX - gap], [midX + gap, win.x1]])
  for (const [c, d] of [[win.y0, midY - gap], [midY + gap, win.y1]]) scene.add(beam(a, b, c, d));

const dustCount = 500;
const dustPos = new Float32Array(dustCount * 3);
const dustSeed = new Float32Array(dustCount);
for (let i = 0; i < dustCount; i++) {
  const t = Math.random(), y = win.y0 + Math.random() * (win.y1 - win.y0);
  const along = t * (y / -sunDir.y);
  dustPos.set([win.x0 + Math.random() * (win.x1 - win.x0) + sunDir.x * along, y + sunDir.y * along, bz + sunDir.z * along], i * 3);
  dustSeed[i] = Math.random() * 100;
}
const dustGeo = new THREE.BufferGeometry();
dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({
  color: 0xffe2b0, size: 0.012, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false,
}));
scene.add(dust);
const dustBase = dustPos.slice();

// ---------- the character ----------
let mixer = null, hero = null;
const glb = Uint8Array.from(atob(characterB64), (ch) => ch.charCodeAt(0)).buffer;
new GLTFLoader().parse(glb, './assets/', (gltf) => {
  hero = gltf.scene;
  hero.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; o.frustumCulled = false; } });
  scene.add(hero);
  mixer = new THREE.AnimationMixer(hero);
  if (gltf.animations[0]) mixer.clipAction(gltf.animations[0]).play();
  msg.style.display = 'none';
}, (err) => { msg.textContent = '人物加载失败：' + err.message; });

// ---------- quality + camera buttons ----------
let high = true, follow = true;
function applyQuality() {
  renderer.setPixelRatio(high ? Math.min(window.devicePixelRatio, 2) : 1);
  sun.shadow.mapSize.set(high ? 2048 : 512, high ? 2048 : 512);
  if (sun.shadow.map) { sun.shadow.map.dispose(); sun.shadow.map = null; }
  dust.visible = high;
  document.getElementById('quality').textContent = '画质：' + (high ? '高' : '低');
  resize();
}
document.getElementById('quality').onclick = () => { high = !high; applyQuality(); };
document.getElementById('cam').onclick = () => {
  follow = !follow;
  document.getElementById('cam').textContent = '镜头：' + (follow ? '跟随' : '固定');
};
function resize() {
  renderer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize);
applyQuality();

// ---------- loop: walk an oval path, camera over the shoulder ----------
const clock = new THREE.Clock();
const camPos = new THREE.Vector3(0.8, 1.7, 2.6), camLook = new THREE.Vector3(0, 1.2, -2);
let s = 0, frames = 0, fpsTime = 0, fps = 0;
function pathAt(u) { return new THREE.Vector3(0.3 + Math.sin(u) * 1.5, 0, 0.2 - Math.cos(u) * 1.4); }

renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.05);
  const now = clock.elapsedTime;
  if (mixer) mixer.update(dt);
  if (hero) {
    s += dt * 0.45; // about 0.65 m/s along the path
    const p = pathAt(s), dir = pathAt(s + 0.01).sub(p).normalize();
    hero.position.copy(p);
    hero.rotation.y = Math.atan2(-dir.x, -dir.z); // the model faces -Z
    if (follow) {
      const right = new THREE.Vector3(-dir.z, 0, dir.x);
      const wantPos = p.clone().addScaledVector(dir, -2.1).addScaledVector(right, 0.55).setY(1.65);
      const wantLook = p.clone().addScaledVector(dir, 2.0).setY(1.15);
      camPos.lerp(wantPos, 1 - Math.exp(-dt * 3));
      camLook.lerp(wantLook, 1 - Math.exp(-dt * 3));
    } else {
      camPos.set(2.4, 2.4, 2.6); camLook.set(-0.2, 0.8, -1.2);
    }
    camera.position.copy(camPos);
    camera.lookAt(camLook);
  }
  // dust drifts slowly
  if (dust.visible) {
    for (let i = 0; i < dustCount; i++) {
      const k = dustSeed[i];
      dustPos[i * 3] = dustBase[i * 3] + Math.sin(now * 0.3 + k) * 0.05;
      dustPos[i * 3 + 1] = dustBase[i * 3 + 1] + Math.sin(now * 0.2 + k * 1.7) * 0.06;
    }
    dustGeo.attributes.position.needsUpdate = true;
  }
  renderer.render(scene, camera);
  frames++; fpsTime += dt;
  if (fpsTime > 0.5) { fps = Math.round(frames / fpsTime); frames = 0; fpsTime = 0; }
  hud.textContent = `画面试验 ${VERSION}（与比赛无关）· 每秒 ${fps} 帧`;
});

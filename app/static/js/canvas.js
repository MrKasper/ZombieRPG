// ==================== TILE THEMES ====================
const TILE_THEMES = {
  street:   { floorA: '#23262b', floorB: '#1c1f23', wall: '#0e1013', accent: '#4f6f8a', shadow: 'rgba(0,0,0,0.45)' },
  gas:      { floorA: '#2a2422', floorB: '#221d1b', wall: '#100c0b', accent: '#8a5a3a', shadow: 'rgba(0,0,0,0.5)' },
  park:     { floorA: '#1f2a1c', floorB: '#1a2417', wall: '#0b110a', accent: '#4f8a3a', shadow: 'rgba(0,0,0,0.45)' },
  forest:   { floorA: '#1c2818', floorB: '#16200f', wall: '#0a1108', accent: '#3f7a2a', shadow: 'rgba(0,0,0,0.5)' },
  cemetery: { floorA: '#1d1d22', floorB: '#15151a', wall: '#0a0a0d', accent: '#5a4f6a', shadow: 'rgba(0,0,0,0.55)' },
  rooftop:  { floorA: '#22262b', floorB: '#1b1e22', wall: '#0d0f11', accent: '#3a5a7a', shadow: 'rgba(0,0,0,0.5)' },
  tower:    { floorA: '#241f24', floorB: '#1c181c', wall: '#0c0a0c', accent: '#6a4f7a', shadow: 'rgba(0,0,0,0.5)' },
  airport:  { floorA: '#26241e', floorB: '#1f1d18', wall: '#0f0e0b', accent: '#7a6a3a', shadow: 'rgba(0,0,0,0.5)' },
  bunker:   { floorA: '#1e2a24', floorB: '#18221d', wall: '#0a100d', accent: '#4f8a5d', shadow: 'rgba(0,0,0,0.5)' },
  pharmacy: { floorA: '#28232e', floorB: '#201c26', wall: '#100c14', accent: '#6a4f8a', shadow: 'rgba(0,0,0,0.5)' },
  market:   { floorA: '#2a2820', floorB: '#221f18', wall: '#100e0a', accent: '#7a6a3a', shadow: 'rgba(0,0,0,0.5)' },
  hospital: { floorA: '#22262e', floorB: '#1b1e26', wall: '#0d0f14', accent: '#4f6f9a', shadow: 'rgba(0,0,0,0.5)' },
  morgue:   { floorA: '#1a1a24', floorB: '#14141c', wall: '#08080e', accent: '#4a3a6a', shadow: 'rgba(0,0,0,0.6)' },
  school:   { floorA: '#24242e', floorB: '#1c1c26', wall: '#0d0d14', accent: '#4f5f8a', shadow: 'rgba(0,0,0,0.5)' },
  cinema:   { floorA: '#261e26', floorB: '#1e181e', wall: '#0f0a0f', accent: '#7a3a5a', shadow: 'rgba(0,0,0,0.55)' },
  basement: { floorA: '#181818', floorB: '#111111', wall: '#050505', accent: '#4a3a2a', shadow: 'rgba(0,0,0,0.6)' },
  metro:    { floorA: '#1c1c28', floorB: '#15151f', wall: '#08080e', accent: '#3a4a6a', shadow: 'rgba(0,0,0,0.6)' },
  sewer:    { floorA: '#1a261c', floorB: '#131c15', wall: '#070d08', accent: '#3a6a4a', shadow: 'rgba(0,0,0,0.6)' },
  hotel:    { floorA: '#262226', floorB: '#1e1a1e', wall: '#0f0a0f', accent: '#6a4a5a', shadow: 'rgba(0,0,0,0.5)' },
  lab:      { floorA: '#1e2a2c', floorB: '#162020', wall: '#080f10', accent: '#3a7a7a', shadow: 'rgba(0,0,0,0.55)' },
  base:     { floorA: '#26262a', floorB: '#1e1e22', wall: '#0d0d11', accent: '#6a6a5a', shadow: 'rgba(0,0,0,0.5)' },
  _default: { floorA: '#22262b', floorB: '#1b1e22', wall: '#0b0d0f', accent: '#4f6f8a', shadow: 'rgba(0,0,0,0.45)' },
};

function themeFor(loc) { return TILE_THEMES[loc.tilemap_id] || TILE_THEMES._default; }

const DARK_TILEMAPS = new Set(['basement', 'metro', 'sewer', 'morgue', 'tower']);

// ==================== HELPERS ====================
function shade(hex, factor) {
  const n = parseInt(hex.slice(1), 16);
  let r = (n >> 16) & 0xff;
  let g = (n >> 8) & 0xff;
  let b = n & 0xff;
  r = Math.max(0, Math.min(255, Math.round(r * factor)));
  g = Math.max(0, Math.min(255, Math.round(g * factor)));
  b = Math.max(0, Math.min(255, Math.round(b * factor)));
  return '#' + ((r << 16) | (g << 8) | b).toString(16).padStart(6, '0');
}

function makeNoiseCanvas(w, h, alpha) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const g = c.getContext('2d');
  const img = g.createImageData(w, h);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = Math.random() < 0.5 ? 0 : 255;
    img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
    img.data[i + 3] = Math.random() * alpha * 255;
  }
  g.putImageData(img, 0, 0);
  return c;
}

const GRAIN_PATTERN = (() => {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 256;
  const g = c.getContext('2d');
  const img = g.createImageData(256, 256);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = Math.random() * 255;
    img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
    img.data[i + 3] = 26;
  }
  g.putImageData(img, 0, 0);
  return c;
})();
let GRAIN_CTX_PATTERN = null;

// ==================== EMOJI HELPERS ====================
function lootEmoji(kind) {
  return ({
    car: '🚗', box: '📦', shelf: '🗄️', corpse: '💀',
    safe: '🔒', military_crate: '🔰', med_cabinet: '💊',
    fridge: '🧊', locker: '🗃️', toolbox: '🧰', airdrop: '🎁',
  })[kind] || '📦';
}

function exitEmoji(dir) {
  return ({ north: '⬆️', south: '⬇️', east: '➡️', west: '⬅️' })[dir] || '🚪';
}

function decoEmoji(kind) {
  return ({
    tree: '🌲', dead_tree: '🪵', bush: '🌿', rock: '🪨',
    blood: '🩸', barrel: '🛢️', tire: '⭕', street_lamp: '💡',
    bench: '🪑', papers: '📄', glass: '💎', hydrant: '🚒',
    puddle: '💧', old_car: '🚙', corpse: '☠️', graffiti: '🎨',
    sign: '🪧', brick: '🧱', window: '🪟', chair: '💺',
    tv: '📺', mailbox: '📫', trash: '🗑️', plant: '🪴', flag: '🚩',
  })[kind] || '·';
}

// ==================== STAIN STYLES ====================
const STAIN_STYLES = {
  street:   [{ color: 'rgba(20,20,25,0.40)', minR: 15, maxR: 35 }, { color: 'rgba(60,100,130,0.22)', minR: 8, maxR: 18 }],
  gas:      [{ color: 'rgba(30,25,20,0.45)', minR: 12, maxR: 30 }, { color: 'rgba(90,60,40,0.28)', minR: 10, maxR: 22 }],
  park:     [{ color: 'rgba(30,50,25,0.35)', minR: 15, maxR: 30 }],
  forest:   [{ color: 'rgba(20,40,15,0.42)', minR: 15, maxR: 35 }],
  cemetery: [{ color: 'rgba(40,30,40,0.35)', minR: 12, maxR: 25 }, { color: 'rgba(80,20,20,0.30)', minR: 8, maxR: 16 }],
  rooftop:  [{ color: 'rgba(30,30,35,0.42)', minR: 12, maxR: 25 }],
  tower:    [{ color: 'rgba(40,30,45,0.42)', minR: 10, maxR: 22 }],
  airport:  [{ color: 'rgba(30,28,22,0.35)', minR: 15, maxR: 30 }],
  bunker:   [{ color: 'rgba(20,30,25,0.28)', minR: 10, maxR: 20 }],
  pharmacy: [{ color: 'rgba(100,30,40,0.25)', minR: 8, maxR: 15 }, { color: 'rgba(30,25,40,0.30)', minR: 10, maxR: 22 }],
  market:   [{ color: 'rgba(40,35,25,0.35)', minR: 12, maxR: 25 }],
  hospital: [{ color: 'rgba(100,20,25,0.35)', minR: 10, maxR: 25 }, { color: 'rgba(30,30,40,0.30)', minR: 12, maxR: 22 }],
  morgue:   [{ color: 'rgba(80,10,15,0.42)', minR: 12, maxR: 25 }],
  school:   [{ color: 'rgba(30,30,45,0.30)', minR: 12, maxR: 25 }],
  cinema:   [{ color: 'rgba(40,20,35,0.40)', minR: 12, maxR: 25 }],
  basement: [{ color: 'rgba(15,15,15,0.50)', minR: 15, maxR: 30 }],
  metro:    [{ color: 'rgba(20,20,30,0.42)', minR: 15, maxR: 30 }, { color: 'rgba(40,60,90,0.22)', minR: 10, maxR: 20 }],
  sewer:    [{ color: 'rgba(30,50,35,0.40)', minR: 15, maxR: 30 }, { color: 'rgba(30,50,60,0.28)', minR: 12, maxR: 25 }],
  hotel:    [{ color: 'rgba(40,25,35,0.30)', minR: 12, maxR: 22 }],
  lab:      [{ color: 'rgba(30,50,55,0.35)', minR: 10, maxR: 22 }, { color: 'rgba(100,20,25,0.25)', minR: 8, maxR: 15 }],
  base:     [{ color: 'rgba(30,30,32,0.40)', minR: 12, maxR: 25 }],
  _default: [{ color: 'rgba(20,20,25,0.35)', minR: 12, maxR: 25 }],
};

// ==================== OBSTACLE DRAWING ====================
function drawObstacle(b, o) {
  const px = o.x * TILE;
  const py = o.y * TILE;
  switch (o.kind) {
    case 'wall':   return drawWall(b, px, py, o.variant);
    case 'door':   return drawDoor(b, px, py, o.variant);
    case 'window': return drawWindow(b, px, py);
    case 'fence':  return drawFence(b, px, py);
    case 'barrel': return drawBarrel(b, px, py);
    case 'car':    return drawCar(b, px, py);
    case 'crate':  return drawCrate(b, px, py);
  }
}

function drawWall(b, x, y, variant) {
  const colors = {
    brick:    { base: '#5a3a2a', line: '#2a1508', hi: '#7a5040' },
    wood:     { base: '#5a4530', line: '#2a1a08', hi: '#7a6040' },
    concrete: { base: '#4a4a4a', line: '#1a1a1a', hi: '#6a6a6a' },
    metal:    { base: '#3a3a40', line: '#101018', hi: '#5a5a60' },
  };
  const c = colors[variant] || colors.concrete;

  const grad = b.createLinearGradient(x, y, x, y + TILE);
  grad.addColorStop(0, shade(c.base, 1.15));
  grad.addColorStop(1, shade(c.base, 0.7));
  b.fillStyle = grad;
  b.fillRect(x, y, TILE, TILE);

  b.strokeStyle = c.line;
  b.lineWidth = 1;

  if (variant === 'brick') {
    for (let i = 1; i < 4; i++) {
      const ly = y + i * (TILE / 4);
      b.beginPath(); b.moveTo(x, ly); b.lineTo(x + TILE, ly); b.stroke();
    }
    b.beginPath();
    b.moveTo(x + TILE / 3, y); b.lineTo(x + TILE / 3, y + TILE / 4); b.stroke();
    b.moveTo(x + 2 * TILE / 3, y + TILE / 4); b.lineTo(x + 2 * TILE / 3, y + TILE / 2); b.stroke();
    b.moveTo(x + TILE / 3, y + TILE / 2); b.lineTo(x + TILE / 3, y + 3 * TILE / 4); b.stroke();
    b.moveTo(x + 2 * TILE / 3, y + 3 * TILE / 4); b.lineTo(x + 2 * TILE / 3, y + TILE); b.stroke();
  } else if (variant === 'wood') {
    for (let i = 1; i < 4; i++) {
      const lx = x + i * (TILE / 4);
      b.beginPath(); b.moveTo(lx, y); b.lineTo(lx, y + TILE); b.stroke();
    }
  } else if (variant === 'metal') {
    b.strokeRect(x + 2, y + 2, TILE - 4, TILE - 4);
    b.beginPath();
    b.moveTo(x + 2, y + 2); b.lineTo(x + TILE - 2, y + TILE - 2); b.stroke();
  }

  b.fillStyle = c.hi;
  b.fillRect(x, y, TILE, 2);
  b.fillStyle = 'rgba(0,0,0,0.45)';
  b.fillRect(x, y + TILE - 3, TILE, 3);
}

function drawDoor(b, x, y) {
  b.fillStyle = '#0a0605';
  b.fillRect(x + 1, y + 1, TILE - 2, TILE - 2);
  b.fillStyle = '#3a2010';
  b.fillRect(x + 3, y + 3, TILE - 10, TILE - 6);
  b.strokeStyle = '#1a0a04';
  b.lineWidth = 1;
  b.strokeRect(x + 3, y + 3, TILE - 10, TILE - 6);
  b.fillStyle = '#d6a23d';
  b.beginPath();
  b.arc(x + TILE - 6, y + TILE / 2, 2, 0, Math.PI * 2);
  b.fill();
  const grad = b.createRadialGradient(x + TILE / 2, y + TILE / 2, 2, x + TILE / 2, y + TILE / 2, TILE / 2);
  grad.addColorStop(0, 'rgba(255,180,80,0.10)');
  grad.addColorStop(1, 'rgba(255,180,80,0)');
  b.fillStyle = grad;
  b.fillRect(x, y, TILE, TILE);
}

function drawWindow(b, x, y) {
  b.fillStyle = 'rgba(120, 160, 180, 0.35)';
  b.fillRect(x + 2, y + 2, TILE - 4, TILE - 4);
  b.strokeStyle = '#3a2015';
  b.lineWidth = 2;
  b.strokeRect(x + 2, y + 2, TILE - 4, TILE - 4);
  b.beginPath();
  b.moveTo(x + TILE / 2, y + 2); b.lineTo(x + TILE / 2, y + TILE - 2); b.stroke();
  b.moveTo(x + 2, y + TILE / 2); b.lineTo(x + TILE - 2, y + TILE / 2); b.stroke();
}

function drawFence(b, x, y) {
  b.strokeStyle = '#6a5040';
  b.lineWidth = 2;
  for (let i = 1; i < 4; i++) {
    const lx = x + i * (TILE / 4);
    b.beginPath(); b.moveTo(lx, y + 4); b.lineTo(lx, y + TILE - 4); b.stroke();
  }
  b.beginPath();
  b.moveTo(x + 2, y + TILE / 3); b.lineTo(x + TILE - 2, y + TILE / 3); b.stroke();
  b.moveTo(x + 2, y + TILE * 2 / 3); b.lineTo(x + TILE - 2, y + TILE * 2 / 3); b.stroke();
}

function drawBarrel(b, x, y) {
  const cx = x + TILE / 2;
  b.fillStyle = 'rgba(0,0,0,0.4)';
  b.beginPath();
  b.ellipse(cx, y + TILE - 4, TILE * 0.35, 4, 0, 0, Math.PI * 2);
  b.fill();
  const grad = b.createLinearGradient(x, 0, x + TILE, 0);
  grad.addColorStop(0, '#4a3020');
  grad.addColorStop(0.5, '#7a5530');
  grad.addColorStop(1, '#4a3020');
  b.fillStyle = grad;
  b.fillRect(x + 4, y + 4, TILE - 8, TILE - 8);
  b.strokeStyle = '#2a1a0a';
  b.lineWidth = 1;
  b.beginPath(); b.moveTo(x + 4, y + 9); b.lineTo(x + TILE - 4, y + 9); b.stroke();
  b.beginPath(); b.moveTo(x + 4, y + TILE - 9); b.lineTo(x + TILE - 4, y + TILE - 9); b.stroke();
  b.fillStyle = '#8a6a4a';
  b.beginPath();
  b.ellipse(cx, y + 6, TILE / 2 - 5, 3, 0, 0, Math.PI * 2);
  b.fill();
  b.strokeStyle = '#2a1a0a';
  b.stroke();
}

function drawCar(b, x, y) {
  b.fillStyle = 'rgba(0,0,0,0.45)';
  b.beginPath();
  b.ellipse(x + TILE / 2, y + TILE - 3, TILE * 0.45, 5, 0, 0, Math.PI * 2);
  b.fill();
  const grad = b.createLinearGradient(x, y, x, y + TILE);
  grad.addColorStop(0, '#5a5a60');
  grad.addColorStop(1, '#2a2a30');
  b.fillStyle = grad;
  b.fillRect(x + 2, y + 4, TILE - 4, TILE - 8);
  b.fillStyle = '#2a2a30';
  b.fillRect(x + 6, y + 6, TILE - 12, TILE - 12);
  b.fillStyle = 'rgba(120, 160, 180, 0.55)';
  b.fillRect(x + 8, y + 8, TILE - 16, 3);
  b.fillStyle = '#ffe9a8';
  b.fillRect(x + 2, y + 3, 3, 4);
  b.fillRect(x + TILE - 5, y + 3, 3, 4);
  b.fillStyle = '#0a0a0f';
  b.fillRect(x + 1, y + TILE - 6, 4, 4);
  b.fillRect(x + TILE - 5, y + TILE - 6, 4, 4);
}

function drawCrate(b, x, y) {
  b.fillStyle = 'rgba(0,0,0,0.35)';
  b.beginPath();
  b.ellipse(x + TILE / 2, y + TILE - 3, TILE * 0.4, 3, 0, 0, Math.PI * 2);
  b.fill();
  const grad = b.createLinearGradient(x, y, x, y + TILE);
  grad.addColorStop(0, '#6a4a30');
  grad.addColorStop(1, '#3a2410');
  b.fillStyle = grad;
  b.fillRect(x + 3, y + 3, TILE - 6, TILE - 6);
  b.strokeStyle = '#2a1a10';
  b.lineWidth = 1;
  b.strokeRect(x + 3, y + 3, TILE - 6, TILE - 6);
  b.beginPath();
  b.moveTo(x + 3, y + 3); b.lineTo(x + TILE - 3, y + TILE - 3); b.stroke();
  b.moveTo(x + TILE - 3, y + 3); b.lineTo(x + 3, y + TILE - 3); b.stroke();
  b.fillStyle = 'rgba(255,255,255,0.10)';
  b.fillRect(x + 3, y + 3, TILE - 6, 1);
}

// ==================== STATIC LAYER ====================
const BG_CACHE = document.createElement('canvas');
let BG_CACHE_KEY = '';

function drawStaticLayer(loc) {
  const key = `${loc.id}:${loc.grid_w}x${loc.grid_h}:${loc.tilemap_id}:v2`;
  if (BG_CACHE_KEY === key) return BG_CACHE;

  const theme = themeFor(loc);
  BG_CACHE.width = loc.grid_w * TILE;
  BG_CACHE.height = loc.grid_h * TILE;
  const b = BG_CACHE.getContext('2d');
  const W = BG_CACHE.width;
  const H = BG_CACHE.height;

  b.fillStyle = theme.floorA;
  b.fillRect(0, 0, W, H);

  const noiseIntensity = DARK_TILEMAPS.has(loc.tilemap_id) ? 0.08 : 0.05;
  const noise = makeNoiseCanvas(W, H, noiseIntensity);
  b.globalCompositeOperation = 'overlay';
  b.drawImage(noise, 0, 0);
  b.globalCompositeOperation = 'source-over';

  drawStains(b, loc, W, H);

  const wallGradTop = b.createLinearGradient(0, 0, 0, TILE);
  wallGradTop.addColorStop(0, shade(theme.wall, 1.4));
  wallGradTop.addColorStop(1, shade(theme.wall, 0.7));
  b.fillStyle = wallGradTop;
  b.fillRect(0, 0, W, TILE);

  const wallGradBot = b.createLinearGradient(0, H - TILE, 0, H);
  wallGradBot.addColorStop(0, shade(theme.wall, 0.7));
  wallGradBot.addColorStop(1, shade(theme.wall, 1.0));
  b.fillStyle = wallGradBot;
  b.fillRect(0, H - TILE, W, TILE);

  b.fillStyle = shade(theme.wall, 0.9);
  b.fillRect(0, 0, TILE, H);
  b.fillRect(W - TILE, 0, TILE, H);

  b.fillStyle = 'rgba(255,255,255,0.06)';
  b.fillRect(TILE, TILE - 2, W - 2 * TILE, 2);
  b.fillRect(TILE, TILE, 2, H - 2 * TILE);
  b.fillRect(W - TILE - 2, TILE, 2, H - 2 * TILE);

  drawEdgeAO(b, W, H);

  b.font = '18px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
  b.textAlign = 'center'; b.textBaseline = 'middle';
  (loc.decorations || []).forEach(d => {
    b.globalAlpha = d.alpha ?? 0.6;
    b.fillText(decoEmoji(d.kind), d.x * TILE + TILE / 2, d.y * TILE + TILE / 2);
  });
  b.globalAlpha = 1;

  (loc.obstacles || []).forEach(o => drawObstacle(b, o));

  (loc.exit_markers || []).forEach(e => {
    const cx = e.x * TILE + TILE / 2;
    const cy = e.y * TILE + TILE / 2;
    b.fillStyle = 'rgba(111, 174, 93, 0.30)';
    b.fillRect(e.x * TILE + 1, e.y * TILE + 1, TILE - 2, TILE - 2);
    b.strokeStyle = 'rgba(143, 209, 119, 0.9)';
    b.lineWidth = 1.5;
    b.strokeRect(e.x * TILE + 1.5, e.y * TILE + 1.5, TILE - 3, TILE - 3);
    b.font = '14px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
    b.fillText(exitEmoji(e.direction), cx, cy);
  });

  BG_CACHE_KEY = key;
  return BG_CACHE;
}

function drawStains(b, loc, W, H) {
  const styles = STAIN_STYLES[loc.tilemap_id] || STAIN_STYLES._default;
  const count = 14 + Math.floor(Math.random() * 8);
  for (let i = 0; i < count; i++) {
    const style = styles[Math.floor(Math.random() * styles.length)];
    const x = Math.random() * W;
    const y = Math.random() * H;
    const r = style.minR + Math.random() * (style.maxR - style.minR);
    const grd = b.createRadialGradient(x, y, 0, x, y, r);
    grd.addColorStop(0, style.color);
    grd.addColorStop(1, 'rgba(0,0,0,0)');
    b.fillStyle = grd;
    b.beginPath();
    b.arc(x, y, r, 0, Math.PI * 2);
    b.fill();
  }
}

function drawEdgeAO(b, W, H) {
  const size = TILE * 2;
  let g = b.createLinearGradient(0, TILE, 0, TILE + size);
  g.addColorStop(0, 'rgba(0,0,0,0.45)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  b.fillStyle = g;
  b.fillRect(TILE, TILE, W - 2 * TILE, size);

  g = b.createLinearGradient(0, H - TILE - size, 0, H - TILE);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.45)');
  b.fillStyle = g;
  b.fillRect(TILE, H - TILE - size, W - 2 * TILE, size);

  g = b.createLinearGradient(TILE, 0, TILE + size, 0);
  g.addColorStop(0, 'rgba(0,0,0,0.45)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  b.fillStyle = g;
  b.fillRect(TILE, TILE, size, H - 2 * TILE);

  g = b.createLinearGradient(W - TILE - size, 0, W - TILE, 0);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.45)');
  b.fillStyle = g;
  b.fillRect(W - TILE - size, TILE, size, H - 2 * TILE);
}

function drawLighting(loc, w, h) {
  const isDark = DARK_TILEMAPS.has(loc.tilemap_id);
  const cx = ST.displayMe.x * TILE + TILE / 2;
  const cy = ST.displayMe.y * TILE + TILE / 2;

  if (isDark) {
    const radius = TILE * 5.5;
    const grad = ctx.createRadialGradient(cx, cy, TILE * 0.4, cx, cy, radius);
    grad.addColorStop(0, 'rgba(0,0,0,0)');
    grad.addColorStop(0.5, 'rgba(0,0,0,0.45)');
    grad.addColorStop(1, 'rgba(0,0,0,0.88)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    const warm = ctx.createRadialGradient(cx, cy, 0, cx, cy, TILE * 3.5);
    warm.addColorStop(0, 'rgba(255,220,150,0.14)');
    warm.addColorStop(0.6, 'rgba(255,200,120,0.06)');
    warm.addColorStop(1, 'rgba(255,200,120,0)');
    ctx.fillStyle = warm;
    ctx.fillRect(0, 0, w, h);
  } else {
    const grad = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.42,
                                           w / 2, h / 2, Math.max(w, h) * 0.78);
    grad.addColorStop(0, 'rgba(0,0,0,0)');
    grad.addColorStop(1, 'rgba(0,0,0,0.42)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
  }
}

function drawFilmGrain(w, h) {
  if (!GRAIN_CTX_PATTERN) {
    GRAIN_CTX_PATTERN = ctx.createPattern(GRAIN_PATTERN, 'repeat');
  }
  ctx.save();
  ctx.globalAlpha = 0.55;
  if (GRAIN_CTX_PATTERN.setTransform && window.DOMMatrix) {
    const ox = Math.random() * 256;
    const oy = Math.random() * 256;
    GRAIN_CTX_PATTERN.setTransform(new DOMMatrix([1, 0, 0, 1, ox, oy]));
  }
  ctx.fillStyle = GRAIN_CTX_PATTERN;
  ctx.fillRect(0, 0, w, h);
  ctx.restore();
}

// ==================== DRAW WORLD ====================
function drawWorld(loc, me) {
  const theme = themeFor(loc);
  const w = loc.grid_w * TILE;
  const h = loc.grid_h * TILE;
  if (canvas.width !== w) canvas.width = w;
  if (canvas.height !== h) canvas.height = h;

  const bg = drawStaticLayer(loc);
  ctx.drawImage(bg, 0, 0);

  (loc.loot_points || []).forEach(lp => {
    const cx = lp.x * TILE + TILE / 2;
    const cy = lp.y * TILE + TILE / 2;
    const isLooted = lp.state === 'looted';
    ctx.globalAlpha = isLooted ? 0.2 : 1;
    if (!isLooted) {
      if (lp.kind === 'airdrop') {
        const pulse = 0.35 + 0.15 * Math.sin(Date.now() / 300);
        ctx.fillStyle = `rgba(255, 200, 60, ${pulse})`;
      } else {
        ctx.fillStyle = 'rgba(214, 162, 61, 0.15)';
      }
      ctx.fillRect(lp.x * TILE + 3, lp.y * TILE + 3, TILE - 6, TILE - 6);
    }
    ctx.font = '16px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(lootEmoji(lp.kind), cx, cy);
    ctx.globalAlpha = 1;
  });

  if (ST.hovered) {
    const { x, y } = ST.hovered;
    ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.fillRect(x * TILE, y * TILE, TILE, TILE);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.strokeRect(x * TILE + 0.5, y * TILE + 0.5, TILE - 1, TILE - 1);
  }

  loc.zombies.forEach(z => {
    const cx = z.x * TILE + TILE / 2;
    const cy = z.y * TILE + TILE / 2;
    ctx.fillStyle = theme.shadow;
    ctx.beginPath();
    ctx.ellipse(cx, cy + TILE * 0.32, TILE * 0.35, TILE * 0.15, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = 'rgba(120, 180, 80, 0.18)';
    ctx.fillRect(z.x * TILE + 2, z.y * TILE + 2, TILE - 4, TILE - 4);
    ctx.font = '18px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(z.icon, cx, cy);
    const p = Math.max(0, Math.min(1, z.hp / z.max_hp));
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(z.x * TILE + 2, z.y * TILE + TILE - 4, TILE - 4, 2);
    ctx.fillStyle = '#c94f4f';
    ctx.fillRect(z.x * TILE + 2, z.y * TILE + TILE - 4, (TILE - 4) * p, 2);
  });

  loc.players.forEach(p => {
    const cx = p.x * TILE + TILE / 2;
    const cy = p.y * TILE + TILE / 2;
    ctx.fillStyle = theme.shadow;
    ctx.beginPath();
    ctx.ellipse(cx, cy + TILE * 0.35, TILE * 0.3, TILE * 0.12, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#66b3ff';
    ctx.beginPath();
    ctx.arc(cx, cy, TILE / 2 - 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#0c0e10';
    ctx.font = 'bold 11px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(p.name.slice(0, 1).toUpperCase(), cx, cy + 1);
  });

  const cx = ST.displayMe.x * TILE + TILE / 2;
  const cy = ST.displayMe.y * TILE + TILE / 2;
  ctx.save();
  ctx.shadowColor = 'rgba(255, 209, 102, 0.8)';
  ctx.shadowBlur = 12;
  ctx.fillStyle = '#ffd166';
  ctx.beginPath();
  ctx.arc(cx, cy, TILE / 2 - 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
  ctx.strokeStyle = 'rgba(255,255,255,0.6)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(cx, cy, TILE / 2 - 3, 0, Math.PI * 2);
  ctx.stroke();
  ctx.fillStyle = '#0c0e10';
  ctx.font = 'bold 11px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(me.name.slice(0, 1).toUpperCase(), cx, cy + 1);

  drawLighting(loc, w, h);
  drawFilmGrain(w, h);

  if (ST.hoveredExit) {
    drawTooltip('🚪 ' + ST.hoveredExit.to_name, ST.hoveredExit.x, ST.hoveredExit.y);
  }
}

function drawTooltip(text, cellX, cellY) {
  ctx.save();
  ctx.font = 'bold 12px system-ui, sans-serif';
  const padding = 8;
  const tw = ctx.measureText(text).width + padding * 2;
  const th = 22;
  let tx = cellX * TILE + TILE / 2 - tw / 2;
  let ty = cellY * TILE - th - 6;
  if (tx < 4) tx = 4;
  if (tx + tw > canvas.width - 4) tx = canvas.width - tw - 4;
  if (ty < 4) ty = cellY * TILE + TILE + 6;
  ctx.fillStyle = 'rgba(20, 23, 26, 0.95)';
  ctx.strokeStyle = 'rgba(111, 174, 93, 0.9)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.rect(tx, ty, tw, th);
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = '#d7dde2';
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, tx + padding, ty + th / 2);
  ctx.restore();
}

// ==================== MINIMAP ====================
const WORLD_MAP = {
  'Бункер выживших':   { x: 0.50, y: 0.94, icon: '🏠', short: 'Бункер' },
  'Улица':             { x: 0.50, y: 0.76, icon: '🛣️', short: 'Улица' },
  'Аптека':            { x: 0.38, y: 0.76, icon: '💊', short: 'Аптека' },
  'Супермаркет':       { x: 0.62, y: 0.76, icon: '🛒', short: 'Маркет' },
  'Заправка':          { x: 0.26, y: 0.76, icon: '⛽', short: 'Заправка' },
  'Лесополоса':        { x: 0.14, y: 0.76, icon: '🌲', short: 'Лес' },
  'Парк':              { x: 0.03, y: 0.76, icon: '🌳', short: 'Парк' },
  'Кладбище':          { x: 0.14, y: 0.62, icon: '🪦', short: 'Погост' },
  'Радиовышка':        { x: 0.14, y: 0.48, icon: '📡', short: 'Радио' },
  'Отель «Приют»':     { x: 0.26, y: 0.62, icon: '🏨', short: 'Отель' },
  'Крыша отеля':       { x: 0.26, y: 0.48, icon: '🏙️', short: 'Крыша' },
  'Больница':          { x: 0.50, y: 0.58, icon: '🏥', short: 'Больница' },
  'Лаборатория':       { x: 0.50, y: 0.42, icon: '🧪', short: 'Лаба' },
  'Морг':              { x: 0.64, y: 0.58, icon: '⚰️', short: 'Морг' },
  'Метро':             { x: 0.40, y: 0.58, icon: '🚇', short: 'Метро' },
  'Канализация':       { x: 0.30, y: 0.48, icon: '🕳️', short: 'Каны' },
  'Школа':             { x: 0.76, y: 0.76, icon: '🏫', short: 'Школа' },
  'Кинотеатр':         { x: 0.64, y: 0.70, icon: '🎬', short: 'Кино' },
  'Подвал кинотеатра': { x: 0.76, y: 0.62, icon: '⬇️', short: 'Подвал' },
  'Военная база':      { x: 0.76, y: 0.50, icon: '🎖️', short: 'База' },
  'Аэропорт':          { x: 0.76, y: 0.30, icon: '✈️', short: 'Аэро' },
};

const WORLD_EDGES = [
  ['Бункер выживших', 'Улица'],
  ['Улица', 'Аптека'],
  ['Улица', 'Супермаркет'],
  ['Улица', 'Больница'],
  ['Аптека', 'Заправка'],
  ['Заправка', 'Лесополоса'],
  ['Заправка', 'Отель «Приют»'],
  ['Лесополоса', 'Парк'],
  ['Лесополоса', 'Кладбище'],
  ['Лесополоса', 'Радиовышка'],
  ['Отель «Приют»', 'Крыша отеля'],
  ['Супермаркет', 'Школа'],
  ['Супермаркет', 'Кинотеатр'],
  ['Кинотеатр', 'Подвал кинотеатра'],
  ['Школа', 'Военная база'],
  ['Военная база', 'Аэропорт'],
  ['Больница', 'Морг'],
  ['Больница', 'Лаборатория'],
  ['Больница', 'Метро'],
  ['Метро', 'Канализация'],
];

function drawMinimap(currentLoc) {
  const W = minimap.width, H = minimap.height;
  mctx.clearRect(0, 0, W, H);
  mctx.fillStyle = '#0c0e10';
  mctx.fillRect(0, 0, W, H);

  const pad = 26;
  const conv = (n) => ({ x: pad + n.x * (W - 2 * pad), y: pad + n.y * (H - 2 * pad) });

  mctx.strokeStyle = 'rgba(111, 174, 93, 0.35)';
  mctx.lineWidth = 2;
  WORLD_EDGES.forEach(([a, b]) => {
    const pa = WORLD_MAP[a], pb = WORLD_MAP[b];
    if (!pa || !pb) return;
    const A = conv(pa), B = conv(pb);
    mctx.beginPath();
    mctx.moveTo(A.x, A.y);
    mctx.lineTo(B.x, B.y);
    mctx.stroke();
  });

  Object.entries(WORLD_MAP).forEach(([name, n]) => {
    const p = conv(n);
    const isHere = currentLoc && name === currentLoc.name;
    const isSafe = name === 'Бункер выживших';

    mctx.beginPath();
    mctx.arc(p.x, p.y, isHere ? 11 : 7, 0, Math.PI * 2);
    mctx.fillStyle = isHere ? '#ffd166' : isSafe ? '#6fae5d' : '#3a4249';
    mctx.fill();
    mctx.strokeStyle = isHere ? '#ffffff' : 'rgba(255,255,255,0.25)';
    mctx.lineWidth = isHere ? 2 : 1;
    mctx.stroke();

    mctx.font = '11px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
    mctx.textAlign = 'center';
    mctx.textBaseline = 'middle';
    mctx.fillStyle = '#fff';
    mctx.fillText(n.icon, p.x, p.y + 0.5);

    if (isHere || isSafe) {
      mctx.font = isHere ? 'bold 10px system-ui' : '9px system-ui';
      mctx.fillStyle = isHere ? '#ffd166' : 'rgba(143,209,119,0.9)';
      mctx.fillText(n.short, p.x, p.y + 20);
    }
  });

  mctx.strokeStyle = 'rgba(255,255,255,0.06)';
  mctx.lineWidth = 1;
  mctx.strokeRect(0.5, 0.5, W - 1, H - 1);
}

// ==================== MOUSE ====================
function cellAt(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const cx = (e.clientX - rect.left) * scaleX;
  const cy = (e.clientY - rect.top) * scaleY;
  return { x: Math.floor(cx / TILE), y: Math.floor(cy / TILE) };
}

canvas.addEventListener('mousemove', (e) => {
  if (!ST.data) return;
  ST.hovered = cellAt(e);
  const loc = ST.data.location;
  ST.hoveredExit = (loc.exit_markers || []).find(
    x => x.x === ST.hovered.x && x.y === ST.hovered.y
  ) || null;
});

canvas.addEventListener('mouseleave', () => {
  ST.hovered = null;
  ST.hoveredExit = null;
});

canvas.addEventListener('click', (e) => {
  if (!ST.data) return;
  const loc = ST.data.location;
  const me = ST.data.character;
  const cell = cellAt(e);
  if (cell.x < 0 || cell.y < 0 || cell.x >= loc.grid_w || cell.y >= loc.grid_h) return;

  const exit = (loc.exit_markers || []).find(x => x.x === cell.x && x.y === cell.y);
  if (exit) {
    const dist = Math.abs(cell.x - me.x) + Math.abs(cell.y - me.y);
    if (dist <= 1) move(exit.direction);
    else toast('Подойди к маркеру перехода', true);
    return;
  }

  const z = loc.zombies.find(z => z.x === cell.x && z.y === cell.y);
  if (z) { startCombat(z.id); return; }

  const lp = (loc.loot_points || []).find(x => x.x === cell.x && x.y === cell.y);
  if (lp) {
    if (lp.state === 'looted') { toast('Уже обобрано', true); return; }
    const dist = Math.abs(cell.x - me.x) + Math.abs(cell.y - me.y);
    if (dist > 1) { toast('Подойди ближе', true); return; }
    pickupLoot(lp.id);
    return;
  }

  const obs = (loc.obstacles || []).find(o => o.x === cell.x && o.y === cell.y);
  if (obs && obs.kind !== 'door') {
    const labels = {
      wall: '🧱 Стена', barrel: '🛢️ Бочка', car: '🚗 Машина',
      crate: '📦 Ящик', fence: '🪵 Забор', window: '🪟 Окно',
    };
    toast(labels[obs.kind] || 'Препятствие', true);
    return;
  }

  const dx = cell.x - me.x;
  const dy = cell.y - me.y;
  if (Math.abs(dx) + Math.abs(dy) === 1) doStep(dx, dy);
});

// ==================== KEYBOARD ====================
document.addEventListener('keydown', (e) => {
  if (document.getElementById('game-screen').hidden) return;
  if (document.activeElement &&
      ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
    if (e.key === 'Escape') document.activeElement.blur();
    return;
  }

  if (!document.getElementById('combat-modal').hidden) {
    if (e.key === 'Escape') return;
    if (['1','2','3','4','5'].includes(e.key)) {
      e.preventDefault();
      const skillIndex = parseInt(e.key) - 1;
      const skillId = skillIndex === 0 ? null : (ST.skills[skillIndex - 1]?.id || null);
      const sel = document.getElementById('skill-select');
      if (sel) sel.value = skillId ? String(skillId) : '';
      document.getElementById('btn-attack')?.click();
      return;
    }
    if (e.key.toLowerCase() === 'r') { e.preventDefault(); document.getElementById('btn-auto')?.click(); return; }
    if (e.key.toLowerCase() === 'f') { e.preventDefault(); document.getElementById('btn-flee')?.click(); return; }
  }

  if (e.key === 'Escape') {
    ['shop-modal', 'quests-modal', 'trade-modal', 'craft-modal',
     'achievements-modal', 'auction-modal', 'pvp-modal',
     'duel-modal', 'duel-result-modal'].forEach(id => {
      const m = document.getElementById(id);
      if (m && !m.hidden) closeModal(id);
    });
    return;
  }

  const map = {
    w: [0, -1], a: [-1, 0], s: [0, 1], d: [1, 0],
    arrowup: [0, -1], arrowleft: [-1, 0], arrowdown: [0, 1], arrowright: [1, 0],
  };
  const d = map[e.key.toLowerCase()];
  if (!d) return;
  e.preventDefault();
  doStep(d[0], d[1]);
});
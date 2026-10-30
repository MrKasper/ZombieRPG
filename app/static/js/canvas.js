const TILE_THEMES = {
  street: { floorA: '#23262b', wall: '#0e1013' },
  gas: { floorA: '#2a2422', wall: '#100c0b' },
  park: { floorA: '#1f2a1c', wall: '#0b110a' },
  forest: { floorA: '#1c2818', wall: '#0a1108' },
  cemetery: { floorA: '#1d1d22', wall: '#0a0a0d' },
  rooftop: { floorA: '#22262b', wall: '#0d0f11' },
  tower: { floorA: '#241f24', wall: '#0c0a0c' },
  airport: { floorA: '#26241e', wall: '#0f0e0b' },
  bunker: { floorA: '#1e2a24', wall: '#0a100d' },
  pharmacy: { floorA: '#28232e', wall: '#100c14' },
  market: { floorA: '#2a2820', wall: '#100e0a' },
  hospital: { floorA: '#22262e', wall: '#0d0f14' },
  morgue: { floorA: '#1a1a24', wall: '#08080e' },
  school: { floorA: '#24242e', wall: '#0d0d14' },
  cinema: { floorA: '#261e26', wall: '#0f0a0f' },
  basement: { floorA: '#181818', wall: '#050505' },
  metro: { floorA: '#1c1c28', wall: '#08080e' },
  sewer: { floorA: '#1a261c', wall: '#070d08' },
  hotel: { floorA: '#262226', wall: '#0f0a0f' },
  lab: { floorA: '#1e2a2c', wall: '#080f10' },
  base: { floorA: '#26262a', wall: '#0d0d11' },
  _default: { floorA: '#22262b', wall: '#0b0d0f' },
};

function themeFor(loc) { return TILE_THEMES[loc.tilemap_id] || TILE_THEMES._default; }

function lootEmoji(kind) {
  return ({ car: '🚗', box: '📦', shelf: '🗄️', corpse: '💀', safe: '🔒', military_crate: '🔰', med_cabinet: '💊', fridge: '🧊', locker: '🗃️', toolbox: '🧰', airdrop: '🎁' })[kind] || '📦';
}

function exitEmoji(dir) {
  return ({ north: '⬆️', south: '⬇️', east: '➡️', west: '⬅️' })[dir] || '🚪';
}

function decoEmoji(kind) {
  return ({ tree: '🌲', dead_tree: '🪵', bush: '🌿', rock: '🪨', blood: '🩸', barrel: '🛢️', tire: '⭕', street_lamp: '💡', bench: '🪑', papers: '📄', glass: '💎', hydrant: '🚒', puddle: '💧', old_car: '🚙', corpse: '☠️', graffiti: '🎨', sign: '🪧', brick: '🧱', window: '🪟', chair: '💺', tv: '📺', mailbox: '📫', trash: '🗑️', plant: '🪴', flag: '🚩' })[kind] || '·';
}

function drawObstacle(b, o) {
  const px = o.x * TILE, py = o.y * TILE;
  if (o.kind === 'wall') {
    b.fillStyle = '#5a3a2a'; b.fillRect(px, py, TILE, TILE);
    b.strokeStyle = '#2a1508'; b.strokeRect(px+1, py+1, TILE-2, TILE-2);
  } else if (o.kind === 'door' || o.kind === 'door_locked') {
    b.fillStyle = '#0a0605'; b.fillRect(px+1, py+1, TILE-2, TILE-2);
    b.fillStyle = o.kind === 'door_locked' ? '#3a2010' : '#4a2a15'; b.fillRect(px+3, py+3, TILE-10, TILE-6);
    if (o.kind === 'door_locked') { b.fillStyle = '#d6a23d'; b.fillRect(px+TILE/2-3, py+TILE/2-2, 6, 6); }
  } else if (o.kind === 'car') {
    b.fillStyle = '#4a4a50'; b.fillRect(px+2, py+4, TILE-4, TILE-8);
    b.fillStyle = '#3a3a40'; b.fillRect(px+6, py+6, TILE-12, TILE-12);
  } else if (o.kind === 'barrel') {
    b.fillStyle = '#6a4a2a'; b.fillRect(px+4, py+4, TILE-8, TILE-8);
  } else if (o.kind === 'crate') {
    b.fillStyle = '#5a4030'; b.fillRect(px+3, py+3, TILE-6, TILE-6);
  }
}

const BG_CACHE = document.createElement('canvas');
let BG_CACHE_KEY = '';

function drawStaticLayer(loc) {
  const key = `${loc.id}:${loc.grid_w}x${loc.grid_h}:${loc.tilemap_id}:v2`;
  if (BG_CACHE_KEY === key) return BG_CACHE;

  const theme = themeFor(loc);
  BG_CACHE.width = loc.grid_w * TILE;
  BG_CACHE.height = loc.grid_h * TILE;
  const b = BG_CACHE.getContext('2d');
  const W = BG_CACHE.width, H = BG_CACHE.height;

  b.fillStyle = theme.floorA; b.fillRect(0, 0, W, H);

  // Сетка (едва заметная)
  b.strokeStyle = 'rgba(255,255,255,0.03)'; b.lineWidth = 1;
  for (let x = 0; x <= loc.grid_w; x++) { b.beginPath(); b.moveTo(x * TILE, 0); b.lineTo(x * TILE, H); b.stroke(); }
  for (let y = 0; y <= loc.grid_h; y++) { b.beginPath(); b.moveTo(0, y * TILE); b.lineTo(W, y * TILE); b.stroke(); }

  // Стены
  b.fillStyle = theme.wall;
  b.fillRect(0, 0, W, TILE); b.fillRect(0, H - TILE, W, TILE); b.fillRect(0, 0, TILE, H); b.fillRect(W - TILE, 0, TILE, H);

  // Декор
  b.font = '18px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
  b.textAlign = 'center'; b.textBaseline = 'middle';
  (loc.decorations || []).forEach(d => {
    b.globalAlpha = d.alpha ?? 0.6;
    b.fillText(decoEmoji(d.kind), d.x * TILE + TILE / 2, d.y * TILE + TILE / 2);
  });
  b.globalAlpha = 1;

  // Препятствия
  (loc.obstacles || []).forEach(o => drawObstacle(b, o));

  // Выходы
  (loc.exit_markers || []).forEach(e => {
    const cx = e.x * TILE + TILE / 2, cy = e.y * TILE + TILE / 2;
    b.fillStyle = 'rgba(111, 174, 93, 0.30)'; b.fillRect(e.x * TILE + 1, e.y * TILE + 1, TILE - 2, TILE - 2);
    b.strokeStyle = 'rgba(143, 209, 119, 0.9)'; b.lineWidth = 1.5; b.strokeRect(e.x * TILE + 1.5, e.y * TILE + 1.5, TILE - 3, TILE - 3);
    b.font = '14px "Segoe UI Emoji"'; b.fillText(exitEmoji(e.direction), cx, cy);
  });

  BG_CACHE_KEY = key;
  return BG_CACHE;
}

function drawWorld(loc, me) {
  const theme = themeFor(loc);
  const w = loc.grid_w * TILE, h = loc.grid_h * TILE;
  if (canvas.width !== w) canvas.width = w;
  if (canvas.height !== h) canvas.height = h;

  const bg = drawStaticLayer(loc);
  ctx.drawImage(bg, 0, 0);

  // Лут
  (loc.loot_points || []).forEach(lp => {
    if (lp.state === 'looted') return;
    const cx = lp.x * TILE + TILE / 2, cy = lp.y * TILE + TILE / 2;
    ctx.fillStyle = lp.kind === 'airdrop' ? `rgba(255, 200, 60, ${0.35 + 0.15 * Math.sin(Date.now() / 300)})` : 'rgba(214, 162, 61, 0.15)';
    ctx.fillRect(lp.x * TILE + 3, lp.y * TILE + 3, TILE - 6, TILE - 6);
    ctx.font = '16px "Segoe UI Emoji"'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(lootEmoji(lp.kind), cx, cy);
  });

  // Записки (Lore)
  (loc.lore_notes || []).forEach(n => {
    ctx.font = '16px "Segoe UI Emoji"'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText('📜', n.x * TILE + TILE/2, n.y * TILE + TILE/2);
  });

  // Hover
  if (ST.hovered) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.fillRect(ST.hovered.x * TILE, ST.hovered.y * TILE, TILE, TILE);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.strokeRect(ST.hovered.x * TILE + 0.5, ST.hovered.y * TILE + 0.5, TILE - 1, TILE - 1);
  }

  // Зомби
  loc.zombies.forEach(z => {
    const cx = z.x * TILE + TILE / 2, cy = z.y * TILE + TILE / 2;
    ctx.fillStyle = 'rgba(120, 180, 80, 0.18)'; ctx.fillRect(z.x * TILE + 2, z.y * TILE + 2, TILE - 4, TILE - 4);
    ctx.font = '18px "Segoe UI Emoji"'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(z.icon, cx, cy);
    const p = Math.max(0, Math.min(1, z.hp / z.max_hp));
    ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillRect(z.x * TILE + 2, z.y * TILE + TILE - 4, TILE - 4, 2);
    ctx.fillStyle = '#c94f4f'; ctx.fillRect(z.x * TILE + 2, z.y * TILE + TILE - 4, (TILE - 4) * p, 2);
  });

  // Игроки
  loc.players.forEach(p => {
    const cx = p.x * TILE + TILE / 2, cy = p.y * TILE + TILE / 2;
    ctx.fillStyle = '#66b3ff'; ctx.beginPath(); ctx.arc(cx, cy, TILE / 2 - 4, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#0c0e10'; ctx.font = 'bold 11px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(p.name[0].toUpperCase(), cx, cy + 1);
  });

  // Я
  const cx = ST.displayMe.x * TILE + TILE / 2, cy = ST.displayMe.y * TILE + TILE / 2;
  ctx.save(); ctx.shadowColor = 'rgba(255, 209, 102, 0.8)'; ctx.shadowBlur = 12;
  ctx.fillStyle = '#ffd166'; ctx.beginPath(); ctx.arc(cx, cy, TILE / 2 - 3, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  ctx.strokeStyle = 'rgba(255,255,255,0.6)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, TILE / 2 - 3, 0, Math.PI * 2); ctx.stroke();
  ctx.fillStyle = '#0c0e10'; ctx.font = 'bold 11px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(me.name[0].toUpperCase(), cx, cy + 1);

  // Виньетка
  const grad = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.35, w / 2, h / 2, Math.max(w, h) * 0.7);
  grad.addColorStop(0, 'rgba(0,0,0,0)'); grad.addColorStop(1, 'rgba(0,0,0,0.35)');
  ctx.fillStyle = grad; ctx.fillRect(0, 0, w, h);

  if (ST.hoveredExit) {
    drawTooltip('🚪 ' + ST.hoveredExit.to_name, ST.hoveredExit.x, ST.hoveredExit.y);
  }
}

function drawTooltip(text, cellX, cellY) {
  ctx.save(); ctx.font = 'bold 12px system-ui, sans-serif';
  const padding = 8, tw = ctx.measureText(text).width + padding * 2, th = 22;
  let tx = cellX * TILE + TILE / 2 - tw / 2, ty = cellY * TILE - th - 6;
  if (tx < 4) tx = 4; if (tx + tw > canvas.width - 4) tx = canvas.width - tw - 4; if (ty < 4) ty = cellY * TILE + TILE + 6;
  ctx.fillStyle = 'rgba(20, 23, 26, 0.95)'; ctx.strokeStyle = 'rgba(111, 174, 93, 0.9)'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.rect(tx, ty, tw, th); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#d7dde2'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(text, tx + padding, ty + th / 2);
  ctx.restore();
}

const WORLD_MAP = {
  'Бункер выживших': { x: 0.50, y: 0.94, icon: '🏠', short: 'Бункер' },
  'Улица': { x: 0.50, y: 0.76, icon: '🛣️', short: 'Улица' },
  'Аптека': { x: 0.38, y: 0.76, icon: '💊', short: 'Аптека' },
  'Супермаркет': { x: 0.62, y: 0.76, icon: '🛒', short: 'Маркет' },
  'Заправка': { x: 0.26, y: 0.76, icon: '⛽', short: 'Заправка' },
  'Лесополоса': { x: 0.14, y: 0.76, icon: '🌲', short: 'Лес' },
  'Парк': { x: 0.03, y: 0.76, icon: '🌳', short: 'Парк' },
  'Кладбище': { x: 0.14, y: 0.62, icon: '🪦', short: 'Погост' },
  'Радиовышка': { x: 0.14, y: 0.48, icon: '📡', short: 'Радио' },
  'Отель «Приют»': { x: 0.26, y: 0.62, icon: '🏨', short: 'Отель' },
  'Крыша отеля': { x: 0.26, y: 0.48, icon: '🏙️', short: 'Крыша' },
  'Больница': { x: 0.50, y: 0.58, icon: '🏥', short: 'Больница' },
  'Лаборатория': { x: 0.50, y: 0.42, icon: '🧪', short: 'Лаба' },
  'Морг': { x: 0.64, y: 0.58, icon: '⚰️', short: 'Морг' },
  'Метро': { x: 0.40, y: 0.58, icon: '🚇', short: 'Метро' },
  'Канализация': { x: 0.30, y: 0.48, icon: '🕳️', short: 'Каны' },
  'Школа': { x: 0.76, y: 0.76, icon: '🏫', short: 'Школа' },
  'Кинотеатр': { x: 0.64, y: 0.70, icon: '🎬', short: 'Кино' },
  'Подвал кинотеатра': { x: 0.76, y: 0.62, icon: '⬇️', short: 'Подвал' },
  'Военная база': { x: 0.76, y: 0.50, icon: '🎖️', short: 'База' },
  'Аэропорт': { x: 0.76, y: 0.30, icon: '✈️', short: 'Аэро' },
};

const WORLD_EDGES = [
  ['Бункер выживших', 'Улица'], ['Улица', 'Аптека'], ['Улица', 'Супермаркет'], ['Улица', 'Больница'],
  ['Аптека', 'Заправка'], ['Заправка', 'Лесополоса'], ['Заправка', 'Отель «Приют»'], ['Лесополоса', 'Парк'],
  ['Лесополоса', 'Кладбище'], ['Лесополоса', 'Радиовышка'], ['Отель «Приют»', 'Крыша отеля'], ['Супермаркет', 'Школа'],
  ['Супермаркет', 'Кинотеатр'], ['Кинотеатр', 'Подвал кинотеатра'], ['Школа', 'Военная база'], ['Военная база', 'Аэропорт'],
  ['Больница', 'Морг'], ['Больница', 'Лаборатория'], ['Больница', 'Метро'], ['Метро', 'Канализация'],
];

function drawMinimap(currentLoc) {
  const W = minimap.width, H = minimap.height;
  mctx.clearRect(0, 0, W, H); mctx.fillStyle = '#0c0e10'; mctx.fillRect(0, 0, W, H);
  const pad = 26; const conv = (n) => ({ x: pad + n.x * (W - 2 * pad), y: pad + n.y * (H - 2 * pad) });

  mctx.strokeStyle = 'rgba(111, 174, 93, 0.2)'; mctx.lineWidth = 2;
  WORLD_EDGES.forEach(([a, b]) => {
    const pa = WORLD_MAP[a], pb = WORLD_MAP[b]; if (!pa || !pb) return;
    const A = conv(pa), B = conv(pb); mctx.beginPath(); mctx.moveTo(A.x, A.y); mctx.lineTo(B.x, B.y); mctx.stroke();
  });

  const visitedIds = ST.data?.character?.visited_locations || [];

  Object.entries(WORLD_MAP).forEach(([name, n]) => {
    const p = conv(n);
    const isHere = currentLoc && name === currentLoc.name;
    const isSafe = name === 'Бункер выживших';

    if (!isHere && !isSafe && visitedIds.length < 5) {
       mctx.beginPath(); mctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
       mctx.fillStyle = 'rgba(255,255,255,0.05)'; mctx.fill(); return;
    }

    mctx.beginPath(); mctx.arc(p.x, p.y, isHere ? 11 : 7, 0, Math.PI * 2);
    mctx.fillStyle = isHere ? '#ffd166' : isSafe ? '#6fae5d' : '#3a4249'; mctx.fill();
    mctx.strokeStyle = isHere ? '#ffffff' : 'rgba(255,255,255,0.25)'; mctx.lineWidth = isHere ? 2 : 1; mctx.stroke();
    mctx.font = '11px "Segoe UI Emoji"'; mctx.textAlign = 'center'; mctx.textBaseline = 'middle'; mctx.fillStyle = '#fff'; mctx.fillText(n.icon, p.x, p.y + 0.5);
    if (isHere || isSafe) {
      mctx.font = isHere ? 'bold 10px system-ui' : '9px system-ui'; mctx.fillStyle = isHere ? '#ffd166' : 'rgba(143,209,119,0.9)'; mctx.fillText(n.short, p.x, p.y + 20);
    }
  });
}

function cellAt(e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width, scaleY = canvas.height / rect.height;
  const cx = (e.clientX - rect.left) * scaleX, cy = (e.clientY - rect.top) * scaleY;
  return { x: Math.floor(cx / TILE), y: Math.floor(cy / TILE) };
}

canvas.addEventListener('mousemove', (e) => {
  if (!ST.data) return;
  ST.hovered = cellAt(e);
  const loc = ST.data.location;
  ST.hoveredExit = (loc.exit_markers || []).find(x => x.x === ST.hovered.x && x.y === ST.hovered.y) || null;
});

canvas.addEventListener('mouseleave', () => { ST.hovered = null; ST.hoveredExit = null; });

canvas.addEventListener('click', (e) => {
  if (!ST.data) return;
  const loc = ST.data.location, me = ST.data.character;
  const cell = cellAt(e);
  if (cell.x < 0 || cell.y < 0 || cell.x >= loc.grid_w || cell.y >= loc.grid_h) return;

  const exit = (loc.exit_markers || []).find(x => x.x === cell.x && x.y === cell.y);
  if (exit) {
    const dist = Math.abs(cell.x - me.x) + Math.abs(cell.y - me.y);
    if (dist <= 1) move(exit.direction); else toast('Подойди к маркеру перехода', true);
    return;
  }

  const z = loc.zombies.find(z => z.x === cell.x && z.y === cell.y);
  if (z) { startCombat(z.id); return; }

  const lp = (loc.loot_points || []).find(x => x.x === cell.x && x.y === cell.y);
  if (lp) {
    if (lp.state === 'looted') { toast('Уже обобрано', true); return; }
    const dist = Math.abs(cell.x - me.x) + Math.abs(cell.y - me.y);
    if (dist > 1) { toast('Подойди ближе', true); return; }
    pickupLoot(lp.id); return;
  }

  const note = (loc.lore_notes || []).find(n => n.x === cell.x && n.y === cell.y);
  if (note) {
    const dist = Math.abs(cell.x - me.x) + Math.abs(cell.y - me.y);
    if (dist > 1) { toast('Подойди ближе', true); return; }
    toast(`📜 ${note.title}: ${note.text}`, false); return;
  }

  const obs = (loc.obstacles || []).find(o => o.x === cell.x && o.y === cell.y);
  if (obs && obs.kind !== 'door') {
    if (obs.kind === 'door_locked') {
      const dist = Math.abs(cell.x - me.x) + Math.abs(cell.y - me.y);
      if (dist === 1) doStep(cell.x - me.x, cell.y - me.y);
      else toast('Подойди к двери', true);
      return;
    }
    toast('Препятствие', true); return;
  }

  const dx = cell.x - me.x, dy = cell.y - me.y;
  if (Math.abs(dx) + Math.abs(dy) === 1) doStep(dx, dy);
});

document.addEventListener('keydown', (e) => {
  if (document.getElementById('game-screen').hidden) return;
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
    if (e.key === 'Escape') document.activeElement.blur(); return;
  }

  if (!document.getElementById('combat-modal').hidden) {
    if (e.key === 'Escape') return;
    if (['1','2','3','4','5'].includes(e.key)) {
      e.preventDefault();
      const skillIndex = parseInt(e.key) - 1;
      const skillId = skillIndex === 0 ? null : (ST.skills[skillIndex - 1]?.id || null);
      const sel = document.getElementById('skill-select');
      if (sel) sel.value = skillId ? String(skillId) : '';
      document.getElementById('btn-attack')?.click(); return;
    }
    if (e.key.toLowerCase() === 'r') { e.preventDefault(); document.getElementById('btn-auto')?.click(); return; }
    if (e.key.toLowerCase() === 'f') { e.preventDefault(); document.getElementById('btn-flee')?.click(); return; }
  }

  if (e.key === 'Escape') {
    ['shop-modal', 'quests-modal', 'trade-modal', 'craft-modal', 'achievements-modal', 'auction-modal', 'pvp-modal', 'duel-modal', 'duel-result-modal', 'factions-modal'].forEach(id => {
      const m = document.getElementById(id); if (m && !m.hidden) closeModal(id);
    }); return;
  }

  const map = { w: [0, -1], a: [-1, 0], s: [0, 1], d: [1, 0], arrowup: [0, -1], arrowleft: [-1, 0], arrowdown: [0, 1], arrowright: [1, 0] };
  const d = map[e.key.toLowerCase()];
  if (!d) return; e.preventDefault(); doStep(d[0], d[1]);
});
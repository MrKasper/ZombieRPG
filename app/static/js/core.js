const ST = {
  data: null, inventory: [], skills: [],
  chatTab: 'location',
  pollTimer: null, toastTimer: null,
  currentShopNpc: null, currentShopData: null, shopTab: 'buy',
  craftRecipes: [],
  hovered: null, hoveredExit: null, busyStep: false,
  lastWasInCombat: false, displayMe: { x: 0, y: 0 },
  lastLevel: null, lastHp: null, soundEnabled: true,
  knownAchievements: new Set(),
  auctionTab: 'buy', auctionList: [], auctionMine: [],
  activeDuelId: null, shownDuelResultId: null, pvpLeaders: [],
};

const TILE = 24;
const canvas = document.getElementById('game-canvas');
const ctx = canvas.getContext('2d');
const minimap = document.getElementById('minimap-canvas');
const mctx = minimap.getContext('2d');

const EQUIP_SLOTS = [
  { slot: 'head', icon: '🪖', label: 'Голова' },
  { slot: 'body', icon: '👕', label: 'Тело' },
  { slot: 'legs', icon: '👖', label: 'Ноги' },
  { slot: 'feet', icon: '👟', label: 'Обувь' },
  { slot: 'weapon', icon: '⚔️', label: 'Оружие' },
  { slot: 'accessory_1', icon: '💍', label: 'Акс.' },
];

let audioCtx = null;
function ensureAudio() {
  if (!audioCtx) {
    try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { audioCtx = null; }
  }
  return audioCtx;
}

function playTone({ freq = 440, type = 'square', duration = 0.08, volume = 0.06, endFreq = null, delay = 0 }) {
  if (!ST.soundEnabled) return;
  const ac = ensureAudio();
  if (!ac) return;
  const t0 = ac.currentTime + delay;
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t0);
  if (endFreq !== null) osc.frequency.linearRampToValueAtTime(endFreq, t0 + duration);
  gain.gain.setValueAtTime(0, t0);
  gain.gain.linearRampToValueAtTime(volume, t0 + 0.01);
  gain.gain.linearRampToValueAtTime(0, t0 + duration);
  osc.connect(gain).connect(ac.destination);
  osc.start(t0); osc.stop(t0 + duration + 0.05);
}

function playSound(name) {
  switch (name) {
    case 'step': playTone({ freq: 160, endFreq: 100, duration: 0.04, volume: 0.03 }); break;
    case 'hit': playTone({ freq: 380, endFreq: 120, type: 'sawtooth', duration: 0.12, volume: 0.06 }); break;
    case 'zombie_hit': playTone({ freq: 90, endFreq: 60, duration: 0.15, volume: 0.05 }); break;
    case 'loot': playTone({ freq: 600, endFreq: 1000, type: 'sine', duration: 0.10, volume: 0.05 }); break;
    case 'empty': playTone({ freq: 300, endFreq: 200, type: 'sine', duration: 0.10, volume: 0.04 }); break;
    case 'error': playTone({ freq: 220, endFreq: 160, duration: 0.15, volume: 0.05 }); break;
    case 'levelup':
      playTone({ freq: 523, duration: 0.10, volume: 0.06, type: 'sine' });
      playTone({ freq: 659, duration: 0.10, volume: 0.06, type: 'sine', delay: 0.10 });
      playTone({ freq: 784, duration: 0.18, volume: 0.06, type: 'sine', delay: 0.20 });
      break;
    case 'victory':
      playTone({ freq: 523, duration: 0.08, type: 'square', volume: 0.05 });
      playTone({ freq: 659, duration: 0.08, type: 'square', volume: 0.05, delay: 0.10 });
      playTone({ freq: 1046, duration: 0.20, type: 'square', volume: 0.05, delay: 0.22 });
      break;
    case 'death': playTone({ freq: 300, endFreq: 80, type: 'sawtooth', duration: 0.6, volume: 0.06 }); break;
    case 'duel': playTone({ freq: 440, endFreq: 660, type: 'sawtooth', duration: 0.18, volume: 0.06 }); break;
  }
}

document.getElementById('sound-btn').onclick = () => {
  ST.soundEnabled = !ST.soundEnabled;
  document.getElementById('sound-btn').textContent = ST.soundEnabled ? '🔊' : '🔇';
};

async function api(path, opts = {}) {
  const res = await fetch('/api' + path, {
    method: opts.method || 'GET',
    headers: { 'Content-Type': 'application/json' },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: 'include',
  });
  let data = {};
  try { data = await res.json(); } catch (e) {}
  return { ok: res.ok, data };
}

function errorText(code) {
  return ({
    unauthorized: 'Сессия истекла', invalid_credentials: 'Неверный логин или пароль',
    username_taken: 'Логин уже занят', name_taken: 'Имя персонажа занято',
    username_length: 'Логин 3-32 символа', password_short: 'Пароль от 6 символов',
    name_length: 'Имя 2-32 символа', cooldown: 'Подожди немного',
    not_enough_mp: 'Мало MP', skill_cooldown: 'Скилл на кулдауне',
    in_combat: 'Нельзя уйти в бою', zombie_busy: 'Зомби занят другим игроком',
    zombie_dead: 'Зомби уже мёртв', already_in_combat: 'Ты уже в бою',
    already_in_party: 'Ты уже в партии', party_full: 'Партия заполнена',
    no_exit: 'Туда не пройти', too_far_from_exit: 'Подойди к маркеру перехода',
    not_a_merchant: 'Это не торговец', npc_not_here: 'NPC не здесь',
    not_in_stock: 'Нет в наличии', not_enough_stock: 'Недостаточно на складе',
    not_enough_gold: 'Не хватает золота', unequip_first: 'Сначала сними предмет',
    not_enough_quantity: 'Недостаточно предметов', not_complete: 'Квест не выполнен',
    not_active: 'Квест не активен', already_taken: 'Квест уже взят',
    already_learned: 'Скилл уже изучен', nothing_happens: 'Ничего не произошло',
    not_usable: 'Нельзя использовать', not_equippable: 'Нельзя надеть',
    no_slot: 'Нет слота', empty_slot: 'Слот пуст', not_found: 'Не найдено',
    not_participant: 'Ты не участник', trade_closed: 'Обмен закрыт',
    not_same_location: 'Вы в разных локациях', trade_only_in_safe_zone: 'Торговля только в безопасной зоне',
    not_leader: 'Только лидер может это делать', party_gone: 'Партия распалась',
    target_in_party: 'Уже в партии', already_invited: 'Уже приглашён',
    self_invite: 'Нельзя пригласить себя', self_trade: 'Нельзя торговать с собой',
    no_such_character: 'Персонаж не найден', bad_qty: 'Неверное количество',
    bad_message: 'Пустое сообщение', bad_scope: 'Неверный канал',
    no_points: 'Нет очков', unknown_stat: 'Неизвестный стат',
    not_in_party: 'Ты не в партии', not_in_combat: 'Ты не в бою',
    combat_finished: 'Бой уже окончен', not_learned: 'Не изучено',
    no_start_location: 'Мир не засеян. Запусти: python run.py --reset',
    out_of_bounds: 'За границей карты', cell_blocked: 'Клетка занята',
    bad_step: 'Неверный шаг', not_here: 'Не здесь', already_looted: 'Уже обобрано',
    too_far: 'Подойди ближе', quest_broken: 'Квест повреждён',
    no_crafter_here: 'Здесь нет мастерской', missing_ingredients: 'Не хватает материалов',
    stunned: 'Оглушён — пропуск хода', too_late: 'Уже поздно — труп исчез',
    prereq_not_done: 'Сначала сдай предыдущий квест', bad_price: 'Неверная цена',
    too_many_lots: 'Слишком много лотов (макс. 10)', auction_closed: 'Лот больше не активен',
    auction_expired: 'Лот истёк', own_auction: 'Нельзя купить свой лот',
    not_your_auction: 'Это не твой лот', self_duel: 'Нельзя дуэлировать с собой',
    duel_only_in_safe_zone: 'Дуэли только в безопасной зоне',
    duel_closed: 'Дуэль закрыта', duel_expired: 'Вызов истёк',
    not_your_duel: 'Это не твой вызов', not_salvageable: 'Нельзя разобрать',
  }[code] || code || 'Ошибка');
}

function toast(msg, isErr = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.toggle('err', isErr);
  el.hidden = false;
  if (isErr) playSound('error');
  clearTimeout(ST.toastTimer);
  ST.toastTimer = setTimeout(() => { el.hidden = true; }, 2400);
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function flashDamage() {
  const el = document.getElementById('damage-flash');
  if (!el) return;
  el.classList.remove('active'); void el.offsetWidth; el.classList.add('active');
  setTimeout(() => el.classList.remove('active'), 180);
}

function flashLevelUp() {
  const el = document.getElementById('levelup-flash');
  if (!el) return;
  el.classList.remove('active'); void el.offsetWidth; el.classList.add('active');
  setTimeout(() => el.classList.remove('active'), 1300);
}
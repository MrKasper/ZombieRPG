document.querySelectorAll('.auth-tabs button').forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll('.auth-tabs button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('login-form').hidden = btn.dataset.tab !== 'login';
    document.getElementById('register-form').hidden = btn.dataset.tab !== 'register';
    document.getElementById('auth-error').textContent = '';
  };
});

document.getElementById('login-form').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const { ok, data } = await api('/auth/login', { method: 'POST', body: { username: fd.get('username'), password: fd.get('password') } });
  if (ok) startGame(); else document.getElementById('auth-error').textContent = errorText(data.error);
};

document.getElementById('register-form').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const { ok, data } = await api('/auth/register', { method: 'POST', body: { username: fd.get('username'), password: fd.get('password'), name: fd.get('name') } });
  if (ok) startGame(); else document.getElementById('auth-error').textContent = errorText(data.error);
};

document.getElementById('logout-btn').onclick = async () => {
  await api('/auth/logout', { method: 'POST' });
  showAuth();
};

async function checkAuth() {
  const { data } = await api('/auth/me');
  data.authenticated ? startGame() : showAuth();
}

function showAuth() {
  if (ST.pollTimer) { clearInterval(ST.pollTimer); ST.pollTimer = null; }
  document.getElementById('auth-screen').hidden = false;
  document.getElementById('game-screen').hidden = true;
  ['combat-modal', 'shop-modal', 'quests-modal', 'trade-modal', 'craft-modal', 'achievements-modal', 'auction-modal', 'pvp-modal', 'duel-modal', 'duel-result-modal', 'factions-modal'].forEach(id => {
    const el = document.getElementById(id); if (el) el.hidden = true;
  });
}

function startGame() {
  document.getElementById('auth-screen').hidden = true;
  document.getElementById('game-screen').hidden = false;
  ST.lastWasInCombat = false; ST.displayMe._init = false;
  refreshAll();
  if (ST.pollTimer) clearInterval(ST.pollTimer);
  ST.pollTimer = setInterval(refreshAll, 1500);
  requestAnimationFrame(animationLoop);
}

async function refreshAll() {
  const [s, inv, sk] = await Promise.all([api('/state'), api('/inventory'), api('/skills')]);
  if (!s.ok) {
    if (s.data && s.data.error === 'unauthorized') { showAuth(); return; }
    toast('Ошибка сервера: ' + (s.data?.error || 'unknown'), true); return;
  }

  const wasInCombat = ST.lastWasInCombat;
  const oldLevel = ST.lastLevel;
  const oldHp = ST.lastHp;

  ST.data = s.data;
  ST.inventory = inv.ok ? inv.data.items || [] : [];
  ST.skills = sk.ok ? sk.data.skills || [] : [];

  const isInCombat = !!(ST.data?.combat?.is_active);
  ST.lastWasInCombat = isInCombat;
  ST.lastLevel = ST.data.character.level;
  ST.lastHp = ST.data.character.hp;

  if (!wasInCombat && isInCombat && ST.data?.combat?.zombie) {
    toast(`🧟 ${ST.data.combat.zombie.name} нападает!`, true); playSound('zombie_hit');
  }
  if (oldHp !== null && ST.lastHp < oldHp) { flashDamage(); playSound('zombie_hit'); }
  if (oldLevel !== null && ST.lastLevel > oldLevel) {
    playSound('levelup'); toast(`✨ Уровень ${ST.lastLevel}!`); flashLevelUp();
  }

  const newAch = (ST.data.achievements?.new_unlocks || []).filter(a => !ST.knownAchievements.has(a.id));
  newAch.forEach(a => { ST.knownAchievements.add(a.id); toast(`🏆 Достижение: ${a.name}`); playSound('levelup'); });

  handleDuelState(ST.data.pvp);

  if (!ST.displayMe._init) {
    ST.displayMe.x = ST.data.character.x; ST.displayMe.y = ST.data.character.y; ST.displayMe._init = true;
  }

  render();

  if (!document.getElementById('auction-modal').hidden) loadAuction();
  if (!document.getElementById('trade-modal').hidden) loadTrade();
}

function animationLoop() {
  if (ST.data && ST.data.character) {
    const target = ST.data.character, speed = 0.28;
    ST.displayMe.x += (target.x - ST.displayMe.x) * speed;
    ST.displayMe.y += (target.y - ST.displayMe.y) * speed;
    if (Math.abs(ST.displayMe.x - target.x) < 0.01) ST.displayMe.x = target.x;
    if (Math.abs(ST.displayMe.y - target.y) < 0.01) ST.displayMe.y = target.y;
    drawWorld(ST.data.location, target);
  }
  requestAnimationFrame(animationLoop);
}
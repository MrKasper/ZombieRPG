function render() {
  if (!ST.data) return;
  const d = ST.data;
  renderCharacter(d.character);
  renderLocation(d.location, d.character);
  renderEquipment();
  renderInventory();
  renderChat(d.chat);
  renderParty(d.party, d.party_invites || []);
  renderCombat(d.combat);
  drawMinimap(d.location);
  renderEvents(d.events || []);
  renderQuestTracker(d.quests_summary);
  updateAuctionBadge();
}

function pct(v, m) { return Math.min(100, Math.round(100 * v / Math.max(1, m))); }

function renderCharacter(c) {
  document.getElementById('char-name').textContent = c.name;
  const titleEl = document.getElementById('char-title');
  if (titleEl) titleEl.textContent = c.title || 'Выживший';

  document.getElementById('char-level').textContent = 'Lv ' + c.level;
  document.getElementById('hp-bar').style.width = pct(c.hp, c.stats.max_hp) + '%';
  document.getElementById('hp-text').textContent = `${c.hp}/${c.stats.max_hp}`;
  document.getElementById('mp-bar').style.width = pct(c.mp, c.stats.max_mp) + '%';
  document.getElementById('mp-text').textContent = `${c.mp}/${c.stats.max_mp}`;
  document.getElementById('xp-bar').style.width = (c.xp_next ? pct(c.xp, c.xp_next) : 100) + '%';
  document.getElementById('xp-text').textContent = c.xp_next ? `${c.xp}/${c.xp_next}` : 'MAX';
  document.getElementById('char-attack').textContent = c.stats.attack;
  document.getElementById('char-defense').textContent = c.stats.defense;
  document.getElementById('char-gold').textContent = c.gold;

  // ВЫЖИВАНИЕ
  const hb = document.getElementById('hunger-bar');
  if (hb) hb.style.width = (c.hunger || 0) + '%';
  const tb = document.getElementById('thirst-bar');
  if (tb) tb.style.width = (c.thirst || 0) + '%';
  const tt = document.getElementById('temp-text');
  if (tt) tt.textContent = (c.temperature || 36.6).toFixed(1) + '°';

  const sp = document.getElementById('char-stat-points');
  const sa = document.getElementById('stat-allocate');
  if(sp) sp.hidden = c.stat_points <= 0;
  if(sa) sa.hidden = c.stat_points <= 0;
  if (c.stat_points > 0 && sp) sp.textContent = 'Очки: ' + c.stat_points;
}

function renderQuestTracker(summary) {
  const list = document.getElementById('active-quests-list');
  if (!list || !summary) return;
  if (summary.active_count === 0) {
    list.innerHTML = '<li class="hint">Нет активных квестов</li>';
    return;
  }
  list.innerHTML = `<li>Активных: <b>${summary.active_count}</b></li>`;
  if (summary.ready_count > 0) {
    list.innerHTML += `<li style="color: var(--accent-2)">🎁 Готовы к сдаче: <b>${summary.ready_count}</b></li>`;
  }
}

function renderEquipment() {
  const grid = document.getElementById('equip-grid');
  if (!grid) return;
  const bySlot = {};
  ST.inventory.forEach(inv => { if (inv.equipped_slot) bySlot[inv.equipped_slot] = inv; });
  grid.innerHTML = '';
  EQUIP_SLOTS.forEach(defn => {
    const inv = bySlot[defn.slot];
    const div = document.createElement('div');
    div.className = 'equip-slot' + (inv ? ' filled' : '');
    div.innerHTML = inv ? `<div class="equip-icon">${inv.icon}</div><div class="equip-name">${escapeHtml(inv.name)}</div>`
                        : `<div class="equip-icon">${defn.icon}</div><div class="equip-name">${defn.label}</div>`;
    if (inv) div.onclick = () => unequip(defn.slot);
    grid.appendChild(div);
  });
}

function renderInventory() {
  const ul = document.getElementById('inv-list');
  ul.innerHTML = '';
  const unequipped = ST.inventory.filter(i => !i.equipped_slot);
  if (unequipped.length === 0) { ul.innerHTML = '<li class="hint">Пусто</li>'; return; }

  unequipped.forEach(inv => {
    const li = document.createElement('li');
    li.innerHTML = `<div class="inv-item-head"><span class="name rarity-${inv.rarity}">${inv.icon} ${inv.name}${inv.quantity > 1 ? ` ×${inv.quantity}` : ''}</span></div>`;
    const actions = document.createElement('div');
    actions.className = 'inv-item-actions';

    if (['weapon', 'armor', 'accessory'].includes(inv.type)) {
      const b = document.createElement('button'); b.textContent = 'Надеть'; b.onclick = () => equipItem(inv.id); actions.appendChild(b);
      const s = document.createElement('button'); s.textContent = '⚒️ Разобрать'; s.onclick = () => salvageItem(inv.id); actions.appendChild(s);
    }
    if (['consumable', 'book'].includes(inv.type)) {
      const b = document.createElement('button'); b.textContent = inv.type === 'book' ? 'Прочесть' : 'Исп.'; b.onclick = () => useItem(inv.id); actions.appendChild(b);
    }
    const drop = document.createElement('button'); drop.textContent = 'Выбросить'; drop.onclick = () => dropItem(inv.id); actions.appendChild(drop);

    li.appendChild(actions);
    ul.appendChild(li);
  });
}

function renderChat(chat) {
  const box = document.getElementById('chat-messages');
  box.innerHTML = '';
  (chat[ST.chatTab] || []).forEach(m => {
    box.innerHTML += `<div><span class="msg-name">${escapeHtml(m.name)}:</span> ${escapeHtml(m.message)}</div>`;
  });
  box.scrollTop = box.scrollHeight;
}

function renderCombat(c) {
  const modal = document.getElementById('combat-modal');
  if (!c) { modal.hidden = true; return; }
  modal.hidden = false;
  // (упрощено)
}

function renderLocation(loc) {
  document.getElementById('loc-name').textContent = loc.name;
  document.getElementById('loc-desc').textContent = loc.description;
}

function renderEvents(events) {
  const bar = document.getElementById('event-bar');
  if (!events || events.length === 0) { bar.hidden = true; return; }
  bar.hidden = false;
  bar.innerHTML = events.map(ev => `<span class="event-badge event-${ev.type}">${ev.type} · ${ev.seconds_left}с</span>`).join(' ');
}

function updateAuctionBadge() {
  const n = ST.data?.auction_active_count || 0;
  const badge = document.getElementById('auction-badge');
  if (badge) { badge.textContent = n; badge.hidden = n === 0; }
}
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
  renderQuestTracker(d.active_quests || []);
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
  document.getElementById('char-evasion').textContent = c.stats.evasion || 0;
  document.getElementById('char-gold').textContent = c.gold;

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

function renderLocation(loc, me) {
  document.getElementById('loc-name').textContent = loc.name;
  document.getElementById('loc-desc').textContent = loc.description;

  const pl = document.getElementById('loc-players');
  pl.innerHTML = '';
  loc.players.forEach(p => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${escapeHtml(p.name)} <span class="hint">Lv${p.level}</span></span>`;
    const invBtn = document.createElement('button'); invBtn.textContent = 'Пригласить'; invBtn.onclick = () => inviteToParty(p.id); li.appendChild(invBtn);
    if (loc.is_safe_zone) {
      const trBtn = document.createElement('button'); trBtn.textContent = '🤝'; trBtn.title = 'Торговать'; trBtn.onclick = () => startTrade(p.id); li.appendChild(trBtn);
      const duelBtn = document.createElement('button'); duelBtn.textContent = '⚔️'; duelBtn.title = 'Вызвать на дуэль'; duelBtn.onclick = () => challengeDuel(p.id); li.appendChild(duelBtn);
    }
    pl.appendChild(li);
  });
  document.getElementById('loc-players-block').hidden = loc.players.length === 0;

  const nl = document.getElementById('loc-npcs');
  nl.innerHTML = '';
  loc.npcs.forEach(n => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${n.icon} ${escapeHtml(n.name)} <span class="hint">${n.role}</span></span>`;
    const btn = document.createElement('button');
    if (n.role === 'merchant') { btn.textContent = '🛒'; btn.title = 'Магазин'; btn.onclick = () => openShop(n.id); }
    else if (n.role === 'crafter') { btn.textContent = '🛠️'; btn.title = 'Мастерская'; btn.onclick = () => openCraft(); }
    else if (n.role === 'quest_giver') { btn.textContent = '📜'; btn.title = 'Квесты'; btn.onclick = () => openQuests(n.id); } // Передаем n.id
    else { btn.textContent = '...'; }
    li.appendChild(btn);
    nl.appendChild(li);
  });
  document.getElementById('loc-npcs-block').hidden = loc.npcs.length === 0;
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
    div.dataset.slot = defn.slot;
    if (inv) div.dataset.rarity = inv.rarity || 'common';

    if (inv) {
      div.innerHTML = `<div class="equip-icon">${inv.icon}</div><div class="equip-name">${escapeHtml(inv.name)}</div>`;
      div.title = `${inv.name}\nКлик — снять`;
      div.onclick = () => unequip(defn.slot);
    } else {
      div.innerHTML = `<div class="equip-icon">${defn.icon}</div><div class="equip-name">${defn.label}</div>`;
      div.title = `${defn.label} — пусто`;
    }
    grid.appendChild(div);
  });
}

function renderInventory() {
  const ul = document.getElementById('inv-list');
  ul.innerHTML = '';
  const unequipped = ST.inventory.filter(i => !i.equipped_slot);
  if (unequipped.length === 0) { ul.innerHTML = '<li class="hint">Пусто</li>'; return; }
  const shopHere = ST.data?.location?.npcs?.find(n => n.role === 'merchant');

  unequipped.forEach(inv => {
    const li = document.createElement('li');
    li.innerHTML = `<div class="inv-item-head"><span class="name rarity-${inv.rarity}">${inv.icon || '📦'} ${inv.name}${inv.quantity > 1 ? ` ×${inv.quantity}` : ''}</span></div>`;
    const actions = document.createElement('div');
    actions.className = 'inv-item-actions';

    if (['weapon', 'armor', 'accessory'].includes(inv.type)) {
      const b = document.createElement('button'); b.textContent = 'Надеть'; b.onclick = () => equipItem(inv.id); actions.appendChild(b);
      const s = document.createElement('button'); s.textContent = '⚒️ Разобрать'; s.onclick = () => salvageItem(inv.id); actions.appendChild(s);
    }
    if (['consumable', 'book'].includes(inv.type)) {
      const b = document.createElement('button'); b.textContent = inv.type === 'book' ? 'Прочесть' : 'Исп.'; b.onclick = () => useItem(inv.id); actions.appendChild(b);
    }
    if (shopHere) {
      const sellBtn = document.createElement('button'); sellBtn.textContent = '💰'; sellBtn.title = 'Продать'; sellBtn.onclick = () => shopSell(shopHere.id, inv.id); actions.appendChild(sellBtn);
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
    const div = document.createElement('div');
    div.innerHTML = `<span class="msg-name">${escapeHtml(m.name)}:</span> ${escapeHtml(m.message)}`;
    box.appendChild(div);
  });
  box.scrollTop = box.scrollHeight;
}

function renderParty(party, invites) {
  const body = document.getElementById('party-body');
  const actions = document.getElementById('party-actions');
  const invBox = document.getElementById('party-invites');
  body.innerHTML = ''; actions.innerHTML = ''; invBox.innerHTML = '';

  if (!party) {
    body.textContent = 'Нет партии';
    const b = document.createElement('button'); b.textContent = 'Создать партию'; b.onclick = createParty; actions.appendChild(b);
  } else {
    const ul = document.createElement('ul'); ul.className = 'list';
    party.members.forEach(m => {
      const li = document.createElement('li');
      const leader = m.id === party.leader_id ? '👑 ' : '';
      li.innerHTML = `<span>${leader}${escapeHtml(m.name)} Lv${m.level}</span><span class="hint">${m.hp}/${m.max_hp}</span>`;
      ul.appendChild(li);
    });
    body.appendChild(ul);
    const leave = document.createElement('button'); leave.textContent = 'Покинуть партию'; leave.onclick = leaveParty; actions.appendChild(leave);
  }

  (invites || []).forEach(inv => {
    const div = document.createElement('div');
    div.className = 'row'; div.style.marginTop = '6px';
    div.innerHTML = `<span style="flex:1">Приглашение от ${escapeHtml(inv.from_name)}</span>`;
    const acc = document.createElement('button'); acc.textContent = 'Принять'; acc.onclick = () => acceptInvite(inv.id);
    const dec = document.createElement('button'); dec.textContent = 'Отклонить'; dec.onclick = () => declineInvite(inv.id);
    div.appendChild(acc); div.appendChild(dec); invBox.appendChild(div);
  });
}

function renderCombat(c) {
  const modal = document.getElementById('combat-modal');
  if (!c) { modal.hidden = true; return; }
  modal.hidden = false;

  const z = c.zombie;
  document.getElementById('combat-zombie-icon').textContent = z.icon;
  document.getElementById('combat-zombie-name').textContent = z.name;
  const atkLabel = { normal: '', fast: ' ⚡быстрый', poison: ' ☠️яд', stun: ' 💫стан', aoe: ' 💥AoE' }[z.attack_type || 'normal'] || '';
  document.getElementById('combat-zombie-lvl').textContent = 'Lv ' + z.level + atkLabel;
  document.getElementById('combat-zombie-hp-bar').style.width = pct(z.hp, z.max_hp) + '%';
  document.getElementById('combat-zombie-hp-text').textContent = `${z.hp}/${z.max_hp}`;
  document.getElementById('combat-next-attack').textContent = c.is_active ? `Удар через ${c.next_zombie_attack_in}с` : '';

  const parts = document.getElementById('combat-participants');
  parts.innerHTML = '';
  c.participants.forEach(p => {
    const div = document.createElement('div');
    div.className = 'participant' + (p.is_dead ? ' dead' : '') + (p.is_me ? ' me' : '');
    div.innerHTML = `<b>${escapeHtml(p.name)}</b>${p.auto_mode ? ' 🤖' : ''}<br>
      <span class="bar bar-hp small" style="display:block"><div style="width:${pct(p.hp, p.max_hp)}%;background:var(--hp);height:100%"></div></span>
      <span class="hint">${p.hp}/${p.max_hp}</span>`;
    parts.appendChild(div);
  });

  const log = document.getElementById('combat-log');
  log.innerHTML = c.log.map(line => `<div>${escapeHtml(line)}</div>`).join('');
  log.scrollTop = log.scrollHeight;

  const sel = document.getElementById('skill-select');
  const prev = sel.value;
  sel.innerHTML = '<option value="">Обычная атака</option>';
  ST.skills.forEach((s, idx) => {
    if (s.effect_type !== 'damage') return;
    const opt = document.createElement('option');
    opt.value = s.id;
    const cdLeft = s.cooldown_until ? Math.max(0, Math.round((new Date(s.cooldown_until) - new Date()) / 1000)) : 0;
    opt.textContent = `${idx + 2}: ${s.icon} ${s.name} (${s.mp_cost} MP)` + (cdLeft > 0 ? ` — ${cdLeft}с` : '');
    opt.disabled = cdLeft > 0;
    sel.appendChild(opt);
  });
  if (prev) sel.value = prev;

  const me = c.participants.find(p => p.is_me);
  document.getElementById('combat-controls').hidden = !c.is_active;
  document.getElementById('combat-result').hidden = c.is_active;

  if (c.is_active && me) {
    const cd = me.action_cd_remaining || 0;
    const atk = document.getElementById('btn-attack');
    atk.disabled = cd > 0;
    atk.textContent = cd > 0 ? `⏳ ${cd.toFixed(1)}с` : '⚔ Атака (1)';
    const auto = document.getElementById('btn-auto');
    auto.textContent = me.auto_mode ? '🤖 Автобой: ВКЛ' : '🤖 Автобой (R)';
    auto.classList.toggle('btn-primary', me.auto_mode);
  }
}

function renderEvents(events) {
  const bar = document.getElementById('event-bar');
  if (!events || events.length === 0) { bar.hidden = true; return; }
  bar.hidden = false;
  bar.innerHTML = events.map(ev => {
    const labels = { airdrop: '📦 Аирдроп', zombie_night: '🌙 Ночь зомби', bounty: '🎯 Награда за голову' };
    let text = labels[ev.type] || ev.type;
    if (ev.location) text += ' — ' + ev.location.name;
    if (ev.type === 'bounty' && ev.zombie_name) text += ': ' + ev.zombie_name + ' ×' + (ev.multiplier || 2);
    text += ' · ' + ev.seconds_left + 'с';
    return `<span class="event-badge event-${ev.type}">${text}</span>`;
  }).join(' ');
}

function renderQuestTracker(quests) {
  const list = document.getElementById('active-quests-list');
  if (!list) return;

  if (!quests || quests.length === 0) {
    list.innerHTML = '<li class="hint">Нет активных квестов</li>';
    return;
  }

  list.innerHTML = quests.map(q => {
    const verb = q.req_type === 'kill' ? 'Убить' :
                 q.req_type === 'collect' ? 'Принести' : 'Дойти:';
    const icon = q.target_icon || '🎯';

    return `
      <li style="flex-direction:column; align-items:flex-start; padding: 8px; margin-bottom: 6px;">
        <div style="font-weight:bold; color:${q.complete ? 'var(--accent)' : 'var(--text)'}">
          ${q.complete ? '✅ ' : ''}${escapeHtml(q.name)}
        </div>
        <div class="hint" style="margin: 4px 0;">${verb} <b>${icon} ${escapeHtml(q.target_name)}</b></div>
        <div style="width:100%; font-size: 11px; color: var(--dim);">
          Прогресс: <b>${q.progress} / ${q.required}</b>
        </div>
      </li>
    `;
  }).join('');
}

function updateAuctionBadge() {
  const n = ST.data?.auction_active_count || 0;
  const badge = document.getElementById('auction-badge');
  if (badge) { badge.textContent = n; badge.hidden = n === 0; }
}
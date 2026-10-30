function closeModal(id) {
  document.getElementById(id).hidden = true;
  if (id === 'shop-modal') ST.currentShopNpc = null;
  if (id === 'duel-result-modal') ST.shownDuelResultId = null;
  if (id === 'quests-modal') ST.currentQuestNpc = null;
}

document.getElementById('factions-btn').onclick = () => {
  const rep = ST.data?.character?.reputation || {scientists: 0, military: 0};
  document.getElementById('factions-list').innerHTML = `
    <div class="lot-item"><span class="lot-name">👨‍🔬 Учёные</span><span class="lot-price">${rep.scientists || 0} очков</span></div>
    <div class="lot-item"><span class="lot-name">🎖️ Военные</span><span class="lot-price">${rep.military || 0} очков</span></div>
    <p class="hint" style="margin-top:10px">Репутация повышается за выполнение квестов фракций.</p>
  `;
  document.getElementById('factions-modal').hidden = false;
};

// ==================== МАГАЗИН ====================
async function openShop(npcId) {
  ST.currentShopNpc = npcId;
  ST.shopTab = 'buy';

  const { ok, data } = await api('/shop/' + npcId);
  if (!ok) { toast(errorText(data.error), true); return; }

  ST.currentShopData = data;
  document.getElementById('shop-title').textContent = '🛒 ' + data.npc.name;
  document.getElementById('shop-gold').textContent = ST.data.character.gold;

  document.querySelectorAll('#shop-modal .shop-tabs button').forEach(btn => {
    btn.onclick = () => { ST.shopTab = btn.dataset.tab; renderShopBody(); };
  });

  renderShopBody();
  document.getElementById('shop-modal').hidden = false;
}

function renderShopBody() {
  const box = document.getElementById('shop-items');
  box.innerHTML = '';

  document.querySelectorAll('#shop-modal .shop-tabs button').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === ST.shopTab);
  });

  if (ST.shopTab === 'buy') {
    const items = ST.currentShopData?.items || [];
    if (items.length === 0) { box.innerHTML = '<p class="hint">Нет товаров</p>'; return; }

    items.forEach(it => {
      const div = document.createElement('div');
      div.className = 'shop-item';
      const stats = [
        it.attack ? '⚔' + it.attack : '', it.defense ? '🛡' + it.defense : '',
        it.hp_bonus ? '❤+' + it.hp_bonus : '', it.mp_bonus ? '💧+' + it.mp_bonus : '',
        it.heal_hp ? '💊' + it.heal_hp : ''
      ].filter(Boolean).join(' ');

      div.innerHTML = `
        <span class="name rarity-${it.rarity}">${it.icon || '📦'} ${it.name}</span>
        <span class="hint">${stats}</span>
        <span class="price">${it.price}💰</span>
      `;
      const btn = document.createElement('button');
      btn.textContent = 'Купить';
      btn.onclick = () => shopBuy(ST.currentShopNpc, it.item_id);
      div.appendChild(btn);
      box.appendChild(div);
    });
  } else {
    const sellable = ST.inventory.filter(i => !i.equipped_slot);
    if (sellable.length === 0) { box.innerHTML = '<p class="hint">Инвентарь пуст</p>'; return; }

    sellable.forEach(inv => {
      const div = document.createElement('div');
      div.className = 'shop-item';
      const price = Math.max(1, Math.floor((inv.base_price || 5) * 0.4));

      div.innerHTML = `
        <span class="name rarity-${inv.rarity}">${inv.icon || '📦'} ${inv.name}${inv.quantity > 1 ? ' ×'+inv.quantity : ''}</span>
        <span class="price">${price}💰</span>
      `;
      const btn = document.createElement('button');
      btn.textContent = 'Продать';
      btn.onclick = () => shopSell(ST.currentShopNpc, inv.id);
      div.appendChild(btn);
      box.appendChild(div);
    });
  }
}

async function shopBuy(npcId, itemId) {
  const { ok, data } = await api(`/shop/${npcId}/buy`, { method: 'POST', body: { item_id: itemId, qty: 1 } });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('Куплено');
  ST.data.character.gold = data.gold;
  document.getElementById('shop-gold').textContent = data.gold;
  document.getElementById('char-gold').textContent = data.gold;

  const [s, inv, shop] = await Promise.all([api('/state'), api('/inventory'), api('/shop/' + npcId)]);
  if (s.ok) ST.data = s.data;
  if (inv.ok) ST.inventory = inv.data.items;
  if (shop.ok) ST.currentShopData = shop.data;

  renderShopBody();
  renderInventory();
}

async function shopSell(npcId, invId) {
  const { ok, data } = await api(`/shop/${npcId}/sell`, { method: 'POST', body: { inv_id: invId, qty: 1 } });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast(`+${data.sold_for}💰`);
  ST.data.character.gold = data.gold;
  document.getElementById('shop-gold').textContent = data.gold;
  document.getElementById('char-gold').textContent = data.gold;

  const [s, inv] = await Promise.all([api('/state'), api('/inventory')]);
  if (s.ok) ST.data = s.data;
  if (inv.ok) ST.inventory = inv.data.items;

  renderShopBody();
  renderInventory();
}

// ==================== КРАФТ ====================
async function openCraft() {
  const { ok, data } = await api('/craft/recipes');
  if (!ok) { toast(errorText(data.error), true); return; }
  ST.craftRecipes = data.recipes || [];
  document.getElementById('craft-recipes').innerHTML = ST.craftRecipes.map(r => `
    <div class="craft-item">
      <div class="craft-head"><span class="name rarity-${r.result.rarity}">${r.result.icon} ${r.result.name}</span></div>
      <div class="ingredients">${r.ingredients.map(i => `<span class="ingredient ${i.enough ? '' : 'missing'}">${i.icon} ${i.name} ${i.have}/${i.qty}</span>`).join('')}</div>
      <button onclick="craftItem(${r.id})" ${!r.can_craft ? 'disabled' : ''}>Скрафтить</button>
    </div>
  `).join('');
  document.getElementById('craft-gold').textContent = ST.data.character.gold;
  document.getElementById('craft-modal').hidden = false;
}

async function craftItem(id) {
  const { ok, data } = await api('/craft/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('✅ Скрафчено'); openCraft(); refreshAll();
}

// ==================== КВЕСТЫ ====================
async function openQuests(npcId = null) {
  ST.currentQuestNpc = npcId; // Запоминаем NPC, чтобы при сдаче обновить его же список

  const url = npcId ? `/quests?npc_id=${npcId}` : '/quests';
  const { ok, data } = await api(url);
  if (!ok) { toast(errorText(data.error), true); return; }

  const formatRewards = (q) => {
    const parts = [];
    if (q.reward_xp) parts.push(`✨${q.reward_xp} XP`);
    if (q.reward_gold) parts.push(`💰${q.reward_gold}`);
    if (q.reward_item) parts.push(`🎁 ${escapeHtml(q.reward_item)}`);
    return parts.length ? `<div class="q-rewards">Награда: ${parts.join(' · ')}</div>` : '';
  };

  document.getElementById('quests-active').innerHTML = data.active.map(q => `
    <div class="quest-card ${q.complete ? 'done' : ''}">
      <b>${escapeHtml(q.name)}</b>
      <div class="hint">${escapeHtml(q.description)}</div>
      <div>Прогресс: <b>${q.progress}/${q.required}</b></div>
      ${formatRewards(q)}
      ${q.complete ? `<button onclick="turnInQuest(${q.cq_id})" style="margin-top: 8px;">Сдать</button>` : ''}
    </div>
  `).join('') || '<p class="hint">Нет активных</p>';

  document.getElementById('quests-available').innerHTML = data.available.map(q => `
    <div class="quest-card">
      <b>${escapeHtml(q.name)}</b>
      <div class="hint">${escapeHtml(q.description)}</div>
      <div>Цель: ${q.required} шт.</div>
      ${formatRewards(q)}
      <button onclick="acceptQuest(${q.id})" style="margin-top: 8px;">Взять</button>
    </div>
  `).join('') || '<p class="hint">Нет доступных</p>';

  // Фильтруем контракты по NPC
  const contracts = ST.data?.location?.contracts || [];
  const filteredContracts = npcId ? contracts.filter(c => c.npc_id === npcId) : contracts;

  document.getElementById('contracts-list').innerHTML = filteredContracts.map(c => `
    <div class="quest-card" style="border-left: 3px solid #d6a23d;">
      <b>${escapeHtml(c.title)}</b>
      <div class="hint">${escapeHtml(c.desc)}</div>
      <div class="q-rewards">Награда: 💰${c.gold} · ✨${c.xp}</div>
      <button onclick="acceptContract(${c.id})" style="margin-top: 8px;">Взять контракт</button>
    </div>
  `).join('') || '<p class="hint">Нет контрактов</p>';

  document.getElementById('quests-modal').hidden = false;
}

async function acceptQuest(id) {
  await api('/quest/accept/' + id, { method: 'POST' });
  openQuests(ST.currentQuestNpc);
  refreshAll();
}
async function turnInQuest(id) {
  await api('/quest/turnin/' + id, { method: 'POST' });
  toast('Награда получена!');
  openQuests(ST.currentQuestNpc);
  refreshAll();
}
async function acceptContract(id) {
  await api('/contracts/accept/' + id, { method: 'POST' });
  toast('Контракт взят!');
  openQuests(ST.currentQuestNpc);
  refreshAll();
}

// ==================== ДОСТИЖЕНИЯ ====================
document.getElementById('achievements-btn').onclick = async () => {
  const { ok, data } = await api('/achievements');
  if (!ok) return;
  document.getElementById('ach-count').textContent = `${data.unlocked_count}/${data.total}`;
  document.getElementById('achievements-list').innerHTML = data.achievements.map(a => `
    <div class="ach-item ${a.unlocked ? 'unlocked' : 'locked'}">
      <div class="ach-icon">${a.icon}</div>
      <div class="ach-body"><div class="ach-name">${escapeHtml(a.name)}</div><div class="ach-desc">${escapeHtml(a.description)}</div></div>
    </div>
  `).join('');
  document.getElementById('achievements-modal').hidden = false;
};

// ==================== АУКЦИОН ====================
document.getElementById('auction-btn').onclick = () => openAuction();

async function openAuction() {
  ST.auctionTab = 'buy';

  document.querySelectorAll('#auction-tabs button').forEach(btn => {
    btn.onclick = () => {
      ST.auctionTab = btn.dataset.ata;
      renderAuctionBody();
    };
  });

  await loadAuction();
  document.getElementById('auction-modal').hidden = false;
}

async function loadAuction() {
  const [list, mine] = await Promise.all([api('/auction/list'), api('/auction/my')]);
  if (list.ok) ST.auctionList = list.data.auctions || [];
  if (mine.ok) ST.auctionMine = mine.data.auctions || [];

  document.getElementById('auction-gold').textContent = ST.data?.character?.gold || 0;
  renderAuctionBody();
}

function renderAuctionBody() {
  const box = document.getElementById('auction-body');
  box.innerHTML = '';

  document.querySelectorAll('#auction-tabs button').forEach(b => {
    b.classList.toggle('active', b.dataset.ata === ST.auctionTab);
  });

  if (ST.auctionTab === 'buy') {
    const visible = ST.auctionList.filter(a => !a.is_mine);
    if (visible.length === 0) { box.innerHTML = '<p class="hint">Нет активных лотов</p>'; return; }
    visible.forEach(a => {
      const div = document.createElement('div');
      div.className = 'lot-item';
      div.innerHTML = `
        <span class="lot-name rarity-${a.item.rarity}">${a.item.icon} ${escapeHtml(a.item.name)} ${a.quantity > 1 ? '×'+a.quantity : ''}</span>
        <span class="hint" style="flex:1">от ${escapeHtml(a.seller.name)}</span>
        <span class="lot-price">${a.price}💰</span>
      `;
      const btn = document.createElement('button');
      btn.textContent = 'Купить';
      btn.disabled = ST.data.character.gold < a.price;
      btn.onclick = () => buyLot(a.id);
      div.appendChild(btn);
      box.appendChild(div);
    });
  }
  else if (ST.auctionTab === 'sell') {
    const sellable = ST.inventory.filter(i => !i.equipped_slot);
    if (sellable.length === 0) { box.innerHTML = '<p class="hint">Нет предметов для продажи</p>'; return; }

    sellable.forEach(inv => {
      const div = document.createElement('div');
      div.className = 'lot-item';
      div.innerHTML = `
        <span class="lot-name rarity-${inv.rarity}">${inv.icon} ${escapeHtml(inv.name)} ${inv.quantity > 1 ? '×'+inv.quantity : ''}</span>
        <input type="number" min="1" value="${Math.max(1, Math.floor((inv.base_price || 5) * 2))}" id="lot-price-${inv.id}" style="width: 70px; padding: 3px 5px;">
      `;
      const btn = document.createElement('button');
      btn.textContent = 'Выставить';
      btn.onclick = () => sellLot(inv.id);
      div.appendChild(btn);
      box.appendChild(div);
    });
  }
  else if (ST.auctionTab === 'mine') {
    if (ST.auctionMine.length === 0) { box.innerHTML = '<p class="hint">У вас нет лотов</p>'; return; }

    ST.auctionMine.forEach(a => {
      const div = document.createElement('div');
      div.className = 'lot-item mine ' + (a.status !== 'active' ? 'sold' : '');
      const statusText = { active: '⏳ Активен', sold: '✅ Продан', expired: '⌛ Истёк', cancelled: '❌ Снят' }[a.status] || a.status;

      div.innerHTML = `
        <span class="lot-name rarity-${a.item.rarity}">${a.item.icon} ${escapeHtml(a.item.name)} ${a.quantity > 1 ? '×'+a.quantity : ''}</span>
        <span class="hint" style="flex:1">${statusText}</span>
        <span class="lot-price">${a.price}💰</span>
      `;
      if (a.status === 'active') {
        const btn = document.createElement('button');
        btn.textContent = 'Снять';
        btn.onclick = () => cancelLot(a.id);
        div.appendChild(btn);
      }
      box.appendChild(div);
    });
  }
}

async function sellLot(invId) {
  const price = parseInt(document.getElementById(`lot-price-${invId}`).value) || 0;
  const { ok, data } = await api('/auction/sell', { method: 'POST', body: { inv_id: invId, price, qty: 1 } });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('✅ Лот выставлен');
  await loadAuction();
  await refreshAll();
}

async function buyLot(id) {
  const { ok, data } = await api('/auction/buy/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast(`Куплено! Комиссия: ${data.commission}💰`);
  await loadAuction();
  await refreshAll();
}

async function cancelLot(id) {
  const { ok, data } = await api('/auction/cancel/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('Лот снят');
  await loadAuction();
  await refreshAll();
}

// ==================== ТРЕЙД ====================
async function startTrade(targetId) { await api('/trade/init/' + targetId, { method: 'POST' }); loadTrade(); document.getElementById('trade-modal').hidden = false; }
async function loadTrade() {
  const { ok, data } = await api('/trade/current');
  if (!ok || !data.trade) { document.getElementById('trade-modal').hidden = true; return; }
  const t = data.trade;
  document.getElementById('trade-body').innerHTML = [t.initiator, t.target].map(p => {
    const offer = t.offers[p.id] || { items: [], gold: 0 };
    const conf = t.confirmed[String(p.id)];
    return `<div class="trade-side"><b>${escapeHtml(p.name)}</b> ${conf ? '✅' : '⏳'}
      <div>💰 ${offer.gold}</div>
      <div>${offer.items.map(i => `${i.icon} ${escapeHtml(i.name)}`).join(', ') || '<i>ничего</i>'}</div>
      ${p.id === ST.data.character.id ? `
        <input type="number" id="trade-gold-input" value="${offer.gold}" style="margin-top:5px; width:80px;">
        <button onclick="submitOffer(${t.id})">Обновить</button>
      ` : ''}</div>`;
  }).join('');
}
async function submitOffer(tradeId) {
  const gold = parseInt(document.getElementById('trade-gold-input').value) || 0;
  await api(`/trade/${tradeId}/offer`, { method: 'POST', body: { items: [], gold } });
  loadTrade();
}
async function tradeConfirm() {
  const { ok, data } = await api('/trade/current');
  if (ok && data.trade) {
    const r = await api(`/trade/${data.trade.id}/confirm`, { method: 'POST' });
    if (r.ok && r.data.trade.status === 'done') { toast('Обмен совершён!'); closeModal('trade-modal'); refreshAll(); }
    else loadTrade();
  }
}
async function tradeCancel() {
  const { ok, data } = await api('/trade/current');
  if (ok && data.trade) await api(`/trade/${data.trade.id}/cancel`, { method: 'POST' });
  closeModal('trade-modal');
}
// ==================== MODALS ====================
function closeModal(id) {
  document.getElementById(id).hidden = true;
  if (id === 'shop-modal') ST.currentShopNpc = null;
  if (id === 'duel-result-modal') ST.shownDuelResultId = null;
}

// ==================== SHOP ====================
async function openShop(npcId) {
  ST.currentShopNpc = npcId;
  ST.shopTab = 'buy';
  document.querySelectorAll('#shop-modal .shop-tabs button').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === 'buy');
    b.onclick = () => {
      document.querySelectorAll('#shop-modal .shop-tabs button')
        .forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      ST.shopTab = b.dataset.tab;
      renderShopBody();
    };
  });

  const { ok, data } = await api('/shop/' + npcId);
  if (!ok) { toast(errorText(data.error), true); return; }
  ST.currentShopData = data;
  document.getElementById('shop-title').textContent = '🛒 ' + data.npc.name;
  document.getElementById('shop-gold').textContent = ST.data.character.gold;
  document.getElementById('shop-modal').hidden = false;
  renderShopBody();
}

function renderShopBody() {
  const box = document.getElementById('shop-items');
  box.innerHTML = '';
  if (ST.shopTab === 'buy') {
    (ST.currentShopData?.items || []).forEach(it => {
      const div = document.createElement('div');
      div.className = 'shop-item';
      const stats = [
        it.attack ? '⚔' + it.attack : '',
        it.defense ? '🛡' + it.defense : '',
        it.hp_bonus ? '+' + it.hp_bonus + 'hp' : '',
        it.mp_bonus ? '+' + it.mp_bonus + 'mp' : '',
        it.heal_hp ? '💊' + it.heal_hp : '',
        it.heal_mp ? '⚡' + it.heal_mp : '',
      ].filter(Boolean).join(' ');
      div.innerHTML = `
        <span class="name rarity-${it.rarity}">${it.icon} ${it.name}</span>
        <span class="hint">${stats}</span>
        <span class="price">${it.price}💰</span>`;
      const b = document.createElement('button');
      b.textContent = 'Купить';
      b.onclick = () => shopBuy(ST.currentShopNpc, it.item_id);
      div.appendChild(b);
      box.appendChild(div);
    });
  } else {
    if (ST.inventory.length === 0) {
      box.innerHTML = '<p class="hint">Инвентарь пуст</p>';
      return;
    }
    ST.inventory.forEach(inv => {
      const price = Math.max(1, Math.floor((inv.base_price || 5) * 0.4));
      const div = document.createElement('div');
      div.className = 'shop-item';
      div.innerHTML = `
        <span class="name rarity-${inv.rarity}">${inv.icon} ${inv.name}${
          inv.quantity > 1 ? ' ×' + inv.quantity : ''
        }${inv.equipped_slot ? ' [E]' : ''}</span>
        <span class="price">${price}💰</span>`;
      const b = document.createElement('button');
      b.textContent = 'Продать';
      b.disabled = !!inv.equipped_slot;
      b.onclick = () => shopSell(ST.currentShopNpc, inv.id);
      div.appendChild(b);
      box.appendChild(div);
    });
  }
}

async function shopBuy(npcId, itemId) {
  const { ok, data } = await api(`/shop/${npcId}/buy`, {
    method: 'POST', body: { item_id: itemId, qty: 1 },
  });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('Куплено');
  openShop(npcId);
  refreshAll();
}

async function shopSell(npcId, invId) {
  const { ok, data } = await api(`/shop/${npcId}/sell`, {
    method: 'POST', body: { inv_id: invId, qty: 1 },
  });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast(`+${data.sold_for}💰`);
  refreshAll();
  if (!document.getElementById('shop-modal').hidden) {
    const { ok: okShop, data: shopData } = await api('/shop/' + npcId);
    if (okShop) {
      ST.currentShopData = shopData;
      document.getElementById('shop-gold').textContent = ST.data.character.gold;
      renderShopBody();
    }
  }
}

// ==================== CRAFT ====================
async function openCraft() {
  const { ok, data } = await api('/craft/recipes');
  if (!ok) { toast(errorText(data.error), true); return; }
  ST.craftRecipes = data.recipes || [];
  renderCraftRecipes();
  document.getElementById('craft-gold').textContent = ST.data.character.gold;
  document.getElementById('craft-modal').hidden = false;
}

function renderCraftRecipes() {
  const box = document.getElementById('craft-recipes');
  box.innerHTML = '';
  if (ST.craftRecipes.length === 0) {
    box.innerHTML = '<p class="hint">Нет рецептов</p>';
    return;
  }
  ST.craftRecipes.forEach(r => {
    const div = document.createElement('div');
    div.className = 'craft-item';
    const ings = r.ingredients.map(i =>
      `<span class="ingredient ${i.enough ? '' : 'missing'}">${i.icon} ${i.name} ${i.have}/${i.qty}</span>`
    ).join('');
    const gold = r.gold_cost > 0 ? ` · 💰${r.gold_cost}` : '';
    div.innerHTML = `
      <div class="craft-head">
        <span class="name rarity-${r.result.rarity}">${r.result.icon} ${r.result.name}${
          r.result.qty > 1 ? ' ×' + r.result.qty : ''
        }</span>
      </div>
      <div class="ingredients">${ings}${gold}</div>`;
    const b = document.createElement('button');
    b.textContent = 'Скрафтить';
    b.disabled = !r.can_craft;
    b.onclick = () => craftItem(r.id);
    div.appendChild(b);
    box.appendChild(div);
  });
}

async function craftItem(recipeId) {
  const { ok, data } = await api('/craft/' + recipeId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('✅ Скрафчено');
  openCraft();
  refreshAll();
}

// ==================== QUESTS ====================
async function openQuests() {
  const { ok, data } = await api('/quests');
  if (!ok) { toast(errorText(data.error), true); return; }

  const act = document.getElementById('quests-active');
  act.innerHTML = data.active.length ? '' : '<p class="hint">Нет активных</p>';
  data.active.forEach(q => {
    const div = document.createElement('div');
    div.className = 'quest-card' + (q.complete ? ' done' : '');
    const verb = q.req_type === 'kill' ? 'Убить' :
                 q.req_type === 'collect' ? 'Принести' : 'Дойти:';
    div.innerHTML = `<b>${escapeHtml(q.name)}</b>
      <div class="hint">${escapeHtml(q.description)}</div>
      <div>${verb} ${escapeHtml(q.target_name)} — <b>${q.progress}/${q.required}</b></div>
      <div class="q-rewards">✨${q.reward_xp} XP · 💰${q.reward_gold}${
        q.reward_item ? ' · 🎁' + escapeHtml(q.reward_item) : ''
      }</div>`;
    if (q.complete) {
      const b = document.createElement('button');
      b.textContent = 'Сдать';
      b.onclick = () => questTurnIn(q.cq_id);
      div.appendChild(b);
    }
    act.appendChild(div);
  });

  const av = document.getElementById('quests-available');
  av.innerHTML = data.available.length ? '' : '<p class="hint">Нет новых заданий здесь</p>';
  data.available.forEach(q => {
    const div = document.createElement('div');
    div.className = 'quest-card';
    const verb = q.req_type === 'kill' ? 'Убить' :
                 q.req_type === 'collect' ? 'Принести' : 'Дойти:';
    div.innerHTML = `<b>${escapeHtml(q.name)}</b>
      <div class="hint">${escapeHtml(q.description)}</div>
      <div>${verb} ${escapeHtml(q.target_name)} × ${q.required}</div>
      <div class="q-rewards">✨${q.reward_xp} XP · 💰${q.reward_gold}${
        q.reward_item ? ' · 🎁' + escapeHtml(q.reward_item) : ''
      }</div>`;
    const b = document.createElement('button');
    b.textContent = 'Взять';
    b.onclick = () => questAccept(q.id);
    div.appendChild(b);
    av.appendChild(div);
  });

  document.getElementById('quests-modal').hidden = false;
}

async function questAccept(id) {
  const { ok, data } = await api('/quest/accept/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  openQuests(); refreshAll();
}

async function questTurnIn(cqId) {
  const { ok, data } = await api('/quest/turnin/' + cqId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('Награда получена!');
  playSound('levelup');
  openQuests(); refreshAll();
}

// ==================== TRADE ====================
async function startTrade(targetId) {
  const { ok, data } = await api('/trade/init/' + targetId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  await loadTrade();
  document.getElementById('trade-modal').hidden = false;
}

async function loadTrade() {
  const { ok, data } = await api('/trade/current');
  if (!ok || !data.trade) {
    document.getElementById('trade-modal').hidden = true;
    return;
  }
  const t = data.trade;
  const box = document.getElementById('trade-body');
  box.innerHTML = '';
  [t.initiator, t.target].forEach(p => {
    const offer = t.offers[p.id] || { items: [], gold: 0 };
    const conf = t.confirmed[String(p.id)];
    const div = document.createElement('div');
    div.className = 'trade-side';
    div.innerHTML = `<b>${escapeHtml(p.name)}</b> ${conf ? '✅' : '⏳'}
      <div>💰 ${offer.gold}</div>
      <div>${offer.items.map(i =>
        `${i.icon} ${escapeHtml(i.name)} ×${i.quantity}`).join(', ') || '<i>ничего</i>'}</div>`;

    if (p.id === ST.data.character.id) {
      const goldInp = document.createElement('input');
      goldInp.type = 'number'; goldInp.min = 0;
      goldInp.value = offer.gold;
      goldInp.placeholder = 'Золото';
      goldInp.id = 'trade-gold-input';
      div.appendChild(goldInp);

      const sel = document.createElement('select');
      sel.id = 'trade-item-select';
      sel.innerHTML = '<option value="">— предмет —</option>';
      ST.inventory.filter(i => !i.equipped_slot).forEach(i => {
        const o = document.createElement('option');
        o.value = i.id;
        o.textContent = `${i.icon} ${i.name}`;
        sel.appendChild(o);
      });
      div.appendChild(sel);

      const addBtn = document.createElement('button');
      addBtn.textContent = 'Обновить оффер';
      addBtn.onclick = () => submitOffer(t.id, p.id);
      div.appendChild(addBtn);
    }
    box.appendChild(div);
  });
}

async function submitOffer(tradeId, myId) {
  const gold = parseInt(document.getElementById('trade-gold-input').value) || 0;
  const selVal = document.getElementById('trade-item-select').value;
  const items = selVal ? [{ inv_id: parseInt(selVal), quantity: 1 }] : [];
  const { ok, data } = await api(`/trade/${tradeId}/offer`, {
    method: 'POST', body: { items, gold },
  });
  if (!ok) { toast(errorText(data.error), true); return; }
  loadTrade();
}

async function tradeConfirm() {
  const { ok, data } = await api('/trade/current');
  if (!ok || !data.trade) return;
  const r = await api(`/trade/${data.trade.id}/confirm`, { method: 'POST' });
  if (!r.ok) { toast(errorText(r.data.error), true); return; }
  if (r.data.trade.status === 'done') {
    toast('🤝 Обмен совершён!');
    closeModal('trade-modal');
    refreshAll();
  } else loadTrade();
}

async function tradeCancel() {
  const { ok, data } = await api('/trade/current');
  if (ok && data.trade) await api(`/trade/${data.trade.id}/cancel`, { method: 'POST' });
  closeModal('trade-modal');
}

setInterval(() => {
  if (!document.getElementById('trade-modal').hidden) loadTrade();
}, 2000);

// ==================== ACHIEVEMENTS ====================
document.getElementById('achievements-btn').onclick = () => openAchievements();

async function openAchievements() {
  const { ok, data } = await api('/achievements');
  if (!ok) { toast(errorText(data.error), true); return; }

  document.getElementById('ach-count').textContent =
    `${data.unlocked_count}/${data.total}`;

  const list = document.getElementById('achievements-list');
  list.innerHTML = '';
  data.achievements.forEach(a => {
    const div = document.createElement('div');
    div.className = 'ach-item ' + (a.unlocked ? 'unlocked' : 'locked');
    const reward = [
      a.reward_xp ? `✨${a.reward_xp}` : '',
      a.reward_gold ? `💰${a.reward_gold}` : '',
    ].filter(Boolean).join(' ');
    div.innerHTML = `
      <div class="ach-icon">${a.icon}</div>
      <div class="ach-body">
        <div class="ach-name">${escapeHtml(a.name)}</div>
        <div class="ach-desc">${escapeHtml(a.description)}</div>
        ${reward ? `<div class="ach-reward">${reward}</div>` : ''}
      </div>`;
    list.appendChild(div);
  });

  document.getElementById('achievements-modal').hidden = false;
}

// ==================== AUCTION ====================
document.getElementById('auction-btn').onclick = () => openAuction();

async function openAuction() {
  ST.auctionTab = 'buy';
  document.querySelectorAll('#auction-tabs button').forEach(b => {
    b.classList.toggle('active', b.dataset.ata === 'buy');
    b.onclick = () => {
      document.querySelectorAll('#auction-tabs button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      ST.auctionTab = b.dataset.ata;
      renderAuctionBody();
    };
  });

  document.getElementById('auction-gold').textContent = ST.data?.character?.gold || 0;
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

  if (ST.auctionTab === 'buy') {
    const visible = ST.auctionList.filter(a => !a.is_mine);
    if (visible.length === 0) { box.innerHTML = '<p class="hint">Нет активных лотов</p>'; return; }
    visible.forEach(a => {
      const div = document.createElement('div');
      div.className = 'lot-item';
      div.innerHTML = `
        <span class="lot-name rarity-${a.item.rarity}">
          ${a.item.icon} ${escapeHtml(a.item.name)}
          ${a.quantity > 1 ? ' ×' + a.quantity : ''}
          <span class="hint">от ${escapeHtml(a.seller.name)}</span>
        </span>
        <span class="lot-price">${a.price}💰</span>
        <span class="lot-timer">${fmtTime(a.seconds_left)}</span>`;
      const b = document.createElement('button');
      b.textContent = 'Купить';
      b.disabled = ST.data.character.gold < a.price;
      b.onclick = () => buyLot(a.id);
      div.appendChild(b);
      box.appendChild(div);
    });
  } else if (ST.auctionTab === 'sell') {
    const sellable = ST.inventory.filter(i => !i.equipped_slot);
    if (sellable.length === 0) { box.innerHTML = '<p class="hint">Нет предметов для продажи</p>'; return; }
    sellable.forEach(inv => {
      const div = document.createElement('div');
      div.className = 'lot-sell-row';
      div.innerHTML = `
        <span class="lot-name rarity-${inv.rarity}">
          ${inv.icon} ${escapeHtml(inv.name)}
          ${inv.quantity > 1 ? ' ×' + inv.quantity : ''}
        </span>
        <input type="number" min="1" value="${Math.max(1, Math.floor((inv.base_price || 5) * 2))}"
               placeholder="Цена" id="lot-price-${inv.id}">
        ${inv.stackable && inv.quantity > 1 ?
          `<input type="number" min="1" max="${inv.quantity}" value="${inv.quantity}"
                  placeholder="Кол-во" id="lot-qty-${inv.id}" style="width:60px">` : ''}
        <button onclick="sellLot(${inv.id})">Выставить</button>`;
      box.appendChild(div);
    });
  } else if (ST.auctionTab === 'mine') {
    if (ST.auctionMine.length === 0) { box.innerHTML = '<p class="hint">Нет лотов</p>'; return; }
    ST.auctionMine.forEach(a => {
      const div = document.createElement('div');
      div.className = 'lot-item mine ' + (a.status !== 'active' ? 'sold' : '');
      const statusText = {
        active: '⏳ активен', sold: '✅ продан',
        expired: '⌛ истёк', cancelled: '❌ снят',
      }[a.status] || a.status;
      div.innerHTML = `
        <span class="lot-name rarity-${a.item.rarity}">
          ${a.item.icon} ${escapeHtml(a.item.name)}
          ${a.quantity > 1 ? ' ×' + a.quantity : ''}
        </span>
        <span class="lot-price">${a.price}💰</span>
        <span class="lot-timer">${statusText}${
          a.status === 'active' ? ' · ' + fmtTime(a.seconds_left) : ''
        }</span>`;
      if (a.status === 'active') {
        const b = document.createElement('button');
        b.textContent = 'Снять';
        b.onclick = () => cancelLot(a.id);
        div.appendChild(b);
      }
      box.appendChild(div);
    });
  }
}

function fmtTime(sec) {
  if (sec <= 0) return 'истёк';
  if (sec < 3600) return Math.floor(sec / 60) + ' мин';
  if (sec < 86400) return Math.floor(sec / 3600) + ' ч';
  return Math.floor(sec / 86400) + ' д';
}

async function sellLot(invId) {
  const price = parseInt(document.getElementById('lot-price-' + invId).value) || 0;
  const qtyInput = document.getElementById('lot-qty-' + invId);
  const qty = qtyInput ? (parseInt(qtyInput.value) || 1) : 1;
  const { ok, data } = await api('/auction/sell', {
    method: 'POST', body: { inv_id: invId, price, qty },
  });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('✅ Лот выставлен');
  await refreshAll();
  await loadAuction();
}

async function buyLot(id) {
  const { ok, data } = await api('/auction/buy/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast(`Куплено! Комиссия ${data.commission}💰`);
  playSound('loot');
  await refreshAll();
  await loadAuction();
}

async function cancelLot(id) {
  const { ok, data } = await api('/auction/cancel/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast('Лот снят');
  await refreshAll();
  await loadAuction();
}

function updateAuctionBadge() {
  const n = ST.data?.auction_active_count || 0;
  const badge = document.getElementById('auction-badge');
  if (!badge) return;
  if (n > 0) { badge.textContent = n; badge.hidden = false; }
  else badge.hidden = true;
}
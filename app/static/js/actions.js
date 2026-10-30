async function doStep(dx, dy) {
  if (ST.busyStep) return; ST.busyStep = true;
  const { ok, data } = await api('/move/step', { method: 'POST', body: { dx, dy } });
  ST.busyStep = false;

  if (!ok) { toast(errorText(data.error), true); return; }

  if (data.msg === 'unlocked') toast('🔓 Дверь открыта!');
  if (data.combat_triggered) toast(`🧟 ${data.combat_triggered.zombie_name} нападает!`, true);

  // Исправлено: проверка на пустой лут
  if (data.loot_picked_from) {
    if (data.picked && data.picked.length) {
      toast('Найдено: ' + data.picked.map(p => `${p.icon || '📦'} ${p.name} x${p.qty}`).join(', '));
      playSound('loot');
    } else {
      toast('Пусто');
      playSound('empty');
    }
  }
  refreshAll();
}

async function pickupLoot(lootId) {
  const { ok, data } = await api('/loot/pickup/' + lootId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }

  // Исправлено: проверка на пустой лут и добавление иконок
  if (data.loot && data.loot.length) {
    toast('Найдено: ' + data.loot.map(l => `${l.icon || '📦'} ${l.name} x${l.qty}`).join(', '));
    playSound('loot');
  } else {
    toast('Пусто');
    playSound('empty');
  }
  refreshAll();
}

async function move(direction) {
  const { ok, data } = await api('/move', { method: 'POST', body: { direction } });
  if (!ok) toast(errorText(data.error), true);
  else if (data.healed) toast('💊 Восстановлено в безопасной зоне');
  ST.hoveredExit = null;
  refreshAll();
}

async function startCombat(id) {
  await api('/combat/start/' + id, { method: 'POST' });
  refreshAll();
}

document.getElementById('btn-attack').onclick = async () => {
  const sid = document.getElementById('skill-select').value;
  const { ok } = await api('/combat/action', { method: 'POST', body: { action: 'attack', skill_id: sid ? parseInt(sid) : null } });
  if (ok) playSound('hit'); refreshAll();
};

document.getElementById('btn-auto').onclick = async () => {
  const me = ST.data?.combat?.participants?.find(p => p.is_me);
  await api('/combat/action', { method: 'POST', body: { action: 'auto', enabled: !me?.auto_mode } });
  refreshAll();
};

document.getElementById('btn-flee').onclick = async () => {
  await api('/combat/action', { method: 'POST', body: { action: 'flee' } });
  refreshAll();
};

document.getElementById('btn-dismiss').onclick = async () => {
  const wasVictory = ST.data?.combat?.status === 'victory';
  const wasDefeat = ST.data?.combat?.status === 'defeat';
  await api('/combat/dismiss', { method: 'POST' });
  if (wasVictory) playSound('victory'); if (wasDefeat) playSound('death');
  refreshAll();
};

async function equipItem(id) { await api('/inventory/equip/' + id, { method: 'POST' }); refreshAll(); }
async function unequip(slot) { await api('/inventory/unequip/' + slot, { method: 'POST' }); refreshAll(); }
async function useItem(id) { await api('/inventory/use/' + id, { method: 'POST' }); refreshAll(); }
async function dropItem(id) { await api('/inventory/drop/' + id, { method: 'POST' }); refreshAll(); }

async function salvageItem(id) {
  const { ok, data } = await api('/inventory/salvage/' + id, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  toast(`Разобрано: ${data.salvaged.map(s => s.name + ' x' + s.qty).join(', ')}`);
  refreshAll();
}

async function createParty() { await api('/party/create', { method: 'POST' }); refreshAll(); }
async function inviteToParty(id) { await api('/party/invite/' + id, { method: 'POST' }); toast('Приглашено'); }
async function acceptInvite(id) { await api('/party/accept/' + id, { method: 'POST' }); refreshAll(); }
async function declineInvite(id) { await api('/party/decline/' + id, { method: 'POST' }); refreshAll(); }
async function leaveParty() { await api('/party/leave', { method: 'POST' }); refreshAll(); }

document.getElementById('stat-allocate').onclick = async (e) => {
  const stat = e.target.dataset.stat;
  if (!stat) return;
  const { ok, data } = await api('/character/allocate', { method: 'POST', body: { stat } });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
};

document.getElementById('chat-form').onsubmit = async (e) => {
  e.preventDefault();
  const inp = document.getElementById('chat-input');
  const msg = inp.value.trim();
  if (!msg) return;
  inp.value = '';
  await api('/chat/send', { method: 'POST', body: { message: msg, scope: ST.chatTab } });
};
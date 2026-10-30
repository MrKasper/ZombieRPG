// ==================== MOVEMENT ====================
async function doStep(dx, dy) {
  if (ST.busyStep) return;
  ST.busyStep = true;
  const { ok, data } = await api('/move/step', { method: 'POST', body: { dx, dy } });
  ST.busyStep = false;

  if (!ok) {
    if (data.error !== 'cell_blocked' && data.error !== 'out_of_bounds') {
      toast(errorText(data.error), true);
    }
    return;
  }

  playSound('step');

  const gotLoot = data.picked && data.picked.length > 0;
  const hadLootPoint = !!data.loot_picked_from;
  const gotCombat = !!data.combat_triggered;

  if (hadLootPoint || gotCombat) {
    const parts = [];
    if (gotLoot) {
      parts.push('Найдено: ' + data.picked.map(l => `${l.icon} ${l.name} ×${l.qty}`).join(', '));
      playSound('loot');
    } else if (hadLootPoint) {
      parts.push('Пусто');
      playSound('empty');
    }
    if (gotCombat) {
      parts.push(`🧟 ${data.combat_triggered.zombie_name} нападает!`);
      playSound('zombie_hit');
    }
    toast(parts.join(' · '), gotCombat);
    refreshAll();
    return;
  }

  ST.data.character.x = data.x;
  ST.data.character.y = data.y;
}

async function pickupLoot(lootId) {
  const { ok, data } = await api('/loot/pickup/' + lootId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  if (data.loot && data.loot.length) {
    toast('Найдено: ' + data.loot.map(l => `${l.icon} ${l.name} ×${l.qty}`).join(', '));
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

// ==================== COMBAT ====================
async function startCombat(zombieId) {
  const { ok, data } = await api('/combat/start/' + zombieId, { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
}

document.getElementById('btn-attack').onclick = async () => {
  const skillId = document.getElementById('skill-select').value;
  const { ok, data } = await api('/combat/action', {
    method: 'POST',
    body: { action: 'attack', skill_id: skillId ? parseInt(skillId) : null },
  });
  if (!ok) toast(errorText(data.error), true);
  else playSound('hit');
  refreshAll();
};

document.getElementById('btn-auto').onclick = async () => {
  const me = ST.data?.combat?.participants?.find(p => p.is_me);
  const enable = !me?.auto_mode;
  await api('/combat/action', { method: 'POST', body: { action: 'auto', enabled: enable } });
  refreshAll();
};

document.getElementById('btn-flee').onclick = async () => {
  const { ok, data } = await api('/combat/action', { method: 'POST', body: { action: 'flee' } });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
};

document.getElementById('btn-dismiss').onclick = async () => {
  const wasVictory = ST.data?.combat?.status === 'victory';
  const wasDefeat = ST.data?.combat?.status === 'defeat';
  await api('/combat/dismiss', { method: 'POST' });
  if (wasVictory) playSound('victory');
  if (wasDefeat) playSound('death');
  refreshAll();
};

// ==================== INVENTORY ====================
async function equipItem(id) {
  const { ok, data } = await api('/inventory/equip/' + id, { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
}
async function unequip(slot) {
  const { ok, data } = await api('/inventory/unequip/' + slot, { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
}
async function useItem(id) {
  const { ok, data } = await api('/inventory/use/' + id, { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  else if (data.healed_hp || data.healed_mp) {
    toast(`+${data.healed_hp} HP, +${data.healed_mp} MP`);
    playSound('loot');
  } else if (data.learned_skill_id) {
    toast('📖 Изучен новый скилл!');
    playSound('levelup');
  }
  refreshAll();
}
async function dropItem(id) {
  await api('/inventory/drop/' + id, { method: 'POST' });
  refreshAll();
}

// ==================== CHARACTER ====================
document.getElementById('stat-allocate').onclick = async (e) => {
  const stat = e.target.dataset.stat;
  if (!stat) return;
  const { ok, data } = await api('/character/allocate', { method: 'POST', body: { stat } });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
};

// ==================== PARTY ====================
async function createParty() {
  const { ok, data } = await api('/party/create', { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
}
async function inviteToParty(charId) {
  const { ok, data } = await api('/party/invite/' + charId, { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  else toast('Приглашение отправлено');
}
async function acceptInvite(id) {
  const { ok, data } = await api('/party/accept/' + id, { method: 'POST' });
  if (!ok) toast(errorText(data.error), true);
  refreshAll();
}
async function declineInvite(id) {
  await api('/party/decline/' + id, { method: 'POST' });
  refreshAll();
}
async function leaveParty() {
  await api('/party/leave', { method: 'POST' });
  refreshAll();
}

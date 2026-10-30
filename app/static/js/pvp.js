// ==================== PVP / DUEL ====================
function handleDuelState(pvp) {
  if (!pvp) return;
  const pd = pvp.pending_duel;

  if (!pd) {
    if (ST.activeDuelId) {
      const m = document.getElementById('duel-modal');
      if (m && !m.hidden) m.hidden = true;
      ST.activeDuelId = null;
    }
    return;
  }

  if (pd.is_target) {
    if (ST.activeDuelId !== pd.id) {
      ST.activeDuelId = pd.id;
      document.getElementById('duel-body').innerHTML = `
        <p>⚔️ <b>${escapeHtml(pd.challenger_name)}</b> вызывает тебя на дуэль!</p>
        <p class="hint">У тебя ${pd.seconds_left} сек. на ответ.</p>`;
      document.getElementById('duel-accept').onclick = () => acceptDuel(pd.id);
      document.getElementById('duel-decline').onclick = () => declineDuel(pd.id);
      document.getElementById('duel-modal').hidden = false;
      playSound('duel');
    }
  } else {
    if (ST.activeDuelId !== pd.id) {
      ST.activeDuelId = pd.id;
      toast(`⚔️ Ожидаем ответа ${pd.target_name}...`);
    }
  }
}

async function challengeDuel(targetId) {
  const { ok, data } = await api('/duel/challenge/' + targetId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  ST.activeDuelId = data.duel_id;
  toast('⚔️ Вызов отправлен');
  refreshAll();
}

async function acceptDuel(duelId) {
  const { ok, data } = await api('/duel/accept/' + duelId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  document.getElementById('duel-modal').hidden = true;
  ST.activeDuelId = null;
  showDuelResult(data.duel);
  playSound('victory');
  refreshAll();
}

async function declineDuel(duelId) {
  const { ok, data } = await api('/duel/decline/' + duelId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  document.getElementById('duel-modal').hidden = true;
  ST.activeDuelId = null;
  toast('Дуэль отклонена');
  refreshAll();
}

function showDuelResult(duel) {
  if (!duel) return;
  if (ST.shownDuelResultId === duel.id) return;
  ST.shownDuelResultId = duel.id;

  const title = document.getElementById('duel-result-title');
  if (duel.winner_id === ST.data?.character?.id) title.textContent = '🏆 Победа в дуэли!';
  else if (duel.winner_id) title.textContent = '💀 Поражение в дуэли';
  else title.textContent = '🤝 Ничья';

  const log = document.getElementById('duel-result-log');
  log.innerHTML = (duel.log || []).map(l => `<div>${escapeHtml(l)}</div>`).join('');
  document.getElementById('duel-result-modal').hidden = false;
}

document.getElementById('pvp-btn').onclick = () => openPvp();

async function openPvp() {
  const { ok, data } = await api('/duel/leaderboard');
  if (!ok) { toast(errorText(data.error), true); return; }

  const pvp = ST.data?.pvp || {};
  document.getElementById('pvp-wins').textContent = pvp.wins || 0;
  document.getElementById('pvp-losses').textContent = pvp.losses || 0;

  const box = document.getElementById('pvp-leaders');
  if (!data.leaders || data.leaders.length === 0) {
    box.innerHTML = '<p class="hint">Пока ни одной дуэли.</p>';
  } else {
    box.innerHTML = data.leaders.map((c, idx) =>
      `<div class="lot-item">
        <span class="lot-name"><b>#${idx + 1}</b> ${escapeHtml(c.name)} <span class="hint">Lv${c.level}</span></span>
        <span class="lot-price">${c.wins}⚔ / ${c.losses}💀</span>
      </div>`
    ).join('');
  }

  document.getElementById('pvp-modal').hidden = false;
}
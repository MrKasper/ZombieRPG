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
      document.getElementById('duel-body').innerHTML = `<p>⚔️ <b>${escapeHtml(pd.challenger_name)}</b> вызывает тебя на дуэль!</p><p class="hint">У тебя ${pd.seconds_left} сек. на ответ.</p>`;
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
  toast('⚔️ Вызов отправлен'); refreshAll();
}

async function acceptDuel(duelId) {
  const { ok, data } = await api('/duel/accept/' + duelId, { method: 'POST' });
  if (!ok) { toast(errorText(data.error), true); return; }
  document.getElementById('duel-modal').hidden = true;
  ST.activeDuelId = null;
  showDuelResult(data.duel); playSound('victory'); refreshAll();
}

async function declineDuel(duelId) {
  await api('/duel/decline/' + duelId, { method: 'POST' });
  document.getElementById('duel-modal').hidden = true;
  ST.activeDuelId = null; toast('Дуэль отклонена'); refreshAll();
}

function showDuelResult(duel) {
  if (!duel || ST.shownDuelResultId === duel.id) return;
  ST.shownDuelResultId = duel.id;
  document.getElementById('duel-result-title').textContent = duel.winner_id === ST.data?.character?.id ? '🏆 Победа!' : duel.winner_id ? '💀 Поражение' : '🤝 Ничья';
  document.getElementById('duel-result-log').innerHTML = (duel.log || []).map(l => `<div>${escapeHtml(l)}</div>`).join('');
  document.getElementById('duel-result-modal').hidden = false;
}

document.getElementById('pvp-btn').onclick = async () => {
  const { ok, data } = await api('/duel/leaderboard');
  if (!ok) return;
  const pvp = ST.data?.pvp || {};
  document.getElementById('pvp-wins').textContent = pvp.wins || 0;
  document.getElementById('pvp-losses').textContent = pvp.losses || 0;
  document.getElementById('pvp-leaders').innerHTML = data.leaders.map((c, i) => `
    <div class="lot-item"><span class="lot-name"><b>#${i+1}</b> ${escapeHtml(c.name)} <span class="hint">Lv${c.level}</span></span><span class="lot-price">${c.wins}⚔ / ${c.losses}💀</span></div>
  `).join('') || '<p class="hint">Пока ни одной дуэли.</p>';
  document.getElementById('pvp-modal').hidden = false;
};
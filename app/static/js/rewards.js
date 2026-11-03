import { state } from './state.js';
import { $, empty, esc, fmt, parseDay, person, uuid } from './helpers.js';
import { actions } from './actions.js';
import { api } from './api.js';
import { confirmDiscard, errorInForm, toast } from './dialogs.js';
import { icon } from './icons.js';

export const rewardRequestRetries = new Map();
export const rewardDecisionRetries = new Map();
export function timestampDay(value) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: state.data.config.timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date(value.replace(' ', 'T') + 'Z'));
}
export function rewardsView() {
  const current = person(state.member),
    balance = state.data.balances[state.member] || {
      balance: 0,
      reserved: 0,
      available: 0
    };
  const requests = state.data.reward_requests.filter(
    (r) => r.member_id === state.member && timestampDay(r.created_at) === state.day
  );
  const transactions = state.data.point_transactions.filter(
    (t) => t.member_id === state.member && timestampDay(t.created_at) === state.day
  );
  const selectedDate = fmt(parseDay(state.day), {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  });
  return `<section class="panel rewards-summary"><div><div class="section-label">Jouw puntensaldo</div><h2>${current ? esc(current.name) : 'Kies een gezinslid'}</h2><p class="muted">${current ? `${balance.available} beschikbaar · ${balance.reserved} gereserveerd voor aanvragen` : 'Selecteer hierboven een profiel om saldo en beloningen te zien.'}</p></div><strong class="reward-balance">✦ ${balance.balance}</strong></section>${!state.data.members.length ? empty('Nog geen gezinsleden', 'Voeg eerst gezinsleden toe via Beheer.', 'people') : ''}<div class="card-title"><h2>Beloningen</h2></div><div class="reward-grid">${state.data.rewards.map((r) => `<article class="panel reward-card"><span class="reward-icon">${esc(r.icon)}</span><h3>${esc(r.title)}</h3><p>${esc(r.description || '')}</p><div class="reward-footer"><span class="points">✦ ${r.price} punten</span><button class="primary small" data-request-reward="${r.id}" ${!current || balance.available < r.price ? 'disabled' : ''}>Aanvragen</button></div></article>`).join('') || empty('Nog geen beloningen', 'De beheerder kan beloningen toevoegen via Beheer.', 'people')}</div>${
    current
      ? `<div class="bottom-grid"><section class="panel"><div class="card-title"><h2>Jouw aanvragen · ${esc(selectedDate)}</h2></div>${
          requests
            .map(
              (r) =>
                `<div class="history-item">${esc(r.reward_name)} · ${r.cost} punten <span class="reward-status ${esc(r.status)}">${
                  {
                    pending: 'In afwachting',
                    approved: 'Goedgekeurd',
                    rejected: 'Afgewezen'
                  }[r.status]
                }</span><small>${fmt(new Date(r.created_at.replace(' ', 'T') + 'Z'), {
                  dateStyle: 'short',
                  timeStyle: 'short',
                  timeZone: state.data.config.timezone
                })}</small></div>`
            )
            .join('') || '<p class="muted">Geen aanvragen op deze datum.</p>'
        }</section><section class="panel"><div class="card-title"><h2>Puntentransacties · ${esc(selectedDate)}</h2></div>${
          transactions
            .map(
              (t) =>
                `<div class="history-item">${esc(
                  t.reason === 'manual-adjustment'
                    ? 'Handmatige correctie'
                    : t.reason.startsWith('manual-adjustment:')
                      ? `Handmatige correctie: ${t.reason.slice('manual-adjustment:'.length)}`
                      : {
                          completion: 'Taak of routine voltooid',
                          'completion-undone': 'Voltooiing ongedaan gemaakt',
                          'reward-redemption': 'Beloning goedgekeurd',
                          'game-purchase': 'Spelsessie gekocht'
                        }[t.reason] || t.reason
                )} <strong class="${t.amount < 0 ? 'negative' : ''}">${t.amount > 0 ? '+' : ''}${t.amount}</strong><small>${fmt(
                  new Date(t.created_at.replace(' ', 'T') + 'Z'),
                  {
                    dateStyle: 'short',
                    timeStyle: 'short',
                    timeZone: state.data.config.timezone
                  }
                )}</small></div>`
            )
            .join('') || '<p class="muted">Geen transacties op deze datum.</p>'
        }</section></div>`
      : ''
  }`;
}
export async function requestReward(rewardId, button) {
  const key = `${state.member}:${rewardId}`;
  const requestId = rewardRequestRetries.get(key) || uuid();
  rewardRequestRetries.set(key, requestId);
  await actions.operation(async () => {
    await api('/api/reward-requests', {
      method: 'POST',
      body: JSON.stringify({
        request_id: requestId,
        member_id: state.member,
        reward_id: rewardId
      })
    });
    rewardRequestRetries.delete(key);
    toast('Aanvraag verstuurd; de punten zijn gereserveerd tot goedkeuring.');
  }, button);
}
export function rewardAdminMarkup() {
  const pending = state.data.reward_requests.filter((r) => r.status === 'pending');
  const rewards = state.data.rewards.length
    ? `<table class="reward-admin-table" aria-label="Beloningen en puntenprijzen"><thead><tr><th scope="col">Beloning</th><th scope="col">Prijs</th><th scope="col">Actie</th></tr></thead><tbody>${state.data.rewards
        .map(
          (r) =>
            `<tr><th scope="row"><span class="reward-admin-name"><span>${esc(r.icon)}</span><span>${esc(r.title)}</span></span></th><td class="reward-admin-price">${r.price} punten</td><td><button type="button" class="secondary small" data-reward-edit="${r.id}">${icon('edit')}Bewerken</button></td></tr>`
        )
        .join('')}</tbody></table>`
    : '<p class="muted">Nog geen beloningen ingesteld.</p>';
  return `<section class="settings-section"><h3>Beloningen</h3><p>Voltooide taken en volledig afgeronde routines boeken punten automatisch. Routinepunten worden één keer toegekend, niet per stap.</p>${rewards}<button type="button" class="secondary reward-admin-add" data-reward-new>${icon('plus')}Beloning toevoegen</button><h3 style="margin-top:22px">Openstaande aanvragen</h3>${pending.map((r) => `<div class="history-item"><strong>${esc(r.member_name)}</strong> vraagt ${esc(r.reward_name)} aan · ${r.cost} punten<div class="inline"><button type="button" class="primary small" data-reward-decision="approve" data-request-id="${r.id}">Goedkeuren</button><button type="button" class="secondary small" data-reward-decision="reject" data-request-id="${r.id}">Afwijzen</button></div></div>`).join('') || '<p class="muted">Geen openstaande aanvragen.</p>'}</section>`;
}
export function bindRewardAdmin() {
  $('#edit-form').insertAdjacentHTML('beforebegin', rewardAdminMarkup());
  document.querySelector('[data-reward-new]').onclick = () => {
    if (state.dialogDirty)
      return confirmDiscard(
        () => actions.editEntity('rewards'),
        'Niet-opgeslagen instellingen verlaten?'
      );
    actions.editEntity('rewards');
  };
  document.querySelectorAll('[data-reward-edit]').forEach(
    (b) =>
      (b.onclick = () => {
        const reward = state.data.rewards.find((r) => r.id === b.dataset.rewardEdit);
        if (state.dialogDirty)
          return confirmDiscard(
            () => actions.editEntity('rewards', reward),
            'Niet-opgeslagen instellingen verlaten?'
          );
        actions.editEntity('rewards', reward);
      })
  );
  document
    .querySelectorAll('[data-reward-decision]')
    .forEach(
      (b) => (b.onclick = () => decideReward(b.dataset.requestId, b.dataset.rewardDecision, b))
    );
}
export async function decideReward(id, action, button) {
  const key = `${id}:${action}`;
  const requestId = rewardDecisionRetries.get(key) || uuid();
  rewardDecisionRetries.set(key, requestId);
  button.disabled = true;
  try {
    await api(`/api/admin/reward-requests/${encodeURIComponent(id)}/decision`, {
      method: 'POST',
      body: JSON.stringify({
        request_id: requestId,
        action
      })
    });
    rewardDecisionRetries.delete(key);
    state.dialogDirty = false;
    await actions.refresh(true);
    await actions.openAdmin();
    toast(
      action === 'approve'
        ? 'Beloning goedgekeurd; punten afgeschreven.'
        : 'Aanvraag afgewezen; gereserveerde punten vrijgegeven.'
    );
  } catch (error) {
    errorInForm(error);
    if (error.status === 409) await actions.refresh(true);
    button.disabled = false;
  }
}

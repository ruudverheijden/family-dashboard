import { state } from '../state.js';
import { $, avatar, esc, uuid } from '../helpers.js';
import { api } from '../api.js';
import { actions } from '../actions.js';
import { toast } from '../dialogs.js';
import { icon } from '../icons.js';
import { games } from './registry.js';

const purchaseRetries = new Map();
let dialog,
  session,
  cleanup = () => {},
  timer,
  pending = false,
  soundEnabled = true;
let moveRetry = null;
let purchasePending = false;

export function isGameOpen() {
  return Boolean(dialog?.open);
}

export function gamesView() {
  const member = state.data.members.find((m) => m.id === state.member);
  const balance = state.data.balances[state.member]?.available || 0;
  const active = state.data.game_sessions?.find((s) => s.member_id === state.member);
  return `<section class="games-page"><h1>Spelletjes</h1><p>Kies je naam en koop één spelsessie met je punten.</p><div class="game-profiles" role="group" aria-label="Speler">${state.data.members.map((m) => `<button class="secondary ${m.id === state.member ? 'active' : ''}" data-member="${m.id}" aria-pressed="${m.id === state.member}">${avatar(m)}${esc(m.name)}</button>`).join('')}</div><p>${member ? `${esc(member.name)} · ${balance} punten beschikbaar` : 'Kies eerst een gezinslid.'}</p>${active ? `<p class="notice">Je hebt een lopende spelsessie. De tijd loopt door als je dit scherm verlaat.</p><button class="primary" data-resume-game="${active.id}">Verder spelen</button>` : ''}<div class="reward-grid">${state.data.games.map((g) => `<article class="panel reward-card"><span class="reward-icon" aria-hidden="true">${esc(g.icon)}</span><h2>${esc(g.title)}</h2><p>${esc(g.description)}</p>${g.id === 'memory' ? '<p class="muted">Foto’s uit jullie geselecteerde Immich-albums. Minstens 6 foto’s nodig.</p>' : ''}<button class="primary" data-buy-game="${g.id}" ${!member || active || balance < g.price || (g.id === 'memory' && state.data.photos.length < 6) ? 'disabled' : ''}>Speel voor ${g.price} punten</button></article>`).join('')}</div><p class="muted">Eén aankoop = één spel. Stoppen of tijd om? De sessie eindigt zonder teruggave van punten. Spelprijzen stel je in via Beheer.</p>${state.childMode ? '<button class="secondary" data-tab="child-dashboard">Terug naar mijn dag</button>' : ''}</section>`;
}

function ensureDialog() {
  if (dialog) return;
  dialog = document.createElement('dialog');
  dialog.id = 'game-dialog';
  dialog.setAttribute('aria-labelledby', 'game-title');
  document.body.append(dialog);
  dialog.addEventListener('cancel', (e) => {
    e.preventDefault();
    stop();
  });
}

async function stop() {
  if (pending) return;
  if (session.status === 'active') {
    if (!confirm('Spel stoppen? Hiermee eindigt deze sessie.')) return;
    await send('stop');
    return;
  }
  close();
}

function close() {
  games[session?.game_id]?.stopAudio?.();
  cleanup();
  clearInterval(timer);
  dialog.close();
  session = null;
  moveRetry = null;
  actions.refresh(true);
}

function draw(next) {
  if (next.status === 'active' && next.expires_at * 1000 <= Date.now())
    next = { ...next, status: 'expired' };
  const completedNow = session?.status === 'active' && next.status === 'completed';
  const changed =
    !session ||
    session.id !== next.id ||
    session.version !== next.version ||
    session.status !== next.status;
  session = next;
  if (!changed) return;
  const focused = dialog.contains(document.activeElement) ? document.activeElement : null;
  const focusKey = focused?.dataset.gameControl;
  const focusId = focused?.id;
  if (session.status !== 'active') games[session.game_id].stopAudio?.();
  cleanup();
  dialog.dataset.game = session.game_id;
  const titleIcon = games[session.game_id].titleIcon;
  const title = state.data.games.find((g) => g.id === session.game_id)?.title || 'Spelletje';
  dialog.innerHTML = `<header class="game-header"><h2 id="game-title">${titleIcon ? `<span class="game-title-icon" aria-hidden="true">${esc(titleIcon)}</span>` : ''}${esc(title)}</h2><span id="game-countdown" role="status"></span><div class="game-header-actions"><button type="button" class="secondary game-sound" id="game-sound"></button><button class="secondary" id="game-stop">${session.status === 'active' ? 'Stoppen' : 'Sluiten'}</button></div></header><div id="game-board"></div><p id="game-error" role="alert"></p>`;
  $('#game-stop').onclick = stop;
  const updateSound = () => {
    const button = $('#game-sound');
    button.innerHTML = `${icon(soundEnabled ? 'volume' : 'muted')}<span>Geluid ${soundEnabled ? 'aan' : 'uit'}</span>`;
    button.setAttribute('aria-pressed', String(soundEnabled));
    button.setAttribute('aria-label', soundEnabled ? 'Geluid uitzetten' : 'Geluid aanzetten');
    button.title = button.getAttribute('aria-label');
  };
  $('#game-sound').onclick = () => {
    soundEnabled = !soundEnabled;
    if (!soundEnabled) games[session.game_id].stopAudio?.();
    updateSound();
  };
  updateSound();
  if (session.status === 'active') {
    cleanup = games[session.game_id].mount(
      $('#game-board'),
      session.board,
      (value) => send('move', value),
      () => soundEnabled
    );
  } else {
    $('#game-board').innerHTML =
      `<div class="game-finish"><span aria-hidden="true">${session.status === 'completed' ? '🌟' : '👋'}</span><h3>${session.status === 'completed' ? 'Goed gedaan! Je spel is klaar.' : 'Je spelsessie is afgelopen.'}</h3><p>Bedankt voor het spelen!</p><button class="primary" id="game-done">Terug naar het dashboard</button></div>`;
    $('#game-done').onclick = close;
    clearInterval(timer);
    if (completedNow) {
      const member = state.data.members.find((person) => person.id === session.member_id);
      cleanup =
        games[session.game_id].celebrateCompletion?.(member?.name || 'topper', dialog) ||
        (() => {});
    }
  }
  if (dialog.open) {
    const target =
      dialog.querySelector('.routine-celebration-close') ||
      $('#game-done') ||
      (focusKey
        ? dialog.querySelector(`[data-game-control="${CSS.escape(focusKey)}"]:not(:disabled)`)
        : null) ||
      (focusId ? dialog.querySelector(`#${CSS.escape(focusId)}`) : null) ||
      (focusKey ? dialog.querySelector('[data-game-control]:not(:disabled)') : null);
    target?.focus();
  }
}

async function send(action, value = null) {
  if (pending || session?.status !== 'active') return;
  pending = true;
  moveRetry ||= { request_id: uuid(), version: session.version, action, value };
  try {
    const next = await api(`/api/game-sessions/${session.id}/actions`, {
      method: 'POST',
      body: JSON.stringify(moveRetry)
    });
    moveRetry = null;
    draw(next);
    if ($('#game-error')) $('#game-error').textContent = '';
  } catch (e) {
    if (e.status && e.status < 500) moveRetry = null;
    if (e.status === 409) await sync(true);
    if ($('#game-error'))
      $('#game-error').textContent =
        e.message + (moveRetry ? ' Tik nogmaals om dezelfde zet opnieuw te versturen.' : '');
  } finally {
    pending = false;
  }
}

async function sync(force = false) {
  if (!session) return;
  const id = session.id;
  try {
    const next = await api(`/api/game-sessions/${id}`);
    if (session?.id === id && next.version >= session.version && (!pending || force)) draw(next);
  } catch (e) {
    if ($('#game-error')) $('#game-error').textContent = e.message;
  }
}

function open(next) {
  ensureDialog();
  if (session) games[session.game_id].stopAudio?.();
  cleanup();
  clearInterval(timer);
  session = null;
  moveRetry = null;
  draw(next);
  dialog.showModal();
  if (next.status === 'active')
    timer = setInterval(() => {
      if (!session) return;
      const remaining = Math.max(0, Math.ceil(session.expires_at - Date.now() / 1000));
      if ($('#game-countdown'))
        $('#game-countdown').textContent = remaining <= 30 ? `Nog ${remaining} seconden` : '';
      if (!remaining) draw({ ...session, status: 'expired' });
      else if (!pending) sync();
    }, 1000);
}

async function buy(id, button) {
  if (purchasePending) return;
  purchasePending = true;
  button.disabled = true;
  const game = state.data.games.find((g) => g.id === id);
  const memberId = state.member;
  const key = `${memberId}:${id}:${game.version}`;
  let body = purchaseRetries.get(key);
  try {
    // Verify selected photos load before spending points. No independent photo cache.
    if (id === 'memory' && !body) {
      try {
        await Promise.all(
          state.data.photos.slice(0, 6).map(async (p) => {
            const response = await fetch(`/api/photos/${encodeURIComponent(p.id)}`);
            if (!response.ok)
              throw new Error(
                'De foto’s laden niet. Controleer Immich; er zijn geen punten afgeschreven.'
              );
            const bitmap = await createImageBitmap(await response.blob());
            bitmap.close();
          })
        );
      } catch {
        throw new Error(
          'De foto’s laden niet. Controleer Immich; er zijn geen punten afgeschreven.'
        );
      }
    }
    body ||= {
      request_id: uuid(),
      member_id: memberId,
      price: game.price,
      version: game.version
    };
    purchaseRetries.set(key, body);
    const next = await api(`/api/games/${id}/sessions`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
    purchaseRetries.delete(key);
    open(next);
    actions.refresh(true);
  } catch (e) {
    if (e.status && e.status < 500) purchaseRetries.delete(key);
    toast(e.message);
  } finally {
    purchasePending = false;
    button.disabled = false;
  }
}

export function bindGames() {
  document
    .querySelectorAll('[data-buy-game]')
    .forEach((b) => (b.onclick = () => buy(b.dataset.buyGame, b)));
  document.querySelectorAll('[data-resume-game]').forEach(
    (b) =>
      (b.onclick = async () => {
        try {
          open(await api(`/api/game-sessions/${b.dataset.resumeGame}`));
        } catch (e) {
          toast(e.message);
        }
      })
  );
}

export function bindGameAdmin(onDirtyChange) {
  const updateDirty = () =>
    onDirtyChange(
      [...document.querySelectorAll('[data-game-price]')].some(
        (form) => form.dataset.dirty === 'true'
      )
    );
  $('#edit-form').insertAdjacentHTML(
    'beforebegin',
    `<section class="settings-section"><h3>Spelletjes</h3><p>Een aankoop schrijft direct punten af voor één sessie van maximaal 3 minuten. Memory gebruikt de geselecteerde Immich-albums.</p>${state.data.games.map((g) => `<form class="game-price-form" data-game-price="${g.id}"><label>${esc(g.title)} · punten per sessie<input name="price" type="number" min="1" max="100000" step="1" required value="${g.price}"></label><button class="secondary" type="submit">Spelprijs opslaan</button><span role="status"></span></form>`).join('')}</section>`
  );
  document.querySelectorAll('[data-game-price]').forEach((form) => {
    form.oninput = (e) => {
      e.stopPropagation();
      form.dataset.dirty = 'true';
      updateDirty();
    };
    form.onsubmit = async (e) => {
      e.preventDefault();
      const button = form.querySelector('button');
      button.disabled = true;
      form.elements.price.disabled = true;
      const game = state.data.games.find((g) => g.id === form.dataset.gamePrice);
      try {
        await api(`/api/admin/games/${game.id}`, {
          method: 'POST',
          body: JSON.stringify({ price: Number(form.elements.price.value), version: game.version })
        });
        form.dataset.dirty = 'false';
        updateDirty();
        await actions.refresh(true);
        form.querySelector('[role="status"]').textContent = 'Opgeslagen';
      } catch (error) {
        form.querySelector('[role="status"]').textContent = error.message;
      } finally {
        button.disabled = false;
        form.elements.price.disabled = false;
      }
    };
  });
}

import { esc } from '../helpers.js';

export function mount(root, board, move) {
  root.innerHTML = `<p>Zoek twee dezelfde foto’s. ${board.matched.length / 2} van 6 paren gevonden.</p><div class="memory-board">${board.cards.map((photo, index) => `<button class="memory-card" aria-label="Kaart ${index + 1}${board.matched.includes(index) ? ', gevonden' : ''}" ${board.open.includes(index) || board.matched.includes(index) ? 'disabled' : ''} data-game-control="card-${index}" data-card="${index}">${photo ? `<img src="/api/photos/${encodeURIComponent(photo)}" alt="Omgedraaide foto" data-game-photo>` : '<span aria-hidden="true">✳</span>'}</button>`).join('')}</div><p class="muted">${esc(board.moves)} pogingen · Tik op een volgende kaart om een ongelijk paar weer te verbergen.</p>`;
  root
    .querySelectorAll('[data-card]')
    .forEach((b) => (b.onclick = () => move(Number(b.dataset.card))));
  root.querySelectorAll('[data-game-photo]').forEach((img) => {
    img.onerror = () => {
      img.alt = 'Foto niet beschikbaar; stop de sessie en controleer Immich.';
    };
  });
  return () => {};
}

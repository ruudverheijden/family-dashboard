export function mount(root, board, move) {
  const [x, y] = board.position;
  root.innerHTML = `<p>Help de muis naar de kaas. Gebruik de pijlen.</p><div class="maze-board" role="img" aria-label="Doolhof, muis op rij ${y}, kolom ${x}">${board.grid.flatMap((row, cy) => row.map((wall, cx) => `<span class="maze-cell ${wall ? 'wall' : ''}">${x === cx && y === cy ? '🐭' : cx === 7 && cy === 7 ? '🧀' : ''}</span>`)).join('')}</div><div class="maze-controls">${[
    ['up', '↑', 'Omhoog'],
    ['left', '←', 'Links'],
    ['down', '↓', 'Omlaag'],
    ['right', '→', 'Rechts']
  ]
    .map(
      ([value, arrow, name]) =>
        `<button class="secondary" data-game-control="${value}" data-direction="${value}" aria-label="${name}">${arrow}</button>`
    )
    .join('')}</div>`;
  root
    .querySelectorAll('[data-direction]')
    .forEach((b) => (b.onclick = () => move(b.dataset.direction)));
  const keys = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right' };
  const keydown = (e) => {
    if (keys[e.key]) {
      e.preventDefault();
      move(keys[e.key]);
    }
  };
  document.addEventListener('keydown', keydown);
  return () => document.removeEventListener('keydown', keydown);
}

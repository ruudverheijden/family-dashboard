export function celebrateTaskCompletion(button) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const bounds = button.getBoundingClientRect(),
    burst = document.createElement('div');
  const colors = ['#bb583f', '#e9b864', '#456350', '#7fa3a1', '#d98168'];
  burst.className = 'confetti-burst';
  burst.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 28; i++) {
    const angle = (Math.PI * 2 * i) / 28 + (Math.random() - 0.5) * 0.4,
      distance = 60 + Math.random() * 100;
    const piece = document.createElement('span');
    piece.className = 'confetti-piece';
    if (Math.random() < 0.25) piece.classList.add('round');
    piece.style.left = `${bounds.left + bounds.width / 2}px`;
    piece.style.top = `${bounds.top + bounds.height / 2}px`;
    piece.style.backgroundColor = colors[i % colors.length];
    piece.style.setProperty('--confetti-x', `${Math.cos(angle) * distance}px`);
    piece.style.setProperty('--confetti-y', `${Math.sin(angle) * distance}px`);
    piece.style.setProperty('--confetti-rotation', `${Math.round((Math.random() - 0.5) * 900)}deg`);
    piece.style.setProperty('--confetti-delay', `${Math.random() * 90}ms`);
    burst.append(piece);
  }
  document.body.append(burst);
  setTimeout(() => burst.remove(), 1100);
}
export const routineCelebrationVariants = [
  {
    id: 'flowers',
    name: 'Bloemenfeest',
    icons: ['🌸', '🌼', '🌷', '🌺', '🌻']
  },
  {
    id: 'rockets',
    name: 'Raketlancering',
    icons: ['🚀', '🪐', '⭐', '☄️', '🌟']
  },
  {
    id: 'butterflies',
    name: 'Vlinderdans',
    icons: ['🦋', '🌈', '🌸', '✨', '🦋']
  },
  {
    id: 'balloons',
    name: 'Ballonnenregen',
    icons: ['🎈', '🎊', '🎉', '✨', '🎈']
  },
  {
    id: 'unicorns',
    name: 'Eenhoornmagie',
    icons: ['🦄', '💫', '🌟', '✨', '🦄']
  },
  {
    id: 'bees',
    name: 'Bijendans',
    icons: ['🐝', '🌻', '🍯', '🌼', '🐝']
  },
  {
    id: 'stars',
    name: 'Sterrenparade',
    icons: ['🌠', '⭐', '🌙', '✨', '💫']
  },
  {
    id: 'ocean',
    name: 'Onderwaterfeest',
    icons: ['🐬', '🐠', '🫧', '🐳', '🐚']
  },
  {
    id: 'magic',
    name: 'Toverfeest',
    icons: ['🪄', '✨', '🔮', '🌙', '💫']
  },
  {
    id: 'trophies',
    name: 'Kampioenenfeest',
    icons: ['🏆', '🥇', '🎊', '🎉', '⭐']
  }
];
export let routineCelebrationIndex = Math.floor(Math.random() * routineCelebrationVariants.length);
export const routineCelebrationMessages = [
  'Supergoed gedaan',
  'Wat heb jij dat goed gedaan',
  'Geweldig gedaan',
  'Fantastisch',
  'Wat een topper ben jij',
  'Jij hebt dit geweldig gedaan',
  'Knap gedaan',
  'Wauw, wat goed',
  'Echt super gedaan',
  'Wat mag je trots zijn'
];
export let previousRoutineCelebrationMessage = -1;
export function celebrateRoutineCompletion(memberName) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const previous = document.querySelector('.routine-celebration');
  if (previous) {
    clearTimeout(previous.dismissTimer);
    previous.remove();
  }
  const variant = routineCelebrationVariants[routineCelebrationIndex];
  routineCelebrationIndex = (routineCelebrationIndex + 1) % routineCelebrationVariants.length;
  const overlay = document.createElement('div');
  overlay.className = 'routine-celebration';
  overlay.dataset.variant = variant.id;
  overlay.setAttribute('role', 'status');
  overlay.setAttribute('aria-live', 'polite');
  const icons = document.createElement('div');
  icons.className = 'routine-celebration-icons';
  icons.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 42; i++) {
    const piece = document.createElement('span');
    const left = 8 + Math.random() * 84,
      top = 8 + Math.random() * 84;
    const dx = left - 50,
      dy = top - 50,
      distance = Math.hypot(dx, dy) || 1;
    piece.className = 'routine-celebration-icon';
    piece.textContent = variant.icons[i % variant.icons.length];
    piece.style.left = `${left}%`;
    piece.style.top = `${top}%`;
    piece.style.setProperty('--fly-x', `${(dx / distance) * 110}vw`);
    piece.style.setProperty('--fly-y', `${(dy / distance) * 110}vh`);
    piece.style.setProperty('--fly-rotation', `${Math.round((Math.random() - 0.5) * 100)}deg`);
    piece.style.setProperty('--fly-delay', `${Math.random() * 500}ms`);
    icons.append(piece);
  }
  const message = document.createElement('div');
  message.className = 'routine-celebration-message';
  let messageIndex = Math.floor(Math.random() * routineCelebrationMessages.length);
  if (messageIndex === previousRoutineCelebrationMessage)
    messageIndex =
      (messageIndex + 1 + Math.floor(Math.random() * (routineCelebrationMessages.length - 1))) %
      routineCelebrationMessages.length;
  previousRoutineCelebrationMessage = messageIndex;
  const sparkle = document.createElement('span');
  sparkle.className = 'routine-celebration-sparkle';
  sparkle.setAttribute('aria-hidden', 'true');
  sparkle.textContent = '✦';
  const heading = document.createElement('h2');
  heading.textContent = `${routineCelebrationMessages[messageIndex]}, ${memberName}!`;
  message.append(sparkle, heading);
  const close = document.createElement('button');
  close.className = 'routine-celebration-close';
  close.type = 'button';
  close.textContent = 'Verder';
  close.setAttribute('aria-label', 'Viering sluiten');
  const dismiss = () => {
    clearTimeout(overlay.dismissTimer);
    overlay.remove();
  };
  close.addEventListener('click', dismiss);
  overlay.append(icons, message, close);
  document.body.append(overlay);
  overlay.dismissTimer = setTimeout(() => overlay.remove(), 4600);
}

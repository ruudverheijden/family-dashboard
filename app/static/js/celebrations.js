let completionAudio;
let supersonicAudioBuffer;
let supersonicAudioLoad;

export function prepareCompletionSound() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return Promise.resolve(false);
  try {
    completionAudio ||= new AudioContextClass();
    if (completionAudio.state !== 'suspended')
      return Promise.resolve(completionAudio.state === 'running');
    return completionAudio
      .resume()
      .then(() => completionAudio.state === 'running')
      .catch((error) => {
        console.error('Het voltooid-geluid kon niet worden gestart.', error);
        return false;
      });
  } catch (error) {
    console.error('Het voltooid-geluid kon niet worden voorbereid.', error);
    return Promise.resolve(false);
  }
}

export function playCompletionSound() {
  if (!completionAudio || completionAudio.state !== 'running') return;
  try {
    const notes = [659.25, 830.61, 987.77];
    const start = completionAudio.currentTime;
    for (const [index, frequency] of notes.entries()) {
      const oscillator = completionAudio.createOscillator();
      const gain = completionAudio.createGain();
      const noteStart = start + index * 0.09;
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(frequency, noteStart);
      gain.gain.setValueAtTime(0.0001, noteStart);
      gain.gain.exponentialRampToValueAtTime(0.07, noteStart + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.22);
      oscillator.connect(gain).connect(completionAudio.destination);
      oscillator.start(noteStart);
      oscillator.stop(noteStart + 0.23);
    }
  } catch (error) {
    console.error('Het voltooid-geluid kon niet worden afgespeeld.', error);
  }
}

export function prepareSupersonicCompletionSound() {
  if (!completionAudio) return Promise.resolve(false);
  if (supersonicAudioBuffer) return Promise.resolve(true);
  supersonicAudioLoad ||= fetch('/static/audio/routine-success-6297.mp3')
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.arrayBuffer();
    })
    .then((audioData) => completionAudio.decodeAudioData(audioData))
    .then((buffer) => {
      supersonicAudioBuffer = buffer;
      return true;
    })
    .catch((error) => {
      supersonicAudioLoad = null;
      console.error('Het supersonische voltooid-geluid kon niet worden geladen.', error);
      return false;
    });
  return supersonicAudioLoad;
}

export function playSupersonicCompletionSound() {
  if (!completionAudio || completionAudio.state !== 'running') return;
  if (!supersonicAudioBuffer) return;
  try {
    const source = completionAudio.createBufferSource();
    const gain = completionAudio.createGain();
    source.buffer = supersonicAudioBuffer;
    gain.gain.setValueAtTime(0.35, completionAudio.currentTime);
    source.connect(gain).connect(completionAudio.destination);
    source.start();
  } catch (error) {
    console.error('Het supersonische voltooid-geluid kon niet worden afgespeeld.', error);
  }
}

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
export function celebrateRoutineCompletion(
  memberName,
  container = document.body,
  customVariant = null,
  onDismiss = () => {}
) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const previous = document.querySelector('.routine-celebration');
  if (previous) {
    previous.dismiss?.();
    clearTimeout(previous.dismissTimer);
    previous.remove();
  }
  const variant = customVariant || routineCelebrationVariants[routineCelebrationIndex];
  if (!customVariant)
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
  let dismissed = false;
  const dismiss = () => {
    if (dismissed) return;
    dismissed = true;
    clearTimeout(overlay.dismissTimer);
    overlay.remove();
    onDismiss();
  };
  overlay.dismiss = dismiss;
  close.addEventListener('click', dismiss);
  overlay.append(icons, message, close);
  container.append(overlay);
  overlay.dismissTimer = setTimeout(dismiss, 4600);
  return dismiss;
}

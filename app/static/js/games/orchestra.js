import { celebrateRoutineCompletion } from '../celebrations.js';
import { icon } from '../icons.js';
import { playAnimal, playError, preloadAudio } from './orchestra-audio.js';
export { stopAudio } from './orchestra-audio.js';

export const titleIcon = '🎶';

const animals = [
  ['🐸', 'Kikker'],
  ['🐱', 'Poes'],
  ['🐶', 'Hond'],
  ['🐤', 'Kuiken']
];
export function mount(root, board, move, sound) {
  root.innerHTML = `<div class="orchestra-stage"><div class="orchestra-instructions"><p id="orchestra-message" aria-live="polite">${board.input.length ? 'Jouw beurt! Maak de reeks af.' : 'Kijk naar de dieren en onthoud de volgorde.'}</p><p>Reeks ${board.round} van 6 · ${board.input.length} dieren nagetikt</p></div><div class="animal-board">${animals.map(([emoji, name], i) => `<button class="animal-button secondary" data-game-control="animal-${i}" data-animal="${i}" aria-label="${name}"><span aria-hidden="true">${emoji}</span>${name}</button>`).join('')}</div><div class="orchestra-controls"><button class="secondary" id="orchestra-repeat" aria-label="Reeks opnieuw afspelen" title="Reeks opnieuw afspelen">${icon('routine')}<span>Opnieuw</span></button></div><p id="orchestra-audio-notice" class="muted" role="status"></p><div class="orchestra-countdown" role="status" aria-live="assertive" aria-atomic="true" hidden><span>Maak je klaar!</span><strong id="orchestra-countdown-number">3</strong></div><div class="orchestra-feedback" role="alert" aria-atomic="true" hidden><div><span class="orchestra-feedback-icon" aria-hidden="true">↺</span><h3>Oeps, die volgorde klopt niet.</h3><p>We proberen dezelfde reeks nog een keer.</p></div></div></div>`;
  preloadAudio();
  const audioError = () => {
    if (root.isConnected)
      root.querySelector('#orchestra-audio-notice').textContent =
        'Het geluid kon niet worden afgespeeld. Je kunt de oplichtende dieren blijven volgen.';
  };
  const dialog = root.closest('dialog');
  const buttons = [...root.querySelectorAll('[data-animal]')];
  let timers = [],
    cancelled = false;
  function demonstration(prepare = false) {
    timers.forEach(clearTimeout);
    timers = [];
    buttons.forEach((b) => {
      b.disabled = true;
      b.classList.remove('animal-cue');
    });
    root.querySelector('#orchestra-repeat').disabled = true;
    root.querySelector('#orchestra-message').textContent =
      'Kijk naar de dieren en onthoud de volgorde.';
    const overlay = root.querySelector('.orchestra-countdown');
    overlay.hidden = !prepare;
    dialog.classList.toggle('game-preparing', prepare);
    const start = prepare ? 4500 : 400;
    if (prepare) {
      dialog.scrollTop = 0;
      root.querySelector('#orchestra-countdown-number').textContent = '3';
      root.querySelector('#orchestra-message').textContent = 'Maak je klaar voor het dierenorkest.';
      for (const [delay, number] of [
        [1000, '2'],
        [2000, '1']
      ]) {
        timers.push(
          setTimeout(() => {
            root.querySelector('#orchestra-countdown-number').textContent = number;
          }, delay)
        );
      }
      timers.push(
        setTimeout(() => {
          overlay.hidden = true;
          dialog.classList.remove('game-preparing');
          root.querySelector('#orchestra-message').textContent = 'Let op, de reeks begint zo.';
        }, 3000)
      );
    }
    board.sequence.forEach((animal, i) => {
      timers.push(
        setTimeout(
          () => {
            if (cancelled) return;
            buttons[animal].classList.add('animal-cue');
            root.querySelector('#orchestra-message').textContent = animals[animal][1];
            playAnimal(animal, sound, audioError);
          },
          start + i * 800
        )
      );
      timers.push(
        setTimeout(() => buttons[animal].classList.remove('animal-cue'), start + 550 + i * 800)
      );
    });
    timers.push(
      setTimeout(
        () => {
          if (cancelled) return;
          buttons.forEach((b) => (b.disabled = false));
          root.querySelector('#orchestra-repeat').disabled = false;
          root.querySelector('#orchestra-message').textContent =
            'Jouw beurt! Tik dezelfde volgorde.';
        },
        start + 100 + board.sequence.length * 800
      )
    );
  }
  buttons.forEach(
    (b) =>
      (b.onclick = () => {
        playAnimal(Number(b.dataset.animal), sound, audioError);
        move(Number(b.dataset.animal));
      })
  );
  root.querySelector('#orchestra-repeat').onclick = () => demonstration();
  if (!board.input.length) {
    if (board.feedback === 'mistake') {
      const feedback = root.querySelector('.orchestra-feedback');
      buttons.forEach((button) => (button.disabled = true));
      root.querySelector('#orchestra-repeat').disabled = true;
      dialog.classList.add('game-preparing');
      dialog.scrollTop = 0;
      feedback.hidden = false;
      playError(sound, audioError);
      timers.push(
        setTimeout(() => {
          if (cancelled) return;
          feedback.hidden = true;
          demonstration(true);
        }, 2000)
      );
    } else demonstration(true);
  }
  return () => {
    cancelled = true;
    timers.forEach(clearTimeout);
    dialog.classList.remove('game-preparing');
  };
}

export function celebrateCompletion(memberName, container) {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  container.classList.add('game-celebrating');
  return celebrateRoutineCompletion(
    memberName,
    container,
    { id: 'orchestra', icons: animals.map(([emoji]) => emoji) },
    () => {
      container.classList.remove('game-celebrating');
      if (container.open) container.querySelector('#game-done')?.focus();
    }
  );
}

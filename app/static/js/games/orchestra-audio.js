/** Local CC0 recordings. One player prevents overlapping animal/error sounds. */
const animalFiles = ['frog', 'cat', 'dog', 'chick'];
const clips = new Map();
let current = null;

function clip(name) {
  if (!clips.has(name)) {
    const media = new Audio(`/static/audio/orchestra/${name}.wav`);
    media.preload = 'auto';
    media.volume = 0.75;
    clips.set(name, media);
  }
  return clips.get(name);
}

export function preloadAudio() {
  for (const name of [...animalFiles, 'error']) clip(name);
}

export function stopAudio() {
  if (!current) return;
  current.pause();
  current.currentTime = 0;
  current = null;
}

function play(name, enabled, onError) {
  if (!enabled()) return;
  stopAudio();
  const media = clip(name);
  current = media;
  try {
    const result = media.play();
    result?.catch((error) => {
      if (current === media && error.name !== 'AbortError') onError();
    });
  } catch {
    onError();
  }
}

export function playAnimal(index, enabled, onError) {
  play(animalFiles[index], enabled, onError);
}

export function playError(enabled, onError) {
  play('error', enabled, onError);
}

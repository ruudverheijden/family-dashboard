import { state } from './state.js';
import { icon } from './icons.js';
import { $, empty, esc } from './helpers.js';
import { actions } from './actions.js';

export function photosView() {
  return state.data.photos.length
    ? `<section class="photo-view"><div class="photo-stage"><img id="photo" alt="Foto uit geselecteerd Immich-album"></div><div class="photo-controls"><button class="secondary" data-photo="prev" aria-label="Vorige foto">${icon('left')}</button><button class="primary" data-photo="pause" aria-label="${state.paused ? 'Diavoorstelling hervatten' : 'Diavoorstelling pauzeren'}">${icon(state.paused ? 'play' : 'pause')} ${state.paused ? 'Afspelen' : 'Pauzeren'}</button><button class="secondary" data-photo="next" aria-label="Volgende foto">${icon('right')}</button></div><div class="photo-caption" id="photo-caption"></div></section>`
    : empty(
        'Jullie herinneringen verdienen een plekje.',
        'Selecteer in Beheer de Immich-albums die hier mogen verschijnen. Alleen foto’s uit die albums worden getoond.',
        'image',
        `<button class="primary" data-action="admin">${icon('image')}Albums kiezen</button>`
      ) +
        (state.data.status.immich?.ok === false
          ? `<p class="notice">${esc(state.data.status.immich.message)}</p>`
          : '');
}
export const photoCache = new Map();
export let photoOrder = [],
  photoOrderKey = '',
  photoRequest = 0;
export function clearPhotoCache(keep = new Set()) {
  for (const [id, entry] of photoCache) {
    if (keep.has(id)) continue;
    entry.controller.abort();
    if (entry.url) URL.revokeObjectURL(entry.url);
    photoCache.delete(id);
  }
}
export function loadPhoto(id) {
  if (photoCache.has(id)) return photoCache.get(id).promise;
  const entry = {
    controller: new AbortController(),
    url: null
  };
  entry.promise = (async () => {
    const response = await fetch('/api/photos/' + encodeURIComponent(id), {
      signal: entry.controller.signal
    });
    if (!response.ok) {
      const error = new Error(
        'De foto’s zijn momenteel niet beschikbaar. Probeer het later opnieuw.'
      );
      if (response.status === 403) {
        const body = await response.json();
        error.message = body.detail;
      }
      throw error;
    }
    const blob = await response.blob();
    if (entry.controller.signal.aborted) throw new DOMException('Geannuleerd', 'AbortError');
    entry.url = URL.createObjectURL(blob);
    return entry.url;
  })();
  photoCache.set(id, entry);
  // Preload failures are shown only when that photo is selected.
  entry.promise.catch(() => {});
  return entry.promise;
}
export async function showPhoto(direction = 0) {
  clearTimeout(state.photoTimer);
  const request = ++photoRequest;
  if (state.tab !== 'photos' || !state.data.photos.length) {
    clearPhotoCache();
    return;
  }
  const key = JSON.stringify([Boolean(state.screen.shuffle), state.data.photos.map((p) => p.id)]);
  if (key !== photoOrderKey) {
    photoOrderKey = key;
    photoOrder = [...state.data.photos];
    if (state.screen.shuffle) {
      for (let i = photoOrder.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [photoOrder[i], photoOrder[j]] = [photoOrder[j], photoOrder[i]];
      }
    }
    state.photoIndex = 0;
  }
  state.photoIndex = (state.photoIndex + direction + photoOrder.length) % photoOrder.length;
  const current = photoOrder[state.photoIndex],
    img = $('#photo');
  if (!img) {
    actions.render();
    return;
  }
  const upcoming = Array.from(
    {
      length: Math.min(5, photoOrder.length - 1)
    },
    (_, i) => photoOrder[(state.photoIndex + i + 1) % photoOrder.length]
  );
  clearPhotoCache(new Set([current.id, ...upcoming.map((p) => p.id)]));
  img.style.objectFit = state.screen.crop ? 'cover' : 'contain';
  $('#photo-caption').textContent =
    `${current.album} · ${state.photoIndex + 1} / ${photoOrder.length}`;
  try {
    const url = await loadPhoto(current.id);
    if (request !== photoRequest || !img.isConnected) return;
    img.onload = () => {
      if (!state.paused)
        state.photoTimer = setTimeout(() => showPhoto(1), state.data.config.slide_seconds * 1000);
    };
    img.onerror = () => {
      clearTimeout(state.photoTimer);
      $('.photo-stage').innerHTML =
        '<p role="alert" style="color:white;padding:30px">De foto’s zijn momenteel niet beschikbaar. Probeer het later opnieuw.</p>';
    };
    img.dataset.assetId = current.id;
    img.src = url;
    for (const photo of upcoming) loadPhoto(photo.id);
  } catch (error) {
    if (request !== photoRequest || !img.isConnected || error.name === 'AbortError') return;
    $('.photo-stage').innerHTML =
      `<p role="alert" style="color:white;padding:30px">${esc(error.message)}</p>`;
  }
}

export function stopPhotos() {
  ++photoRequest;
  clearPhotoCache();
}

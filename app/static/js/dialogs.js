import { $, esc } from './helpers.js';
import { state } from './state.js';
import { icon } from './icons.js';
import { actions } from './actions.js';

export function toast(message) {
  $('#toast').textContent = message;
  $('#toast').classList.remove('hidden');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => $('#toast').classList.add('hidden'), 4200);
}
export function hasInput() {
  return $('#dialog').open || !!$('#quick-add input')?.value;
}
export function bindBackdropClose(dialog, onClose = () => dialog.close()) {
  dialog.addEventListener('click', (event) => {
    const bounds = dialog.getBoundingClientRect();
    const outside =
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom;
    if (event.target === dialog && outside) onClose();
  });
}
export function modal(title, content) {
  state.dialogDirty = false;
  $('#dialog-content').innerHTML =
    `<div class="modal-head"><h2>${title}</h2><button id="close-dialog" aria-label="Sluiten">${icon('close')}</button></div>${content}<div id="form-error" class="form-error hidden" role="alert"></div>`;
  $('#close-dialog').onclick = closeDialog;
  if (!$('#dialog').open) $('#dialog').showModal();
  $('#dialog').oninput = () => (state.dialogDirty = true);
}
export function confirmDiscard(onLeave, message = 'Niet-opgeslagen invoer verlaten?') {
  const confirmation = $('#discard-confirmation');
  $('#discard-confirmation-message').textContent = message;
  $('#keep-editing').onclick = () => confirmation.close();
  $('#leave-without-saving').onclick = () => {
    confirmation.close();
    onLeave();
  };
  confirmation.showModal();
}
export function closeDialog() {
  if (state.dialogDirty) return confirmDiscard(() => finishCloseDialog());
  finishCloseDialog();
}
export function finishCloseDialog() {
  $('#dialog').close();
  state.dialogDirty = false;
  if (state.pendingRefresh) actions.render();
}
export function errorInForm(err) {
  $('#form-error').textContent =
    err.message +
    (err.status === 409
      ? ' Je invoer blijft staan. Sluit dit venster en open het item opnieuw om de nieuwste versie te bewerken.'
      : '');
  $('#form-error').classList.remove('hidden');
}
export function bindForm(fn, afterSave, onSaved) {
  $('#edit-form').onsubmit = async (e) => {
    e.preventDefault();
    const buttons = e.target.querySelectorAll('button');
    buttons.forEach((b) => (b.disabled = true));
    $('#form-error').classList.add('hidden');
    try {
      await fn(new FormData(e.target));
      state.dialogDirty = afterSave ? afterSave() : false;
      if (!state.dialogDirty) $('#dialog').close();
      await actions.refresh(true);
      if (onSaved) await onSaved();
      toast('Opgeslagen');
    } catch (err) {
      errorInForm(err);
      if (err.status === 409) await actions.refresh();
    } finally {
      buttons.forEach((b) => (b.disabled = false));
    }
  };
}
export const field = (label, name, value = '', type = 'text', extra = '') =>
  `<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${extra}></label>`;

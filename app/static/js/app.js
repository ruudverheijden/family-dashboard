import { isGameOpen } from './games/index.js';
import { icon } from './icons.js';
import { applyTheme, navigate, operation, refresh, render } from './shell.js';
import { $ } from './helpers.js';
import { bindBackdropClose, closeDialog, hasInput } from './dialogs.js';
import { openAdmin, renderAdmin } from './admin.js';
import { state } from './state.js';
import {
  syncAgendaColumnWidths,
  syncClockToAgendaBlock,
  updateCurrentTimeIndicator,
  updateHeaderDate
} from './calendar.js';
import { actions } from './actions.js';
import { editEntity, showHistory, showTemplates } from './editor.js';
import { updateChildRoutineSelection } from './child-mode.js';

Object.assign(actions, {
  render,
  refresh,
  operation,
  navigate,
  openAdmin,
  editEntity,
  showTemplates,
  showHistory,
  renderAdmin
});

document.querySelectorAll('[data-icon]').forEach((e) => (e.innerHTML = icon(e.dataset.icon)));
applyTheme();
$('#dialog').addEventListener('cancel', (e) => {
  e.preventDefault();
  closeDialog();
});
document.querySelectorAll('dialog').forEach((dialog) => {
  bindBackdropClose(dialog, dialog === $('#dialog') ? closeDialog : () => dialog.close());
});
$('#admin').onclick = openAdmin;
$('#connection-retry').onclick = () => refresh(true);
const clock = $('#analog-clock');
const clockDialog = $('#clock-dialog');
$('#clock-toggle').onclick = () => {
  const popupFace = $('#clock-popup-face');
  if (!popupFace.firstElementChild) {
    const largeClock = clock.cloneNode(true);
    largeClock.removeAttribute('id');
    largeClock.removeAttribute('role');
    largeClock.removeAttribute('tabindex');
    largeClock.removeAttribute('aria-haspopup');
    largeClock.removeAttribute('aria-controls');
    largeClock.removeAttribute('aria-label');
    largeClock.style.width = '';
    largeClock.style.height = '';
    largeClock.classList.add('clock-popup-face');
    largeClock.querySelectorAll('[id]').forEach((element) => element.removeAttribute('id'));
    popupFace.append(largeClock);
  }
  clockDialog.showModal();
};
$('#clock-close').onclick = () => clockDialog.close();
window.addEventListener('beforeunload', (e) => {
  if (state.dialogDirty || $('#quick-add input')?.value) {
    e.preventDefault();
    e.returnValue = '';
  }
});
for (const event of ['pointerdown', 'keydown', 'input'])
  document.addEventListener(
    event,
    () => {
      state.lastActivity = Date.now();
    },
    {
      passive: true
    }
  );
setInterval(() => {
  if (
    state.screen.idle > 0 &&
    Date.now() - state.lastActivity > state.screen.idle * 60000 &&
    !hasInput() &&
    !isGameOpen() &&
    !(state.tab === 'calendar' && state.sub === 'routines') &&
    state.data?.photos.length &&
    state.tab !== 'photos'
  ) {
    state.tab = 'photos';
    render();
  }
  updateHeaderDate();
  if (state.data) {
    updateCurrentTimeIndicator();
    if (updateChildRoutineSelection()) render();
  }
}, 1000);
window.addEventListener('resize', () => {
  syncAgendaColumnWidths();
  syncClockToAgendaBlock();
});
new ResizeObserver(syncClockToAgendaBlock).observe($('#calendar-date'));
syncClockToAgendaBlock();
matchMedia('(max-width:760px)').addEventListener('change', (event) => {
  if (state.calendarViewPreference) return;
  state.view = event.matches ? 'day' : 'week';
  if (state.data && state.tab === 'calendar' && state.sub === 'agenda') refresh(true);
});
setInterval(() => {
  if (!document.hidden) refresh();
}, 1500);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) refresh(true);
});
refresh();

import { state } from './state.js';
import { $, avatar, esc, personName, plusDay, today, uuid } from './helpers.js';
import { api, mutate } from './api.js';
import {
  calendarShell,
  eventLocalParts,
  renderCalendarStatus,
  syncAgendaColumnWidths,
  updateHeaderDate
} from './calendar.js';
import { homeView } from './home.js';
import { groceriesView } from './groceries.js';
import { stopPhotos, photosView, showPhoto } from './photos.js';
import { icon } from './icons.js';
import { childModeView } from './child-mode.js';
import { requestReward, rewardsView } from './rewards.js';
import { toast } from './dialogs.js';
import { actions } from './actions.js';
import { celebrateRoutineCompletion, celebrateTaskCompletion } from './celebrations.js';

const taskHideTimers = new Map();

function delayCompletedTaskHide(runId) {
  clearTimeout(taskHideTimers.get(runId));
  state.agendaTasksAwaitingHide.add(runId);
  taskHideTimers.set(
    runId,
    setTimeout(() => {
      taskHideTimers.delete(runId);
      state.agendaTasksAwaitingHide.delete(runId);
      render();
    }, 5000)
  );
}

function cancelCompletedTaskHide(runId) {
  clearTimeout(taskHideTimers.get(runId));
  taskHideTimers.delete(runId);
  state.agendaTasksAwaitingHide.delete(runId);
}

export function applyTheme() {
  document.documentElement.dataset.theme = state.darkMode ? 'dark' : 'light';
  document.documentElement.style.colorScheme = state.darkMode ? 'dark' : 'light';
  $('meta[name="theme-color"]').content = state.darkMode ? '#171b18' : '#f7f5f0';
}
export async function refresh(force = false) {
  if (state.busy) {
    state.pendingRefresh = true;
    return;
  }
  state.busy = true;
  try {
    const params = new URLSearchParams();
    if (state.day) params.set('day', state.day);
    if (state.tab === 'calendar' && state.sub === 'agenda' && state.view !== 'day')
      params.set('period', state.view === 'week' ? 'week' : 'three-day');
    const query = params.toString();
    const fresh = await api('/api/state' + (query ? '?' + query : ''));
    $('#connection').classList.add('hidden');
    const serialized = JSON.stringify(fresh);
    state.data = fresh;
    if (!state.day) state.day = fresh.day;
    if (serialized !== state.lastJSON || force || state.pendingRefresh) {
      state.lastJSON = serialized;
      if (
        !$('#dialog').open &&
        !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)
      )
        render();
      else state.pendingRefresh = true;
    }
  } catch (e) {
    const message =
      e.status >= 500
        ? `De server gaf een foutmelding (${e.status}). ${e.message}`
        : e.status
          ? `Het dashboard kon niet worden geladen (${e.status}). ${e.message}`
          : e.networkError
            ? 'Geen verbinding met de server. Controleer de verbinding en probeer opnieuw.'
            : e.message;
    if (state.data) {
      $('#connection [data-connection-message]').textContent = message;
      $('#connection').classList.remove('hidden');
    } else {
      $('#connection').classList.add('hidden');
      if (!$('#retry-load')) {
        $('#app').innerHTML =
          `<section class="load-error" role="alert"><h2>Het dashboard kon niet worden geladen</h2><p id="load-error-message"></p><button id="retry-load" class="primary">Opnieuw proberen</button></section>`;
        $('#retry-load').onclick = () => refresh(true);
      }
      $('#load-error-message').textContent = message;
    }
  } finally {
    state.busy = false;
  }
}
export function render() {
  if (!state.data) return;
  const previousAgendaScroll = $('.calendar-time-scroll');
  if (previousAgendaScroll) {
    state.agendaScrollKey = previousAgendaScroll.dataset.days;
    state.agendaScrollTop = previousAgendaScroll.scrollTop;
  }
  document.querySelectorAll('[data-tab]').forEach((b) => {
    const active = b.dataset.tab === state.tab;
    b.classList.toggle('active', active);
    if (active) b.setAttribute('aria-current', 'page');
    else b.removeAttribute('aria-current');
  });
  document.body.classList.toggle(
    'integration-view',
    state.tab === 'home' || state.tab === 'photos'
  );
  document.body.classList.toggle('child-mode', state.childMode);
  $('#child-profile-switcher').innerHTML = state.data.members
    .filter((member) => (member.role || 'child') === 'child')
    .map(
      (member) =>
        `<button type="button" class="child-profile-button" data-child-mode="enter" data-child-profile="${esc(member.id)}" aria-label="Kindmodus voor ${esc(member.name)}" title="${esc(member.name)}">${avatar(member)}</button>`
    )
    .join('');
  updateHeaderDate();
  updateBrand();
  $('#app').innerHTML =
    state.tab === 'calendar'
      ? state.childMode
        ? childModeView()
        : calendarShell()
      : state.tab === 'home'
        ? homeView()
        : state.tab === 'groceries'
          ? groceriesView()
          : photosView();
  renderCalendarStatus();
  const plannerNav = $('.subnav');
  if (plannerNav) {
    const rewardsTab = document.createElement('button');
    rewardsTab.dataset.sub = 'rewards';
    rewardsTab.className = state.sub === 'rewards' ? 'active' : '';
    rewardsTab.innerHTML = `${icon('gift')}Beloningen`;
    plannerNav.append(rewardsTab);
    if (state.sub === 'rewards')
      $('.workspace').innerHTML = `${plannerNav.outerHTML}${rewardsView()}`;
  }
  bindContent();
  const agendaScroll = $('.calendar-time-scroll');
  if (agendaScroll) {
    const scrollKey = agendaScroll.dataset.days;
    if (scrollKey === state.agendaScrollKey && state.agendaScrollTop !== null) {
      agendaScroll.scrollTop = state.agendaScrollTop;
    } else {
      const currentDay = today();
      const currentIndex = scrollKey.split(',').indexOf(currentDay);
      if (currentIndex >= 0) {
        const now = eventLocalParts(new Date().toISOString());
        agendaScroll.scrollTop = Math.max(0, Math.min(18 * 60, now.minutes - 2 * 60));
      }
      state.agendaScrollKey = scrollKey;
      state.agendaScrollTop = agendaScroll.scrollTop;
    }
  }

  function updateBrand() {
    const { brand_title: title, brand_subtitle: subtitle, brand_image: image } = state.data.config;
    const logo = $('.brandmark');
    logo.innerHTML = image
      ? `<img src="/brand-image/${state.data.config.brand_version}" alt="">`
      : '<span>s</span><span>✳</span>';
    $('#brand-title').textContent = title;
    $('#brand-caption').textContent = subtitle;
    $('.brand').setAttribute('aria-label', `${title} startpagina`);
    document.title = `${title} — gezinsdashboard`;
  }
  syncAgendaColumnWidths();
  if (state.tab === 'photos') showPhoto();
  else {
    stopPhotos();
  }
  state.pendingRefresh = false;
}
export async function operation(fn, button) {
  if (button) button.disabled = true;
  try {
    await fn();
    await refresh(true);
  } catch (e) {
    toast(e.message);
    if (e.status === 409) await refresh(true);
  } finally {
    if (button) button.disabled = false;
  }
}
export function bindContent() {
  document.querySelectorAll('[data-child-mode="enter"]').forEach(
    (button) =>
      (button.onclick = () => {
        const selectedChild = state.data.members.find(
          (member) =>
            member.id === button.dataset.childProfile && (member.role || 'child') === 'child'
        );
        if (!selectedChild) return;
        state.childModeReturn = {
          tab: state.tab,
          sub: state.sub,
          member: state.member,
          day: state.day,
          view: state.view
        };
        state.childMode = true;
        state.tab = 'calendar';
        state.member = selectedChild.id;
        state.day = today();
        state.view = 'day';
        refresh(true);
      })
  );
  document.querySelectorAll('[data-child-mode="exit"]').forEach(
    (button) =>
      (button.onclick = () => {
        state.childMode = false;
        if (state.childModeReturn) Object.assign(state, state.childModeReturn);
        state.childModeReturn = null;
        render();
        refresh(true);
      })
  );
  document.querySelectorAll('[data-child-member]').forEach(
    (button) =>
      (button.onclick = () => {
        const selectedMember = state.data.members.find(
          (member) => member.id === button.dataset.childMember
        );
        if (!selectedMember || (selectedMember.role || 'child') !== 'child') return;
        state.member = selectedMember.id;
        render();
      })
  );
  document
    .querySelectorAll('[data-tab]')
    .forEach((b) => (b.onclick = () => navigate(b.dataset.tab, b.dataset.sub)));
  document.querySelectorAll('[data-member]').forEach(
    (b) =>
      (b.onclick = () => {
        state.member = b.dataset.member;
        render();
      })
  );
  document
    .querySelectorAll('[data-sub]')
    .forEach((b) => (b.onclick = () => navigate('calendar', b.dataset.sub)));
  document.querySelectorAll('[data-view]').forEach(
    (b) =>
      (b.onclick = () => {
        state.view = b.dataset.view;
        state.calendarViewPreference = state.view;
        try {
          localStorage.setItem('samen-calendar-view', state.view);
        } catch {
          toast('De agendaweergave kan niet op dit scherm worden opgeslagen.');
        }
        refresh(true);
      })
  );
  document.querySelectorAll('[data-date]').forEach(
    (b) =>
      (b.onclick = () => {
        state.day = plusDay(state.day, Number(b.dataset.date));
        refresh(true);
      })
  );
  document.querySelectorAll('[data-day]').forEach(
    (b) =>
      (b.onclick = () => {
        state.day = b.dataset.day;
        refresh(true);
      })
  );
  document
    .querySelectorAll('[data-new]')
    .forEach((b) => (b.onclick = () => actions.editEntity(b.dataset.new)));
  document.querySelectorAll('[data-edit]').forEach(
    (b) =>
      (b.onclick = () => {
        const [k, id] = b.dataset.edit.split(':');
        actions.editEntity(
          k,
          state.data[k].find((x) => x.id === id)
        );
      })
  );
  document.querySelectorAll('[data-run]').forEach(
    (b) =>
      (b.onclick = () =>
        operation(async () => {
          const r = state.data.runs.find((x) => x.id === b.dataset.run),
            step = Number(b.dataset.step),
            completing = !r.done.includes(step),
            done = completing ? [...r.done, step] : r.done.filter((s) => s !== step);
          await mutate('runs', r, {
            done
          });
          if (r.kind === 'tasks') {
            if (completing) delayCompletedTaskHide(r.id);
            else cancelCompletedTaskHide(r.id);
          }
          if (completing) {
            if (r.kind === 'routines') {
              if (done.length === r.body.steps.length)
                celebrateRoutineCompletion(personName(r.member));
            } else celebrateTaskCompletion(b);
          }
        }, b))
  );
  document.querySelectorAll('[data-grocery]').forEach(
    (b) =>
      (b.onclick = () =>
        operation(async () => {
          const g = state.data.groceries.find((x) => x.id === b.dataset.grocery);
          await mutate('groceries', g, {
            ...g,
            done: !g.done
          });
        }, b))
  );
  document
    .querySelectorAll('[data-action]')
    .forEach((b) => (b.onclick = () => action(b.dataset.action, b)));
  document
    .querySelectorAll('[data-request-reward]')
    .forEach((b) => (b.onclick = () => requestReward(b.dataset.requestReward, b)));
  document.querySelectorAll('[data-photo]').forEach(
    (b) =>
      (b.onclick = () => {
        if (b.dataset.photo === 'pause') {
          state.paused = !state.paused;
          render();
        } else showPhoto(b.dataset.photo === 'prev' ? -1 : 1);
      })
  );
  const form = $('#quick-add');
  if (form) {
    form.elements.namedItem('name').oninput = () => {
      state.quickDraft = form.elements.namedItem('name').value;
    };
    let submission;
    form.onsubmit = async (e) => {
      e.preventDefault();
      if (!submission || submission.name !== form.elements.namedItem('name').value.trim())
        submission = {
          name: form.elements.namedItem('name').value.trim(),
          id: uuid(),
          request: uuid()
        };
      const b = form.querySelector('button');
      b.disabled = true;
      try {
        await mutate(
          'groceries',
          {
            id: submission.id,
            version: 0
          },
          {
            name: submission.name,
            done: false
          },
          'save',
          submission.request
        );
        form.reset();
        state.quickDraft = '';
        submission = null;
        document.activeElement.blur();
        await refresh(true);
        toast('Toegevoegd aan jullie lijst');
      } catch (err) {
        toast(err.message);
      } finally {
        b.disabled = false;
      }
    };
  }
}
export function navigate(next, section) {
  if (
    $('#quick-add input')?.value &&
    !confirm('Je hebt nog een niet-opgeslagen boodschap. Invoer verlaten?')
  )
    return;
  state.quickDraft = '';
  state.tab = next;
  if (section) state.sub = section;
  clearTimeout(state.photoTimer);
  render();
}
export async function action(name, button) {
  if (name === 'admin') return actions.openAdmin();
  if (name === 'today') {
    state.day = today();
    return refresh(true);
  }
  if (name === 'history') return actions.showHistory();
  if (name.startsWith('templates-')) return actions.showTemplates(name.slice(10));
  if (name === 'clear-groceries') {
    if (!confirm('Alle afgevinkte boodschappen verwijderen?')) return;
    await operation(async () => {
      for (const g of state.data.groceries.filter((x) => x.done))
        await mutate('groceries', g, {}, 'delete');
    }, button);
  }
}

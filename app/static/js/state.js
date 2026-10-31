/** Shared screen state. Feature modules keep their private caches and drafts locally. */
export const state = {
  calendarViewPreference: null,
  data: undefined,
  day: '',
  tab: 'calendar',
  sub: 'agenda',
  member: '',
  view: '',
  lastJSON: '',
  busy: false,
  pendingRefresh: false,
  dialogDirty: false,
  photoIndex: 0,
  paused: false,
  photoTimer: undefined,
  lastActivity: Date.now(),
  adminCfg: undefined,
  quickDraft: '',
  agendaScrollKey: '',
  agendaScrollTop: null,
  agendaTasksAwaitingHide: new Set(),
  childMode: false,
  childModeReturn: null,
  screen: {},
  darkMode: false
};
try {
  const saved = localStorage.getItem('samen-calendar-view');
  if (['day', 'three-day', 'week'].includes(saved)) state.calendarViewPreference = saved;
} catch {}
state.view =
  state.calendarViewPreference || (matchMedia('(max-width:760px)').matches ? 'day' : 'week');
try {
  state.screen = JSON.parse(localStorage.getItem('samen-screen') || '{}');
} catch {}
try {
  state.darkMode = localStorage.getItem('samen-theme') === 'dark';
} catch {}

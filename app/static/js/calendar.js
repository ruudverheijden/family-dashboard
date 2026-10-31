import { state } from './state.js';
import {
  $,
  avatar,
  empty,
  esc,
  fmt,
  parseDay,
  person,
  personName,
  plusDay,
  today,
  weekdayNames
} from './helpers.js';
import { icon } from './icons.js';
import { rewardsView } from './rewards.js';
import { groceryRow } from './groceries.js';

export function updateHeaderDate() {
  const now = new Date();
  const timezone = state.data?.config.timezone || 'Europe/Amsterdam';
  const date = parseDay(today());
  $('#calendar-date-full').textContent = fmt(date, {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  });
  $('#calendar-date-compact').textContent = fmt(date, {
    weekday: 'short',
    day: 'numeric',
    month: 'short'
  });
  const clockParts = Object.fromEntries(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hourCycle: 'h23'
    })
      .formatToParts(now)
      .filter((part) => part.type !== 'literal')
      .map((part) => [part.type, Number(part.value)])
  );
  const hourAngle = ((clockParts.hour % 12) + clockParts.minute / 60) * 30;
  const minuteAngle = (clockParts.minute + clockParts.second / 60) * 6;
  document
    .querySelectorAll('.hour-hand')
    .forEach((hand) => hand.setAttribute('transform', `rotate(${hourAngle} 36 36)`));
  document
    .querySelectorAll('.minute-hand')
    .forEach((hand) => hand.setAttribute('transform', `rotate(${minuteAngle} 36 36)`));
  document
    .querySelectorAll('.second-hand')
    .forEach((hand) => hand.setAttribute('transform', `rotate(${clockParts.second * 6} 36 36)`));
  const currentTime = fmt(now, {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: timezone
  });
  $('#analog-clock').setAttribute(
    'aria-label',
    `Analoge klok, ${currentTime}. Klik voor een grote klok`
  );
  $('#clock-popup-time').textContent = currentTime;
  const nextEvent = state.data?.events
    ?.filter((event) => (event.all_day ? event.start >= today() : new Date(event.start) > now))
    .sort((a, b) => {
      const start = (event) =>
        event.all_day ? Date.parse(`${event.start}T00:00:00Z`) : new Date(event.start).getTime();
      return start(a) - start(b);
    })[0];
  const nextItem = $('#next-agenda-item');
  if (!nextEvent) {
    nextItem.textContent = 'Geen volgende afspraak gepland';
    nextItem.removeAttribute('title');
    return;
  }
  const eventDate = nextEvent.all_day
    ? new Date(`${nextEvent.start}T12:00:00Z`)
    : new Date(nextEvent.start);
  const isToday = nextEvent.all_day
    ? nextEvent.start === today()
    : eventLocalParts(nextEvent.start).date === today();
  const dateLabel = isToday
    ? ''
    : `${fmt(eventDate, {
        weekday: 'short',
        day: 'numeric',
        month: 'short',
        timeZone: nextEvent.all_day ? 'UTC' : timezone
      })} · `;
  const timeLabel = nextEvent.all_day
    ? 'Hele dag'
    : fmt(eventDate, {
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
        timeZone: timezone
      });
  const label = `${dateLabel}${timeLabel} · ${nextEvent.title}`;
  nextItem.textContent = label;
  nextItem.title = label;
}
export function filteredRuns(kind) {
  return state.data.runs.filter(
    (r) =>
      r.day === state.day &&
      r.kind === kind &&
      (!state.member ||
        r.member === state.member ||
        (r.member === 'shared' && r.body.members.includes(state.member)))
  );
}
export function runsFor(d, kind) {
  return state.data.runs.filter(
    (r) =>
      r.day === d &&
      r.kind === kind &&
      (!state.member ||
        r.member === state.member ||
        (r.member === 'shared' && r.body.members.includes(state.member)))
  );
}
export function eventsFor(d) {
  return state.data.events
    .filter((e) => {
      if (state.member && e.member && e.member !== state.member) return false;
      const start = e.all_day
        ? e.start
        : new Intl.DateTimeFormat('en-CA', {
            timeZone: state.data.config.timezone,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
          }).format(new Date(e.start));
      const end = e.all_day
        ? e.end
        : new Intl.DateTimeFormat('en-CA', {
            timeZone: state.data.config.timezone,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
          }).format(new Date(new Date(e.end).getTime() - 1));
      return start <= d && (e.all_day ? end > d || start === d : end >= d || start === d);
    })
    .sort((a, b) => a.start.localeCompare(b.start));
}
export function syncAgendaColumnWidths() {
  const calendar = $('.timetable-calendar'),
    timeScroll = $('.calendar-time-scroll');
  if (calendar && timeScroll) {
    calendar.style.setProperty(
      '--calendar-scrollbar-width',
      `${timeScroll.offsetWidth - timeScroll.clientWidth}px`
    );
  }
}
export function updateCurrentTimeIndicator() {
  const marker = $('.current-time-indicator');
  if (!marker) return;
  const now = eventLocalParts(new Date().toISOString());
  marker.style.setProperty('--current-time-top', `${now.minutes}px`);
  const label = `Huidige tijd ${fmt(new Date(), {
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZone: state.data.config.timezone
  })}`;
  marker.setAttribute('aria-label', label);
  marker.title = label;
}
export function renderCalendarStatus() {
  const calendars = Object.values(state.data.status)
    .filter((status) => status.calendars?.length)
    .flatMap((status) =>
      status.calendars.map((calendar) => {
        const lastSuccess = status.last_success
          ? fmt(new Date(status.last_success), {
              day: 'numeric',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
              timeZone: state.data.config.timezone
            })
          : '';
        const update = lastSuccess
          ? `${status.ok ? 'Bijgewerkt' : 'Synchronisatie mislukt · laatst bijgewerkt'}: ${lastSuccess}`
          : status.ok
            ? 'Nog niet bijgewerkt'
            : 'Synchronisatie mislukt · nog niet bijgewerkt';
        return `<li class="footer-agenda-entry"><strong>${esc(calendar.name)}</strong><span>${esc(update)}</span></li>`;
      })
    );
  $('#agenda-status').innerHTML = calendars.length
    ? `<section class="footer-agenda-status" aria-label="Agenda-verbindingen"><ul class="footer-agenda-list">${calendars.join('')}</ul></section>`
    : '';
}
export function calendarShell() {
  const openTasks = filteredRuns('tasks').filter((r) => !r.done.length).length;
  const datebar = `<div class="toolbar planner-datebar">${dateNav(state.sub === 'agenda' ? (state.view === 'day' ? 'day' : state.view) : 'day')}${state.sub === 'agenda' ? `<div class="segmented" role="group" aria-label="Agendaweergave"><button data-view="day" class="${state.view === 'day' ? 'active' : ''}" aria-pressed="${state.view === 'day'}">Dag</button><button data-view="three-day" class="${state.view === 'three-day' ? 'active' : ''}" aria-pressed="${state.view === 'three-day'}">3 dagen</button><button data-view="week" class="${state.view === 'week' ? 'active' : ''}" aria-pressed="${state.view === 'week'}">Week</button></div>` : ''}</div>`;
  const guide = !state.data.members.length
    ? `<section class="setup-guide"><div><h2>Begin met jullie gezin</h2><p>Voeg gezinsleden toe. Daarna kun je samen taken plannen.</p></div><div class="setup-actions"><button class="primary" data-action="admin">${icon('plus')}Gezin instellen</button><button class="secondary small" data-action="admin">CalDAV koppelen (optioneel)</button></div></section>`
    : !state.data.tasks.some((task) => !task.archived)
      ? `<section class="setup-guide"><div><h2>Jullie agenda is klaar voor de eerste plannen</h2><p>Voeg een taak toe; die verschijnt vanzelf op de geplande dag. CalDAV is optioneel voor privéafspraken.</p></div><div class="setup-actions"><button class="primary" data-new="tasks">${icon('plus')}Eerste taak toevoegen</button><button class="secondary small" data-action="admin">CalDAV koppelen (optioneel)</button></div></section>`
      : '';
  return `${datebar}<div class="calendar-layout"><section class="family-filter panel" aria-label="Gezinsfilter"><h2 class="section-label">Ons gezin</h2><div class="family-list" role="group" aria-label="Filter agenda op gezinslid"><button class="person ${!state.member ? 'active' : ''}" data-member="" aria-pressed="${!state.member}"><span class="avatar">${icon('people')}</span>Iedereen${!state.member ? '<span class="checkmark" aria-hidden="true">✓</span>' : ''}</button>${state.data.members.map((m) => `<button class="person ${state.member === m.id ? 'active' : ''}" data-member="${m.id}" aria-pressed="${state.member === m.id}">${avatar(m)}${esc(m.name)}${state.member === m.id ? '<span class="checkmark" aria-hidden="true">✓</span>' : ''}</button>`).join('')}</div></section>${guide}<section class="workspace"><nav class="subnav" aria-label="Gezinsplanner">${[
    ['agenda', 'Agenda', 'calendar', ''],
    ['tasks', 'Taken', 'tasks', openTasks],
    ['routines', 'Routines', 'routine', '']
  ]
    .map(
      ([id, label, i, n]) =>
        `<button data-sub="${id}" class="${state.sub === id ? 'active' : ''}" ${state.sub === id ? 'aria-current="page"' : ''}>${icon(i)}${label}${n !== '' ? `<span class="count">${n}</span>` : ''}</button>`
    )
    .join(
      ''
    )}</nav>${state.sub === 'agenda' ? agendaView() : state.sub === 'tasks' ? tasksView() : state.sub === 'routines' ? routinesView() : rewardsView()}</section></div>`;
}
export function dateNav(mode = 'day') {
  const step = mode === 'week' ? 7 : mode === 'three-day' ? 3 : 1;
  const title =
    mode === 'week'
      ? weekTitle()
      : mode === 'three-day'
        ? dateRangeTitle(state.day, 3)
        : fmt(parseDay(state.day), {
            weekday: 'long',
            day: 'numeric',
            month: 'long'
          });
  const period = mode === 'week' ? 'week' : mode === 'three-day' ? '3 dagen' : 'dag';
  return `<div class="date-nav"><h2>${title}</h2><button data-date="-${step}" aria-label="Vorige ${period}">${icon('left')}</button><button data-date="${step}" aria-label="Volgende ${period}">${icon('right')}</button><button data-action="today" class="secondary small">Vandaag</button></div>`;
}
export function weekStart() {
  return plusDay(state.day, -((parseDay(state.day).getDay() + 6) % 7));
}
export function dateRangeTitle(start, count) {
  const end = plusDay(start, count - 1),
    differentMonth = parseDay(start).getMonth() !== parseDay(end).getMonth();
  return `${fmt(
    parseDay(start),
    differentMonth
      ? {
          day: 'numeric',
          month: 'short'
        }
      : {
          day: 'numeric'
        }
  )} – ${fmt(parseDay(end), {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })}`;
}
export function weekTitle() {
  const start = weekStart(),
    end = plusDay(start, 6);
  return `${fmt(
    parseDay(start),
    parseDay(start).getMonth() !== parseDay(end).getMonth()
      ? {
          day: 'numeric',
          month: 'short'
        }
      : {
          day: 'numeric'
        }
  )} – ${fmt(parseDay(end), {
    day: 'numeric',
    month: 'long',
    year: 'numeric'
  })}`;
}
export function agendaTaskCard(r) {
  const task = state.data.tasks.find((t) => t.id === r.template_id) || r.body;
  const owners =
    r.member === 'shared' ? task.members.map(personName).join(', ') : personName(r.member);
  return `<article class="agenda-task ${r.done.length ? 'done' : ''}"><button class="checkbox ${r.done.length ? 'done' : ''}" data-run="${r.id}" data-step="0" aria-label="${r.done.length ? 'Heropen' : 'Voltooi'} ${esc(task.title)}" aria-pressed="${!!r.done.length}">${icon('check')}</button><div class="agenda-task-copy"><strong>${esc(task.icon)} ${esc(task.title)}</strong><small>${esc(owners)}</small></div></article>`;
}
export function eventLocalParts(value) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: state.data.config.timezone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23'
  }).formatToParts(new Date(value));
  const result = Object.fromEntries(
    parts.filter((part) => part.type !== 'literal').map((part) => [part.type, part.value])
  );
  return {
    ...result,
    date: `${result.year}-${result.month}-${result.day}`,
    minutes: Number(result.hour) * 60 + Number(result.minute)
  };
}
export function timedEventsForDay(date) {
  const visibleStart = 0,
    visibleEnd = 24 * 60;
  const timed = [];
  for (const event of eventsFor(date).filter((item) => !item.all_day)) {
    const start = eventLocalParts(event.start),
      end = eventLocalParts(event.end);
    const startMinute = start.date < date ? visibleStart : start.minutes;
    const endMinute = end.date > date ? visibleEnd : end.minutes;
    const from = Math.max(startMinute, visibleStart),
      to = Math.min(endMinute, visibleEnd);
    if (to > from)
      timed.push({
        event,
        start: from,
        end: to
      });
  }
  timed.sort((a, b) => a.start - b.start || a.end - b.end);
  let group = [],
    groupEnd = -1;
  const positionGroup = (items) => {
    const laneEnds = [];
    for (const item of items) {
      let lane = laneEnds.findIndex((end) => end <= item.start);
      if (lane < 0) lane = laneEnds.length;
      laneEnds[lane] = item.end;
      item.lane = lane;
    }
    items.forEach((item) => {
      item.laneCount = Math.max(1, laneEnds.length);
    });
  };
  for (const item of timed) {
    if (group.length && item.start >= groupEnd) {
      positionGroup(group);
      group = [];
      groupEnd = -1;
    }
    group.push(item);
    groupEnd = Math.max(groupEnd, item.end);
  }
  if (group.length) positionGroup(group);
  return {
    timed: timed.map(
      (item) =>
        `<article class="event timed-event" style="--event-top:${item.start - visibleStart}px;--event-height:${item.end - item.start}px;--event-left:${(item.lane / item.laneCount) * 100}%;--event-width:${100 / item.laneCount}%;${eventStyle(item.event)}">${eventContents(item.event)}</article>`
    )
  };
}
export function eventStyle(e) {
  const m = person(e.member);
  return `--event-color:${esc(m?.color || '#839870')};--event-bg:${esc(m?.color || '#839870')}16`;
}
export function eventTime(e) {
  return e.all_day
    ? 'Hele dag'
    : `${fmt(new Date(e.start), {
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
        timeZone: state.data.config.timezone
      })}–${fmt(new Date(e.end), {
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
        timeZone: state.data.config.timezone
      })}`;
}
export function eventContents(e) {
  const m = person(e.member);
  return `<time>${eventTime(e)}</time><strong>${esc(e.title)}</strong><small>${esc(m?.name || e.calendar || personName(e.member))}${e.location ? ' · ' + esc(e.location) : ''}</small>`;
}
export function eventCard(e, className = '') {
  const time = eventTime(e);
  return `<article class="event ${className}" title="${esc(`${time} · ${e.title}`)}" style="${eventStyle(e)}">${eventContents(e)}</article>`;
}
export function agendaView() {
  const days =
    state.view === 'week'
      ? Array.from(
          {
            length: 7
          },
          (_, i) => plusDay(weekStart(), i)
        )
      : state.view === 'three-day'
        ? Array.from(
            {
              length: 3
            },
            (_, i) => plusDay(state.day, i)
          )
        : [state.day];
  const mode = state.view === 'week' ? 'week' : state.view === 'three-day' ? 'three-day' : 'day',
    columns = `52px repeat(${days.length},minmax(0,1fr))`;
  const dayHeaders = days
    .map(
      (d) =>
        `<button class="day-heading ${d === today() ? 'today' : ''} ${d === state.day ? 'selected' : ''}" data-day="${d}" aria-label="Selecteer ${fmt(
          parseDay(d),
          {
            day: 'numeric',
            month: 'long'
          }
        )}" aria-pressed="${d === state.day}"><span>${fmt(parseDay(d), {
          weekday: 'short'
        })}</span><strong>${parseDay(d).getDate()}</strong></button>`
    )
    .join('');
  const taskCells = days
    .map(
      (d) =>
        `<section class="day-column day-task-cell ${d === state.day ? 'selected' : ''}" data-day-column="${d}">${
          runsFor(d, 'tasks')
            .filter((r) => !r.done.length || state.agendaTasksAwaitingHide.has(r.id))
            .map(agendaTaskCard)
            .join('') || '<span class="no-day-tasks">Geen taken</span>'
        }</section>`
    )
    .join('');
  const dailyEvents = days.map((d) => ({
    date: d,
    allDay: eventsFor(d).filter((e) => e.all_day),
    ...timedEventsForDay(d)
  }));
  const allDayRow = dailyEvents.some((column) => column.allDay.length)
    ? `<div class="calendar-row calendar-all-day-row"><div class="calendar-row-label">Hele dag</div>${dailyEvents.map((column) => `<div class="calendar-special-cell">${column.allDay.map((e) => eventCard(e, 'all-day-event')).join('')}</div>`).join('')}</div>`
    : '';
  const hours = Array.from(
    {
      length: 25
    },
    (_, i) =>
      `<span class="calendar-hour-label ${i === 0 ? 'first' : ''} ${i === 24 ? 'last' : ''}" style="top:${i * 60}px">${String(i).padStart(2, '0')}:00</span>`
  ).join('');
  const lines = Array.from(
    {
      length: 24
    },
    (_, i) => `<span class="calendar-hour-line" style="top:${i * 60}px"></span>`
  ).join('');
  const schedules = dailyEvents
    .map(
      (column) =>
        `<section class="day-timeline ${column.date === state.day ? 'selected' : ''}" data-timeline-day="${column.date}"><div class="calendar-hour-lines" aria-hidden="true">${lines}</div>${column.timed.join('')}</section>`
    )
    .join('');
  const currentTime = days.includes(today())
    ? `<div class="current-time-indicator" role="img" aria-label="Huidige tijd" style="--current-time-top:${eventLocalParts(new Date().toISOString()).minutes}px"></div>`
    : '';
  return `<div class="calendar timetable-calendar ${state.view === 'day' ? 'day-view' : ''} ${state.view === 'three-day' ? 'three-day-view' : ''}" style="--calendar-columns:${columns};--calendar-days:${days.length}" aria-label="${state.view === 'week' ? 'Weekagenda' : state.view === 'three-day' ? '3-daagse agenda' : 'Dagagenda'}"><div class="calendar-row calendar-day-headings"><div class="calendar-row-label"></div>${dayHeaders}</div><div class="calendar-row calendar-task-row"><div class="calendar-row-label">Taken</div>${taskCells}</div>${allDayRow}<div class="calendar-time-scroll" data-days="${days.join(',')}" tabindex="0" aria-label="Tijdlijn, scroll verticaal om andere tijden te bekijken"><div class="calendar-schedule-row"><div class="calendar-time-axis">${hours}</div><div class="calendar-day-schedules">${schedules}${currentTime}</div></div></div></div><div class="bottom-grid"><section class="panel"><div class="card-title"><h2>Te doen op ${fmt(
    parseDay(state.day),
    {
      day: 'numeric',
      month: 'short'
    }
  )}</h2><button data-sub="tasks">Alle taken ${icon('right')}</button></div><div class="list">${
    filteredRuns('tasks')
      .filter((r) => !r.done.length)
      .slice(0, 2)
      .map(taskRow)
      .join('') ||
    '<div class="empty compact"><p>Alles rustig hier. Voeg een taak toe voor vandaag.</p></div>'
  }</div></section><section class="panel"><div class="card-title"><h2>Niet vergeten in de winkel</h2><button data-tab="groceries">De lijst ${icon('right')}</button></div><div class="list">${
    state.data.groceries
      .filter((g) => !g.done)
      .slice(0, 2)
      .map(groceryRow)
      .join('') ||
    '<div class="empty compact"><p>De boodschappenlijst is nog leeg. Wat hebben we nodig?</p></div>'
  }</div></section></div>`;
}
export function taskSchedule(task) {
  if (task.repeat === 'once')
    return `Eenmalig · ${fmt(parseDay(task.date), {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    })}`;
  if (task.repeat === 'daily') return 'Elke dag';
  return weekdayNames.filter((_, i) => task.weekdays?.includes(i)).join(', ');
}
export function taskRow(r) {
  const task = state.data.tasks.find((t) => t.id === r.template_id) || r.body;
  const owners = task.members.map((id) => person(id)?.name).filter(Boolean);
  return `<div class="task-row"><button class="checkbox ${r.done.length ? 'done' : ''}" data-run="${r.id}" data-step="0" aria-label="${r.done.length ? 'Heropen' : 'Voltooi'} ${esc(task.title)}" aria-pressed="${!!r.done.length}">${icon('check')}</button><span class="task-icon">${esc(task.icon)}</span><div class="row-text ${r.done.length ? 'done' : ''}"><strong>${esc(task.title)}</strong><small class="task-owners">Voor: ${esc(owners.join(', ') || personName(r.member))}</small>${task.description ? `<small>${esc(task.description)}</small>` : ''}<span class="task-schedule">${esc(taskSchedule(task))}</span></div>${task.points ? `<span class="points">✦ ${task.points}</span>` : ''}<button data-edit="tasks:${r.template_id}" aria-label="Taak bewerken">${icon('edit')}</button></div>`;
}
export function tasksView() {
  const runs = filteredRuns('tasks');
  return `<div class="toolbar"><button class="primary" data-new="tasks">${icon('plus')}Nieuwe taak</button></div><div class="list">${runs.map(taskRow).join('') || empty('Kleine taken, samen gedaan.', 'Voeg een eenmalige of terugkerende taak toe. Ieder gezinslid kan een eigen uitvoering krijgen.', 'tasks', `<button class="primary" data-new="tasks">${icon('plus')}Eerste taak toevoegen</button>`)}</div><div class="toolbar" style="margin-top:20px"><button class="subtle-button" data-action="templates-tasks">Taaksjablonen beheren</button><button class="subtle-button" data-action="history">${icon('history')}Historie bekijken</button></div>`;
}
export function routinesView() {
  const runs = filteredRuns('routines');
  const templates = state.data.routines.filter(
    (r) => !r.archived && (!state.member || r.members.includes(state.member))
  );
  const runsByTemplate = new Map();
  runs.forEach((run) => {
    if (!runsByTemplate.has(run.template_id)) runsByTemplate.set(run.template_id, []);
    runsByTemplate.get(run.template_id).push(run);
  });
  const cards = runs.length
    ? [...runsByTemplate.values()]
        .map((group) => {
          const routine = group[0].body;
          const progress = group
            .map(
              (r) =>
                `<div class="routine-member-progress">${avatar(person(r.member))}<span>${esc(personName(r.member))} · ${r.done.length} van ${r.body.steps.length} stappen klaar</span><div class="progress" aria-label="${r.done.length} van ${r.body.steps.length} stappen voltooid"><span style="width:${(r.done.length / r.body.steps.length) * 100}%"></span></div></div>`
            )
            .join('');
          const steps = routine.steps
            .map((s, i) => {
              const complete = group.every((r) => r.done.includes(i));
              const controls = group
                .map(
                  (r) =>
                    `<span class="routine-step-owner" title="${esc(personName(r.member))}">${avatar(person(r.member))}<button class="checkbox ${r.done.includes(i) ? 'done' : ''}" data-run="${r.id}" data-step="${i}" aria-label="${r.done.includes(i) ? 'Heropen' : 'Voltooi'} ${esc(s.text)} voor ${esc(personName(r.member))}" aria-pressed="${r.done.includes(i)}">${icon('check')}</button></span>`
                )
                .join('');
              return `<div class="step ${complete ? 'done' : ''}"><span class="routine-step-label">${esc(s.icon)} ${esc(s.text)}</span><div class="routine-step-controls">${controls}</div></div>`;
            })
            .join('');
          return `<section class="panel"><div class="routine-header"><div><h2>${esc(routine.icon)} ${esc(routine.title)}</h2><small>${esc(group.map((r) => personName(r.member)).join(', '))} · ${esc(routine.start_time)} – ${esc(routine.end_time)}</small></div><button data-edit="routines:${group[0].template_id}" aria-label="Routine bewerken">${icon('edit')}</button></div><div class="routine-member-progress-list">${progress}</div>${steps}</section>`;
        })
        .join('')
    : templates.length
      ? `<section class="panel"><h2>Geen routine gepland op ${esc(
          fmt(parseDay(state.day), {
            weekday: 'long'
          })
        )}</h2><p>Hieronder staan de actieve routines op hun ingeplande dagen.</p></section>${templates
          .map(
            (r) =>
              `<section class="panel routine-preview"><div class="routine-header"><div><h2>${esc(r.icon)} ${esc(r.title)}</h2><small>${esc(r.members.map(personName).join(', '))} · ${esc(r.start_time)} – ${esc(r.end_time)}</small></div><button data-edit="routines:${r.id}" aria-label="Routine bewerken">${icon('edit')}</button></div><p class="small muted">Gepland: ${esc(weekdayNames.filter((_, i) => r.weekdays.includes(i)).join(', '))}${
                r.date > state.day
                  ? ` · Startdatum: ${esc(
                      fmt(parseDay(r.date), {
                        weekday: 'long',
                        day: 'numeric',
                        month: 'long'
                      })
                    )}`
                  : ''
              }</p>${r.steps.map((s) => `<div class="step"><span>${esc(s.icon)} ${esc(s.text)}</span></div>`).join('')}</section>`
          )
          .join('')}`
      : empty(
          'Een fijn ritme voor elke dag.',
          'Maak een ochtend- of avondroutine met stappen, gezinsleden en vaste weekdagen.',
          'routine',
          `<button class="primary" data-new="routines">${icon('plus')}Eerste routine maken</button>`
        );
  return `<div class="toolbar"><button class="primary" data-new="routines">${icon('plus')}Nieuwe routine</button></div><div class="routine-grid">${cards}</div><div class="toolbar" style="margin-top:20px"><button class="subtle-button" data-action="templates-routines">Routinesjablonen beheren</button><button class="subtle-button" data-action="history">${icon('history')}Historie bekijken</button></div>`;
}
export function syncClockToAgendaBlock() {
  const height = $('#calendar-date').getBoundingClientRect().height;
  if (height > 0) {
    $('#analog-clock').style.width = `${height}px`;
    $('#analog-clock').style.height = `${height}px`;
  }
}

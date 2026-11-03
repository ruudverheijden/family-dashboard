import { state } from './state.js';
import { avatar, esc, fmt, parseDay, person, personName } from './helpers.js';
import { icon } from './icons.js';

let routineSelection = { day: '', member: '', runId: '', manual: false };

function runsForMember(kind) {
  return state.data.runs.filter(
    (run) =>
      run.day === state.day &&
      run.kind === kind &&
      (run.member === state.member ||
        (run.member === 'shared' && run.body.members.includes(state.member)))
  );
}

function routinesForMember() {
  const routines = new Map();
  for (const run of runsForMember('routines')) {
    const group = routines.get(run.template_id) || [];
    group.push(run);
    routines.set(run.template_id, group);
  }
  return [...routines.values()]
    .map((group) => group[0])
    .sort((a, b) => {
      const startA = a.body.start_time || '';
      const startB = b.body.start_time || '';
      if (!startA && startB) return 1;
      if (startA && !startB) return -1;
      return startA.localeCompare(startB) || a.body.title.localeCompare(b.body.title, 'nl');
    });
}

function isRoutineDone(run) {
  return run.done.length >= run.body.steps.length;
}

function minutesOfDay(value) {
  const [hours, minutes] = value.split(':').map(Number);
  return hours * 60 + minutes;
}

function currentMinutes() {
  const timezone = state.data.config.timezone || 'Europe/Amsterdam';
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: timezone,
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23'
    })
      .formatToParts(new Date())
      .filter((part) => part.type !== 'literal')
      .map((part) => [part.type, Number(part.value)])
  );
  return parts.hour * 60 + parts.minute;
}

function preferredRoutine(routines) {
  const incompleteTimed = routines.filter((run) => run.body.start_time && !isRoutineDone(run));
  const now = currentMinutes();
  const active = incompleteTimed.find((run) => {
    const start = minutesOfDay(run.body.start_time);
    const end = minutesOfDay(run.body.end_time);
    return start <= now && now < end;
  });
  if (active) return active;

  const upcoming = incompleteTimed.find((run) => minutesOfDay(run.body.start_time) >= now);
  if (upcoming) return upcoming;

  return routines.find((run) => !run.body.start_time && !isRoutineDone(run)) || routines[0];
}

function synchronizeRoutineSelection(routines) {
  const memberChanged =
    routineSelection.day !== state.day || routineSelection.member !== state.member;
  const selected = routines.find((run) => run.id === routineSelection.runId);
  if (memberChanged || !selected) {
    const preferred = preferredRoutine(routines);
    routineSelection = {
      day: state.day,
      member: state.member,
      runId: preferred?.id || '',
      manual: false
    };
    return;
  }
  if (!routineSelection.manual) {
    const preferred = preferredRoutine(routines);
    if (preferred && preferred.id !== selected.id) routineSelection.runId = preferred.id;
  }
}

export function updateChildRoutineSelection() {
  if (!state.childMode || !state.data) return false;
  const routines = routinesForMember();
  const previous = routineSelection.runId;
  synchronizeRoutineSelection(routines);
  return previous !== routineSelection.runId;
}

export function resetChildRoutineSelection() {
  routineSelection = { day: '', member: '', runId: '', manual: false };
}

export function navigateChildRoutine(offset) {
  const routines = routinesForMember();
  synchronizeRoutineSelection(routines);
  const index = routines.findIndex((run) => run.id === routineSelection.runId);
  const next = routines[index + offset];
  if (!next) return false;
  routineSelection.runId = next.id;
  routineSelection.manual = true;
  return true;
}

function taskCard(run) {
  const task = state.data.tasks.find((item) => item.id === run.template_id) || run.body;
  const done = run.done.length > 0;
  return `<article class="child-task ${done ? 'done' : ''}"><button class="checkbox ${done ? 'done' : ''}" data-run="${run.id}" data-step="0" aria-label="${done ? 'Heropen' : 'Voltooi'} ${esc(task.title)}" aria-pressed="${done}">${icon('check')}</button><div class="child-task-copy"><span class="child-task-icon" aria-hidden="true">${esc(task.icon)}</span><div><h3>${esc(task.title)}</h3>${task.description ? `<p>${esc(task.description)}</p>` : ''}${done ? '<span class="child-done-label">Klaar!</span>' : ''}</div></div></article>`;
}

function routineClock(startTime) {
  const [hours, minutes] = startTime.split(':').map(Number);
  const hourAngle = ((hours % 12) + minutes / 60) * 30;
  const minuteAngle = minutes * 6;
  return `<div class="child-routine-time"><svg class="child-routine-clock" viewBox="0 0 72 72" role="img" aria-label="Analoge klok voor starttijd ${esc(startTime)}"><circle class="child-routine-clock-face" cx="36" cy="36" r="33"></circle><g class="child-routine-clock-numerals"><text x="36" y="12">12</text><text x="48" y="15">1</text><text x="57" y="24">2</text><text x="60" y="37">3</text><text x="57" y="50">4</text><text x="48" y="59">5</text><text x="36" y="62">6</text><text x="24" y="59">7</text><text x="15" y="50">8</text><text x="12" y="37">9</text><text x="15" y="24">10</text><text x="24" y="15">11</text></g><line class="child-routine-clock-hand child-routine-hour-hand" x1="36" y1="38" x2="36" y2="22" transform="rotate(${hourAngle} 36 36)"></line><line class="child-routine-clock-hand child-routine-minute-hand" x1="36" y1="38" x2="36" y2="12" transform="rotate(${minuteAngle} 36 36)"></line><circle class="child-routine-clock-center" cx="36" cy="36" r="2"></circle></svg><div><span>Begint om</span><time datetime="${esc(startTime)}">${esc(startTime)}</time></div></div>`;
}

function routineCard(run) {
  const routine = run.body;
  const doneCount = run.done.length;
  const allDone = doneCount === routine.steps.length;
  const scheduledClock = routine.start_time ? routineClock(routine.start_time) : '';
  return `<section class="child-routine-card ${allDone ? 'done' : ''}"><header class="${scheduledClock ? 'has-time' : ''}"><div class="child-routine-heading"><h2>${esc(routine.icon)} ${esc(routine.title)}</h2><p>${allDone ? 'Alles klaar! Goed gedaan!' : `${doneCount} van ${routine.steps.length} klaar`}</p></div>${scheduledClock}<div class="child-progress child-routine-progress" role="progressbar" aria-label="Voortgang ${esc(routine.title)}" aria-valuemin="0" aria-valuemax="${routine.steps.length}" aria-valuenow="${doneCount}"><span style="width:${(doneCount / routine.steps.length) * 100}%"></span></div></header><ol>${routine.steps
    .map((step, index) => {
      const done = run.done.includes(index);
      return `<li class="${done ? 'done' : ''}"><span class="child-step-label"><span aria-hidden="true">${esc(step.icon)}</span>${esc(step.text)}</span><button class="checkbox ${done ? 'done' : ''}" data-run="${run.id}" data-step="${index}" aria-label="${done ? 'Heropen' : 'Voltooi'} ${esc(step.text)} voor ${esc(personName(state.member))}" aria-pressed="${done}">${icon('check')}</button></li>`;
    })
    .join('')}</ol></section>`;
}

function routineCarousel(routines) {
  if (!routines.length) return '<p class="child-empty">Geen routines voor vandaag.</p>';
  synchronizeRoutineSelection(routines);
  const index = routines.findIndex((run) => run.id === routineSelection.runId);
  const run = routines[index];
  return `<div class="child-routine-carousel"><nav class="child-routine-navigation" aria-label="Routines van vandaag"><button type="button" class="secondary" data-child-routine-nav="-1" ${index <= 0 ? 'disabled' : ''}>${icon('left')}Vorige</button><span aria-live="polite">Routine ${index + 1} van ${routines.length}</span><button type="button" class="secondary" data-child-routine-nav="1" ${index >= routines.length - 1 ? 'disabled' : ''}>Volgende${icon('right')}</button></nav>${routineCard(run)}</div>`;
}

function rewardsView() {
  const balance = state.data.balances[state.member] || { available: 0 };
  const available = balance.available || 0;
  const requests = state.data.reward_requests.filter(
    (request) => request.member_id === state.member && request.status === 'pending'
  );
  const pendingRewardIds = new Set(requests.map((request) => request.reward_id));
  const nextReward = state.data.rewards
    .filter((reward) => reward.price > available)
    .sort((a, b) => a.price - b.price)[0];
  const progressMessage = nextReward
    ? `Nog ${nextReward.price - available} sterren voor ${esc(nextReward.title)}`
    : state.data.rewards.length
      ? 'Je kunt een beloning kiezen!'
      : 'Vraag een volwassene om een beloning toe te voegen.';

  return `<section class="child-rewards"><header><div><h2>Mijn beloningen</h2><p>${progressMessage}</p></div><div class="child-star-balance" aria-label="${available} sterren">${icon('gift')}<strong>${available}</strong></div></header>${requests.length ? `<p class="child-request-status" role="status">Je aanvraag wacht op een volwassene.</p>` : ''}<div class="child-reward-list">${
    state.data.rewards
      .map((reward) => {
        const pending = pendingRewardIds.has(reward.id);
        const canRequest = available >= reward.price && !pending;
        const buttonText = pending
          ? 'Aangevraagd'
          : canRequest
            ? 'Vraag aan'
            : `Nog ${reward.price - available} nodig`;
        return `<article class="child-reward-card"><span class="child-reward-icon" aria-hidden="true">${esc(reward.icon)}</span><div><h3>${esc(reward.title)}</h3><p>${reward.price} ${reward.price === 1 ? 'ster' : 'sterren'}</p></div><button class="primary" data-request-reward="${reward.id}" ${canRequest ? '' : 'disabled'}>${buttonText}</button></article>`;
      })
      .join('') || '<p class="child-empty">Er zijn nog geen beloningen.</p>'
  }</div></section>`;
}

export function childModeView() {
  const date = `<time datetime="${esc(state.day)}">${esc(fmt(parseDay(state.day), { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }))}</time>`;
  const member = person(state.member);
  if (!member || (member.role || 'child') !== 'child') {
    return `<section class="child-mode-page child-profile-picker"><header><span class="child-welcome-icon" aria-hidden="true">👋</span><h1>Wie ben jij?</h1><p>${date}</p><p>Kies je naam.</p></header><div class="child-profile-list">${
      state.data.members
        .filter((person) => (person.role || 'child') === 'child')
        .map(
          (person) =>
            `<button class="child-profile-option" data-child-member="${person.id}">${avatar(person)}<span>${esc(person.name)}</span>${icon('right')}</button>`
        )
        .join('') || '<p class="child-empty">Er zijn nog geen kinderen ingesteld.</p>'
    }</div></section>`;
  }

  const tasks = runsForMember('tasks');
  const routines = routinesForMember();

  return `<section class="child-mode-page"><header class="child-welcome">${avatar(member)}<div><h1>Hoi ${esc(member.name)}!</h1><p>${date}</p><p>Dit kun jij vandaag doen.</p></div></header><section class="child-activities" aria-labelledby="child-tasks-title"><h2 id="child-tasks-title">Mijn taken</h2><div class="child-task-list">${tasks.map(taskCard).join('') || '<p class="child-empty">Geen taken voor vandaag. Fijn!</p>'}</div></section><section class="child-activities" aria-labelledby="child-routines-title"><h2 id="child-routines-title">Mijn routines</h2><div class="child-routine-list">${routineCarousel(routines)}</div></section>${rewardsView()}<section class="child-activities"><h2>Spelletjes</h2><p>Koop een spelsessie met je sterren.</p><button class="primary" data-tab="games">🎮 Naar de spelletjes</button></section></section>`;
}

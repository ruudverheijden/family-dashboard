import { state } from './state.js';
import { avatar, esc, person, personName } from './helpers.js';
import { icon } from './icons.js';

function runsForMember(kind) {
  return state.data.runs.filter(
    (run) =>
      run.day === state.day &&
      run.kind === kind &&
      (run.member === state.member ||
        (run.member === 'shared' && run.body.members.includes(state.member)))
  );
}

function taskCard(run) {
  const task = state.data.tasks.find((item) => item.id === run.template_id) || run.body;
  const done = run.done.length > 0;
  return `<article class="child-task ${done ? 'done' : ''}"><button class="checkbox ${done ? 'done' : ''}" data-run="${run.id}" data-step="0" aria-label="${done ? 'Heropen' : 'Voltooi'} ${esc(task.title)}" aria-pressed="${done}">${icon('check')}</button><div class="child-task-copy"><span class="child-task-icon" aria-hidden="true">${esc(task.icon)}</span><div><h3>${esc(task.title)}</h3>${task.description ? `<p>${esc(task.description)}</p>` : ''}${done ? '<span class="child-done-label">Klaar!</span>' : ''}</div></div></article>`;
}

function routineCard(runs) {
  const run = runs[0];
  const routine = run.body;
  const doneCount = run.done.length;
  const allDone = doneCount === routine.steps.length;
  return `<section class="child-routine-card ${allDone ? 'done' : ''}"><header><div><h2>${esc(routine.icon)} ${esc(routine.title)}</h2><p>${allDone ? 'Alles klaar! Goed gedaan!' : `${doneCount} van ${routine.steps.length} klaar`}</p></div><div class="child-progress" role="progressbar" aria-label="Voortgang ${esc(routine.title)}" aria-valuemin="0" aria-valuemax="${routine.steps.length}" aria-valuenow="${doneCount}"><span style="width:${(doneCount / routine.steps.length) * 100}%"></span></div></header><ol>${routine.steps
    .map((step, index) => {
      const done = run.done.includes(index);
      return `<li class="${done ? 'done' : ''}"><span class="child-step-label"><span aria-hidden="true">${esc(step.icon)}</span>${esc(step.text)}</span><button class="checkbox ${done ? 'done' : ''}" data-run="${run.id}" data-step="${index}" aria-label="${done ? 'Heropen' : 'Voltooi'} ${esc(step.text)} voor ${esc(personName(state.member))}" aria-pressed="${done}">${icon('check')}</button></li>`;
    })
    .join('')}</ol></section>`;
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

  return `<section class="child-rewards"><header><div><h2>Mijn beloningen</h2><p>${progressMessage}</p></div><div class="child-star-balance" aria-label="${available} sterren">${icon('gift')}<strong>${available}</strong></div></header>${requests.length ? `<p class="child-request-status" role="status">Je aanvraag wacht op een volwassene.</p>` : ''}<div class="child-reward-list">${state.data.rewards
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
    .join('') || '<p class="child-empty">Er zijn nog geen beloningen.</p>'}</div></section>`;
}

export function childModeView() {
  const member = person(state.member);
  if (!member) {
    return `<section class="child-mode-page child-profile-picker"><header><span class="child-welcome-icon" aria-hidden="true">👋</span><h1>Wie ben jij?</h1><p>Kies je naam.</p></header><div class="child-profile-list">${state.data.members
      .map(
        (person) =>
          `<button class="child-profile-option" data-child-member="${person.id}">${avatar(person)}<span>${esc(person.name)}</span>${icon('right')}</button>`
      )
      .join('') || '<p class="child-empty">Er zijn nog geen gezinsleden ingesteld.</p>'}</div><button class="child-exit" data-child-mode="exit">Terug naar ouderweergave</button></section>`;
  }

  const tasks = runsForMember('tasks');
  const routineRuns = runsForMember('routines');
  const routines = new Map();
  for (const run of routineRuns) {
    const group = routines.get(run.template_id) || [];
    group.push(run);
    routines.set(run.template_id, group);
  }

  return `<section class="child-mode-page"><header class="child-welcome">${avatar(member)}<div><h1>Hoi ${esc(member.name)}!</h1><p>Dit kun jij vandaag doen.</p></div><button class="child-exit" data-child-mode="exit">Naar ouderweergave</button></header><section class="child-activities" aria-labelledby="child-tasks-title"><h2 id="child-tasks-title">Mijn taken</h2><div class="child-task-list">${tasks.map(taskCard).join('') || '<p class="child-empty">Geen taken voor vandaag. Fijn!</p>'}</div></section><section class="child-activities" aria-labelledby="child-routines-title"><h2 id="child-routines-title">Mijn routines</h2><div class="child-routine-list">${[...routines.values()].map(routineCard).join('') || '<p class="child-empty">Geen routines voor vandaag.</p>'}</div></section>${rewardsView()}</section>`;
}

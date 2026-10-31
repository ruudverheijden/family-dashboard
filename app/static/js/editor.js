import {
  icon,
  normalizeIconSearch,
  taskIconCategories,
  taskIconMetadata,
  taskIcons
} from './icons.js';
import { $, esc, fmt, selected, uuid, weekdays } from './helpers.js';
import { bindForm, errorInForm, field, modal, toast } from './dialogs.js';
import { state } from './state.js';
import { actions } from './actions.js';
import { api, mutate } from './api.js';

export function editEntity(kind, item) {
  const isTask = kind === 'tasks',
    isRoutine = kind === 'routines',
    isReward = kind === 'rewards';
  const x = item || {};
  let html = '';
  const iconField = (name, value, id, label) => {
    const choices =
      value && !taskIcons.some(([choice]) => choice === value)
        ? [...taskIcons, [value, 'Huidig pictogram']]
        : taskIcons;
    const groupedChoices = new Map();
    choices.forEach(([choice, choiceLabel]) => {
      const metadata = taskIconMetadata(choice, choiceLabel);
      if (!groupedChoices.has(metadata.category)) groupedChoices.set(metadata.category, []);
      groupedChoices.get(metadata.category).push({
        choice,
        choiceLabel,
        search: metadata.search
      });
    });
    const groups = [...groupedChoices].sort(
      ([a], [b]) => taskIconCategories.indexOf(a) - taskIconCategories.indexOf(b)
    );
    return `<div class="task-icon-field${isRoutine && name === 'icon' ? ' routine-icon-field' : ''}"><span class="task-icon-label">${esc(label)}</span><input type="hidden" name="${esc(name)}" value="${esc(value)}"><button type="button" class="task-icon-trigger" aria-haspopup="dialog" aria-expanded="false" aria-controls="${esc(id)}"><span>Kies pictogram</span><span class="task-icon-current">${esc(value)}</span></button><div id="${esc(id)}" class="task-icon-picker" role="group" aria-label="Kies een pictogram voor ${esc(label.toLowerCase())}" hidden><input type="search" class="task-icon-search" aria-label="Zoek pictogrammen" placeholder="Zoek op naam of pictogram"><p class="task-icon-no-results" role="status" hidden>Geen pictogrammen gevonden.</p>${groups
      .map(
        ([category, icons]) =>
          `<section class="task-icon-category"><h4>${esc(category)}</h4><div class="task-icon-category-grid">${icons
            .map(
              ({ choice, choiceLabel, search }) =>
                `<button type="button" class="task-icon-option" data-task-icon="${esc(choice)}" data-search="${esc(search)}" aria-label="${esc(choiceLabel)}" aria-pressed="${value === choice}">${esc(choice)}</button>`
            )
            .join('')}</div></section>`
      )
      .join('')}</div></div>`;
  };
  const routineSteps = x.steps?.length
    ? x.steps
    : [
        {
          icon: '✓',
          text: ''
        }
      ];
  let nextRoutineStepId = routineSteps.length;
  const routineStep = (step, index) =>
    `<div class="routine-step-row"><label>Titel stap ${index + 1}<input name="step_text" type="text" value="${esc(step.text)}" required maxlength="150"></label>${iconField('step_icon', step.icon || '✓', `routine-step-icon-${index}`, `Pictogram stap ${index + 1}`)}<button type="button" class="danger remove-routine-step" aria-label="Stap ${index + 1} verwijderen">${icon('close')}</button></div>`;
  if (kind === 'members')
    html = `<div class="form-grid">${field('Naam', 'name', x.name, 'text', 'required maxlength="60"')}${field('Kleur', 'color', x.color || '#b97b63', 'color')}${field('Avatar (emoji, optioneel)', 'avatar', x.avatar, 'text', 'maxlength="8"')}</div>`;
  else if (kind === 'groceries')
    html = `${field('Wat hebben we nodig?', 'name', x.name, 'text', 'required maxlength="150"')}${field('Hoeveelheid / eenheid', 'quantity', x.quantity, 'text', 'maxlength="60"')}${field('Notitie', 'note', x.note, 'text', 'maxlength="500"')}`;
  else if (isReward)
    html = `<div class="form-grid">${field('Naam', 'title', x.title, 'text', 'required maxlength="100"')}${field('Pictogram', 'icon', x.icon || '🎁', 'text', 'maxlength="8"')}${field('Prijs in punten', 'price', x.price || 1, 'number', 'min="1" max="100000" required')}<label class="full">Beschrijving<textarea name="description" maxlength="500">${esc(x.description || '')}</textarea></label></div>`;
  else {
    if (!state.data.members.length) {
      modal(
        'Eerst je gezin toevoegen',
        `<p class="muted">Voeg in Beheer minstens één gezinslid toe. Daarna kun je taken en routines toewijzen.</p><div class="form-actions"><button id="go-admin" class="primary">Gezin instellen</button></div>`
      );
      $('#go-admin').onclick = actions.openAdmin;
      return;
    }
    const entityIcon = isTask
      ? iconField('icon', x.icon || '✓', 'task-icon-picker', 'Pictogram')
      : iconField('icon', x.icon || '☀️', 'routine-icon-picker', 'Pictogram');
    html = `<div class="form-grid">${field('Titel', 'title', x.title, 'text', 'required maxlength="150"')}${entityIcon}<label class="full">Beschrijving<textarea name="description" maxlength="1000">${esc(x.description || '')}</textarea></label>${field('Startdatum', 'date', x.date || state.day, 'date', 'required')}${isTask ? `<label>Herhaling<select name="repeat"><option value="once"${selected(x.repeat, 'once')}>Eenmalig</option><option value="daily"${selected(x.repeat, 'daily')}>Elke dag</option><option value="weekly"${selected(x.repeat, 'weekly')}>Op gekozen weekdagen</option></select></label>` : ''}</div><label>Voor wie?</label><div class="member-chips">${state.data.members.map((m) => `<label class="check-label"><input type="checkbox" name="members" value="${m.id}" ${(x.members || [state.member]).includes(m.id) ? 'checked' : ''}>${esc(m.name)}</label>`).join('')}</div><label style="margin-top:16px">Weekdagen ${isTask ? '(bij weekherhaling)' : ''}</label><div class="weekdays">${weekdays.map((d, i) => `<label><input type="checkbox" name="weekdays" value="${i}" ${(x.weekdays || [0, 1, 2, 3, 4, 5, 6]).includes(i) ? 'checked' : ''}>${d}</label>`).join('')}</div>`;
    if (isTask)
      html += `<div class="form-grid"><label>Uitvoering<select name="mode"><option value="individual"${selected(x.mode, 'individual')}>Iedereen een eigen taak</option><option value="shared"${selected(x.mode, 'shared')}>Samen één taak</option></select></label>${field('Punten bij voltooien', 'points', x.points || 0, 'number', 'min="0" max="10000"')}</div>`;
    else
      html += `<div class="form-grid">${field('Punten bij volledige routine', 'points', x.points || 0, 'number', 'min="0" max="10000"')}${field('Vanaf', 'start_time', x.start_time || '07:00', 'time', 'required')}${field('Tot', 'end_time', x.end_time || '09:00', 'time', 'required')}</div><section class="routine-steps"><div class="routine-steps-head"><strong>Stappen</strong><button type="button" id="add-routine-step" class="secondary">Stap toevoegen</button></div><div id="routine-step-list">${routineSteps.map(routineStep).join('')}</div></section>`;
    if (item && (isTask || isRoutine))
      html +=
        '<p class="notice">Wijzigingen gelden voor nog niet aangemaakte uitvoeringen. Bestaande uitvoeringen en historie blijven behouden.</p>';
  }
  modal(
    item
      ? 'Bewerken'
      : {
          members: 'Een nieuw gezinslid',
          groceries: 'Op de boodschappenlijst',
          tasks: 'Een nieuwe taak',
          routines: 'Een nieuwe routine',
          rewards: 'Een nieuwe beloning'
        }[kind],
    `<form id="edit-form">${html}<div class="form-actions">${item ? `<button type="button" id="delete-entity" class="danger">${isTask || isRoutine ? 'Archiveren' : 'Verwijderen'}</button>` : ''}<button type="submit" class="primary">Opslaan ${icon('check')}</button></div></form>`
  );
  const bindIconField = (iconFieldElement) => {
    const trigger = iconFieldElement.querySelector('.task-icon-trigger'),
      picker = iconFieldElement.querySelector('.task-icon-picker'),
      search = picker.querySelector('.task-icon-search'),
      options = [...picker.querySelectorAll('[data-task-icon]')],
      noResults = picker.querySelector('.task-icon-no-results');
    trigger.onclick = () => {
      picker.hidden = !picker.hidden;
      trigger.setAttribute('aria-expanded', String(!picker.hidden));
      if (!picker.hidden) {
        const content = $('#dialog-content'),
          contentRect = content.getBoundingClientRect(),
          contentStyle = getComputedStyle(content),
          leftEdge = contentRect.left + parseFloat(contentStyle.paddingLeft),
          rightEdge = contentRect.right - parseFloat(contentStyle.paddingRight),
          width = Math.min(420, rightEdge - leftEdge),
          fieldRect = iconFieldElement.getBoundingClientRect();
        picker.style.width = `${width}px`;
        picker.style.left = `${Math.max(leftEdge, Math.min(fieldRect.left, rightEdge - width)) - fieldRect.left}px`;
        search.focus();
      }
    };
    search.oninput = () => {
      const query = normalizeIconSearch(search.value.trim());
      let visible = 0;
      options.forEach((option) => {
        const matches = option.dataset.search.includes(query);
        option.hidden = !matches;
        if (matches) visible++;
      });
      picker.querySelectorAll('.task-icon-category').forEach((category) => {
        category.hidden = !category.querySelector('[data-task-icon]:not([hidden])');
      });
      noResults.hidden = visible > 0;
    };
    picker.onkeydown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        picker.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
      }
    };
    options.forEach(
      (button) =>
        (button.onclick = () => {
          iconFieldElement.querySelector('input[type="hidden"]').value = button.dataset.taskIcon;
          iconFieldElement.querySelector('.task-icon-current').textContent =
            button.dataset.taskIcon;
          options.forEach((option) =>
            option.setAttribute('aria-pressed', String(option === button))
          );
          picker.hidden = true;
          trigger.setAttribute('aria-expanded', 'false');
          trigger.focus();
          state.dialogDirty = true;
        })
    );
  };
  $('#dialog-content').querySelectorAll('.task-icon-field').forEach(bindIconField);
  if (isRoutine) {
    const stepList = $('#routine-step-list'),
      addStep = $('#add-routine-step');
    const updateStepButtons = () => {
      const rows = stepList.querySelectorAll('.routine-step-row');
      rows.forEach((row, index) => {
        row.querySelector('label').firstChild.textContent = `Titel stap ${index + 1}`;
        row.querySelector('.task-icon-label').textContent = `Pictogram stap ${index + 1}`;
        row
          .querySelector('.task-icon-picker')
          .setAttribute('aria-label', `Kies een pictogram voor pictogram stap ${index + 1}`);
        row.querySelector('.remove-routine-step').disabled = rows.length === 1;
        row
          .querySelector('.remove-routine-step')
          .setAttribute('aria-label', `Stap ${index + 1} verwijderen`);
      });
      addStep.disabled = rows.length >= 30;
    };
    addStep.onclick = () => {
      const count = stepList.querySelectorAll('.routine-step-row').length;
      if (count >= 30) return;
      stepList.insertAdjacentHTML(
        'beforeend',
        routineStep(
          {
            icon: '✓',
            text: ''
          },
          nextRoutineStepId++
        )
      );
      bindIconField(stepList.lastElementChild.querySelector('.task-icon-field'));
      updateStepButtons();
      stepList.lastElementChild.querySelector('[name="step_text"]').focus();
      state.dialogDirty = true;
    };
    stepList.onclick = (e) => {
      const button = e.target.closest('.remove-routine-step');
      if (!button || stepList.querySelectorAll('.routine-step-row').length === 1) return;
      button.closest('.routine-step-row').remove();
      updateStepButtons();
      state.dialogDirty = true;
    };
    updateStepButtons();
  }
  const id = item?.id || uuid(),
    requestId = uuid();
  let previousPayload = '',
    retryId = requestId;
  bindForm(async (f) => {
    let body = Object.fromEntries(f);
    if (isTask || isRoutine) {
      body.members = f.getAll('members');
      body.weekdays = f.getAll('weekdays').map(Number);
      body.points = Number(f.get('points'));
      if (isRoutine)
        body.steps = f.getAll('step_text').map((text, index) => ({
          text,
          icon: f.getAll('step_icon')[index] || '✓'
        }));
    }
    if (kind === 'groceries') body.done = x.done || false;
    if (isReward) body.price = Number(f.get('price'));
    const payload = JSON.stringify(body);
    if (previousPayload && previousPayload !== payload) retryId = uuid();
    previousPayload = payload;
    await mutate(
      kind,
      {
        id,
        version: item?.version || 0
      },
      body,
      'save',
      retryId
    );
  });
  if (item)
    $('#delete-entity').onclick = async () => {
      if (
        !confirm(
          isTask || isRoutine
            ? 'Dit sjabloon archiveren? Bestaande uitvoeringen blijven bewaard.'
            : 'Dit item verwijderen?'
        )
      )
        return;
      try {
        await mutate(
          kind,
          item,
          isTask || isRoutine
            ? {
                ...item,
                archived: true
              }
            : {},
          isTask || isRoutine ? 'save' : 'delete'
        );
        state.dialogDirty = false;
        $('#dialog').close();
        await actions.refresh(true);
      } catch (e) {
        errorInForm(e);
      }
    };
}
export function showTemplates(kind) {
  modal(
    kind === 'tasks' ? 'Taaksjablonen' : 'Routinesjablonen',
    `<p class="notice">Bestaande uitvoeringen blijven behouden wanneer je een sjabloon wijzigt of archiveert.</p><div class="list">${state.data[kind].map((x) => `<button class="secondary" data-template="${x.id}">${esc(x.icon)} ${esc(x.title)} ${x.archived ? '· gearchiveerd' : ''}${icon('edit')}</button>`).join('') || '<p class="muted">Nog geen sjablonen.</p>'}</div>`
  );
  document.querySelectorAll('[data-template]').forEach(
    (b) =>
      (b.onclick = () =>
        editEntity(
          kind,
          state.data[kind].find((x) => x.id === b.dataset.template)
        ))
  );
}
export async function showHistory() {
  try {
    const rows = await api('/api/history');
    modal(
      'Recente wijzigingen',
      `<p class="notice">De laatste 100 wijzigingen. Ook ongedaan gemaakte voltooiingen blijven bewaard.</p>${
        rows
          .map((r) => {
            const b = JSON.parse(r.body);
            return `<div class="history-item">${esc(
              {
                tasks: 'Taak',
                routines: 'Routine',
                groceries: 'Boodschap',
                members: 'Gezinslid',
                runs: 'Voortgang'
              }[r.kind]
            )} · ${esc(b.after?.title || b.after?.name || b.before?.title || b.before?.name || (Array.isArray(b.after) ? `${b.after.length} stap(pen) voltooid` : 'Verwijderd'))}<small>${fmt(
              new Date(r.at.replace(' ', 'T') + 'Z'),
              {
                dateStyle: 'short',
                timeStyle: 'short',
                timeZone: state.data.config.timezone
              }
            )}</small></div>`;
          })
          .join('') || '<p>Nog geen wijzigingen.</p>'
      }`
    );
  } catch (e) {
    toast(e.message);
  }
}

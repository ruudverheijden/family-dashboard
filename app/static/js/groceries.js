import { empty, esc } from './helpers.js';
import { icon } from './icons.js';
import { state } from './state.js';

export function groceryRow(g) {
  return `<div class="grocery-row"><button class="checkbox ${g.done ? 'done' : ''}" data-grocery="${g.id}" aria-label="${g.done ? 'Heropen' : 'Vink af'} ${esc(g.name)}" aria-pressed="${g.done}">${icon('check')}</button><div class="row-text ${g.done ? 'done' : ''}"><strong>${esc(g.name)}</strong><small>${esc([g.quantity, g.note].filter(Boolean).join(' · '))}</small></div><button data-edit="groceries:${g.id}" aria-label="${esc(g.name)} bewerken">${icon('edit')}</button></div>`;
}
export function groceriesView() {
  const done = state.data.groceries.filter((g) => g.done),
    open = state.data.groceries.filter((g) => !g.done);
  return `<div class="toolbar"><div><h2>Wat hebben we nodig?</h2><p class="small muted" style="margin-top:8px">Eén lijst voor het hele gezin. Ook op je telefoon.</p></div></div><form id="quick-add" class="quick-add"><input aria-label="Boodschap" name="name" value="${esc(state.quickDraft)}" placeholder="Bijvoorbeeld melk, appels of brood…" required maxlength="150" autocomplete="off"><button type="button" class="secondary" data-new="groceries">${icon('plus')}Met details</button><button class="primary" type="submit">${icon('plus')}Toevoegen</button></form><div class="list-label"><span>NOG NODIG · ${open.length}</span></div><div class="list">${open.map(groceryRow).join('') || empty('De lijst is helemaal bij.', 'Voeg hierboven iets toe zodra je eraan denkt.', 'basket')}</div>${done.length ? `<div class="list-label"><span>IN HET MANDJE · ${done.length}</span><button data-action="clear-groceries" class="small">Afgevinkte opruimen</button></div><div class="list">${done.map(groceryRow).join('')}</div>` : ''}`;
}

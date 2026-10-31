import { state } from './state.js';
import { empty, esc } from './helpers.js';
import { icon } from './icons.js';

export function homeView() {
  const url = state.data.config.ha_url
    ? `${state.data.config.ha_url}${state.data.config.ha_dashboard}`
    : '';
  return `<section class="integration">${url ? `<iframe id="ha-dashboard" class="ha-dashboard" src="${esc(url)}" title="Home Assistant-dashboard" allow="fullscreen; clipboard-read; clipboard-write" referrerpolicy="no-referrer"></iframe>` : empty('Verbind je huis.', 'Stel in Beheer het Home Assistant-serveradres en het dashboardpad in.', 'home', `<button class="primary" data-action="admin">${icon('settings')}Home Assistant instellen</button>`)}</section>`;
}

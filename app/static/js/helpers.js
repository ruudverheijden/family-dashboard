import { state } from './state.js';
import { icon } from './icons.js';

export const $ = (s) => document.querySelector(s);
export const esc = (v) =>
  String(v ?? '').replace(
    /[&<>"']/g,
    (c) =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
      })[c]
  );
export const uuid = () =>
  crypto.randomUUID
    ? crypto.randomUUID()
    : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const n = crypto.getRandomValues(new Uint8Array(1))[0] % 16;
        return (c === 'x' ? n : (n & 3) | 8).toString(16);
      });
export const weekdays = ['ma', 'di', 'wo', 'do', 'vr', 'za', 'zo'];
export const weekdayNames = [
  'maandag',
  'dinsdag',
  'woensdag',
  'donderdag',
  'vrijdag',
  'zaterdag',
  'zondag'
];
export const fmt = (date, options) => new Intl.DateTimeFormat('nl-NL', options).format(date);
export const parseDay = (value) => new Date(value + 'T12:00:00');
export const plusDay = (value, n) => {
  const d = parseDay(value);
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};
export const today = () =>
  new Intl.DateTimeFormat('en-CA', {
    timeZone: state.data?.config.timezone || 'Europe/Amsterdam',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).format(new Date());
export const person = (id) => state.data.members.find((m) => m.id === id);
export const personName = (id) => (id === 'shared' ? 'Samen' : person(id)?.name || 'Gezin');
export const initials = (name) =>
  name
    .split(' ')
    .map((x) => x[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
export const avatar = (m) =>
  `<span class="avatar" style="background:${esc(m.color)}20;color:${esc(m.color)}">${esc(m.avatar || initials(m.name))}</span>`;
export const selected = (a, b) => (a === b ? ' selected' : '');
export function empty(title, desc, i, button = '') {
  return `<div class="panel empty"><span class="empty-icon">${icon(i)}</span><h3>${title}</h3><p>${desc}</p>${button}</div>`;
}

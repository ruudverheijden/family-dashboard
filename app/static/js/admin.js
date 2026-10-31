import { state } from './state.js';
import { api } from './api.js';
import { bindForm, confirmDiscard, errorInForm, field, modal, toast } from './dialogs.js';
import { icon } from './icons.js';
import { $, avatar, esc, person, selected, uuid } from './helpers.js';
import { applyTheme } from './shell.js';
import { actions } from './actions.js';
import { bindRewardAdmin } from './rewards.js';

export async function openAdmin() {
  try {
    state.adminCfg = await api('/api/admin/settings');
    renderAdmin();
  } catch (e) {
    if (e.status !== 401) {
      toast(e.message);
      return;
    }
    modal(
      'Beheer openen',
      `<p class="notice">Dagelijkse bediening is voor het hele gezin. Instellingen zijn beveiligd met het beheerwachtwoord van de server.</p><form id="edit-form">${field('Beheerwachtwoord', 'password', '', 'password', 'required autocomplete="current-password"')}<div class="form-actions"><button class="primary" type="submit">${icon('lock')}Ontgrendelen</button></div></form>`
    );
    $('#edit-form').onsubmit = async (event) => {
      event.preventDefault();
      const b = event.target.querySelector('button');
      b.disabled = true;
      try {
        await api('/api/login', {
          method: 'POST',
          body: JSON.stringify({
            password: event.target.password.value
          })
        });
        state.dialogDirty = false;
        await openAdmin();
      } catch (err) {
        errorInForm(err);
      } finally {
        b.disabled = false;
      }
    };
  }
}
export function accountMarkup(a, index) {
  return `<div class="account" data-account="${esc(a.id)}"><div class="account-head"><h3>CalDAV-account ${index + 1}</h3><button type="button" class="danger remove-account" aria-label="Account verwijderen">${icon('close')}</button></div>${field('Serveradres', 'caldav-url', a.url, 'url', 'required placeholder="https://calendar.example.org/dav/"')}${field('Gebruikersnaam', 'caldav-user', a.username, 'text', 'required autocomplete="off"')}${field(a.configured ? 'Nieuw wachtwoord (leeg = behouden)' : 'Wachtwoord', 'caldav-pass', '', 'password', 'autocomplete="new-password"')}<button type="button" class="secondary discover-cal">Agenda’s ophalen</button><div class="discovery">${calendarChoices(a.calendars || [], a.calendars || [])}</div></div>`;
}
export function calendarChoices(available, chosen) {
  return available
    .map((c) => {
      const existing = chosen.find((x) => x.url === c.url);
      return `<div class="calendar-choice" data-url="${esc(c.url)}" data-name="${esc(c.name)}"><label class="check-label"><input type="checkbox" ${existing ? 'checked' : ''}>${esc(c.name)}</label><label>Gezinslid<select><option value="">Hele gezin</option>${state.data.members.map((m) => `<option value="${m.id}"${selected(existing?.member, m.id)}>${esc(m.name)}</option>`).join('')}</select></label></div>`;
    })
    .join('');
}
export async function openAlbumPicker() {
  const button = $('#discover-albums'),
    form = $('#edit-form'),
    dialog = $('#album-dialog'),
    content = $('#album-dialog-content');
  const chosen = new Set(
    [...document.querySelectorAll('#albums [name=albums]:checked')].map((input) => input.value)
  );
  button.disabled = true;
  content.innerHTML = `<div class="modal-head"><h2 id="album-picker-title">Immich-albums kiezen</h2><button type="button" id="close-album-dialog" aria-label="Sluiten">${icon('close')}</button></div><p class="album-picker-intro">Selecteer de albums die je in het dashboard wilt tonen.</p><div id="album-picker-list" class="album-picker-list"><p class="muted">Albums ophalen…</p></div><div class="form-actions"><button type="button" id="cancel-album-selection" class="secondary">Annuleren</button><button type="button" id="apply-album-selection" class="primary" disabled>Selectie toepassen</button></div><div id="album-picker-error" class="form-error hidden" role="alert"></div>`;
  dialog.showModal();
  const close = () => dialog.close();
  $('#close-album-dialog').onclick = close;
  $('#cancel-album-selection').onclick = close;
  try {
    const albums = await api('/api/admin/discover/immich', {
      method: 'POST',
      body: JSON.stringify({
        url: form.immich_url.value,
        key: form.immich_key.value
      })
    });
    if (!Array.isArray(albums))
      throw new Error('De albumlijst heeft een ongeldig antwoord opgeleverd.');
    $('#album-picker-list').innerHTML =
      albums
        .map(
          (album) =>
            `<label class="check-label"><input type="checkbox" value="${esc(album.id)}" ${chosen.has(album.id) ? 'checked' : ''}>${esc(album.name)}</label>`
        )
        .join('') || '<p class="muted">Geen toegankelijke albums gevonden.</p>';
    const applyButton = $('#apply-album-selection');
    applyButton.disabled = false;
    applyButton.onclick = () => {
      const selected = [...document.querySelectorAll('#album-picker-list input:checked')].map(
        (input) => ({
          id: input.value,
          name: input.parentElement.textContent.trim()
        })
      );
      $('#albums').innerHTML =
        selected
          .map(
            (album) =>
              `<label class="check-label"><input type="checkbox" name="albums" value="${esc(album.id)}" checked>${esc(album.name)}</label>`
          )
          .join('') || '<p class="muted">Geen albums geselecteerd.</p>';
      $('#albums').dispatchEvent(
        new Event('input', {
          bubbles: true
        })
      );
      close();
    };
  } catch (error) {
    $('#album-picker-error').textContent = error.message;
    $('#album-picker-error').classList.remove('hidden');
  } finally {
    button.disabled = false;
  }
}
export function renderAdmin() {
  const c = state.adminCfg;
  modal(
    'Ons dashboard instellen',
    `<div class="toolbar"><span class="small muted">Beheersessie · 30 minuten</span><button id="logout" class="secondary small">${icon('lock')}Vergrendelen</button></div><div class="admin-tabs" role="tablist" aria-label="Instellingen"><button type="button" id="admin-tab-general" role="tab" aria-selected="true" aria-controls="admin-general" data-admin-tab="general">Algemeen</button><button type="button" id="admin-tab-device" role="tab" aria-selected="false" aria-controls="admin-device" tabindex="-1" data-admin-tab="device">Dit apparaat</button></div><div id="admin-general" role="tabpanel" aria-labelledby="admin-tab-general"><section class="settings-section"><h3>Ons gezin</h3><div class="family-list">${state.data.members.map((m) => `<button class="person" data-admin-member="${m.id}">${avatar(m)}${esc(m.name)}${icon('edit')}</button>`).join('')}</div><button id="new-member" class="secondary">${icon('plus')}Gezinslid toevoegen</button></section><form id="edit-form"><section class="settings-section"><h3>Logo en teksten</h3>${field('Titel', 'brand_title', c.brand_title, 'text', 'maxlength="40" required')}${field('Subtitel', 'brand_subtitle', c.brand_subtitle, 'text', 'maxlength="80"')}<div class="brand-image-controls"><div id="brand-image-preview" class="brand-image-preview">${c.brand_image ? `<img src="${esc(c.brand_image)}" alt="">` : '<span>s</span><span>✳</span>'}</div><div class="brand-image-actions"><label for="brand-image-file">Gezinsfoto voor het logo</label><input id="brand-image-file" type="file" accept="image/jpeg,image/png,image/webp"><small>JPEG, PNG of WebP; wordt verkleind opgeslagen.</small><button type="button" id="remove-brand-image" class="secondary small" ${c.brand_image ? '' : 'hidden'}>Foto verwijderen</button></div></div><input id="brand_image" name="brand_image" type="hidden" value="${esc(c.brand_image)}"></section><section class="settings-section"><h3>Algemeen</h3>${field('Tijdzone', 'timezone', c.timezone, 'text', 'required')}</section><section class="settings-section"><h3>Agenda · CalDAV</h3><p>Alleen-lezen. Selecteer de agenda’s die je wilt tonen. Synchronisatie loopt elke drie minuten; inloggegevens blijven op de server.</p><div id="accounts">${c.caldav.map(accountMarkup).join('')}</div><button type="button" id="add-account" class="secondary">${icon('plus')}Account toevoegen</button></section><section class="settings-section"><h3>Home Assistant-dashboard</h3>${field('Serveradres', 'ha_url', c.ha_url, 'url', 'placeholder="http://homeassistant.local:8123"')}${field('Dashboardpad', 'ha_dashboard', c.ha_dashboard || '/lovelace/0', 'text', 'required placeholder="/lovelace/0"')}<p>Vul het pad in van het dashboard dat je in Home Assistant hebt gemaakt, bijvoorbeeld <code>/lovelace/0</code> of <code>/dashboard-gezinsdashboard/overzicht</code>. Home Assistant verzorgt zelf de inhoud en bediening. Je browser moet toegang hebben tot dit adres en daar zo nodig zijn aangemeld.</p></section><section class="settings-section"><h3>Immich</h3>${field('Serveradres (zonder /api)', 'immich_url', c.immich_url, 'url', 'placeholder="http://immich.local:2283"')}${field(c.immich_configured ? 'Nieuwe API-sleutel (leeg = behouden)' : 'API-sleutel', 'immich_key', '', 'password', 'autocomplete="new-password"')}<button type="button" id="discover-albums" class="secondary">Albums ophalen</button><div id="albums" class="discovery">${c.albums.map((id) => `<label class="check-label"><input type="checkbox" name="albums" value="${esc(id)}" checked>Geselecteerd album ${esc(id.slice(0, 8))}</label>`).join('')}</div>${field('Wisseltijd (seconden)', 'slide_seconds', c.slide_seconds, 'number', 'min="5" max="300" required')}<p>Alleen geselecteerde albums zijn toegestaan. Foto’s worden uitsluitend gelezen. De servercache is begrensd.</p></section><div class="form-actions"><button type="submit" class="primary">Instellingen opslaan</button></div></form><section class="settings-section"><button id="sync-now" class="secondary">${icon('routine')}Nu synchroniseren</button><p class="notice">Sla gewijzigde instellingen eerst op.</p></section></div><div id="admin-device" role="tabpanel" aria-labelledby="admin-tab-device" hidden></div>`
  );
  $('#admin-device').insertAdjacentHTML(
    'beforeend',
    `<section class="settings-section theme-setting"><h3>Weergave</h3><button id="theme-toggle" type="button" class="theme-toggle" role="switch" aria-checked="${state.darkMode}"><span class="theme-toggle-label"><strong>Donkere modus</strong><small>Alleen op dit scherm opgeslagen</small></span><span class="theme-switch-track" aria-hidden="true"><span></span></span></button></section>`
  );
  $('#theme-toggle').onclick = (event) => {
    const toggle = event.currentTarget,
      next = !state.darkMode;
    try {
      localStorage.setItem('samen-theme', next ? 'dark' : 'light');
    } catch {
      toast('De thema-instelling kan niet op dit scherm worden opgeslagen.');
      return;
    }
    state.darkMode = next;
    applyTheme();
    toggle.setAttribute('aria-checked', String(state.darkMode));
    toggle.classList.toggle('active', state.darkMode);
  };
  let generalDirty = false,
    deviceDirty = false,
    brandImageTask = Promise.resolve(),
    brandImageError = null,
    brandImageSelection = 0;
  $('#dialog').oninput = (event) => {
    if (event.target.closest('#admin-device')) deviceDirty = true;
    else generalDirty = true;
    state.dialogDirty = generalDirty || deviceDirty;
  };
  const updateBrandImagePreview = (value) => {
    const preview = $('#brand-image-preview');
    preview.innerHTML = value
      ? `<img src="${esc(value)}" alt="">`
      : '<span>s</span><span>✳</span>';
  };
  $('#brand-image-file').onchange = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const selection = ++brandImageSelection;
    brandImageError = null;
    brandImageTask = (async () => {
      if (
        !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) ||
        file.size > 12 * 1024 * 1024
      )
        throw new Error('Kies een JPEG-, PNG- of WebP-foto van maximaal 12 MB.');
      const bitmap = await createImageBitmap(file);
      try {
        const scale = Math.min(1, 512 / Math.max(bitmap.width, bitmap.height)),
          canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round(bitmap.width * scale));
        canvas.height = Math.max(1, Math.round(bitmap.height * scale));
        const context = canvas.getContext('2d');
        context.fillStyle = '#fff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
        const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.82));
        if (!blob || blob.size > 400_000)
          throw new Error('Deze foto kan niet klein genoeg worden gemaakt. Kies een andere foto.');
        const image = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = () => reject(new Error('De foto kon niet worden gelezen.'));
          reader.readAsDataURL(blob);
        });
        if (selection !== brandImageSelection) return;
        $('#brand_image').value = image;
        updateBrandImagePreview(image);
        $('#remove-brand-image').hidden = false;
        generalDirty = true;
        state.dialogDirty = true;
      } finally {
        bitmap.close();
      }
    })().catch((error) => {
      if (selection !== brandImageSelection) return;
      brandImageError = error;
      errorInForm(error);
    });
  };
  $('#remove-brand-image').onclick = () => {
    brandImageSelection++;
    brandImageTask = Promise.resolve();
    $('#brand_image').value = '';
    $('#brand-image-file').value = '';
    updateBrandImagePreview('');
    $('#remove-brand-image').hidden = true;
    brandImageError = null;
    generalDirty = true;
    state.dialogDirty = true;
  };
  const tabs = [...document.querySelectorAll('[data-admin-tab]')];

  function selectAdminTab(button) {
    for (const t of tabs) {
      const active = t === button;
      t.setAttribute('aria-selected', String(active));
      t.tabIndex = active ? 0 : -1;
      $('#admin-' + t.dataset.adminTab).hidden = !active;
    }
  }
  tabs.forEach((button, index) => {
    button.onclick = () => selectAdminTab(button);
    button.onkeydown = (event) => {
      let next;
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') next = tabs[1 - index];
      else if (event.key === 'Home') next = tabs[0];
      else if (event.key === 'End') next = tabs[1];
      if (next) {
        event.preventDefault();
        selectAdminTab(next);
        next.focus();
      }
    };
  });
  $('#admin-device').insertAdjacentHTML(
    'beforeend',
    `<p class="notice">Deze voorkeuren worden in deze browser opgeslagen en gelden niet voor andere apparaten.</p><form id="screen-form">${field('Na inactiviteit naar Immich (minuten, 0 = uit)', 'idle', state.screen.idle || 0, 'number', 'min="0" max="180" required')}<label class="check-label"><input type="checkbox" name="shuffle" ${state.screen.shuffle ? 'checked' : ''}>Willekeurige fotovolgorde</label><label class="check-label"><input type="checkbox" name="crop" ${state.screen.crop ? 'checked' : ''}>Foto’s beeldvullend uitsnijden</label><p class="notice">Tijdens invoer en op het tabblad Routines wisselen we nooit automatisch.</p><div class="form-actions"><button class="primary" type="submit">Opslaan op dit scherm</button></div></form>`
  );
  $('#screen-form').onsubmit = async (event) => {
    event.preventDefault();
    try {
      const f = new FormData(event.target),
        next = {
          idle: Number(f.get('idle')),
          shuffle: f.has('shuffle'),
          crop: f.has('crop')
        };
      localStorage.setItem('samen-screen', JSON.stringify(next));
      state.screen = next;
      deviceDirty = false;
      state.dialogDirty = generalDirty;
      if (!state.dialogDirty) $('#dialog').close();
      await actions.refresh(true);
      toast('Opgeslagen op dit scherm');
    } catch (error) {
      errorInForm(error);
    }
  };
  bindRewardAdmin();
  $('#logout').onclick = async () => {
    await api('/api/logout', {
      method: 'POST'
    });
    state.dialogDirty = false;
    $('#dialog').close();
    toast('Beheer vergrendeld');
  };
  $('#new-member').onclick = () => {
    if (state.dialogDirty)
      return confirmDiscard(
        () => actions.editEntity('members'),
        'Niet-opgeslagen instellingen verlaten?'
      );
    actions.editEntity('members');
  };
  document.querySelectorAll('[data-admin-member]').forEach(
    (b) =>
      (b.onclick = () => {
        const memberToEdit = person(b.dataset.adminMember);
        if (state.dialogDirty)
          return confirmDiscard(
            () => actions.editEntity('members', memberToEdit),
            'Niet-opgeslagen instellingen verlaten?'
          );
        actions.editEntity('members', memberToEdit);
      })
  );
  $('#add-account').onclick = () => {
    $('#accounts').insertAdjacentHTML(
      'beforeend',
      accountMarkup(
        {
          id: uuid(),
          url: '',
          username: '',
          calendars: []
        },
        document.querySelectorAll('.account').length
      )
    );
    generalDirty = true;
    state.dialogDirty = true;
    bindAccounts();
  };
  bindAccounts();
  $('#discover-albums').onclick = openAlbumPicker;
  bindForm(
    async () => {
      let selection;
      do {
        selection = brandImageSelection;
        await brandImageTask;
      } while (selection !== brandImageSelection);
      if (brandImageError) throw brandImageError;
      const f = new FormData($('#edit-form')),
        cfg = {
          ...c,
          brand_title: f.get('brand_title'),
          brand_subtitle: f.get('brand_subtitle'),
          brand_image: f.get('brand_image'),
          timezone: f.get('timezone'),
          ha_url: f.get('ha_url'),
          ha_dashboard: f.get('ha_dashboard'),
          immich_url: f.get('immich_url'),
          immich_key: f.get('immich_key'),
          slide_seconds: Number(f.get('slide_seconds')),
          albums: f.getAll('albums'),
          caldav: [...document.querySelectorAll('.account')].map(readAccount)
        };
      await api('/api/admin/settings', {
        method: 'POST',
        body: JSON.stringify(cfg)
      });
      api('/api/admin/sync', {
        method: 'POST'
      })
        .then(() => actions.refresh())
        .catch((e) => toast(e.message));
    },
    () => {
      generalDirty = false;
      return deviceDirty;
    }
  );
  $('#sync-now').onclick = async () => {
    const b = $('#sync-now');
    b.disabled = true;
    b.textContent = 'Synchroniseren…';
    try {
      await api('/api/admin/sync', {
        method: 'POST'
      });
      await actions.refresh();
      const failed = Object.values(state.data.status).some((s) => !s.ok);
      toast(
        failed
          ? 'Synchronisatie afgerond met fouten. Bekijk de verbindingsstatus.'
          : 'Synchronisatie afgerond'
      );
    } catch (e) {
      errorInForm(e);
    } finally {
      b.disabled = false;
      b.textContent = 'Nu synchroniseren';
    }
  };
}
export function readAccount(el) {
  return {
    id: el.dataset.account,
    url: el.querySelector('[name=caldav-url]').value,
    username: el.querySelector('[name=caldav-user]').value,
    password: el.querySelector('[name=caldav-pass]').value,
    calendars: [...el.querySelectorAll('.calendar-choice')]
      .filter((c) => c.querySelector('input').checked)
      .map((c) => ({
        url: c.dataset.url,
        name: c.dataset.name,
        member: c.querySelector('select').value
      }))
  };
}
export function bindAccounts() {
  document.querySelectorAll('.account').forEach((el) => {
    el.querySelector('.remove-account').onclick = () => {
      if (confirm('Dit account uit de configuratie verwijderen? Sla daarna de instellingen op.')) {
        el.dispatchEvent(
          new Event('input', {
            bubbles: true
          })
        );
        el.remove();
        state.dialogDirty = true;
      }
    };
    el.querySelector('.discover-cal').onclick = async () => {
      const b = el.querySelector('.discover-cal');
      b.disabled = true;
      try {
        const a = readAccount(el),
          available = await api('/api/admin/discover/caldav', {
            method: 'POST',
            body: JSON.stringify(a)
          });
        el.querySelector('.discovery').innerHTML =
          calendarChoices(available, a.calendars) || '<p>Geen agenda’s gevonden.</p>';
      } catch (e) {
        errorInForm(e);
      } finally {
        b.disabled = false;
      }
    };
  });
}

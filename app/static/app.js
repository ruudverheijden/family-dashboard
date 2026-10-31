'use strict';
const $ = s => document.querySelector(s);
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths = {calendar:'M4 5h16v16H4z M4 10h16 M8 3v4 M16 3v4 M8 14h2 M14 14h2 M8 18h2',home:'m3 11 9-8 9 8 M5 10v11h14V10 M9 21v-7h6v7',image:'M3 4h18v16H3z m0 12 6-6 5 5 3-3 4 4 M15 8h.01',settings:'M9 2h6l.6 2.3a7.5 7.5 0 0 1 1.6.9l2.2-1.1 3 5.2-2 1.3a7.5 7.5 0 0 1 0 1.8l2 1.3-3 5.2-2.2-1.1a7.5 7.5 0 0 1-1.6.9L15 21h-6l-.6-2.3a7.5 7.5 0 0 1-1.6-.9l-2.2 1.1-3-5.2 2-1.3a7.5 7.5 0 0 1 0-1.8l-2-1.3 3-5.2 2.2 1.1a7.5 7.5 0 0 1 1.6-.9L9 2z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',check:'m5 12 4 4L19 6',tasks:'M9 6h12 M9 12h12 M9 18h12 M3 6h1 M3 12h1 M3 18h1',routine:'M20 7a9 9 0 0 0-15-2L2 8 M2 3v5h5 M4 17a9 9 0 0 0 15 2l3-3 M22 21v-5h-5',basket:'m3 8 2 13h14l2-13H3 M8 8l4-6 4 6 M9 12v5 M15 12v5',gift:'M20 12v10H4V12 M2 7h20v5H2z M12 7v15 M12 7H7.5a2.5 2.5 0 1 1 2.5-2.5V7 M12 7h4.5a2.5 2.5 0 1 0-2.5-2.5V7',left:'m14 5-7 7 7 7',right:'m10 5 7 7-7 7',plus:'M12 4v16 M4 12h16',close:'m6 6 12 12 M6 18 18 6',edit:'m4 16 12-12 4 4L8 20H4z M14 6l4 4',people:'M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M2 21v-2a6 6 0 0 1 12 0v2 M16 4a4 4 0 0 1 0 8 M17 15a5 5 0 0 1 5 5',pause:'M8 5v14 M16 5v14',play:'m8 4 12 8-12 8z',lock:'M5 10h14v11H5z M8 10V6a4 4 0 0 1 8 0v4',leaf:'M19 3C6 3 2 8 5 15s16 5 14-12 M5 20 15 9',history:'M3 10a9 9 0 1 1 2 8 M3 4v6h6 M12 7v6l4 2',sun:'M12 3v2 M12 19v2 M3 12h2 M19 12h2 M5.6 5.6 7 7 M17 17l1.4 1.4 M18.4 5.6 17 7 M7 17l-1.4 1.4 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',moon:'M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5z'};
const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.calendar}"/></svg>`;
document.querySelectorAll('[data-icon]').forEach(e => e.innerHTML = icon(e.dataset.icon));
const uuid = () => crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {const n = crypto.getRandomValues(new Uint8Array(1))[0] % 16; return (c === 'x' ? n : (n & 3 | 8)).toString(16)});
let calendarViewPreference = null;
try {
  const savedView = localStorage.getItem('samen-calendar-view');
  if (savedView === 'day' || savedView === 'three-day' || savedView === 'week') calendarViewPreference = savedView;
} catch {}
let data, day = '', tab = 'calendar', sub = 'agenda', member = '', view = calendarViewPreference || (matchMedia('(max-width:760px)').matches ? 'day' : 'week'), lastJSON = '', busy = false, pendingRefresh = false, dialogDirty = false, photoIndex = 0, paused = false, photoTimer, lastActivity = Date.now(), adminCfg, quickDraft = '', agendaScrollKey = '', agendaScrollTop = null;
const rewardRequestRetries = new Map();
const rewardDecisionRetries = new Map();
let screen;
try { screen = JSON.parse(localStorage.getItem('samen-screen') || '{}'); } catch { screen = {}; }
let darkMode = false;
try { darkMode = localStorage.getItem('samen-theme') === 'dark'; } catch {}
function applyTheme() {
  document.documentElement.dataset.theme = darkMode ? 'dark' : 'light';
  document.documentElement.style.colorScheme = darkMode ? 'dark' : 'light';
  $('meta[name="theme-color"]').content = darkMode ? '#171b18' : '#f7f5f0';
}
applyTheme();
const weekdays = ['ma','di','wo','do','vr','za','zo'];
const weekdayNames = ['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag'];
const taskIcons = [['✓','Standaard'],['🧹','Vegen'],['🧽','Schoonmaken'],['🧼','Zeep'],['🫧','Sop'],['🪣','Emmer'],['🧺','Wasmand'],['👕','Kleding'],['👖','Broek'],['🧦','Sokken'],['🧥','Jas'],['🛏️','Bed'],['🛌','Slapen'],['🪟','Ramen'],['🪞','Spiegel'],['🚪','Deur'],['🍽️','Servies'],['🍴','Bestek'],['🥄','Lepel'],['🥣','Kom'],['🍳','Koken'],['🥘','Maaltijd'],['🧂','Kruiden'],['🧊','IJs'],['🥤','Drinken'],['🫖','Thee'],['☕','Koffie'],['🗑️','Afval'],['♻️','Recyclen'],['📦','Pakket'],['🛒','Boodschappen'],['🥕','Groente'],['🍎','Fruit'],['🥛','Melk'],['🍞','Brood'],['🥫','Voorraad'],['🪴','Plant'],['🌱','Tuinieren'],['🌷','Bloemen'],['🍂','Bladeren'],['🐕','Hond'],['🐈','Kat'],['🐾','Pootafdrukken'],['🐟','Vis'],['🦜','Vogel'],['🦴','Hondenbot'],['🚿','Douche'],['🛁','Bad'],['🚽','Toilet'],['🪥','Tandenpoetsen'],['🦷','Tand'],['🧻','Toiletpapier'],['🧴','Verzorging'],['🎒','Tas'],['📚','Boeken'],['✏️','Schrijven'],['🧸','Speelgoed'],['🧩','Puzzel'],['🎨','Knutselen'],['⚽','Sport'],['👟','Schoenen'],['🧢','Pet'],['🧰','Gereedschap'],['🔧','Repareren'],['🔨','Klus'],['🪛','Schroevendraaier'],['🪜','Ladder'],['🔋','Batterij'],['💡','Lamp'],['🔑','Sleutel'],['📬','Post ophalen'],['📮','Brief posten'],['🧾','Bon'],['📅','Plannen'],['🌤️','Buiten'],['🌧️','Regen'],['🚗','Auto'],['🚲','Fiets'],['🪑','Stoel'],['🛋️','Bank'],['🖼️','Schilderij'],['😊','Blij'],['😄','Lach'],['😎','Cool'],['🤩','Super'],['🥳','Feest vieren'],['😴','Moe'],['💪','Sterk'],['🙌','Goed gedaan'],['❤️','Hart'],['⭐','Ster'],['🌈','Regenboog'],['🦄','Eenhoorn'],['🦖','Dinosaurus'],['🐸','Kikker'],['🐼','Panda'],['🐢','Schildpad'],['🐬','Dolfijn'],['🐝','Bij'],['🍕','Pizza'],['🍦','IJsje'],['🍪','Koekje'],['🧁','Cupcake'],['🍉','Watermeloen'],['🎮','Gamen'],['🎲','Spelletje'],['🎵','Muziek'],['🎸','Gitaar'],['🏀','Basketbal'],['🏊','Zwemmen'],['🛴','Step'],['🏆','Trofee'],['🎉','Hoera'],['🪠','Ontstoppen'],['🧯','Brandveiligheid'],['🧤','Handschoenen'],['🧣','Sjaal'],['🧵','Naaien'],['🪡','Naald en draad'],['📝','Notitie maken'],['🧠','Leren'],['🧑‍🍳','Koken'],['👶','Baby verzorgen'],['🍼','Fles klaarmaken'],['🏠','Opruimen'],['🚰','Water drinken'],['🚶','Wandelen'],['🧘','Rekken'],['💊','Medicijnen'],['🩹','Pleister'],['🎹','Piano spelen'],['🎤','Zingen'],['🛝','Naar de speeltuin']];
const extraTaskIcons = [
 ['🧳','Koffer','Klusjes en reizen',['bagage','vakantie','op reis']],
 ['🪙','Munt','Klusjes en reizen',['geld','muntstuk','sparen']],
 ['🛍️','Winkeltassen','Klusjes en reizen',['boodschappen','shoppen','winkel']],
 ['🕯️','Kaars','Huis en schoonmaken',['licht','kaars aansteken']],
 ['🛠️','Gereedschap','Klusjes en reizen',['gereedschap','repareren','onderhoud']],
 ['🔒','Slot','Huis en schoonmaken',['deur op slot','afsluiten','veiligheid']],
 ['📖','Lezen','School en creativiteit',['boek','studeren','lezen']],
 ['✂️','Knippen','School en creativiteit',['schaar','knutselen','knippen']],
 ['🧶','Breien','School en creativiteit',['wol','haken','breien']],
 ['🧲','Magneet','School en creativiteit',['magneet','proefje']],
 ['🔍','Zoeken','School en creativiteit',['vergrootglas','zoeken','speuren']],
 ['🪄','Toveren','Spel en plezier',['magie','tovenaar','fantasie']],
 ['🌍','Aarde','Natuur en dieren',['wereld','planeet','milieu']],
 ['🌲','Boom','Natuur en dieren',['bos','boom','natuur']],
 ['🌻','Zonnebloem','Natuur en dieren',['bloem','tuin','zonnebloem']],
 ['🍄','Paddenstoel','Natuur en dieren',['bos','paddenstoel']],
 ['🦋','Vlinder','Natuur en dieren',['insect','vlinder','natuur']],
 ['🐇','Konijn','Natuur en dieren',['huisdier','konijn']],
 ['🐹','Hamster','Natuur en dieren',['huisdier','hamster']],
 ['🐦','Vogel','Natuur en dieren',['vogels voeren','vogel']],
 ['🐠','Tropische vis','Natuur en dieren',['aquarium','vis voeren','vis']],
 ['🐞','Lieveheersbeestje','Natuur en dieren',['insect','lieveheersbeestje']],
 ['🦔','Egel','Natuur en dieren',['egel','dier']],
 ['🦎','Hagedis','Natuur en dieren',['reptiel','hagedis']],
 ['🦆','Eend','Natuur en dieren',['eend','dieren']],
 ['🦁','Leeuw','Natuur en dieren',['dierentuin','leeuw']],
 ['🐘','Olifant','Natuur en dieren',['dierentuin','olifant']],
 ['🤗','Knuffel','Smileys en beloningen',['knuffelen','lief','blij']],
 ['😃','Glimlach','Smileys en beloningen',['glimlachen','blij','smiley']],
 ['😇','Engel','Smileys en beloningen',['lief','onschuldig','smiley']],
 ['🫶','Hartjeshanden','Smileys en beloningen',['liefde','handenhart','dankbaar']],
 ['👋','Zwaaien','Smileys en beloningen',['hallo','dag zeggen','zwaaien']],
 ['🙏','Bedanken','Smileys en beloningen',['dankjewel','bidden','bedankt']],
 ['🧍','Aankleden','Verzorging en gezondheid',['staan','klaarmaken','aankleden']],
 ['🧡','Oranje hart','Smileys en beloningen',['hart','liefde','oranje']],
 ['🥗','Salade','Eten en drinken',['groente','gezond eten','salade']],
 ['🍌','Banaan','Eten en drinken',['fruit','banaan']],
 ['🍓','Aardbei','Eten en drinken',['fruit','aardbei']],
 ['🥚','Ei','Eten en drinken',['ontbijt','ei']],
 ['🧀','Kaas','Eten en drinken',['eten','kaas']],
 ['🥪','Boterham','Eten en drinken',['lunch','broodje','sandwich']],
 ['🥞','Pannenkoeken','Eten en drinken',['ontbijt','pannenkoek']],
 ['🧃','Sap','Eten en drinken',['drinken','sapje','pakje drinken']],
 ['🍿','Popcorn','Eten en drinken',['film','snack','popcorn']],
 ['🍰','Taart','Eten en drinken',['bakken','gebak','verjaardag']],
 ['🎭','Toneel','School en creativiteit',['theater','toneelspelen','verkleden']],
 ['🪇','Muziek maken','School en creativiteit',['muziek','instrument','maracas']],
 ['🎻','Viool','School en creativiteit',['muziek','instrument','viool spelen']],
 ['🏸','Badminton','Sport en buiten',['sport','racket','badminton']],
 ['🏓','Tafeltennis','Sport en buiten',['pingpong','sport','tafeltennis']],
];
taskIcons.push(...extraTaskIcons.map(([emoji,label])=>[emoji,label]));
const extraTaskIconMetadata=new Map(extraTaskIcons.map(([emoji,,category,aliases])=>[emoji,{category,aliases}]));
const taskIconAliases={
 '🧹':['stofzuigen','schoonmaken','vegen'],'👕':['was doen','wassen','wasgoed'],'🛒':['supermarkt','winkel','inkopen'],
 '🗑️':['vuilnis','prullenbak','weggooien'],'🍽️':['afwassen','tafel dekken','eten'],'🪥':['tanden','poetsen','mondverzorging'],
 '🎒':['rugzak','schooltas','tas inpakken'],'📚':['lezen','boek','studeren'],'🧸':['knuffel','opruimen','speelgoed'],
 '🚿':['wassen','douchen','douche nemen'],'🛏️':['bed opmaken','opstaan','slaapkamer'],'🐕':['hond uitlaten','uitlaten','wandelen'],
 '🐈':['kattenbak','kat verzorgen','voer geven'],'🐾':['huisdier','dieren verzorgen'],'🧾':['boodschappenbon','rekening'],
 '📅':['agenda','afspraak','kalender'],'🚲':['fietsen','fiets pakken'],'🚗':['autorijden','auto wassen'],
 '💊':['medicijn','medicatie','innemen'],'🧘':['yoga','ontspannen','stretching'],'🪴':['plant water geven','plant verzorgen'],
 '🧺':['was verzamelen','was sorteren'],'🧽':['afwas','spons','schoonmaken'],'🧴':['shampoo','zeep','verzorging'],
};
const taskIconCategories=[
 'Start','Huis en schoonmaken','Eten en drinken','Natuur en dieren','Verzorging en gezondheid',
 'School en creativiteit','Sport en buiten','Klusjes en reizen','Smileys en beloningen','Spel en plezier','Overig',
];
const taskIconCategoryRules=[
 ['Start',/^Standaard$/],
 ['Eten en drinken',/Koken|Maaltijd|Kruiden|IJs|Drinken|Thee|Koffie|Servies|Bestek|Lepel|Kom|Groente|Fruit|Melk|Brood|Voorraad|Pizza|Koekje|Cupcake|Watermeloen|IJsje/],
 ['Natuur en dieren',/Plant|Tuinieren|Bloemen|Bladeren|Hond|Kat|Pootafdrukken|Vis|Vogel|Hondenbot|Eenhoorn|Dinosaurus|Kikker|Panda|Schildpad|Dolfijn|Bij/],
 ['Verzorging en gezondheid',/Douche|Bad|Toilet|Tandenpoetsen|Tand|Toiletpapier|Verzorging|Baby verzorgen|Fles klaarmaken|Water drinken|Rekken|Medicijnen|Pleister|Moe|Slapen/],
 ['School en creativiteit',/Boeken|Schrijven|Knutselen|Leren|Plannen|Bon|Muziek|Gitaar|Piano spelen|Zingen/],
 ['Sport en buiten',/Sport|Schoenen|Buiten|Wandelen|Zwemmen|Basketbal|Step|Speeltuin|Hoera/],
 ['Klusjes en reizen',/Gereedschap|Repareren|Klus|Schroevendraaier|Ladder|Batterij|Lamp|Sleutel|Post ophalen|Brief posten|Auto|Fiets|Pakket|Reizen|Munt|Winkelen/],
 ['Smileys en beloningen',/Blij|Lach|Cool|Super|Feest vieren|Sterk|Goed gedaan|Hart|Ster|Regenboog|Oranje hart|Glimlach|Knuffel|Engel|Hartjeshanden|Zwaaien|Bedanken|Trofee/],
 ['Spel en plezier',/Speelgoed|Puzzel|Eenhoorn|Dinosaurus|Gamen|Spelletje|Feest/],
 ['Huis en schoonmaken',/Vegen|Schoonmaken|Zeep|Sop|Emmer|Wasmand|Kleding|Broek|Sokken|Jas|Bed|Ramen|Spiegel|Deur|Afval|Recyclen|Boodschappen|Schoenen|Pet|Bank|Stoel|Schilderij|Opruimen|Winkelen/],
];
const taskIconMetadata=(emoji,label)=>{
 const extra=extraTaskIconMetadata.get(emoji);
 const category=extra?.category||taskIconCategoryRules.find(([,pattern])=>pattern.test(label))?.[0]||'Overig';
 return {category,search:normalizeIconSearch([emoji,label,category,...(taskIconAliases[emoji]||[]),...(extra?.aliases||[])].join(' '))};
};
const fmt = (date, options) => new Intl.DateTimeFormat('nl-NL', options).format(date);
const parseDay = value => new Date(value + 'T12:00:00');
const plusDay = (value, n) => {const d = parseDay(value); d.setDate(d.getDate() + n); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`};
const today = () => new Intl.DateTimeFormat('en-CA',{timeZone:data?.config.timezone || 'Europe/Amsterdam',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const person = id => data.members.find(m => m.id === id);
const personName = id => id === 'shared' ? 'Samen' : person(id)?.name || 'Gezin';
const initials = name => name.split(' ').map(x => x[0]).slice(0,2).join('').toUpperCase();
const avatar = m => `<span class="avatar" style="background:${esc(m.color)}20;color:${esc(m.color)}">${esc(m.avatar || initials(m.name))}</span>`;
const selected = (a,b) => a === b ? ' selected' : '';
function updateHeaderDate() {
  const now = new Date();
  const timezone = data?.config.timezone || 'Europe/Amsterdam';
  const date = parseDay(today());
  $('#calendar-date-full').textContent = fmt(date,{weekday:'long',day:'numeric',month:'long'});
  $('#calendar-date-compact').textContent = fmt(date,{weekday:'short',day:'numeric',month:'short'});
  const clockParts = Object.fromEntries(new Intl.DateTimeFormat('en-GB',{
    timeZone:timezone,hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'
  }).formatToParts(now).filter(part=>part.type!=='literal').map(part=>[part.type,Number(part.value)]));
  const hourAngle = (clockParts.hour % 12 + clockParts.minute / 60) * 30;
  const minuteAngle = (clockParts.minute + clockParts.second / 60) * 6;
  $('#clock-hour-hand').setAttribute('transform',`rotate(${hourAngle} 36 36)`);
  $('#clock-minute-hand').setAttribute('transform',`rotate(${minuteAngle} 36 36)`);
  $('#clock-second-hand').setAttribute('transform',`rotate(${clockParts.second * 6} 36 36)`);
  $('#analog-clock').setAttribute('aria-label',`Analoge klok, ${fmt(now,{hour:'2-digit',minute:'2-digit',timeZone:timezone})}`);
  const nextEvent = data?.events?.filter(event => event.all_day
    ? event.start >= today()
    : new Date(event.start) > now
  ).sort((a,b) => {
    const start = event => event.all_day ? Date.parse(`${event.start}T00:00:00Z`) : new Date(event.start).getTime();
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
  const dateLabel = isToday ? '' : `${fmt(eventDate,{weekday:'short',day:'numeric',month:'short',timeZone:nextEvent.all_day?'UTC':timezone})} · `;
  const timeLabel = nextEvent.all_day
    ? 'Hele dag'
    : fmt(eventDate,{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:timezone});
  const label = `${dateLabel}${timeLabel} · ${nextEvent.title}`;
  nextItem.textContent = label;
  nextItem.title = label;
}
function toast(message) {$('#toast').textContent = message; $('#toast').classList.remove('hidden'); clearTimeout(toast.timer); toast.timer = setTimeout(() => $('#toast').classList.add('hidden'), 4200)}
async function api(url, options = {}) {
  let response;
  try {response = await fetch(url, {...options, headers:{'Content-Type':'application/json','X-Family-Request':'1',...options.headers}})} catch {const error=new Error('Geen verbinding. Je wijziging is niet bevestigd. Probeer opnieuw.');error.networkError=true;throw error}
  let result; try {result = await response.json()} catch {const error=new Error('De server geeft geen geldig antwoord. Probeer opnieuw.');if(!response.ok)error.status=response.status;throw error}
  if (!response.ok) {const error = new Error(typeof result.detail === 'string' ? result.detail : 'Controleer de ingevulde gegevens.'); error.status = response.status; throw error;}
  return result;
}
async function refresh(force = false) {
  if (busy) {pendingRefresh = true; return;}
  busy = true;
  try {
    const params = new URLSearchParams();
    if (day) params.set('day', day);
    if (tab === 'calendar' && sub === 'agenda' && view !== 'day') params.set('period', view === 'week' ? 'week' : 'three-day');
    const query = params.toString();
    const fresh = await api('/api/state' + (query ? '?' + query : ''));
    $('#connection').classList.add('hidden');
    const serialized = JSON.stringify(fresh);
    data = fresh; if (!day) day = fresh.day;
    if (serialized !== lastJSON || force || pendingRefresh) {lastJSON = serialized; if (!$('#dialog').open && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName)) render(); else pendingRefresh = true;}
  } catch (e) {
    const message = e.status >= 500
      ? `De server gaf een foutmelding (${e.status}). ${e.message}`
      : e.status
        ? `Het dashboard kon niet worden geladen (${e.status}). ${e.message}`
        : e.networkError
          ? 'Geen verbinding met de server. Controleer de verbinding en probeer opnieuw.'
        : e.message;
    if (data) {
      $('#connection [data-connection-message]').textContent = message;
      $('#connection').classList.remove('hidden');
    } else {
      $('#connection').classList.add('hidden');
      if (!$('#retry-load')) {
        $('#app').innerHTML = `<section class="load-error" role="alert"><h2>Het dashboard kon niet worden geladen</h2><p id="load-error-message"></p><button id="retry-load" class="primary">Opnieuw proberen</button></section>`;
        $('#retry-load').onclick = () => refresh(true);
      }
      $('#load-error-message').textContent = message;
    }
  }
  finally {busy = false;}
}
function filteredRuns(kind) {return data.runs.filter(r => r.day === day && r.kind === kind && (!member || r.member === member || r.member === 'shared' && r.body.members.includes(member)))}
function runsFor(d,kind) {return data.runs.filter(r => r.day === d && r.kind === kind && (!member || r.member === member || r.member === 'shared' && r.body.members.includes(member)))}
function eventsFor(d) {return data.events.filter(e => {
  if (member && e.member && e.member !== member) return false;
  const start = e.all_day ? e.start : new Intl.DateTimeFormat('en-CA',{timeZone:data.config.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(e.start));
  const end = e.all_day ? e.end : new Intl.DateTimeFormat('en-CA',{timeZone:data.config.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(new Date(e.end).getTime() - 1));
  return start <= d && (e.all_day ? end > d || start === d : end >= d || start === d);
}).sort((a,b)=>a.start.localeCompare(b.start));}
function render() {
  if (!data) return;
  const previousAgendaScroll = $('.calendar-time-scroll');
  if (previousAgendaScroll) {
    agendaScrollKey = previousAgendaScroll.dataset.days;
    agendaScrollTop = previousAgendaScroll.scrollTop;
  }
  document.querySelectorAll('[data-tab]').forEach(b=>{const active=b.dataset.tab===tab;b.classList.toggle('active',active);if(active)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
  document.body.classList.toggle('integration-view',tab==='home'||tab==='photos');
  updateHeaderDate();
  updateBrand();
  $('#app').innerHTML = tab === 'calendar' ? calendarShell() : tab === 'home' ? homeView() : tab === 'groceries' ? groceriesView() : photosView();
  renderCalendarStatus();
  const plannerNav = $('.subnav');
  if (plannerNav) {
    const rewardsTab = document.createElement('button');
    rewardsTab.dataset.sub = 'rewards';
    rewardsTab.className = sub === 'rewards' ? 'active' : '';
    rewardsTab.innerHTML = `${icon('gift')}Beloningen`;
    plannerNav.append(rewardsTab);
    if (sub === 'rewards') $('.workspace').innerHTML = `${plannerNav.outerHTML}${rewardsView()}`;
  }
  bindContent();
  const agendaScroll = $('.calendar-time-scroll');
  if (agendaScroll) {
    const scrollKey = agendaScroll.dataset.days;
    if (scrollKey === agendaScrollKey && agendaScrollTop !== null) {
      agendaScroll.scrollTop = agendaScrollTop;
    } else {
      const currentDay = today();
      const currentIndex = scrollKey.split(',').indexOf(currentDay);
      if (currentIndex >= 0) {
        const now = eventLocalParts(new Date().toISOString());
        agendaScroll.scrollTop = Math.max(0, Math.min(18 * 60, now.minutes - 2 * 60));
      }
      agendaScrollKey = scrollKey;
      agendaScrollTop = agendaScroll.scrollTop;
    }
  }
  function updateBrand() {
    const {brand_title:title,brand_subtitle:subtitle,brand_image:image}=data.config;
    const logo=$('.brandmark');
    logo.innerHTML=image?`<img src="/brand-image/${data.config.brand_version}" alt="">`:'<span>s</span><span>✳</span>';
    $('#brand-title').textContent=title;
    $('#brand-caption').textContent=subtitle;
    $('.brand').setAttribute('aria-label',`${title} startpagina`);
    document.title=`${title} — gezinsdashboard`;
  }
  syncAgendaColumnWidths();
  if (tab === 'photos') showPhoto(); else {++photoRequest;clearPhotoCache();}
  pendingRefresh = false;
}
function syncAgendaColumnWidths() {
  const calendar = $('.timetable-calendar'), timeScroll = $('.calendar-time-scroll');
  if (calendar && timeScroll) {
    calendar.style.setProperty('--calendar-scrollbar-width', `${timeScroll.offsetWidth-timeScroll.clientWidth}px`);
  }
}
function updateCurrentTimeIndicator() {
  const marker = $('.current-time-indicator');
  if (!marker) return;
  const now = eventLocalParts(new Date().toISOString());
  marker.style.setProperty('--current-time-top', `${now.minutes}px`);
  const label = `Huidige tijd ${fmt(new Date(),{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:data.config.timezone})}`;
  marker.setAttribute('aria-label', label);
  marker.title = label;
}
function renderCalendarStatus() {
  const calendars = Object.values(data.status)
    .filter(status => status.calendars?.length)
    .flatMap(status => status.calendars.map(calendar => {
      const lastSuccess = status.last_success
        ? fmt(new Date(status.last_success), {day:'numeric', month:'short', hour:'2-digit', minute:'2-digit', timeZone:data.config.timezone})
        : '';
      const update = lastSuccess
        ? `${status.ok ? 'Bijgewerkt' : 'Synchronisatie mislukt · laatst bijgewerkt'}: ${lastSuccess}`
        : status.ok ? 'Nog niet bijgewerkt' : 'Synchronisatie mislukt · nog niet bijgewerkt';
      return `<li class="footer-agenda-entry"><strong>${esc(calendar.name)}</strong><span>${esc(update)}</span></li>`;
    }));
  $('#agenda-status').innerHTML = calendars.length
      ? `<section class="footer-agenda-status" aria-label="Agenda-verbindingen"><ul class="footer-agenda-list">${calendars.join('')}</ul></section>`
    : '';
}
function calendarShell() {
  const openTasks = filteredRuns('tasks').filter(r=>!r.done.length).length;
  const datebar = `<div class="toolbar planner-datebar">${dateNav(sub==='agenda'?(view==='day'?'day':view):'day')}${sub==='agenda'?`<div class="segmented" role="group" aria-label="Agendaweergave"><button data-view="day" class="${view==='day'?'active':''}" aria-pressed="${view==='day'}">Dag</button><button data-view="three-day" class="${view==='three-day'?'active':''}" aria-pressed="${view==='three-day'}">3 dagen</button><button data-view="week" class="${view==='week'?'active':''}" aria-pressed="${view==='week'}">Week</button></div>`:''}</div>`;
  const guide = !data.members.length
    ? `<section class="setup-guide"><div><h2>Begin met jullie gezin</h2><p>Voeg gezinsleden toe. Daarna kun je samen taken plannen.</p></div><div class="setup-actions"><button class="primary" data-action="admin">${icon('plus')}Gezin instellen</button><button class="secondary small" data-action="admin">CalDAV koppelen (optioneel)</button></div></section>`
    : !data.tasks.some(task=>!task.archived)
      ? `<section class="setup-guide"><div><h2>Jullie agenda is klaar voor de eerste plannen</h2><p>Voeg een taak toe; die verschijnt vanzelf op de geplande dag. CalDAV is optioneel voor privéafspraken.</p></div><div class="setup-actions"><button class="primary" data-new="tasks">${icon('plus')}Eerste taak toevoegen</button><button class="secondary small" data-action="admin">CalDAV koppelen (optioneel)</button></div></section>`
      : '';
  return `${datebar}<div class="calendar-layout"><section class="family-filter panel" aria-label="Gezinsfilter"><h2 class="section-label">Ons gezin</h2><div class="family-list" role="group" aria-label="Filter agenda op gezinslid"><button class="person ${!member?'active':''}" data-member="" aria-pressed="${!member}"><span class="avatar">${icon('people')}</span>Iedereen${!member?'<span class="checkmark" aria-hidden="true">✓</span>':''}</button>${data.members.map(m=>`<button class="person ${member===m.id?'active':''}" data-member="${m.id}" aria-pressed="${member===m.id}">${avatar(m)}${esc(m.name)}${member===m.id?'<span class="checkmark" aria-hidden="true">✓</span>':''}</button>`).join('')}</div></section>${guide}<section class="workspace"><nav class="subnav" aria-label="Gezinsplanner">${[['agenda','Agenda','calendar',''],['tasks','Taken','tasks',openTasks],['routines','Routines','routine','']].map(([id,label,i,n])=>`<button data-sub="${id}" class="${sub===id?'active':''}" ${sub===id?'aria-current="page"':''}>${icon(i)}${label}${n!==''?`<span class="count">${n}</span>`:''}</button>`).join('')}</nav>${sub==='agenda'?agendaView():sub==='tasks'?tasksView():sub==='routines'?routinesView():rewardsView()}</section></div>`;
}
function dateNav(mode='day') {const step=mode==='week'?7:mode==='three-day'?3:1;const title=mode==='week'?weekTitle():mode==='three-day'?dateRangeTitle(day,3):fmt(parseDay(day),{weekday:'long',day:'numeric',month:'long'});const period=mode==='week'?'week':mode==='three-day'?'3 dagen':'dag';return `<div class="date-nav"><h2>${title}</h2><button data-date="-${step}" aria-label="Vorige ${period}">${icon('left')}</button><button data-date="${step}" aria-label="Volgende ${period}">${icon('right')}</button><button data-action="today" class="secondary small">Vandaag</button></div>`}
function weekStart(){return plusDay(day,-((parseDay(day).getDay()+6)%7))}
function dateRangeTitle(start,count){const end=plusDay(start,count-1),differentMonth=parseDay(start).getMonth()!==parseDay(end).getMonth();return `${fmt(parseDay(start),differentMonth?{day:'numeric',month:'short'}:{day:'numeric'})} – ${fmt(parseDay(end),{day:'numeric',month:'long',year:'numeric'})}`}
function weekTitle(){const start=weekStart(),end=plusDay(start,6);return `${fmt(parseDay(start),parseDay(start).getMonth()!==parseDay(end).getMonth()?{day:'numeric',month:'short'}:{day:'numeric'})} – ${fmt(parseDay(end),{day:'numeric',month:'long',year:'numeric'})}`}
function agendaTaskCard(r){const task=data.tasks.find(t=>t.id===r.template_id)||r.body;const owners=r.member==='shared'?task.members.map(personName).join(', '):personName(r.member);return `<article class="agenda-task ${r.done.length?'done':''}"><button class="checkbox ${r.done.length?'done':''}" data-run="${r.id}" data-step="0" aria-label="${r.done.length?'Heropen':'Voltooi'} ${esc(task.title)}" aria-pressed="${!!r.done.length}">${icon('check')}</button><div class="agenda-task-copy"><strong>${esc(task.icon)} ${esc(task.title)}</strong><small>${esc(owners)}</small></div></article>`}
function eventLocalParts(value){const parts=new Intl.DateTimeFormat('en-CA',{timeZone:data.config.timezone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(value));const result=Object.fromEntries(parts.filter(part=>part.type!=='literal').map(part=>[part.type,part.value]));return {...result,date:`${result.year}-${result.month}-${result.day}`,minutes:Number(result.hour)*60+Number(result.minute)}}
function timedEventsForDay(date){
 const visibleStart=0,visibleEnd=24*60;
 const timed=[];
 for(const event of eventsFor(date).filter(item=>!item.all_day)){
  const start=eventLocalParts(event.start),end=eventLocalParts(event.end);
  const startMinute=start.date<date?visibleStart:start.minutes;
  const endMinute=end.date>date?visibleEnd:end.minutes;
  const from=Math.max(startMinute,visibleStart),to=Math.min(endMinute,visibleEnd);
  if(to>from)timed.push({event,start:from,end:to});
 }
 timed.sort((a,b)=>a.start-b.start||a.end-b.end);
 let group=[],groupEnd=-1;
 const positionGroup=items=>{
  const laneEnds=[];
  for(const item of items){let lane=laneEnds.findIndex(end=>end<=item.start);if(lane<0)lane=laneEnds.length;laneEnds[lane]=item.end;item.lane=lane}
  items.forEach(item=>{item.laneCount=Math.max(1,laneEnds.length)});
 };
 for(const item of timed){
  if(group.length&&item.start>=groupEnd){positionGroup(group);group=[];groupEnd=-1}
  group.push(item);groupEnd=Math.max(groupEnd,item.end);
 }
 if(group.length)positionGroup(group);
 return {timed:timed.map(item=>`<article class="event timed-event" style="--event-top:${item.start-visibleStart}px;--event-height:${item.end-item.start}px;--event-left:${item.lane/item.laneCount*100}%;--event-width:${100/item.laneCount}%;${eventStyle(item.event)}">${eventContents(item.event)}</article>`)};
}
function eventStyle(e){const m=person(e.member);return `--event-color:${esc(m?.color||'#839870')};--event-bg:${esc(m?.color||'#839870')}16`}
function eventTime(e){return e.all_day?'Hele dag':`${fmt(new Date(e.start),{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:data.config.timezone})}–${fmt(new Date(e.end),{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:data.config.timezone})}`}
function eventContents(e){const m=person(e.member);return `<time>${eventTime(e)}</time><strong>${esc(e.title)}</strong><small>${esc(m?.name||e.calendar||personName(e.member))}${e.location?' · '+esc(e.location):''}</small>`}
function eventCard(e,className=''){const time=eventTime(e);return `<article class="event ${className}" title="${esc(`${time} · ${e.title}`)}" style="${eventStyle(e)}">${eventContents(e)}</article>`}
function agendaView(){
 const days=view==='week'?Array.from({length:7},(_,i)=>plusDay(weekStart(),i)):view==='three-day'?Array.from({length:3},(_,i)=>plusDay(day,i)):[day];
 const mode=view==='week'?'week':view==='three-day'?'three-day':'day',columns=`52px repeat(${days.length},minmax(0,1fr))`;
 const dayHeaders=days.map(d=>`<button class="day-heading ${d===today()?'today':''} ${d===day?'selected':''}" data-day="${d}" aria-label="Selecteer ${fmt(parseDay(d),{day:'numeric',month:'long'})}" aria-pressed="${d===day}"><span>${fmt(parseDay(d),{weekday:'short'})}</span><strong>${parseDay(d).getDate()}</strong></button>`).join('');
 const taskCells=days.map(d=>`<section class="day-column day-task-cell ${d===day?'selected':''}" data-day-column="${d}">${runsFor(d,'tasks').map(agendaTaskCard).join('')||'<span class="no-day-tasks">Geen taken</span>'}</section>`).join('');
 const dailyEvents=days.map(d=>({date:d,allDay:eventsFor(d).filter(e=>e.all_day),...timedEventsForDay(d)}));
 const allDayRow=dailyEvents.some(column=>column.allDay.length)?`<div class="calendar-row calendar-all-day-row"><div class="calendar-row-label">Hele dag</div>${dailyEvents.map(column=>`<div class="calendar-special-cell">${column.allDay.map(e=>eventCard(e,'all-day-event')).join('')}</div>`).join('')}</div>`:'';
 const hours=Array.from({length:25},(_,i)=>`<span class="calendar-hour-label ${i===0?'first':''} ${i===24?'last':''}" style="top:${i*60}px">${String(i).padStart(2,'0')}:00</span>`).join('');
 const lines=Array.from({length:24},(_,i)=>`<span class="calendar-hour-line" style="top:${i*60}px"></span>`).join('');
 const schedules=dailyEvents.map(column=>`<section class="day-timeline ${column.date===day?'selected':''}" data-timeline-day="${column.date}"><div class="calendar-hour-lines" aria-hidden="true">${lines}</div>${column.timed.join('')}</section>`).join('');
 const currentTime=days.includes(today())?`<div class="current-time-indicator" role="img" aria-label="Huidige tijd" style="--current-time-top:${eventLocalParts(new Date().toISOString()).minutes}px"></div>`:'';
 return `<div class="calendar timetable-calendar ${view==='day'?'day-view':''} ${view==='three-day'?'three-day-view':''}" style="--calendar-columns:${columns};--calendar-days:${days.length}" aria-label="${view==='week'?'Weekagenda':view==='three-day'?'3-daagse agenda':'Dagagenda'}"><div class="calendar-row calendar-day-headings"><div class="calendar-row-label"></div>${dayHeaders}</div><div class="calendar-row calendar-task-row"><div class="calendar-row-label">Taken</div>${taskCells}</div>${allDayRow}<div class="calendar-time-scroll" data-days="${days.join(',')}" tabindex="0" aria-label="Tijdlijn, scroll verticaal om andere tijden te bekijken"><div class="calendar-schedule-row"><div class="calendar-time-axis">${hours}</div><div class="calendar-day-schedules">${schedules}${currentTime}</div></div></div></div><div class="bottom-grid"><section class="panel"><div class="card-title"><h2>Te doen op ${fmt(parseDay(day),{day:'numeric',month:'short'})}</h2><button data-sub="tasks">Alle taken ${icon('right')}</button></div><div class="list">${filteredRuns('tasks').filter(r=>!r.done.length).slice(0,2).map(taskRow).join('')||'<div class="empty compact"><p>Alles rustig hier. Voeg een taak toe voor vandaag.</p></div>'}</div></section><section class="panel"><div class="card-title"><h2>Niet vergeten in de winkel</h2><button data-tab="groceries">De lijst ${icon('right')}</button></div><div class="list">${data.groceries.filter(g=>!g.done).slice(0,2).map(groceryRow).join('')||'<div class="empty compact"><p>De boodschappenlijst is nog leeg. Wat hebben we nodig?</p></div>'}</div></section></div>`;
}
function empty(title,desc,i,button=''){return `<div class="panel empty"><span class="empty-icon">${icon(i)}</span><h3>${title}</h3><p>${desc}</p>${button}</div>`}
function taskSchedule(task){if(task.repeat==='once')return `Eenmalig · ${fmt(parseDay(task.date),{weekday:'long',day:'numeric',month:'long'})}`;if(task.repeat==='daily')return 'Elke dag';return weekdayNames.filter((_,i)=>task.weekdays?.includes(i)).join(', ')}
function taskRow(r){const task=data.tasks.find(t=>t.id===r.template_id)||r.body;const owners=task.members.map(id=>person(id)?.name).filter(Boolean);return `<div class="task-row"><button class="checkbox ${r.done.length?'done':''}" data-run="${r.id}" data-step="0" aria-label="${r.done.length?'Heropen':'Voltooi'} ${esc(task.title)}" aria-pressed="${!!r.done.length}">${icon('check')}</button><span class="task-icon">${esc(task.icon)}</span><div class="row-text ${r.done.length?'done':''}"><strong>${esc(task.title)}</strong><small class="task-owners">Voor: ${esc(owners.join(', ')||personName(r.member))}</small>${task.description?`<small>${esc(task.description)}</small>`:''}<span class="task-schedule">${esc(taskSchedule(task))}</span></div>${task.points?`<span class="points">✦ ${task.points}</span>`:''}<button data-edit="tasks:${r.template_id}" aria-label="Taak bewerken">${icon('edit')}</button></div>`}
function tasksView(){const runs=filteredRuns('tasks');return `<div class="toolbar"><button class="primary" data-new="tasks">${icon('plus')}Nieuwe taak</button></div><div class="list">${runs.map(taskRow).join('')||empty('Kleine taken, samen gedaan.','Voeg een eenmalige of terugkerende taak toe. Ieder gezinslid kan een eigen uitvoering krijgen.','tasks',`<button class="primary" data-new="tasks">${icon('plus')}Eerste taak toevoegen</button>`)}</div><div class="toolbar" style="margin-top:20px"><button class="subtle-button" data-action="templates-tasks">Taaksjablonen beheren</button><button class="subtle-button" data-action="history">${icon('history')}Historie bekijken</button></div>`}
function routinesView(){
  const runs=filteredRuns('routines');
  const templates=data.routines.filter(r=>!r.archived&&(!member||r.members.includes(member)));
  const runsByTemplate=new Map();
  runs.forEach(run=>{
    if(!runsByTemplate.has(run.template_id))runsByTemplate.set(run.template_id,[]);
    runsByTemplate.get(run.template_id).push(run);
  });
  const cards=runs.length
    ? [...runsByTemplate.values()].map(group=>{
      const routine=group[0].body;
      const progress=group.map(r=>`<div class="routine-member-progress">${avatar(person(r.member))}<span>${esc(personName(r.member))} · ${r.done.length} van ${r.body.steps.length} stappen klaar</span><div class="progress" aria-label="${r.done.length} van ${r.body.steps.length} stappen voltooid"><span style="width:${r.done.length/r.body.steps.length*100}%"></span></div></div>`).join('');
      const steps=routine.steps.map((s,i)=>{
        const complete=group.every(r=>r.done.includes(i));
        const controls=group.map(r=>`<span class="routine-step-owner" title="${esc(personName(r.member))}">${avatar(person(r.member))}<button class="checkbox ${r.done.includes(i)?'done':''}" data-run="${r.id}" data-step="${i}" aria-label="${r.done.includes(i)?'Heropen':'Voltooi'} ${esc(s.text)} voor ${esc(personName(r.member))}" aria-pressed="${r.done.includes(i)}">${icon('check')}</button></span>`).join('');
        return `<div class="step ${complete?'done':''}"><span class="routine-step-label">${esc(s.icon)} ${esc(s.text)}</span><div class="routine-step-controls">${controls}</div></div>`;
      }).join('');
      return `<section class="panel"><div class="routine-header"><div><h2>${esc(routine.icon)} ${esc(routine.title)}</h2><small>${esc(group.map(r=>personName(r.member)).join(', '))} · ${esc(routine.start_time)} – ${esc(routine.end_time)}</small></div><button data-edit="routines:${group[0].template_id}" aria-label="Routine bewerken">${icon('edit')}</button></div><div class="routine-member-progress-list">${progress}</div>${steps}</section>`;
    }).join('')
    : templates.length
      ? `<section class="panel"><h2>Geen routine gepland op ${esc(fmt(parseDay(day),{weekday:'long'}))}</h2><p>Hieronder staan de actieve routines op hun ingeplande dagen.</p></section>${templates.map(r=>`<section class="panel routine-preview"><div class="routine-header"><div><h2>${esc(r.icon)} ${esc(r.title)}</h2><small>${esc(r.members.map(personName).join(', '))} · ${esc(r.start_time)} – ${esc(r.end_time)}</small></div><button data-edit="routines:${r.id}" aria-label="Routine bewerken">${icon('edit')}</button></div><p class="small muted">Gepland: ${esc(weekdayNames.filter((_,i)=>r.weekdays.includes(i)).join(', '))}${r.date>day?` · Startdatum: ${esc(fmt(parseDay(r.date),{weekday:'long',day:'numeric',month:'long'}))}`:''}</p>${r.steps.map(s=>`<div class="step"><span>${esc(s.icon)} ${esc(s.text)}</span></div>`).join('')}</section>`).join('')}`
      : empty('Een fijn ritme voor elke dag.','Maak een ochtend- of avondroutine met stappen, gezinsleden en vaste weekdagen.','routine',`<button class="primary" data-new="routines">${icon('plus')}Eerste routine maken</button>`);
  return `<div class="toolbar"><button class="primary" data-new="routines">${icon('plus')}Nieuwe routine</button></div><div class="routine-grid">${cards}</div><div class="toolbar" style="margin-top:20px"><button class="subtle-button" data-action="templates-routines">Routinesjablonen beheren</button><button class="subtle-button" data-action="history">${icon('history')}Historie bekijken</button></div>`;
}
function groceryRow(g){return `<div class="grocery-row"><button class="checkbox ${g.done?'done':''}" data-grocery="${g.id}" aria-label="${g.done?'Heropen':'Vink af'} ${esc(g.name)}" aria-pressed="${g.done}">${icon('check')}</button><div class="row-text ${g.done?'done':''}"><strong>${esc(g.name)}</strong><small>${esc([g.quantity,g.note].filter(Boolean).join(' · '))}</small></div><button data-edit="groceries:${g.id}" aria-label="${esc(g.name)} bewerken">${icon('edit')}</button></div>`}
function groceriesView(){const done=data.groceries.filter(g=>g.done),open=data.groceries.filter(g=>!g.done);return `<div class="toolbar"><div><h2>Wat hebben we nodig?</h2><p class="small muted" style="margin-top:8px">Eén lijst voor het hele gezin. Ook op je telefoon.</p></div></div><form id="quick-add" class="quick-add"><input aria-label="Boodschap" name="name" value="${esc(quickDraft)}" placeholder="Bijvoorbeeld melk, appels of brood…" required maxlength="150" autocomplete="off"><button type="button" class="secondary" data-new="groceries">${icon('plus')}Met details</button><button class="primary" type="submit">${icon('plus')}Toevoegen</button></form><div class="list-label"><span>NOG NODIG · ${open.length}</span></div><div class="list">${open.map(groceryRow).join('')||empty('De lijst is helemaal bij.','Voeg hierboven iets toe zodra je eraan denkt.','basket')}</div>${done.length?`<div class="list-label"><span>IN HET MANDJE · ${done.length}</span><button data-action="clear-groceries" class="small">Afgevinkte opruimen</button></div><div class="list">${done.map(groceryRow).join('')}</div>`:''}`}
function timestampDay(value){return new Intl.DateTimeFormat('en-CA',{timeZone:data.config.timezone,year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value.replace(' ','T')+'Z'))}
function rewardsView(){
 const current=person(member),balance=data.balances[member]||{balance:0,reserved:0,available:0};
 const requests=data.reward_requests.filter(r=>r.member_id===member&&timestampDay(r.created_at)===day);
 const transactions=data.point_transactions.filter(t=>t.member_id===member&&timestampDay(t.created_at)===day);
 const selectedDate=fmt(parseDay(day),{day:'numeric',month:'long',year:'numeric'});
 return `<section class="panel rewards-summary"><div><div class="section-label">Jouw puntensaldo</div><h2>${current?esc(current.name):'Kies een gezinslid'}</h2><p class="muted">${current?`${balance.available} beschikbaar · ${balance.reserved} gereserveerd voor aanvragen`:'Selecteer hierboven een profiel om saldo en beloningen te zien.'}</p></div><strong class="reward-balance">✦ ${balance.balance}</strong></section>${!data.members.length?empty('Nog geen gezinsleden','Voeg eerst gezinsleden toe via Beheer.','people'):''}<div class="card-title"><h2>Beloningen</h2></div><div class="reward-grid">${data.rewards.map(r=>`<article class="panel reward-card"><span class="reward-icon">${esc(r.icon)}</span><h3>${esc(r.title)}</h3><p>${esc(r.description||'')}</p><div class="reward-footer"><span class="points">✦ ${r.price} punten</span><button class="primary small" data-request-reward="${r.id}" ${!current||balance.available<r.price?'disabled':''}>Aanvragen</button></div></article>`).join('')||empty('Nog geen beloningen','De beheerder kan beloningen toevoegen via Beheer.','people')}</div>${current?`<div class="bottom-grid"><section class="panel"><div class="card-title"><h2>Jouw aanvragen · ${esc(selectedDate)}</h2></div>${requests.map(r=>`<div class="history-item">${esc(r.reward_name)} · ${r.cost} punten <span class="reward-status ${esc(r.status)}">${({pending:'In afwachting',approved:'Goedgekeurd',rejected:'Afgewezen'})[r.status]}</span><small>${fmt(new Date(r.created_at.replace(' ','T')+'Z'),{dateStyle:'short',timeStyle:'short',timeZone:data.config.timezone})}</small></div>`).join('')||'<p class="muted">Geen aanvragen op deze datum.</p>'}</section><section class="panel"><div class="card-title"><h2>Puntentransacties · ${esc(selectedDate)}</h2></div>${transactions.map(t=>`<div class="history-item">${esc(({completion:'Taak of routine voltooid','completion-undone':'Voltooiing ongedaan gemaakt','reward-redemption':'Beloning goedgekeurd'})[t.reason]||t.reason)} <strong class="${t.amount<0?'negative':''}">${t.amount>0?'+':''}${t.amount}</strong><small>${fmt(new Date(t.created_at.replace(' ','T')+'Z'),{dateStyle:'short',timeStyle:'short',timeZone:data.config.timezone})}</small></div>`).join('')||'<p class="muted">Geen transacties op deze datum.</p>'}</section></div>`:''}`;
}
function homeView(){
 const url=data.config.ha_url?`${data.config.ha_url}${data.config.ha_dashboard}`:'';
 return `<section class="integration">${url?`<iframe id="ha-dashboard" class="ha-dashboard" src="${esc(url)}" title="Home Assistant-dashboard" allow="fullscreen; clipboard-read; clipboard-write" referrerpolicy="no-referrer"></iframe>`:empty('Verbind je huis.','Stel in Beheer het Home Assistant-serveradres en het dashboardpad in.','home',`<button class="primary" data-action="admin">${icon('settings')}Home Assistant instellen</button>`)}</section>`;
}
function photosView(){return data.photos.length?`<section class="photo-view"><div class="photo-stage"><img id="photo" alt="Foto uit geselecteerd Immich-album"></div><div class="photo-controls"><button class="secondary" data-photo="prev" aria-label="Vorige foto">${icon('left')}</button><button class="primary" data-photo="pause" aria-label="${paused?'Diavoorstelling hervatten':'Diavoorstelling pauzeren'}">${icon(paused?'play':'pause')} ${paused?'Afspelen':'Pauzeren'}</button><button class="secondary" data-photo="next" aria-label="Volgende foto">${icon('right')}</button></div><div class="photo-caption" id="photo-caption"></div></section>`:empty('Jullie herinneringen verdienen een plekje.','Selecteer in Beheer de Immich-albums die hier mogen verschijnen. Alleen foto’s uit die albums worden getoond.','image',`<button class="primary" data-action="admin">${icon('image')}Albums kiezen</button>`) + (data.status.immich?.ok===false?`<p class="notice">${esc(data.status.immich.message)}</p>`:'')}
const photoCache = new Map();
let photoOrder = [], photoOrderKey = '', photoRequest = 0;
function clearPhotoCache(keep = new Set()) {
  for (const [id, entry] of photoCache) {
    if (keep.has(id)) continue;
    entry.controller.abort();
    if (entry.url) URL.revokeObjectURL(entry.url);
    photoCache.delete(id);
  }
}
function loadPhoto(id) {
  if (photoCache.has(id)) return photoCache.get(id).promise;
  const entry = {controller: new AbortController(), url: null};
  entry.promise = (async () => {
    const response = await fetch('/api/photos/'+encodeURIComponent(id), {signal: entry.controller.signal});
    if (!response.ok) {
      const error = new Error('De foto’s zijn momenteel niet beschikbaar. Probeer het later opnieuw.');
      if (response.status === 403) {
        const body = await response.json();
        error.message = body.detail;
      }
      throw error;
    }
    const blob = await response.blob();
    if (entry.controller.signal.aborted) throw new DOMException('Geannuleerd', 'AbortError');
    entry.url = URL.createObjectURL(blob);
    return entry.url;
  })();
  photoCache.set(id, entry);
  // Preload failures are shown only when that photo is selected.
  entry.promise.catch(() => {});
  return entry.promise;
}
async function showPhoto(direction=0) {
  clearTimeout(photoTimer);
  const request = ++photoRequest;
  if (tab !== 'photos' || !data.photos.length) {clearPhotoCache(); return;}
  const key = JSON.stringify([Boolean(screen.shuffle), data.photos.map(p => p.id)]);
  if (key !== photoOrderKey) {
    photoOrderKey = key;
    photoOrder = [...data.photos];
    if (screen.shuffle) {
      for (let i=photoOrder.length-1;i>0;i--) {
        const j = Math.floor(Math.random()*(i+1));
        [photoOrder[i],photoOrder[j]] = [photoOrder[j],photoOrder[i]];
      }
    }
    photoIndex = 0;
  }
  photoIndex = (photoIndex+direction+photoOrder.length)%photoOrder.length;
  const current = photoOrder[photoIndex], img = $('#photo');
  if (!img) {render();return;}
  const upcoming = Array.from({length: Math.min(5,photoOrder.length-1)},
    (_,i) => photoOrder[(photoIndex+i+1)%photoOrder.length]);
  clearPhotoCache(new Set([current.id, ...upcoming.map(p => p.id)]));
  img.style.objectFit = screen.crop ? 'cover' : 'contain';
  $('#photo-caption').textContent = `${current.album} · ${photoIndex+1} / ${photoOrder.length}`;
  try {
    const url = await loadPhoto(current.id);
    if (request !== photoRequest || !img.isConnected) return;
    img.onload = () => {if (!paused) photoTimer=setTimeout(()=>showPhoto(1),data.config.slide_seconds*1000)};
    img.onerror = () => {
      clearTimeout(photoTimer);
      $('.photo-stage').innerHTML = '<p role="alert" style="color:white;padding:30px">De foto’s zijn momenteel niet beschikbaar. Probeer het later opnieuw.</p>';
    };
    img.dataset.assetId = current.id;
    img.src = url;
    for (const photo of upcoming) loadPhoto(photo.id);
  } catch (error) {
    if (request !== photoRequest || !img.isConnected || error.name === 'AbortError') return;
    $('.photo-stage').innerHTML = `<p role="alert" style="color:white;padding:30px">${esc(error.message)}</p>`;
  }
}
async function mutate(kind, item, body, action='save', requestId=uuid()) {return api('/api/entities/'+kind,{method:'POST',body:JSON.stringify({request_id:requestId,id:item?.id||uuid(),version:item?.version||0,action,body})})}
async function operation(fn, button){if(button)button.disabled=true;try{await fn();await refresh(true);}catch(e){toast(e.message);if(e.status===409)await refresh(true)}finally{if(button)button.disabled=false}}
function celebrateTaskCompletion(button) {
 if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
 const bounds=button.getBoundingClientRect(),burst=document.createElement('div');
 const colors=['#bb583f','#e9b864','#456350','#7fa3a1','#d98168'];
 burst.className='confetti-burst';
 burst.setAttribute('aria-hidden','true');
 for(let i=0;i<28;i++){
  const angle=(Math.PI*2*i/28)+(Math.random()-.5)*.4,distance=60+Math.random()*100;
  const piece=document.createElement('span');
  piece.className='confetti-piece';
  if(Math.random()<.25)piece.classList.add('round');
  piece.style.left=`${bounds.left+bounds.width/2}px`;
  piece.style.top=`${bounds.top+bounds.height/2}px`;
  piece.style.backgroundColor=colors[i%colors.length];
  piece.style.setProperty('--confetti-x',`${Math.cos(angle)*distance}px`);
  piece.style.setProperty('--confetti-y',`${Math.sin(angle)*distance}px`);
  piece.style.setProperty('--confetti-rotation',`${Math.round((Math.random()-.5)*900)}deg`);
  piece.style.setProperty('--confetti-delay',`${Math.random()*90}ms`);
  burst.append(piece);
 }
 document.body.append(burst);
 setTimeout(()=>burst.remove(),1100);
}
const routineCelebrationVariants=[
 {id:'flowers',name:'Bloemenfeest',icons:['🌸','🌼','🌷','🌺','🌻']},
 {id:'rockets',name:'Raketlancering',icons:['🚀','🪐','⭐','☄️','🌟']},
 {id:'butterflies',name:'Vlinderdans',icons:['🦋','🌈','🌸','✨','🦋']},
 {id:'balloons',name:'Ballonnenregen',icons:['🎈','🎊','🎉','✨','🎈']},
 {id:'unicorns',name:'Eenhoornmagie',icons:['🦄','💫','🌟','✨','🦄']},
 {id:'bees',name:'Bijendans',icons:['🐝','🌻','🍯','🌼','🐝']},
 {id:'stars',name:'Sterrenparade',icons:['🌠','⭐','🌙','✨','💫']},
 {id:'ocean',name:'Onderwaterfeest',icons:['🐬','🐠','🫧','🐳','🐚']},
 {id:'magic',name:'Toverfeest',icons:['🪄','✨','🔮','🌙','💫']},
 {id:'trophies',name:'Kampioenenfeest',icons:['🏆','🥇','🎊','🎉','⭐']}
];
let routineCelebrationIndex=Math.floor(Math.random()*routineCelebrationVariants.length);
const routineCelebrationMessages=[
 'Supergoed gedaan',
 'Wat heb jij dat goed gedaan',
 'Geweldig gedaan',
 'Fantastisch',
 'Wat een topper ben jij',
 'Jij hebt dit geweldig gedaan',
 'Knap gedaan',
 'Wauw, wat goed',
 'Echt super gedaan',
 'Wat mag je trots zijn'
];
let previousRoutineCelebrationMessage=-1;
function celebrateRoutineCompletion(memberName) {
 if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
 const previous=document.querySelector('.routine-celebration');
 if(previous){clearTimeout(previous.dismissTimer);previous.remove()}
 const variant=routineCelebrationVariants[routineCelebrationIndex];
 routineCelebrationIndex=(routineCelebrationIndex+1)%routineCelebrationVariants.length;
 const overlay=document.createElement('div');
 overlay.className='routine-celebration';
 overlay.dataset.variant=variant.id;
 overlay.setAttribute('role','status');
 overlay.setAttribute('aria-live','polite');
 const icons=document.createElement('div');
 icons.className='routine-celebration-icons';
 icons.setAttribute('aria-hidden','true');
 for(let i=0;i<42;i++){
  const piece=document.createElement('span');
  const left=8+Math.random()*84,top=8+Math.random()*84;
  const dx=left-50,dy=top-50,distance=Math.hypot(dx,dy)||1;
  piece.className='routine-celebration-icon';
  piece.textContent=variant.icons[i%variant.icons.length];
  piece.style.left=`${left}%`;
  piece.style.top=`${top}%`;
  piece.style.setProperty('--fly-x',`${dx/distance*110}vw`);
  piece.style.setProperty('--fly-y',`${dy/distance*110}vh`);
  piece.style.setProperty('--fly-rotation',`${Math.round((Math.random()-.5)*100)}deg`);
  piece.style.setProperty('--fly-delay',`${Math.random()*500}ms`);
  icons.append(piece);
 }
 const message=document.createElement('div');
 message.className='routine-celebration-message';
 let messageIndex=Math.floor(Math.random()*routineCelebrationMessages.length);
 if(messageIndex===previousRoutineCelebrationMessage)messageIndex=(messageIndex+1+Math.floor(Math.random()*(routineCelebrationMessages.length-1)))%routineCelebrationMessages.length;
 previousRoutineCelebrationMessage=messageIndex;
 const sparkle=document.createElement('span');
 sparkle.className='routine-celebration-sparkle';
 sparkle.setAttribute('aria-hidden','true');
 sparkle.textContent='✦';
 const heading=document.createElement('h2');
 heading.textContent=`${routineCelebrationMessages[messageIndex]}, ${memberName}!`;
 message.append(sparkle,heading);
 const close=document.createElement('button');
 close.className='routine-celebration-close';
 close.type='button';
 close.textContent='Verder';
 close.setAttribute('aria-label','Viering sluiten');
 const dismiss=()=>{clearTimeout(overlay.dismissTimer);overlay.remove()};
 close.addEventListener('click',dismiss);
 overlay.append(icons,message,close);
 document.body.append(overlay);
 overlay.dismissTimer=setTimeout(()=>overlay.remove(),4600);
}
function bindContent(){
 document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>navigate(b.dataset.tab,b.dataset.sub));
 document.querySelectorAll('[data-member]').forEach(b=>b.onclick=()=>{member=b.dataset.member;render()});
 document.querySelectorAll('[data-sub]').forEach(b=>b.onclick=()=>navigate('calendar',b.dataset.sub));
 document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;calendarViewPreference=view;try{localStorage.setItem('samen-calendar-view',view)}catch{toast('De agendaweergave kan niet op dit scherm worden opgeslagen.')}refresh(true)});
 document.querySelectorAll('[data-date]').forEach(b=>b.onclick=()=>{day=plusDay(day,Number(b.dataset.date));refresh(true)});
 document.querySelectorAll('[data-day]').forEach(b=>b.onclick=()=>{day=b.dataset.day;refresh(true)});
 document.querySelectorAll('[data-new]').forEach(b=>b.onclick=()=>editEntity(b.dataset.new));
 document.querySelectorAll('[data-edit]').forEach(b=>b.onclick=()=>{const[k,id]=b.dataset.edit.split(':');editEntity(k,data[k].find(x=>x.id===id))});
 document.querySelectorAll('[data-run]').forEach(b=>b.onclick=()=>operation(async()=>{const r=data.runs.find(x=>x.id===b.dataset.run),step=Number(b.dataset.step),completing=!r.done.includes(step),done=completing?[...r.done,step]:r.done.filter(s=>s!==step);await mutate('runs',r,{done});if(completing){if(r.kind==='routines'){if(done.length===r.body.steps.length)celebrateRoutineCompletion(personName(r.member))}else celebrateTaskCompletion(b)}},b));
 document.querySelectorAll('[data-grocery]').forEach(b=>b.onclick=()=>operation(async()=>{const g=data.groceries.find(x=>x.id===b.dataset.grocery);await mutate('groceries',g,{...g,done:!g.done})},b));
 document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>action(b.dataset.action,b));
 document.querySelectorAll('[data-request-reward]').forEach(b=>b.onclick=()=>requestReward(b.dataset.requestReward,b));
 document.querySelectorAll('[data-photo]').forEach(b=>b.onclick=()=>{if(b.dataset.photo==='pause'){paused=!paused;render()}else showPhoto(b.dataset.photo==='prev'?-1:1)});
 const form=$('#quick-add');if(form){form.elements.namedItem('name').oninput=()=>{quickDraft=form.elements.namedItem('name').value};let submission;form.onsubmit=async e=>{e.preventDefault();if(!submission||submission.name!==form.elements.namedItem('name').value.trim())submission={name:form.elements.namedItem('name').value.trim(),id:uuid(),request:uuid()};const b=form.querySelector('button');b.disabled=true;try{await mutate('groceries',{id:submission.id,version:0},{name:submission.name,done:false},'save',submission.request);form.reset();quickDraft='';submission=null;document.activeElement.blur();await refresh(true);toast('Toegevoegd aan jullie lijst')}catch(err){toast(err.message)}finally{b.disabled=false}}}
}
async function requestReward(rewardId,button){
 const key=`${member}:${rewardId}`;
 const requestId=rewardRequestRetries.get(key)||uuid();
 rewardRequestRetries.set(key,requestId);
 await operation(async()=>{
  await api('/api/reward-requests',{method:'POST',body:JSON.stringify({request_id:requestId,member_id:member,reward_id:rewardId})});
  rewardRequestRetries.delete(key);
  toast('Aanvraag verstuurd; de punten zijn gereserveerd tot goedkeuring.');
 },button);
}
function hasInput(){return $('#dialog').open||!!$('#quick-add input')?.value}
function navigate(next, section){if($('#quick-add input')?.value&&!confirm('Je hebt nog een niet-opgeslagen boodschap. Invoer verlaten?'))return;quickDraft='';tab=next;if(section)sub=section;clearTimeout(photoTimer);render()}
async function action(name,button){if(name==='admin')return openAdmin();if(name==='today'){day=today();return refresh(true)}if(name==='history')return showHistory();if(name.startsWith('templates-'))return showTemplates(name.slice(10));if(name==='clear-groceries'){if(!confirm('Alle afgevinkte boodschappen verwijderen?'))return;await operation(async()=>{for(const g of data.groceries.filter(x=>x.done))await mutate('groceries',g,{},'delete')},button)}}
function modal(title,content){dialogDirty=false;$('#dialog-content').innerHTML=`<div class="modal-head"><h2>${title}</h2><button id="close-dialog" aria-label="Sluiten">${icon('close')}</button></div>${content}<div id="form-error" class="form-error hidden" role="alert"></div>`;$('#close-dialog').onclick=closeDialog;if(!$('#dialog').open)$('#dialog').showModal();$('#dialog').oninput=()=>dialogDirty=true;}
function confirmDiscard(onLeave,message='Niet-opgeslagen invoer verlaten?'){
 const confirmation=$('#discard-confirmation');
 $('#discard-confirmation-message').textContent=message;
 $('#keep-editing').onclick=()=>confirmation.close();
 $('#leave-without-saving').onclick=()=>{confirmation.close();onLeave()};
 confirmation.showModal();
}
function closeDialog(){if(dialogDirty)return confirmDiscard(()=>finishCloseDialog());finishCloseDialog()}
function finishCloseDialog(){$('#dialog').close();dialogDirty=false;if(pendingRefresh)render()}
$('#dialog').addEventListener('cancel',e=>{e.preventDefault();closeDialog()});
function errorInForm(err){$('#form-error').textContent=err.message+(err.status===409?' Je invoer blijft staan. Sluit dit venster en open het item opnieuw om de nieuwste versie te bewerken.':'');$('#form-error').classList.remove('hidden')}
function bindForm(fn,afterSave){$('#edit-form').onsubmit=async e=>{e.preventDefault();const buttons=e.target.querySelectorAll('button');buttons.forEach(b=>b.disabled=true);$('#form-error').classList.add('hidden');try{await fn(new FormData(e.target));dialogDirty=afterSave?afterSave():false;if(!dialogDirty)$('#dialog').close();await refresh(true);toast('Opgeslagen')}catch(err){errorInForm(err);if(err.status===409)await refresh()}finally{buttons.forEach(b=>b.disabled=false)}}}
const field=(label,name,value='',type='text',extra='')=>`<label>${label}<input name="${name}" type="${type}" value="${esc(value)}" ${extra}></label>`;
const normalizeIconSearch=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase();
function editEntity(kind,item){
 const isTask=kind==='tasks',isRoutine=kind==='routines',isReward=kind==='rewards';const x=item||{};let html='';
 const iconField=(name,value,id,label)=>{
   const choices=value&&!taskIcons.some(([choice])=>choice===value)?[...taskIcons,[value,'Huidig pictogram']]:taskIcons;
   const groupedChoices=new Map();
   choices.forEach(([choice,choiceLabel])=>{
     const metadata=taskIconMetadata(choice,choiceLabel);
     if(!groupedChoices.has(metadata.category))groupedChoices.set(metadata.category,[]);
     groupedChoices.get(metadata.category).push({choice,choiceLabel,search:metadata.search});
   });
   const groups=[...groupedChoices].sort(([a],[b])=>taskIconCategories.indexOf(a)-taskIconCategories.indexOf(b));
   return `<div class="task-icon-field${isRoutine&&name==='icon'?' routine-icon-field':''}"><span class="task-icon-label">${esc(label)}</span><input type="hidden" name="${esc(name)}" value="${esc(value)}"><button type="button" class="task-icon-trigger" aria-haspopup="dialog" aria-expanded="false" aria-controls="${esc(id)}"><span>Kies pictogram</span><span class="task-icon-current">${esc(value)}</span></button><div id="${esc(id)}" class="task-icon-picker" role="group" aria-label="Kies een pictogram voor ${esc(label.toLowerCase())}" hidden><input type="search" class="task-icon-search" aria-label="Zoek pictogrammen" placeholder="Zoek op naam of pictogram"><p class="task-icon-no-results" role="status" hidden>Geen pictogrammen gevonden.</p>${groups.map(([category,icons])=>`<section class="task-icon-category"><h4>${esc(category)}</h4><div class="task-icon-category-grid">${icons.map(({choice,choiceLabel,search})=>`<button type="button" class="task-icon-option" data-task-icon="${esc(choice)}" data-search="${esc(search)}" aria-label="${esc(choiceLabel)}" aria-pressed="${value===choice}">${esc(choice)}</button>`).join('')}</div></section>`).join('')}</div></div>`;
 };
 const routineSteps=x.steps?.length?x.steps:[{icon:'✓',text:''}];
 let nextRoutineStepId=routineSteps.length;
 const routineStep=(step,index)=>`<div class="routine-step-row"><label>Titel stap ${index+1}<input name="step_text" type="text" value="${esc(step.text)}" required maxlength="150"></label>${iconField('step_icon',step.icon||'✓',`routine-step-icon-${index}`,`Pictogram stap ${index+1}`)}<button type="button" class="danger remove-routine-step" aria-label="Stap ${index+1} verwijderen">${icon('close')}</button></div>`;
 if(kind==='members')html=`<div class="form-grid">${field('Naam','name',x.name,'text','required maxlength="60"')}${field('Kleur','color',x.color||'#b97b63','color')}${field('Avatar (emoji, optioneel)','avatar',x.avatar,'text','maxlength="8"')}</div>`;
 else if(kind==='groceries')html=`${field('Wat hebben we nodig?','name',x.name,'text','required maxlength="150"')}${field('Hoeveelheid / eenheid','quantity',x.quantity,'text','maxlength="60"')}${field('Notitie','note',x.note,'text','maxlength="500"')}`;
 else if(isReward)html=`<div class="form-grid">${field('Naam','title',x.title,'text','required maxlength="100"')}${field('Pictogram','icon',x.icon||'🎁','text','maxlength="8"')}${field('Prijs in punten','price',x.price||1,'number','min="1" max="100000" required')}<label class="full">Beschrijving<textarea name="description" maxlength="500">${esc(x.description||'')}</textarea></label></div>`;
 else {
 if(!data.members.length){modal('Eerst je gezin toevoegen',`<p class="muted">Voeg in Beheer minstens één gezinslid toe. Daarna kun je taken en routines toewijzen.</p><div class="form-actions"><button id="go-admin" class="primary">Gezin instellen</button></div>`);$('#go-admin').onclick=openAdmin;return;}
 const entityIcon=isTask?iconField('icon',x.icon||'✓','task-icon-picker','Pictogram'):iconField('icon',x.icon||'☀️','routine-icon-picker','Pictogram');
 html=`<div class="form-grid">${field('Titel','title',x.title,'text','required maxlength="150"')}${entityIcon}<label class="full">Beschrijving<textarea name="description" maxlength="1000">${esc(x.description||'')}</textarea></label>${field('Startdatum','date',x.date||day,'date','required')}${isTask?`<label>Herhaling<select name="repeat"><option value="once"${selected(x.repeat,'once')}>Eenmalig</option><option value="daily"${selected(x.repeat,'daily')}>Elke dag</option><option value="weekly"${selected(x.repeat,'weekly')}>Op gekozen weekdagen</option></select></label>`:''}</div><label>Voor wie?</label><div class="member-chips">${data.members.map(m=>`<label class="check-label"><input type="checkbox" name="members" value="${m.id}" ${(x.members||[member]).includes(m.id)?'checked':''}>${esc(m.name)}</label>`).join('')}</div><label style="margin-top:16px">Weekdagen ${isTask?'(bij weekherhaling)':''}</label><div class="weekdays">${weekdays.map((d,i)=>`<label><input type="checkbox" name="weekdays" value="${i}" ${(x.weekdays||[0,1,2,3,4,5,6]).includes(i)?'checked':''}>${d}</label>`).join('')}</div>`;
 if(isTask)html+=`<div class="form-grid"><label>Uitvoering<select name="mode"><option value="individual"${selected(x.mode,'individual')}>Iedereen een eigen taak</option><option value="shared"${selected(x.mode,'shared')}>Samen één taak</option></select></label>${field('Punten bij voltooien','points',x.points||0,'number','min="0" max="10000"')}</div>`;
 else html+=`<div class="form-grid">${field('Punten bij volledige routine','points',x.points||0,'number','min="0" max="10000"')}${field('Vanaf','start_time',x.start_time||'07:00','time','required')}${field('Tot','end_time',x.end_time||'09:00','time','required')}</div><section class="routine-steps"><div class="routine-steps-head"><strong>Stappen</strong><button type="button" id="add-routine-step" class="secondary">Stap toevoegen</button></div><div id="routine-step-list">${routineSteps.map(routineStep).join('')}</div></section>`;
 if(item&&(isTask||isRoutine))html+='<p class="notice">Wijzigingen gelden voor nog niet aangemaakte uitvoeringen. Bestaande uitvoeringen en historie blijven behouden.</p>';
 }
 modal(item?'Bewerken':({'members':'Een nieuw gezinslid','groceries':'Op de boodschappenlijst','tasks':'Een nieuwe taak','routines':'Een nieuwe routine','rewards':'Een nieuwe beloning'}[kind]),`<form id="edit-form">${html}<div class="form-actions">${item?`<button type="button" id="delete-entity" class="danger">${isTask||isRoutine?'Archiveren':'Verwijderen'}</button>`:''}<button type="submit" class="primary">Opslaan ${icon('check')}</button></div></form>`);
 const bindIconField=iconFieldElement=>{
   const trigger=iconFieldElement.querySelector('.task-icon-trigger'),picker=iconFieldElement.querySelector('.task-icon-picker'),search=picker.querySelector('.task-icon-search'),options=[...picker.querySelectorAll('[data-task-icon]')],noResults=picker.querySelector('.task-icon-no-results');
   trigger.onclick=()=>{
     picker.hidden=!picker.hidden;
     trigger.setAttribute('aria-expanded',String(!picker.hidden));
     if(!picker.hidden){
       const content=$('#dialog-content'),contentRect=content.getBoundingClientRect(),contentStyle=getComputedStyle(content),leftEdge=contentRect.left+parseFloat(contentStyle.paddingLeft),rightEdge=contentRect.right-parseFloat(contentStyle.paddingRight),width=Math.min(420,rightEdge-leftEdge),fieldRect=iconFieldElement.getBoundingClientRect();
       picker.style.width=`${width}px`;
       picker.style.left=`${Math.max(leftEdge,Math.min(fieldRect.left,rightEdge-width))-fieldRect.left}px`;
       search.focus();
     }
   };
   search.oninput=()=>{
     const query=normalizeIconSearch(search.value.trim());
     let visible=0;
     options.forEach(option=>{
       const matches=option.dataset.search.includes(query);
       option.hidden=!matches;
       if(matches)visible++;
     });
     picker.querySelectorAll('.task-icon-category').forEach(category=>{category.hidden=!category.querySelector('[data-task-icon]:not([hidden])')});
     noResults.hidden=visible>0;
   };
   picker.onkeydown=e=>{
     if(e.key==='Escape'){e.preventDefault();e.stopPropagation();picker.hidden=true;trigger.setAttribute('aria-expanded','false');trigger.focus()}
   };
   options.forEach(button=>button.onclick=()=>{
     iconFieldElement.querySelector('input[type="hidden"]').value=button.dataset.taskIcon;
     iconFieldElement.querySelector('.task-icon-current').textContent=button.dataset.taskIcon;
     options.forEach(option=>option.setAttribute('aria-pressed',String(option===button)));
     picker.hidden=true;
     trigger.setAttribute('aria-expanded','false');
     trigger.focus();
     dialogDirty=true;
   });
 };
 $('#dialog-content').querySelectorAll('.task-icon-field').forEach(bindIconField);
 if(isRoutine){
   const stepList=$('#routine-step-list'),addStep=$('#add-routine-step');
   const updateStepButtons=()=>{const rows=stepList.querySelectorAll('.routine-step-row');rows.forEach((row,index)=>{row.querySelector('label').firstChild.textContent=`Titel stap ${index+1}`;row.querySelector('.task-icon-label').textContent=`Pictogram stap ${index+1}`;row.querySelector('.task-icon-picker').setAttribute('aria-label',`Kies een pictogram voor pictogram stap ${index+1}`);row.querySelector('.remove-routine-step').disabled=rows.length===1;row.querySelector('.remove-routine-step').setAttribute('aria-label',`Stap ${index+1} verwijderen`)});addStep.disabled=rows.length>=30};
   addStep.onclick=()=>{const count=stepList.querySelectorAll('.routine-step-row').length;if(count>=30)return;stepList.insertAdjacentHTML('beforeend',routineStep({icon:'✓',text:''},nextRoutineStepId++));bindIconField(stepList.lastElementChild.querySelector('.task-icon-field'));updateStepButtons();stepList.lastElementChild.querySelector('[name="step_text"]').focus();dialogDirty=true};
   stepList.onclick=e=>{const button=e.target.closest('.remove-routine-step');if(!button||stepList.querySelectorAll('.routine-step-row').length===1)return;button.closest('.routine-step-row').remove();updateStepButtons();dialogDirty=true};
   updateStepButtons();
 }
 const id=item?.id||uuid(),requestId=uuid();let previousPayload='',retryId=requestId;
 bindForm(async f=>{let body=Object.fromEntries(f);if(isTask||isRoutine){body.members=f.getAll('members');body.weekdays=f.getAll('weekdays').map(Number);body.points=Number(f.get('points'));if(isRoutine)body.steps=f.getAll('step_text').map((text,index)=>({text,icon:f.getAll('step_icon')[index]||'✓'}))}if(kind==='groceries')body.done=x.done||false;if(isReward)body.price=Number(f.get('price'));const payload=JSON.stringify(body);if(previousPayload&&previousPayload!==payload)retryId=uuid();previousPayload=payload;await mutate(kind,{id,version:item?.version||0},body,'save',retryId)});
 if(item)$('#delete-entity').onclick=async()=>{if(!confirm(isTask||isRoutine?'Dit sjabloon archiveren? Bestaande uitvoeringen blijven bewaard.':'Dit item verwijderen?'))return;try{await mutate(kind,item,isTask||isRoutine?{...item,archived:true}:{},isTask||isRoutine?'save':'delete');dialogDirty=false;$('#dialog').close();await refresh(true)}catch(e){errorInForm(e)}};
}
function showTemplates(kind){modal(kind==='tasks'?'Taaksjablonen':'Routinesjablonen',`<p class="notice">Bestaande uitvoeringen blijven behouden wanneer je een sjabloon wijzigt of archiveert.</p><div class="list">${data[kind].map(x=>`<button class="secondary" data-template="${x.id}">${esc(x.icon)} ${esc(x.title)} ${x.archived?'· gearchiveerd':''}${icon('edit')}</button>`).join('')||'<p class="muted">Nog geen sjablonen.</p>'}</div>`);document.querySelectorAll('[data-template]').forEach(b=>b.onclick=()=>editEntity(kind,data[kind].find(x=>x.id===b.dataset.template)))}
async function showHistory(){try{const rows=await api('/api/history');modal('Recente wijzigingen',`<p class="notice">De laatste 100 wijzigingen. Ook ongedaan gemaakte voltooiingen blijven bewaard.</p>${rows.map(r=>{const b=JSON.parse(r.body);return `<div class="history-item">${esc(({tasks:'Taak',routines:'Routine',groceries:'Boodschap',members:'Gezinslid',runs:'Voortgang'})[r.kind])} · ${esc(b.after?.title||b.after?.name||b.before?.title||b.before?.name||(Array.isArray(b.after)?`${b.after.length} stap(pen) voltooid`:'Verwijderd'))}<small>${fmt(new Date(r.at.replace(' ','T')+'Z'),{dateStyle:'short',timeStyle:'short',timeZone:data.config.timezone})}</small></div>`}).join('')||'<p>Nog geen wijzigingen.</p>'}`)}catch(e){toast(e.message)}}
async function openAdmin(){
 try{adminCfg=await api('/api/admin/settings');renderAdmin()}catch(e){if(e.status!==401){toast(e.message);return;}modal('Beheer openen',`<p class="notice">Dagelijkse bediening is voor het hele gezin. Instellingen zijn beveiligd met het beheerwachtwoord van de server.</p><form id="edit-form">${field('Beheerwachtwoord','password','','password','required autocomplete="current-password"')}<div class="form-actions"><button class="primary" type="submit">${icon('lock')}Ontgrendelen</button></div></form>`);$('#edit-form').onsubmit=async event=>{event.preventDefault();const b=event.target.querySelector('button');b.disabled=true;try{await api('/api/login',{method:'POST',body:JSON.stringify({password:event.target.password.value})});dialogDirty=false;await openAdmin()}catch(err){errorInForm(err)}finally{b.disabled=false}};}
}
function accountMarkup(a,index){return `<div class="account" data-account="${esc(a.id)}"><div class="account-head"><h3>CalDAV-account ${index+1}</h3><button type="button" class="danger remove-account" aria-label="Account verwijderen">${icon('close')}</button></div>${field('Serveradres','caldav-url',a.url,'url','required placeholder="https://calendar.example.org/dav/"')}${field('Gebruikersnaam','caldav-user',a.username,'text','required autocomplete="off"')}${field(a.configured?'Nieuw wachtwoord (leeg = behouden)':'Wachtwoord','caldav-pass','','password','autocomplete="new-password"')}<button type="button" class="secondary discover-cal">Agenda’s ophalen</button><div class="discovery">${calendarChoices(a.calendars||[],a.calendars||[])}</div></div>`}
function calendarChoices(available,chosen){return available.map(c=>{const existing=chosen.find(x=>x.url===c.url);return `<div class="calendar-choice" data-url="${esc(c.url)}" data-name="${esc(c.name)}"><label class="check-label"><input type="checkbox" ${existing?'checked':''}>${esc(c.name)}</label><label>Gezinslid<select><option value="">Hele gezin</option>${data.members.map(m=>`<option value="${m.id}"${selected(existing?.member,m.id)}>${esc(m.name)}</option>`).join('')}</select></label></div>`}).join('')}
function rewardAdminMarkup(){
 const pending=data.reward_requests.filter(r=>r.status==='pending');
 return `<section class="settings-section"><h3>Beloningen</h3><p>Voltooide taken en volledig afgeronde routines boeken punten automatisch. Routinepunten worden één keer toegekend, niet per stap.</p><div class="list">${data.rewards.map(r=>`<div class="history-item"><strong>${esc(r.icon)} ${esc(r.title)}</strong> · ${r.price} punten<button class="secondary small" data-reward-edit="${r.id}">${icon('edit')}Bewerken</button></div>`).join('')||'<p class="muted">Nog geen beloningen ingesteld.</p>'}</div><button type="button" class="secondary" data-reward-new>${icon('plus')}Beloning toevoegen</button><h3 style="margin-top:22px">Openstaande aanvragen</h3>${pending.map(r=>`<div class="history-item"><strong>${esc(r.member_name)}</strong> vraagt ${esc(r.reward_name)} aan · ${r.cost} punten<div class="inline"><button type="button" class="primary small" data-reward-decision="approve" data-request-id="${r.id}">Goedkeuren</button><button type="button" class="secondary small" data-reward-decision="reject" data-request-id="${r.id}">Afwijzen</button></div></div>`).join('')||'<p class="muted">Geen openstaande aanvragen.</p>'}</section>`;
}
function bindRewardAdmin(){
 $('#edit-form').insertAdjacentHTML('beforebegin',rewardAdminMarkup());
 document.querySelector('[data-reward-new]').onclick=()=>{if(dialogDirty)return confirmDiscard(()=>editEntity('rewards'),'Niet-opgeslagen instellingen verlaten?');editEntity('rewards')};
 document.querySelectorAll('[data-reward-edit]').forEach(b=>b.onclick=()=>{const reward=data.rewards.find(r=>r.id===b.dataset.rewardEdit);if(dialogDirty)return confirmDiscard(()=>editEntity('rewards',reward),'Niet-opgeslagen instellingen verlaten?');editEntity('rewards',reward)});
 document.querySelectorAll('[data-reward-decision]').forEach(b=>b.onclick=()=>decideReward(b.dataset.requestId,b.dataset.rewardDecision,b));
}
async function decideReward(id,action,button){
 const key=`${id}:${action}`;
 const requestId=rewardDecisionRetries.get(key)||uuid();
 rewardDecisionRetries.set(key,requestId);
 button.disabled=true;
 try{
  await api(`/api/admin/reward-requests/${encodeURIComponent(id)}/decision`,{method:'POST',body:JSON.stringify({request_id:requestId,action})});
  rewardDecisionRetries.delete(key);
  dialogDirty=false;
  await refresh(true);
  await openAdmin();
  toast(action==='approve'?'Beloning goedgekeurd; punten afgeschreven.':'Aanvraag afgewezen; gereserveerde punten vrijgegeven.');
 }catch(error){errorInForm(error);if(error.status===409)await refresh(true);button.disabled=false}
}
async function openAlbumPicker(){
 const button=$('#discover-albums'),form=$('#edit-form'),dialog=$('#album-dialog'),content=$('#album-dialog-content');
 const chosen=new Set([...document.querySelectorAll('#albums [name=albums]:checked')].map(input=>input.value));
 button.disabled=true;
 content.innerHTML=`<div class="modal-head"><h2 id="album-picker-title">Immich-albums kiezen</h2><button type="button" id="close-album-dialog" aria-label="Sluiten">${icon('close')}</button></div><p class="album-picker-intro">Selecteer de albums die je in het dashboard wilt tonen.</p><div id="album-picker-list" class="album-picker-list"><p class="muted">Albums ophalen…</p></div><div class="form-actions"><button type="button" id="cancel-album-selection" class="secondary">Annuleren</button><button type="button" id="apply-album-selection" class="primary" disabled>Selectie toepassen</button></div><div id="album-picker-error" class="form-error hidden" role="alert"></div>`;
 dialog.showModal();
 const close=()=>dialog.close();
 $('#close-album-dialog').onclick=close;
 $('#cancel-album-selection').onclick=close;
 try{
  const albums=await api('/api/admin/discover/immich',{method:'POST',body:JSON.stringify({url:form.immich_url.value,key:form.immich_key.value})});
  if(!Array.isArray(albums))throw new Error('De albumlijst heeft een ongeldig antwoord opgeleverd.');
  $('#album-picker-list').innerHTML=albums.map(album=>`<label class="check-label"><input type="checkbox" value="${esc(album.id)}" ${chosen.has(album.id)?'checked':''}>${esc(album.name)}</label>`).join('')||'<p class="muted">Geen toegankelijke albums gevonden.</p>';
  const applyButton=$('#apply-album-selection');applyButton.disabled=false;
  applyButton.onclick=()=>{
   const selected=[...document.querySelectorAll('#album-picker-list input:checked')].map(input=>({id:input.value,name:input.parentElement.textContent.trim()}));
   $('#albums').innerHTML=selected.map(album=>`<label class="check-label"><input type="checkbox" name="albums" value="${esc(album.id)}" checked>${esc(album.name)}</label>`).join('')||'<p class="muted">Geen albums geselecteerd.</p>';
   $('#albums').dispatchEvent(new Event('input',{bubbles:true}));
   close();
  };
 }catch(error){
  $('#album-picker-error').textContent=error.message;
  $('#album-picker-error').classList.remove('hidden');
 }finally{button.disabled=false}
}
function renderAdmin(){const c=adminCfg;modal('Ons dashboard instellen',`<div class="toolbar"><span class="small muted">Beheersessie · 30 minuten</span><button id="logout" class="secondary small">${icon('lock')}Vergrendelen</button></div><div class="admin-tabs" role="tablist" aria-label="Instellingen"><button type="button" id="admin-tab-general" role="tab" aria-selected="true" aria-controls="admin-general" data-admin-tab="general">Algemeen</button><button type="button" id="admin-tab-device" role="tab" aria-selected="false" aria-controls="admin-device" tabindex="-1" data-admin-tab="device">Dit apparaat</button></div><div id="admin-general" role="tabpanel" aria-labelledby="admin-tab-general"><section class="settings-section"><h3>Ons gezin</h3><div class="family-list">${data.members.map(m=>`<button class="person" data-admin-member="${m.id}">${avatar(m)}${esc(m.name)}${icon('edit')}</button>`).join('')}</div><button id="new-member" class="secondary">${icon('plus')}Gezinslid toevoegen</button></section><form id="edit-form"><section class="settings-section"><h3>Logo en teksten</h3>${field('Titel','brand_title',c.brand_title,'text','maxlength="40" required')}${field('Subtitel','brand_subtitle',c.brand_subtitle,'text','maxlength="80"')}<div class="brand-image-controls"><div id="brand-image-preview" class="brand-image-preview">${c.brand_image?`<img src="${esc(c.brand_image)}" alt="">`:'<span>s</span><span>✳</span>'}</div><div class="brand-image-actions"><label for="brand-image-file">Gezinsfoto voor het logo</label><input id="brand-image-file" type="file" accept="image/jpeg,image/png,image/webp"><small>JPEG, PNG of WebP; wordt verkleind opgeslagen.</small><button type="button" id="remove-brand-image" class="secondary small" ${c.brand_image?'':'hidden'}>Foto verwijderen</button></div></div><input id="brand_image" name="brand_image" type="hidden" value="${esc(c.brand_image)}"></section><section class="settings-section"><h3>Algemeen</h3>${field('Tijdzone','timezone',c.timezone,'text','required')}</section><section class="settings-section"><h3>Agenda · CalDAV</h3><p>Alleen-lezen. Selecteer de agenda’s die je wilt tonen. Synchronisatie loopt elke twee minuten; inloggegevens blijven op de server.</p><div id="accounts">${c.caldav.map(accountMarkup).join('')}</div><button type="button" id="add-account" class="secondary">${icon('plus')}Account toevoegen</button></section><section class="settings-section"><h3>Home Assistant-dashboard</h3>${field('Serveradres','ha_url',c.ha_url,'url','placeholder="http://homeassistant.local:8123"')}${field('Dashboardpad','ha_dashboard',c.ha_dashboard||'/lovelace/0','text','required placeholder="/lovelace/0"')}<p>Vul het pad in van het dashboard dat je in Home Assistant hebt gemaakt, bijvoorbeeld <code>/lovelace/0</code> of <code>/dashboard-gezinsdashboard/overzicht</code>. Home Assistant verzorgt zelf de inhoud en bediening. Je browser moet toegang hebben tot dit adres en daar zo nodig zijn aangemeld.</p></section><section class="settings-section"><h3>Immich</h3>${field('Serveradres (zonder /api)','immich_url',c.immich_url,'url','placeholder="http://immich.local:2283"')}${field(c.immich_configured?'Nieuwe API-sleutel (leeg = behouden)':'API-sleutel','immich_key','','password','autocomplete="new-password"')}<button type="button" id="discover-albums" class="secondary">Albums ophalen</button><div id="albums" class="discovery">${c.albums.map(id=>`<label class="check-label"><input type="checkbox" name="albums" value="${esc(id)}" checked>Geselecteerd album ${esc(id.slice(0,8))}</label>`).join('')}</div>${field('Wisseltijd (seconden)','slide_seconds',c.slide_seconds,'number','min="5" max="300" required')}<p>Alleen geselecteerde albums zijn toegestaan. Foto’s worden uitsluitend gelezen. De servercache is begrensd.</p></section><div class="form-actions"><button type="submit" class="primary">Instellingen opslaan</button></div></form><section class="settings-section"><button id="sync-now" class="secondary">${icon('routine')}Nu synchroniseren</button><p class="notice">Sla gewijzigde instellingen eerst op.</p></section></div><div id="admin-device" role="tabpanel" aria-labelledby="admin-tab-device" hidden></div>`);
 $('#admin-device').insertAdjacentHTML('beforeend',`<section class="settings-section theme-setting"><h3>Weergave</h3><button id="theme-toggle" type="button" class="theme-toggle" role="switch" aria-checked="${darkMode}"><span class="theme-toggle-label"><strong>Donkere modus</strong><small>Alleen op dit scherm opgeslagen</small></span><span class="theme-switch-track" aria-hidden="true"><span></span></span></button></section>`);
 $('#theme-toggle').onclick=event=>{const toggle=event.currentTarget,next=!darkMode;try{localStorage.setItem('samen-theme',next?'dark':'light')}catch{toast('De thema-instelling kan niet op dit scherm worden opgeslagen.');return}darkMode=next;applyTheme();toggle.setAttribute('aria-checked',String(darkMode));toggle.classList.toggle('active',darkMode)};

 let generalDirty=false,deviceDirty=false,brandImageTask=Promise.resolve(),brandImageError=null,brandImageSelection=0;
 $('#dialog').oninput=event=>{if(event.target.closest('#admin-device'))deviceDirty=true;else generalDirty=true;dialogDirty=generalDirty||deviceDirty};
 const updateBrandImagePreview=value=>{
  const preview=$('#brand-image-preview');
  preview.innerHTML=value?`<img src="${esc(value)}" alt="">`:'<span>s</span><span>✳</span>';
 };
 $('#brand-image-file').onchange=event=>{
  const file=event.target.files[0];
  if(!file)return;
  const selection=++brandImageSelection;
  brandImageError=null;
  brandImageTask=(async()=>{
   if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size>12*1024*1024)throw new Error('Kies een JPEG-, PNG- of WebP-foto van maximaal 12 MB.');
   const bitmap=await createImageBitmap(file);
   try{
    const scale=Math.min(1,512/Math.max(bitmap.width,bitmap.height)),canvas=document.createElement('canvas');
    canvas.width=Math.max(1,Math.round(bitmap.width*scale));canvas.height=Math.max(1,Math.round(bitmap.height*scale));
    const context=canvas.getContext('2d');
    context.fillStyle='#fff';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(bitmap,0,0,canvas.width,canvas.height);
    const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.82));
    if(!blob||blob.size>400_000)throw new Error('Deze foto kan niet klein genoeg worden gemaakt. Kies een andere foto.');
    const image=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(new Error('De foto kon niet worden gelezen.'));reader.readAsDataURL(blob)});
    if(selection!==brandImageSelection)return;
    $('#brand_image').value=image;updateBrandImagePreview(image);$('#remove-brand-image').hidden=false;
    generalDirty=true;dialogDirty=true;
   }finally{bitmap.close()}
  })().catch(error=>{if(selection!==brandImageSelection)return;brandImageError=error;errorInForm(error)});
 };
 $('#remove-brand-image').onclick=()=>{
  brandImageSelection++;brandImageTask=Promise.resolve();
  $('#brand_image').value='';$('#brand-image-file').value='';updateBrandImagePreview('');
  $('#remove-brand-image').hidden=true;brandImageError=null;generalDirty=true;dialogDirty=true;
 };
 const tabs=[...document.querySelectorAll('[data-admin-tab]')];
 function selectAdminTab(button){for(const t of tabs){const active=t===button;t.setAttribute('aria-selected',String(active));t.tabIndex=active?0:-1;$('#admin-'+t.dataset.adminTab).hidden=!active}}
 tabs.forEach((button,index)=>{button.onclick=()=>selectAdminTab(button);button.onkeydown=event=>{let next;if(event.key==='ArrowRight'||event.key==='ArrowLeft')next=tabs[1-index];else if(event.key==='Home')next=tabs[0];else if(event.key==='End')next=tabs[1];if(next){event.preventDefault();selectAdminTab(next);next.focus()}}});
 $('#admin-device').insertAdjacentHTML('beforeend',`<p class="notice">Deze voorkeuren worden in deze browser opgeslagen en gelden niet voor andere apparaten.</p><form id="screen-form">${field('Na inactiviteit naar Immich (minuten, 0 = uit)','idle',screen.idle||0,'number','min="0" max="180" required')}<label class="check-label"><input type="checkbox" name="shuffle" ${screen.shuffle?'checked':''}>Willekeurige fotovolgorde</label><label class="check-label"><input type="checkbox" name="crop" ${screen.crop?'checked':''}>Foto’s beeldvullend uitsnijden</label><p class="notice">Tijdens invoer en op het tabblad Routines wisselen we nooit automatisch.</p><div class="form-actions"><button class="primary" type="submit">Opslaan op dit scherm</button></div></form>`);
 $('#screen-form').onsubmit=async event=>{event.preventDefault();try{const f=new FormData(event.target),next={idle:Number(f.get('idle')),shuffle:f.has('shuffle'),crop:f.has('crop')};localStorage.setItem('samen-screen',JSON.stringify(next));screen=next;deviceDirty=false;dialogDirty=generalDirty;if(!dialogDirty)$('#dialog').close();await refresh(true);toast('Opgeslagen op dit scherm')}catch(error){errorInForm(error)}};
 bindRewardAdmin();
 $('#logout').onclick=async()=>{await api('/api/logout',{method:'POST'});dialogDirty=false;$('#dialog').close();toast('Beheer vergrendeld')};
 $('#new-member').onclick=()=>{if(dialogDirty)return confirmDiscard(()=>editEntity('members'),'Niet-opgeslagen instellingen verlaten?');editEntity('members')};
 document.querySelectorAll('[data-admin-member]').forEach(b=>b.onclick=()=>{const memberToEdit=person(b.dataset.adminMember);if(dialogDirty)return confirmDiscard(()=>editEntity('members',memberToEdit),'Niet-opgeslagen instellingen verlaten?');editEntity('members',memberToEdit)});
 $('#add-account').onclick=()=>{$('#accounts').insertAdjacentHTML('beforeend',accountMarkup({id:uuid(),url:'',username:'',calendars:[]},document.querySelectorAll('.account').length));generalDirty=true;dialogDirty=true;bindAccounts()};bindAccounts();
 $('#discover-albums').onclick=openAlbumPicker;
 bindForm(async()=>{let selection;do{selection=brandImageSelection;await brandImageTask}while(selection!==brandImageSelection);if(brandImageError)throw brandImageError;const f=new FormData($('#edit-form')),cfg={...c,brand_title:f.get('brand_title'),brand_subtitle:f.get('brand_subtitle'),brand_image:f.get('brand_image'),timezone:f.get('timezone'),ha_url:f.get('ha_url'),ha_dashboard:f.get('ha_dashboard'),immich_url:f.get('immich_url'),immich_key:f.get('immich_key'),slide_seconds:Number(f.get('slide_seconds')),albums:f.getAll('albums'),caldav:[...document.querySelectorAll('.account')].map(readAccount)};await api('/api/admin/settings',{method:'POST',body:JSON.stringify(cfg)});api('/api/admin/sync',{method:'POST'}).then(()=>refresh()).catch(e=>toast(e.message))},()=>{generalDirty=false;return deviceDirty});
 $('#sync-now').onclick=async()=>{const b=$('#sync-now');b.disabled=true;b.textContent='Synchroniseren…';try{await api('/api/admin/sync',{method:'POST'});await refresh();const failed=Object.values(data.status).some(s=>!s.ok);toast(failed?'Synchronisatie afgerond met fouten. Bekijk de verbindingsstatus.':'Synchronisatie afgerond')}catch(e){errorInForm(e)}finally{b.disabled=false;b.textContent='Nu synchroniseren'}};
}
function readAccount(el){return {id:el.dataset.account,url:el.querySelector('[name=caldav-url]').value,username:el.querySelector('[name=caldav-user]').value,password:el.querySelector('[name=caldav-pass]').value,calendars:[...el.querySelectorAll('.calendar-choice')].filter(c=>c.querySelector('input').checked).map(c=>({url:c.dataset.url,name:c.dataset.name,member:c.querySelector('select').value}))}}
function bindAccounts(){document.querySelectorAll('.account').forEach(el=>{el.querySelector('.remove-account').onclick=()=>{if(confirm('Dit account uit de configuratie verwijderen? Sla daarna de instellingen op.')){el.dispatchEvent(new Event('input',{bubbles:true}));el.remove();dialogDirty=true}};el.querySelector('.discover-cal').onclick=async()=>{const b=el.querySelector('.discover-cal');b.disabled=true;try{const a=readAccount(el),available=await api('/api/admin/discover/caldav',{method:'POST',body:JSON.stringify(a)});el.querySelector('.discovery').innerHTML=calendarChoices(available,a.calendars)||'<p>Geen agenda’s gevonden.</p>'}catch(e){errorInForm(e)}finally{b.disabled=false}}})}
$('#admin').onclick=openAdmin;
$('#connection-retry').onclick=()=>refresh(true);
window.addEventListener('beforeunload',e=>{if(dialogDirty||$('#quick-add input')?.value){e.preventDefault();e.returnValue=''}});
for(const event of ['pointerdown','keydown','input'])document.addEventListener(event,()=>{lastActivity=Date.now()},{passive:true});
setInterval(()=>{if(screen.idle>0&&Date.now()-lastActivity>screen.idle*60000&&!hasInput()&&!(tab==='calendar'&&sub==='routines')&&data?.photos.length&&tab!=='photos'){tab='photos';render()}updateHeaderDate();if(data)updateCurrentTimeIndicator();},1000);
window.addEventListener('resize',syncAgendaColumnWidths);
function syncClockToAgendaBlock(){
 const height=$('#calendar-date').getBoundingClientRect().height;
 if(height>0){$('#analog-clock').style.width=`${height}px`;$('#analog-clock').style.height=`${height}px`}
}
new ResizeObserver(syncClockToAgendaBlock).observe($('#calendar-date'));
syncClockToAgendaBlock();
matchMedia('(max-width:760px)').addEventListener('change',event=>{if(calendarViewPreference)return;view=event.matches?'day':'week';if(data&&tab==='calendar'&&sub==='agenda')refresh(true)});
setInterval(()=>{if(!document.hidden)refresh()},1500);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh(true)});
refresh();

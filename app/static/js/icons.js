export const paths = {
  calendar: 'M4 5h16v16H4z M4 10h16 M8 3v4 M16 3v4 M8 14h2 M14 14h2 M8 18h2',
  gamepad:
    'M7.5 6h9a4 4 0 0 1 4 3.4l1 6.1a2.4 2.4 0 0 1-4.1 2l-2.2-2.2H8.8l-2.2 2.2a2.4 2.4 0 0 1-4.1-2l1-6.1A4 4 0 0 1 7.5 6z M6 10.5h4 M8 8.5v4 M15.5 10.5h.01 M18 12.5h.01',
  home: 'm3 11 9-8 9 8 M5 10v11h14V10 M9 21v-7h6v7',
  image: 'M3 4h18v16H3z m0 12 6-6 5 5 3-3 4 4 M15 8h.01',
  settings:
    'M9 2h6l.6 2.3a7.5 7.5 0 0 1 1.6.9l2.2-1.1 3 5.2-2 1.3a7.5 7.5 0 0 1 0 1.8l2 1.3-3 5.2-2.2-1.1a7.5 7.5 0 0 1-1.6.9L15 21h-6l-.6-2.3a7.5 7.5 0 0 1-1.6-.9l-2.2 1.1-3-5.2 2-1.3a7.5 7.5 0 0 1 0-1.8l-2-1.3 3-5.2 2.2 1.1a7.5 7.5 0 0 1 1.6-.9L9 2z M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  check: 'm5 12 4 4L19 6',
  tasks: 'M9 6h12 M9 12h12 M9 18h12 M3 6h1 M3 12h1 M3 18h1',
  routine: 'M20 7a9 9 0 0 0-15-2L2 8 M2 3v5h5 M4 17a9 9 0 0 0 15 2l3-3 M22 21v-5h-5',
  basket: 'm3 8 2 13h14l2-13H3 M8 8l4-6 4 6 M9 12v5 M15 12v5',
  gift: 'M20 12v10H4V12 M2 7h20v5H2z M12 7v15 M12 7H7.5a2.5 2.5 0 1 1 2.5-2.5V7 M12 7h4.5a2.5 2.5 0 1 0-2.5-2.5V7',
  left: 'm14 5-7 7 7 7',
  right: 'm10 5 7 7-7 7',
  plus: 'M12 4v16 M4 12h16',
  close: 'm6 6 12 12 M6 18 18 6',
  edit: 'm4 16 12-12 4 4L8 20H4z M14 6l4 4',
  people:
    'M8 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M2 21v-2a6 6 0 0 1 12 0v2 M16 4a4 4 0 0 1 0 8 M17 15a5 5 0 0 1 5 5',
  volume: 'M11 5 6 9H3v6h3l5 4V5 M15 8a6 6 0 0 1 0 8 M18 5a10 10 0 0 1 0 14',
  muted: 'M11 5 6 9H3v6h3l5 4V5 M16 9l6 6 M22 9l-6 6',
  pause: 'M8 5v14 M16 5v14',
  play: 'm8 4 12 8-12 8z',
  lock: 'M5 10h14v11H5z M8 10V6a4 4 0 0 1 8 0v4',
  leaf: 'M19 3C6 3 2 8 5 15s16 5 14-12 M5 20 15 9',
  history: 'M3 10a9 9 0 1 1 2 8 M3 4v6h6 M12 7v6l4 2',
  sun: 'M12 3v2 M12 19v2 M3 12h2 M19 12h2 M5.6 5.6 7 7 M17 17l1.4 1.4 M18.4 5.6 17 7 M7 17l-1.4 1.4 M16 12a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
  moon: 'M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5z'
};
export const icon = (name) =>
  `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[name] || paths.calendar}"/></svg>`;
export const taskIcons = [
  ['✓', 'Standaard'],
  ['☀️', 'Zon'],
  ['🎁', 'Cadeau'],
  ['🧹', 'Vegen'],
  ['🧽', 'Schoonmaken'],
  ['🧼', 'Zeep'],
  ['🫧', 'Sop'],
  ['🪣', 'Emmer'],
  ['🧺', 'Wasmand'],
  ['👕', 'Kleding'],
  ['👖', 'Broek'],
  ['🧦', 'Sokken'],
  ['🧥', 'Jas'],
  ['🛏️', 'Bed'],
  ['🛌', 'Slapen'],
  ['🪟', 'Ramen'],
  ['🪞', 'Spiegel'],
  ['🚪', 'Deur'],
  ['🍽️', 'Servies'],
  ['🍴', 'Bestek'],
  ['🥄', 'Lepel'],
  ['🥣', 'Kom'],
  ['🍳', 'Koken'],
  ['🥘', 'Maaltijd'],
  ['🧂', 'Kruiden'],
  ['🧊', 'IJs'],
  ['🥤', 'Drinken'],
  ['🫖', 'Thee'],
  ['☕', 'Koffie'],
  ['🗑️', 'Afval'],
  ['♻️', 'Recyclen'],
  ['📦', 'Pakket'],
  ['🛒', 'Boodschappen'],
  ['🥕', 'Groente'],
  ['🍎', 'Fruit'],
  ['🥛', 'Melk'],
  ['🍞', 'Brood'],
  ['🥫', 'Voorraad'],
  ['🪴', 'Plant'],
  ['🌱', 'Tuinieren'],
  ['🌷', 'Bloemen'],
  ['🍂', 'Bladeren'],
  ['🐕', 'Hond'],
  ['🐈', 'Kat'],
  ['🐾', 'Pootafdrukken'],
  ['🐟', 'Vis'],
  ['🦜', 'Vogel'],
  ['🦴', 'Hondenbot'],
  ['🚿', 'Douche'],
  ['🛁', 'Bad'],
  ['🚽', 'Toilet'],
  ['🪥', 'Tandenpoetsen'],
  ['🦷', 'Tand'],
  ['🧻', 'Toiletpapier'],
  ['🧴', 'Verzorging'],
  ['🎒', 'Tas'],
  ['📚', 'Boeken'],
  ['✏️', 'Schrijven'],
  ['🧸', 'Speelgoed'],
  ['🧩', 'Puzzel'],
  ['🎨', 'Knutselen'],
  ['⚽', 'Sport'],
  ['👟', 'Schoenen'],
  ['🧢', 'Pet'],
  ['🧰', 'Gereedschap'],
  ['🔧', 'Repareren'],
  ['🔨', 'Klus'],
  ['🪛', 'Schroevendraaier'],
  ['🪜', 'Ladder'],
  ['🔋', 'Batterij'],
  ['💡', 'Lamp'],
  ['🔑', 'Sleutel'],
  ['📬', 'Post ophalen'],
  ['📮', 'Brief posten'],
  ['🧾', 'Bon'],
  ['📅', 'Plannen'],
  ['🌤️', 'Buiten'],
  ['🌧️', 'Regen'],
  ['🚗', 'Auto'],
  ['🚲', 'Fiets'],
  ['🪑', 'Stoel'],
  ['🛋️', 'Bank'],
  ['🖼️', 'Schilderij'],
  ['😊', 'Blij'],
  ['😄', 'Lach'],
  ['😎', 'Cool'],
  ['🤩', 'Super'],
  ['🥳', 'Feest vieren'],
  ['😴', 'Moe'],
  ['💪', 'Sterk'],
  ['🙌', 'Goed gedaan'],
  ['❤️', 'Hart'],
  ['⭐', 'Ster'],
  ['🌈', 'Regenboog'],
  ['🦄', 'Eenhoorn'],
  ['🦖', 'Dinosaurus'],
  ['🐸', 'Kikker'],
  ['🐼', 'Panda'],
  ['🐢', 'Schildpad'],
  ['🐬', 'Dolfijn'],
  ['🐝', 'Bij'],
  ['🍕', 'Pizza'],
  ['🍦', 'IJsje'],
  ['🍪', 'Koekje'],
  ['🧁', 'Cupcake'],
  ['🍉', 'Watermeloen'],
  ['🎮', 'Gamen'],
  ['🎲', 'Spelletje'],
  ['🎵', 'Muziek'],
  ['🎸', 'Gitaar'],
  ['🏀', 'Basketbal'],
  ['🏊', 'Zwemmen'],
  ['🛴', 'Step'],
  ['🏆', 'Trofee'],
  ['🎉', 'Hoera'],
  ['🪠', 'Ontstoppen'],
  ['🧯', 'Brandveiligheid'],
  ['🧤', 'Handschoenen'],
  ['🧣', 'Sjaal'],
  ['🧵', 'Naaien'],
  ['🪡', 'Naald en draad'],
  ['📝', 'Notitie maken'],
  ['🧠', 'Leren'],
  ['🧑‍🍳', 'Koken'],
  ['👶', 'Baby verzorgen'],
  ['🍼', 'Fles klaarmaken'],
  ['🏠', 'Opruimen'],
  ['🚰', 'Water drinken'],
  ['🚶', 'Wandelen'],
  ['🧘', 'Rekken'],
  ['💊', 'Medicijnen'],
  ['🩹', 'Pleister'],
  ['🎹', 'Piano spelen'],
  ['🎤', 'Zingen'],
  ['🛝', 'Naar de speeltuin']
];
export const extraTaskIcons = [
  ['🧳', 'Koffer', 'Klusjes en reizen', ['bagage', 'vakantie', 'op reis']],
  ['🪙', 'Munt', 'Klusjes en reizen', ['geld', 'muntstuk', 'sparen']],
  ['🛍️', 'Winkeltassen', 'Klusjes en reizen', ['boodschappen', 'shoppen', 'winkel']],
  ['🕯️', 'Kaars', 'Huis en schoonmaken', ['licht', 'kaars aansteken']],
  ['🛠️', 'Gereedschap', 'Klusjes en reizen', ['gereedschap', 'repareren', 'onderhoud']],
  ['🔒', 'Slot', 'Huis en schoonmaken', ['deur op slot', 'afsluiten', 'veiligheid']],
  ['📖', 'Lezen', 'School en creativiteit', ['boek', 'studeren', 'lezen']],
  ['✂️', 'Knippen', 'School en creativiteit', ['schaar', 'knutselen', 'knippen']],
  ['🧶', 'Breien', 'School en creativiteit', ['wol', 'haken', 'breien']],
  ['🧲', 'Magneet', 'School en creativiteit', ['magneet', 'proefje']],
  ['🔍', 'Zoeken', 'School en creativiteit', ['vergrootglas', 'zoeken', 'speuren']],
  ['🪄', 'Toveren', 'Spel en plezier', ['magie', 'tovenaar', 'fantasie']],
  ['🌍', 'Aarde', 'Natuur en dieren', ['wereld', 'planeet', 'milieu']],
  ['🌲', 'Boom', 'Natuur en dieren', ['bos', 'boom', 'natuur']],
  ['🌻', 'Zonnebloem', 'Natuur en dieren', ['bloem', 'tuin', 'zonnebloem']],
  ['🍄', 'Paddenstoel', 'Natuur en dieren', ['bos', 'paddenstoel']],
  ['🦋', 'Vlinder', 'Natuur en dieren', ['insect', 'vlinder', 'natuur']],
  ['🐇', 'Konijn', 'Natuur en dieren', ['huisdier', 'konijn']],
  ['🐹', 'Hamster', 'Natuur en dieren', ['huisdier', 'hamster']],
  ['🐦', 'Vogel', 'Natuur en dieren', ['vogels voeren', 'vogel']],
  ['🐠', 'Tropische vis', 'Natuur en dieren', ['aquarium', 'vis voeren', 'vis']],
  ['🐞', 'Lieveheersbeestje', 'Natuur en dieren', ['insect', 'lieveheersbeestje']],
  ['🦔', 'Egel', 'Natuur en dieren', ['egel', 'dier']],
  ['🦎', 'Hagedis', 'Natuur en dieren', ['reptiel', 'hagedis']],
  ['🦆', 'Eend', 'Natuur en dieren', ['eend', 'dieren']],
  ['🦁', 'Leeuw', 'Natuur en dieren', ['dierentuin', 'leeuw']],
  ['🐘', 'Olifant', 'Natuur en dieren', ['dierentuin', 'olifant']],
  ['🤗', 'Knuffel', 'Smileys en beloningen', ['knuffelen', 'lief', 'blij']],
  ['😃', 'Glimlach', 'Smileys en beloningen', ['glimlachen', 'blij', 'smiley']],
  ['😇', 'Engel', 'Smileys en beloningen', ['lief', 'onschuldig', 'smiley']],
  ['🫶', 'Hartjeshanden', 'Smileys en beloningen', ['liefde', 'handenhart', 'dankbaar']],
  ['👋', 'Zwaaien', 'Smileys en beloningen', ['hallo', 'dag zeggen', 'zwaaien']],
  ['🙏', 'Bedanken', 'Smileys en beloningen', ['dankjewel', 'bidden', 'bedankt']],
  ['🧍', 'Aankleden', 'Verzorging en gezondheid', ['staan', 'klaarmaken', 'aankleden']],
  ['🧡', 'Oranje hart', 'Smileys en beloningen', ['hart', 'liefde', 'oranje']],
  ['🥗', 'Salade', 'Eten en drinken', ['groente', 'gezond eten', 'salade']],
  ['🍌', 'Banaan', 'Eten en drinken', ['fruit', 'banaan']],
  ['🍓', 'Aardbei', 'Eten en drinken', ['fruit', 'aardbei']],
  ['🥚', 'Ei', 'Eten en drinken', ['ontbijt', 'ei']],
  ['🧀', 'Kaas', 'Eten en drinken', ['eten', 'kaas']],
  ['🥪', 'Boterham', 'Eten en drinken', ['lunch', 'broodje', 'sandwich']],
  ['🥞', 'Pannenkoeken', 'Eten en drinken', ['ontbijt', 'pannenkoek']],
  ['🧃', 'Sap', 'Eten en drinken', ['drinken', 'sapje', 'pakje drinken']],
  ['🍿', 'Popcorn', 'Eten en drinken', ['film', 'snack', 'popcorn']],
  ['🍰', 'Taart', 'Eten en drinken', ['bakken', 'gebak', 'verjaardag']],
  ['🎭', 'Toneel', 'School en creativiteit', ['theater', 'toneelspelen', 'verkleden']],
  ['📺', 'Televisie', 'School en creativiteit', ['tv', 'televisie kijken', 'programma kijken']],
  ['📻', 'Radio', 'School en creativiteit', ['radio luisteren', 'luisteren naar de radio']],
  [
    '🎧',
    'Muziek luisteren',
    'School en creativiteit',
    ['muziek', 'koptelefoon', 'hoofdtelefoon', 'luisteren']
  ],
  ['🪇', 'Muziek maken', 'School en creativiteit', ['muziek', 'instrument', 'maracas']],
  ['🎻', 'Viool', 'School en creativiteit', ['muziek', 'instrument', 'viool spelen']],
  ['🏸', 'Badminton', 'Sport en buiten', ['sport', 'racket', 'badminton']],
  ['🏓', 'Tafeltennis', 'Sport en buiten', ['pingpong', 'sport', 'tafeltennis']]
];
taskIcons.push(...extraTaskIcons.map(([emoji, label]) => [emoji, label]));
export const extraTaskIconMetadata = new Map(
  extraTaskIcons.map(([emoji, , category, aliases]) => [
    emoji,
    {
      category,
      aliases
    }
  ])
);
export const taskIconAliases = {
  '🧹': ['stofzuigen', 'schoonmaken', 'vegen'],
  '👕': ['was doen', 'wassen', 'wasgoed'],
  '🛒': ['supermarkt', 'winkel', 'inkopen'],
  '🗑️': ['vuilnis', 'prullenbak', 'weggooien'],
  '🍽️': ['afwassen', 'tafel dekken', 'eten'],
  '🪥': ['tanden', 'poetsen', 'mondverzorging'],
  '🎒': ['rugzak', 'schooltas', 'tas inpakken'],
  '📚': ['lezen', 'boek', 'studeren'],
  '🧸': ['knuffel', 'opruimen', 'speelgoed'],
  '🚿': ['wassen', 'douchen', 'douche nemen'],
  '🛏️': ['bed opmaken', 'opstaan', 'slaapkamer'],
  '🐕': ['hond uitlaten', 'uitlaten', 'wandelen'],
  '🐈': ['kattenbak', 'kat verzorgen', 'voer geven'],
  '🐾': ['huisdier', 'dieren verzorgen'],
  '🧾': ['boodschappenbon', 'rekening'],
  '📅': ['agenda', 'afspraak', 'kalender'],
  '🚲': ['fietsen', 'fiets pakken'],
  '🚗': ['autorijden', 'auto wassen'],
  '💊': ['medicijn', 'medicatie', 'innemen'],
  '🧘': ['yoga', 'ontspannen', 'stretching'],
  '🪴': ['plant water geven', 'plant verzorgen'],
  '🧺': ['was verzamelen', 'was sorteren'],
  '🧽': ['afwas', 'spons', 'schoonmaken'],
  '🧴': ['shampoo', 'zeep', 'verzorging']
};
export const taskIconCategories = [
  'Start',
  'Huis en schoonmaken',
  'Eten en drinken',
  'Natuur en dieren',
  'Verzorging en gezondheid',
  'School en creativiteit',
  'Sport en buiten',
  'Klusjes en reizen',
  'Smileys en beloningen',
  'Spel en plezier',
  'Overig'
];
export const taskIconCategoryRules = [
  ['Start', /^Standaard$/],
  [
    'Eten en drinken',
    /Koken|Maaltijd|Kruiden|IJs|Drinken|Thee|Koffie|Servies|Bestek|Lepel|Kom|Groente|Fruit|Melk|Brood|Voorraad|Pizza|Koekje|Cupcake|Watermeloen|IJsje/
  ],
  [
    'Natuur en dieren',
    /Zon|Plant|Tuinieren|Bloemen|Bladeren|Hond|Kat|Pootafdrukken|Vis|Vogel|Hondenbot|Eenhoorn|Dinosaurus|Kikker|Panda|Schildpad|Dolfijn|Bij/
  ],
  [
    'Verzorging en gezondheid',
    /Douche|Bad|Toilet|Tandenpoetsen|Tand|Toiletpapier|Verzorging|Baby verzorgen|Fles klaarmaken|Water drinken|Rekken|Medicijnen|Pleister|Moe|Slapen/
  ],
  [
    'School en creativiteit',
    /Boeken|Schrijven|Knutselen|Leren|Plannen|Bon|Muziek|Gitaar|Piano spelen|Zingen/
  ],
  ['Sport en buiten', /Sport|Schoenen|Buiten|Wandelen|Zwemmen|Basketbal|Step|Speeltuin|Hoera/],
  [
    'Klusjes en reizen',
    /Gereedschap|Repareren|Klus|Schroevendraaier|Ladder|Batterij|Lamp|Sleutel|Post ophalen|Brief posten|Auto|Fiets|Pakket|Reizen|Munt|Winkelen/
  ],
  [
    'Smileys en beloningen',
    /Cadeau|Blij|Lach|Cool|Super|Feest vieren|Sterk|Goed gedaan|Hart|Ster|Regenboog|Oranje hart|Glimlach|Knuffel|Engel|Hartjeshanden|Zwaaien|Bedanken|Trofee/
  ],
  ['Spel en plezier', /Speelgoed|Puzzel|Eenhoorn|Dinosaurus|Gamen|Spelletje|Feest/],
  [
    'Huis en schoonmaken',
    /Vegen|Schoonmaken|Zeep|Sop|Emmer|Wasmand|Kleding|Broek|Sokken|Jas|Bed|Ramen|Spiegel|Deur|Afval|Recyclen|Boodschappen|Schoenen|Pet|Bank|Stoel|Schilderij|Opruimen|Winkelen/
  ]
];
export const taskIconMetadata = (emoji, label) => {
  const extra = extraTaskIconMetadata.get(emoji);
  const category =
    extra?.category ||
    taskIconCategoryRules.find(([, pattern]) => pattern.test(label))?.[0] ||
    'Overig';
  return {
    category,
    search: normalizeIconSearch(
      [emoji, label, category, ...(taskIconAliases[emoji] || []), ...(extra?.aliases || [])].join(
        ' '
      )
    )
  };
};
export const normalizeIconSearch = (value) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLocaleLowerCase();

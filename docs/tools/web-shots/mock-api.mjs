// Minimal stand-in for the Shvatka REST API, just enough to render the web UI
// for documentation screenshots. Fixtures mirror the bot preview data:
// team Пони, players bomzheg / rainbow_dash, game "Схватка это чудо".
import http from 'node:http';

// Fixture timestamps are relative to "now" so the running-game counters read
// naturally whenever the screenshots are re-taken.
const iso = minutesAgo => new Date(Date.now() - minutesAgo * 60000).toISOString().slice(0, 19);
const GAME_START = iso(63);
const LEVEL1_START = iso(63);
const LEVEL2_START = iso(17);
const MODE = process.env.MODE ?? 'started';

const me = {
  id: 1, username: 'bomzheg', name_mention: 'bomzheg', can_be_author: true,
  tg: {tg_id: 1, username: 'bomzheg', first_name: 'Юрий', last_name: null},
  forum: null, email: {email: 'bomzheg@example.com', is_verified: true}, is_admin: false,
};
const captain = {id: 1, can_be_author: true, name_mention: 'bomzheg'};
const rd = {id: 2, can_be_author: false, name_mention: 'rainbow_dash'};
const flutter = {id: 3, can_be_author: false, name_mention: 'fluttershy'};
const team = {id: 1, name: 'Пони', description: 'Дружба - это чудо', captain};
const team2 = {id: 2, name: 'Дискорд', description: 'Хаос', captain: rd};

const perms = (all = false) => ({
  can_manage_waivers: all, can_manage_players: all, can_change_team_name: all,
  can_add_players: all, can_remove_players: all,
});
const members = [
  {team_player_id: 1, id: 1, username: 'bomzheg', can_be_author: true, emoji: '👑',
   role: 'мозг', permissions: perms(true), date_joined: '2023-05-19T21:00:00', played_games_count: 12},
  {team_player_id: 2, id: 2, username: 'rainbow_dash', can_be_author: false, emoji: '✈️',
   role: 'пилот', permissions: {...perms(), can_manage_waivers: true, can_add_players: true},
   date_joined: '2023-05-19T21:00:00', played_games_count: 7},
  {team_player_id: 3, id: 3, username: 'fluttershy', can_be_author: false, emoji: '🦋',
   role: 'полевой', permissions: perms(), date_joined: '2024-01-11T18:30:00', played_games_count: 3},
];

const text = t => ({type: 'text', text: t});
const hint = (time, ...parts) => ({time, hint: parts});
const winKey = (...keys) => ({type: 'WIN_KEY', keys});
const effectsKey = (keys, effects) => ({type: 'EFFECTS_KEY', keys, effects});
const effectsTimer = (action_time, effects) => ({type: 'EFFECTS_TIMER', action_time, effects});

const levels = [
  {
    db_id: 1, name_id: 'pinky_pie', author: captain, game_id: 1, number_in_game: 0,
    scenario: {
      id: 'pinky_pie',
      time_hints: [
        hint(0, text('В этот момент Пинки почувствовала, что готова заниматься праздниками всю жизнь и через секунду получила свой знак отличия')),
        hint(10, text('Позже она открыла заведение, на лого которого разместила свой знак отличия')),
        hint(20, text('Город Праздников')),
      ],
      conditions: [
        winKey('СХПИНКИ'),
        effectsKey(['СХБОНУС'], [{id: 'e1', hints_: [], bonus_minutes: 10, level_up: false, next_level: null}]),
        effectsTimer(30, [{id: 'e2', hints_: [text('Пинки может и уехать, если не поспешить')], bonus_minutes: -5, level_up: false, next_level: null}]),
      ],
    },
  },
  {
    db_id: 2, name_id: 'fluttershy', author: captain, game_id: 1, number_in_game: 1,
    scenario: {
      id: 'fluttershy',
      time_hints: [
        hint(0, text('Флаттершай была полной противоположностью Пинки и её дом был таким же')),
        hint(15, text('Какой-то шутник повесил на её доме надпись "Трактир"')),
      ],
      conditions: [winKey('СХФЛАТТЕР'), effectsTimer(40, [{id: 'e3', hints_: [], bonus_minutes: 0, level_up: true, next_level: null}])],
    },
  },
  {
    db_id: 3, name_id: 'rainbow', author: captain, game_id: 1, number_in_game: 2,
    scenario: {
      id: 'rainbow',
      time_hints: [hint(0, text('Радуга Деш произвела звуковую радугу - эффект который считался мифическим'))],
      conditions: [winKey('СХРАДУГА')],
    },
  },
];

const game = {
  id: 1, author: captain, name: 'Схватка это чудо', status: 'getting_waivers',
  start_at: GAME_START, number: null, levels,
};
const myGames = [
  {id: 1, author: captain, name: 'Схватка это чудо', status: 'getting_waivers', start_at: GAME_START, number: null},
  {id: 2, author: captain, name: 'Ночь длинных ключей', status: 'underconstruction', start_at: null, number: null},
  {id: 3, author: captain, name: 'Схватка №41', status: 'complete', start_at: '2025-11-02T22:00:00', number: 41},
];

const levelTime = (id, team_, level_number, name_id, start_at, is_finished = false) =>
  ({id, game: {id: 1, name: 'Схватка это чудо', status: 'started'}, team: team_, level_number, name_id, start_at, is_finished});

const routes = {
  'GET /users/me': me,
  'GET /version': {version: '1.0.0'},
  'GET /push/config': {vapid_public_key: null, enabled: false},


  'GET /users/1/details': {
    id: 1, username: 'bomzheg', can_be_author: true,
    tg: {tg_id: 1, username: 'bomzheg', first_name: 'Юрий', last_name: null},
    player_in_team: {id: 1, team: {id: 1, name: 'Пони', description: 'Дружба - это чудо', captain},
                     date_joined: '2023-05-19T21:00:00', role: 'мозг', emoji: '👑'},
  },
  'GET /users/1/stat': {
    id: 1, username: 'bomzheg', can_be_author: true,
    typed_keys_count: 412, typed_correct_keys_count: 268,
    team_history: [{team_player_id: 1, team: {id: 1, name: 'Пони', description: null, captain},
                    date_joined: '2023-05-19T21:00:00', date_left: null, role: 'мозг', emoji: '👑'}],
    played_games: [{id: 3, author: captain, name: 'Схватка №41', status: 'complete',
                    start_at: '2025-11-02T22:00:00', number: 41}],
  },
  'GET /users': {items: [rd, flutter]},

  'GET /teams/my': team,
  'GET /teams': {items: [{...team, played_games_count: 12}, {...team2, played_games_count: 5}]},
  'GET /teams/1': {...team, played_games_count: 12},
  'GET /teams/1/players': {items: members},
  'GET /teams/1/stat': {items: [
    {id: 3, author: captain, name: 'Схватка №41', status: 'complete', start_at: '2025-11-02T22:00:00', number: 41},
  ]},

  'GET /games/my': {items: myGames, total: myGames.length},
  'GET /games/my/1': game,
  'GET /games/1': game,
  'GET /games/active': {id: 1, author: captain, name: 'Схватка это чудо', status: MODE === 'waivers' ? 'getting_waivers' : 'started', start_at: GAME_START, number: null},
  'GET /games/1/organizers': {content: [
    {org_id: null, player: captain, can_spy: true, can_see_log_keys: true, can_validate_waivers: true, view_scenario: true, deleted: false},
    {org_id: 1, player: rd, can_spy: true, can_see_log_keys: true, can_validate_waivers: false, view_scenario: true, deleted: false},
    {org_id: 2, player: flutter, can_spy: false, can_see_log_keys: false, can_validate_waivers: false, view_scenario: false, deleted: false},
  ], total: 3},

  'GET /games/active/me': {
    waiver_vote: 'yes', team: {id: 1, name: 'Пони', captain, description: 'Дружба - это чудо'},
    org: {player: captain, can_spy: true, can_see_log_keys: true, can_validate_waivers: true, view_scenario: true, deleted: false},
  },
  'GET /games/running/level/current': {
    level_number: 1, level_time_id: 2, started_at: LEVEL2_START, game_id: 1, is_finished: false,
    hints: [
      hint(0, text('Флаттершай была полной противоположностью Пинки и её дом был таким же')),
      hint(15, text('Какой-то шутник повесил на её доме надпись "Трактир"')),
    ],
    typed_keys: [
      {text: 'СХПИНКИ', type_: 'simple', is_duplicate: false, at: LEVEL2_START, level_number: 0, player: rd, team},
      {text: 'СХБОНУС', type_: 'effects', is_duplicate: false, at: iso(20), level_number: 0, player: captain, team,
       effects: [{id: 'e1', hints_: [], bonus_minutes: 10, level_up: false, next_level: null}]},
      {text: 'СХНЕВЕРНЫЙ', type_: 'wrong', is_duplicate: false, at: iso(25), level_number: 0, player: flutter, team},
    ],
    events: [
      {id: 1, level_time_id: 1, at: iso(20), is_timer: false, key: 'СХБОНУС',
       effects: [{id: 'e1', hints_: [], bonus_minutes: 10, level_up: false, next_level: null}]},
    ],
  },
  'GET /waivers/game/current': {
    teams: [{id: 1, name: 'Пони'}, {id: 2, name: 'Дискорд'}],
    waivers: {'1': [{player: captain}, {player: rd}, {player: flutter}], '2': [{player: rd}]},
  },
  'GET /waivers/game/1': {
    teams: [team, team2],
    waivers: {'1': [{player: captain}, {player: rd}, {player: flutter}], '2': [{player: rd}]},
  },

  'GET /games/1/keys': {
    '1': [
      {text: 'СХПИНКИ', type_: 'simple', is_duplicate: false, at: LEVEL2_START, level_number: 0, player: rd, team},
      {text: 'СХБОНУС', type_: 'effects', is_duplicate: false, at: iso(20), level_number: 0, player: captain, team},
      {text: 'СХНЕВЕРНЫЙ', type_: 'wrong', is_duplicate: false, at: iso(25), level_number: 0, player: flutter, team},
    ],
    '2': [
      {text: 'СХПИНКИ', type_: 'simple', is_duplicate: false, at: iso(32), level_number: 0, player: rd, team: team2},
      {text: 'СХФЛАТТЕР', type_: 'simple', is_duplicate: false, at: iso(6), level_number: 1, player: rd, team: team2},
    ],
  },
  'GET /games/1/stat': {
    level_times: {
      '1': [levelTime(1, team, 0, 'pinky_pie', LEVEL1_START), levelTime(2, team, 1, 'fluttershy', LEVEL2_START)],
      '2': [levelTime(3, team2, 0, 'pinky_pie', LEVEL1_START), levelTime(4, team2, 1, 'fluttershy', iso(32)),
            levelTime(5, team2, 2, 'rainbow', iso(6), true)],
    },
    bonuses: {
      '1': [{at: iso(20), source: 'key', key: 'СХБОНУС', level_time_id: 1, level_number: 0,
             effects: {id: 'e1', hints_: [], bonus_minutes: 10, level_up: false, next_level: null}}],
    },
  },

  'GET /notifications/unread-count': {count: 2},
  'GET /notifications': {
    items: [
      {id: 1, type: 'team_join_invite', severity: 'important', read: false, created_at: iso(90),
       actor_id: 1, request_id: 1,
       payload: {inviter_id: 1, inviter_name: 'bomzheg', player_id: 4, player_name: 'twilight',
                 team_id: 1, team_name: 'Пони'}},
      {id: 2, type: 'player_joined_team', severity: 'normal', read: false, created_at: iso(70),
       actor_id: 2, request_id: null,
       payload: {player_id: 3, player_name: 'fluttershy', team_id: 1, team_name: 'Пони'}},
      {id: 3, type: 'game_schedule_changed', severity: 'normal', read: true, created_at: iso(65),
       actor_id: 1, request_id: null,
       payload: {game_id: 1, game_name: 'Схватка это чудо', start_at: GAME_START}},
    ],
    limit: 20, offset: 0, unread_only: false,
  },
  'GET /requests': url => {
    const incoming = [
      {id: 1, type: 'team_join_request', status: 'pending', initiator_id: 4, target_player_id: 1,
       team_id: 1, game_id: null, created_at: iso(120), responded_at: null,
       payload: {player_id: 4, player_name: 'twilight', team_id: 1, team_name: 'Пони'}},
    ];
    const outgoing = [
      {id: 2, type: 'org_invite', status: 'pending', initiator_id: 1, target_player_id: 2,
       team_id: null, game_id: 1, created_at: iso(140), responded_at: null,
       payload: {player_id: 2, player_name: 'rainbow_dash', game_id: 1, game_name: 'Схватка это чудо'}},
    ];
    return {items: url.searchParams.get('direction') === 'outgoing' ? outgoing : incoming};
  },
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const key = `${req.method} ${url.pathname}`;
  let body = routes[key] ?? routes[`${req.method} ${url.pathname.replace(/\/$/, '')}`];
  if (typeof body === 'function') body = body(url);
  res.setHeader('access-control-allow-origin', req.headers.origin ?? '*');
  res.setHeader('access-control-allow-credentials', 'true');
  if (req.method === 'OPTIONS') return res.writeHead(204).end();
  if (body === undefined) {
    console.log('MISS', key + url.search);
    return res.writeHead(404, {'content-type': 'application/json'}).end('{"detail":"not found"}');
  }
  console.log('HIT ', key + url.search);
  res.writeHead(200, {'content-type': 'application/json'}).end(JSON.stringify(body));
});
server.listen(8099, () => console.log('mock api on 8099'));

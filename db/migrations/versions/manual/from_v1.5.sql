INSERT INTO public.chats (tg_id, title, username)
SELECT oc.chat_id, oc.title, oc.username FROM old.chats oc;

UPDATE public.chats SET type='supergroup';
-- manual set other types to chats

INSERT INTO public.users (tg_id, first_name, last_name, username, is_bot)
SELECT oc.user_id, oc.first_name, oc.last_name, oc.username, false FROM old.users oc;

INSERT INTO public.players (user_id, can_be_author, promoted_by_id)
SELECT u.id, ou.can_be_author, null -- manual change it to correct player_id
FROM public.users u
         JOIN old.users ou
              ON u.tg_id = ou.user_id;

INSERT INTO public.teams (name, chat_id, captain_id, description)
SELECT ot.team_name, c.id, p.id, ot.description
FROM old.teams ot
         JOIN public.chats c ON c.tg_id = ot.chat_id
         JOIN users u ON u.tg_id = ot.captain_id
         JOIN players p ON u.id = p.user_id;

INSERT INTO public.team_players (player_id, team_id, date_joined, role, emoji, date_left, can_manage_waivers, can_manage_players, can_change_team_name, can_add_players, can_remove_players)
SELECT p.id, t.id, otp.date_joined, otp.role, otp.emoji, otp.date_left, otp.can_manage_waivers, otp.can_manage_players, otp.can_change_team_name, otp.can_add_players, otp.can_remove_players
FROM old.users_in_teams otp
         JOIN public.users u ON u.tg_id = otp.user_id
         JOIN public.players p ON p.user_id = u.id
         JOIN old.teams ot ON ot.team_id = otp.team_id
         JOIN public.chats c ON c.tg_id = ot.chat_id
         JOIN public.teams t ON t.chat_id = c.id;

INSERT INTO public.files_info (file_path, guid, original_filename, extension, file_id, content_type, author_id)
SELECT ofi.file_path, ofi.guid_, ofi.original_filename, ofi.extension, ofi.file_id, ofi.content_type, 162
FROM old.files_info ofi;

INSERT INTO public.games (author_id, name, start_at, published_channel_id, manage_token)
SELECT p.id, og.name, og.start_datetime, og.published_channel_id, og.manage_token
FROM old.games og
         JOIN public.users u ON u.tg_id = og.author_id
         JOIN public.players p ON p.user_id = u.id
ORDER BY og.game_id;

INSERT INTO public.levels (name_id, game_id, author_id, number_in_game, scenario)
SELECT ol.name_id, g.id, p.id, ol.number_in_game, ol.scenario::json
FROM old.levels ol
         JOIN public.users u ON u.tg_id = ol.author_id
         JOIN public.players p ON p.user_id = u.id
         JOIN old.games og ON og.game_id = ol.game_id
         JOIN public.games g ON g.name = og.name;

INSERT INTO public.levels_times (game_id, team_id, level_number, start_at)
SELECT g.id, t.id, olt.level_number, olt.start_at
FROM old.level_times olt
         JOIN old.games og ON og.game_id = olt.game_id
         JOIN public.games g ON g.name = og.name
         JOIN old.teams ot ON ot.team_id = olt.team_id
         JOIN public.chats c ON c.tg_id = ot.chat_id
         JOIN public.teams t ON t.chat_id = c.id;

INSERT INTO public.log_keys (player_id, team_id, game_id, level_number, key_text, is_correct, is_duplicate)
SELECT p.id, t.id, g.id, olk.level_number, olk.key_text, COALESCE(olk.is_correct, TRUE), olk.is_correct is null
FROM old.log_keys olk
         JOIN public.users u ON u.tg_id = olk.user_id
         JOIN public.players p ON p.user_id = u.id
         JOIN old.games og ON og.game_id = olk.game_id
         JOIN public.games g ON g.name = og.name
         JOIN old.teams ot ON ot.team_id = olk.team_id
         JOIN public.chats c ON c.tg_id = ot.chat_id
         JOIN public.teams t ON t.chat_id = c.id;

INSERT INTO public.organizers (player_id, game_id, can_spy, can_see_log_keys, can_validate_waivers, deleted)
SELECT p.id, g.id, oo.can_spy, oo.can_see_log_keys, oo.can_validate_waivers, oo.deleted
FROM old.organizers oo
         JOIN public.users u ON u.tg_id = oo.user_id
         JOIN public.players p ON p.user_id = u.id
         JOIN old.games og ON og.game_id = oo.game_id
         JOIN public.games g ON g.name = og.name;

INSERT INTO public.waivers (player_id, team_id, game_id, role, played)
SELECT p.id, t.id, g.id, ow.role, ow.played::text::played
FROM old.waivers ow
         JOIN public.users u ON u.tg_id = ow.user_id
         JOIN public.players p ON p.user_id = u.id
         JOIN old.games og ON og.game_id = ow.game_id
         JOIN public.games g ON g.name = og.name
         JOIN old.teams ot ON ot.team_id = ow.team_id
         JOIN public.chats c ON c.tg_id = ot.chat_id
         JOIN public.teams t ON t.chat_id = c.id;

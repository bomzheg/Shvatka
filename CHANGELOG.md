# Changelog

## 3.6.0

### Improvements

**Search everywhere.** One request now searches games, levels, teams and players at once — including the text
inside level hints, so you can find "that level with the riddle about the bridge" without opening every game.
Each result knows where the match was found, so the UI can take you straight to it. (#286)

**Merging players and teams became a normal, reviewable procedure.** Merging now also carries over the
player's email account (#293, #291). Before merging, an admin can see the periods where a player's team is
fixed by their waivers, and hand-build the resulting team history when the two timelines overlap and can't be
stitched automatically — instead of the old error page (#294). And a merge proposal is no longer a message
with buttons in a channel: it becomes a regular action request that any superuser can accept or decline from
the web admin panel or from the bot, whichever is closer at hand (#296).

**More things admins can fix without a database console.** Completed games can be edited — scenario,
author, media files (#297). A player can be promoted to author right from the web, through the same
request/accept flow the bot uses (#299). A player's username can be changed by an admin, next to the
existing email and telegram controls (#310).

**Game results.** Results can now be downloaded as an xlsx table straight from the web, not only through the
bot (#300). Bonuses and penalties from keys and timers are finally counted into the results: the times you
see are the times that decide the standings (#308, #258).

**Playing in a team chat got tidier.** The bot pins the current level's puzzle and its time hints, and unpins
them when the team moves on; bonus hints are pinned too and cleaned up when the game ends — so the chat
always has the relevant text one tap away (#303, #269).

**iPhone photos just work.** HEIC/HEIF images are converted to JPEG when uploaded, so they display in the
browser and in Telegram instead of turning into an unopenable file (#302, #289).

**Friendlier usernames.** A new player without a telegram username used to end up as `id1234`. Now the
username is built from their transliterated telegram name — `Гарри Поттер` becomes `garri_potter` — and the
id-based name is only a last resort (#309).

### Bug fixes

- Scenario re-upload no longer crashes when the game contains a file that was uploaded through the web and
  has no telegram file id yet. Fixed along the way: files could be stored empty after being uploaded to
  Telegram (#301, #298)
- Pressing a waiver vote button that changes nothing no longer raises "message is not modified" and no longer
  spams the admin log chat. Handled globally, so every other place that edits a message is covered too
  (#307, #149)
- Merging players now also merges their email account, instead of leaving it behind (#293, #291)

### Tech tasks

- The API layer is split by subdomain: models first (#311), then routes moved next to the models they speak,
  with framework plumbing pulled out into `api/app` (#312). A change in one subdomain no longer touches files
  shared by all of them
- Outgoing Telegram Bot API requests are instrumented with Prometheus metrics — request rate, error rate,
  latency and in-flight requests per API method (#313, #97)
- Bot dialogs can be rendered as a preview again: every one of the 75 windows now has preview data (#316),
  and transitions made from handlers are declared explicitly, so the dialogs diagram no longer shows
  unreachable islands (#317)
- `context.md` at the repo root records the project's ubiquitous language: bounded contexts, a Russian ↔
  English glossary, game statuses, naming rules, and the words we deliberately don't use (#318)
- User documentation expanded with 11 new pages for captains, players, authors and organizers, with bot and
  web screenshots side by side (#315)

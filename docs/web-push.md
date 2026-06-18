# Web Push — backend contract & frontend debugging brief

This documents exactly what the Shvatka backend sends and expects, so the
frontend (service worker + subscription flow) can be verified against it.

If pushes "don't arrive", the cause is almost always one of:
1. VAPID keys are not configured on the server → backend silently no-ops.
2. The service worker has **no `push` event handler** (or it doesn't call
   `showNotification`) → the message is delivered but nothing is shown.
3. The browser never created/registered a subscription (permission not
   granted, or `PUT /push/subscriptions` was never called).

The backend itself needs **no further changes** for pushes to work, but the
service worker **does** need a `push` handler — payloads are never shown
automatically.

---

## 1. Backend → push payload (what the SW receives)

The server sends a JSON body via the Web Push protocol. Shape
(`shvatka/api/utils/push.py`, `PushMessage.to_json`):

```json
{
  "title": "string",          // always present
  "body": "string",           // always present
  "url": "/games/running",    // always present, defaults to "/"
  "tag": "string",            // optional
  "data": { "kind": "...", "...": "..." }   // optional, see kinds below
}
```

`data.kind` values currently emitted:

| kind                   | source              | extra fields in `data`                  |
|------------------------|---------------------|-----------------------------------------|
| `puzzle`               | new level for team  | `team_id`, `level_id`                   |
| `hint`                 | new hint            | `team_id`, `level_id`, `hint_number`    |
| `team_finished`        | team finished       | `team_id`                               |
| `game_finished`        | all finished        | `team_id`                               |
| `effects`              | level effect        | `team_id`, `effects_id`                 |
| `org_level_up`         | **org** notifier    | `team_id`, `level_id`                   |
| `new_org`              | **org** notifier    | `game_id`, `org_id`                     |
| `level_test_completed` | **org** notifier    | `level_name_id`                         |

The service worker must:

```js
self.addEventListener('push', (event) => {
  const payload = event.data ? event.data.json() : {};
  const { title, body, url, tag, data } = payload;
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      tag,
      data: { ...data, url },   // keep url so the click handler can use it
      // icon/badge optional
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(clients.openWindow(url));
});
```

**Without the `push` listener above, nothing is shown — this is the most
likely reason pushes "don't come".**

---

## 2. Subscription flow (what the frontend must do)

> Paths below are the FastAPI app routes (`/push/...`). If the deployment
> fronts the API behind a gateway that prefixes `/api`, use `/api/push/...`
> accordingly — match whatever prefix the rest of the API uses.

1. `GET /push/config` → `{ "enabled": bool, "public_key": string | null }`.
   - If `enabled` is `false` or `public_key` is `null`, the server is not
     configured for push — stop, there is nothing the frontend can do.
2. Register the service worker, then request notification permission.
3. Subscribe:
   ```js
   const reg = await navigator.serviceWorker.ready;
   const sub = await reg.pushManager.subscribe({
     userVisibleOnly: true,
     applicationServerKey: urlBase64ToUint8Array(public_key), // from step 1
   });
   ```
4. Send the subscription to the server:
   `PUT /push/subscriptions` with body matching the `PushSubscriptionJSON`
   shape (this is exactly what `sub.toJSON()` returns):
   ```json
   {
     "endpoint": "https://...",
     "keys": { "p256dh": "...", "auth": "..." }
   }
   ```
   The request must be authenticated (same cookie/JWT auth as the rest of the
   API) — the server ties the subscription to the logged-in player.
5. To unsubscribe: `DELETE /push/subscriptions` with the same body.

Notes:
- `applicationServerKey` must be the VAPID **public** key from `/push/config`,
  base64url-decoded to a `Uint8Array`. A wrong/missing key is a common silent
  failure.
- The endpoint is unique per browser+device; re-subscribing upserts server-side.

---

## 3. Who receives which push

- **In-game pushes** (`puzzle`, `hint`, `team_finished`, `game_finished`,
  `effects`) go only to players who voted "yes" for the current game (the
  team's waiver list).
- **Org pushes** (`org_level_up`, `new_org`, `level_test_completed`) go to
  **every organizer** of the game (primary author + secondary orgs), mirroring
  the Telegram bot.

A subscription is only delivered to if `enabled = true` for that player's
subscription row. The server auto-disables a subscription (sets
`enabled = false`) when the push provider returns `404`/`410` (expired).

---

## 4. Debugging checklist (frontend)

- [ ] `GET /push/config` returns `enabled: true` and a non-null
      `public_key`. If not, it's a **server config** problem (VAPID keys),
      not frontend.
- [ ] `Notification.permission === 'granted'`.
- [ ] A service worker is registered and active for the app's scope.
- [ ] `reg.pushManager.getSubscription()` returns a non-null subscription.
- [ ] That subscription was sent to `PUT /push/subscriptions` and got a
      `204`.
- [ ] The service worker has a `push` event listener that calls
      `showNotification` (check `chrome://serviceworker-internals` or DevTools
      → Application → Service Workers → "Push" test button).
- [ ] Use DevTools → Application → Service Workers → **Push** to send a test
      payload like `{"title":"t","body":"b","url":"/"}` and confirm a
      notification appears. If the test button works but real pushes don't, the
      problem is subscription/permission/auth, not the SW handler.
- [ ] The account being tested is actually a participant: for in-game pushes
      the player must have voted "yes"; for org pushes the player must be an
      org of that game.

## 5. Debugging checklist (server side, for reference)

- [ ] `push.enabled = true` and `vapid_public_key` / `vapid_private_key` /
      `vapid_claims_sub` are all set in the API config (otherwise
      `WebPushSender.send_to_players` logs `"web push is disabled or not
      configured"` and returns).
- [ ] `vapid_claims_sub` is a valid `mailto:` or origin `sub` claim.
- [ ] Server logs around send: look for `"web push provider rejected
      subscription"` or `"web push send failed"` warnings.
- [ ] There is at least one row in `push_subscription` with `enabled = true`
      for the target player id.

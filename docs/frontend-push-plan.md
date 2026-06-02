= Frontend PWA Push Plan

== Goal
Enable browser push notifications in the Angular PWA using only the existing backend push endpoints.

== Backend contract
* `GET /push/config` returns `{ enabled: boolean, public_key: string | null }`.
* `PUT /push/subscriptions` registers or refreshes the current browser subscription. Send the native `PushSubscription.toJSON()` payload.
* `DELETE /push/subscriptions` removes the current browser subscription. Send the same payload shape as registration.
* Push payloads contain `title`, `body`, `url`, optional `tag`, and optional `data`.

== Angular implementation steps
. Verify Angular service worker is already enabled (`ServiceWorkerModule.register(...)`) and the app is served over HTTPS in production.
. Add a `PushApiService` that loads `/push/config`, calls `SwPush.requestSubscription({ serverPublicKey })`, and sends the subscription to `PUT /push/subscriptions`.
. Add an explicit user action such as `Enable notifications`; do not request permission automatically on page load.
. On login/app bootstrap, if permission is already `granted`, refresh the saved subscription by calling `SwPush.subscription` and `PUT /push/subscriptions`.
. On logout or a user `Disable notifications` action, read the current subscription, call `DELETE /push/subscriptions`, then call `subscription.unsubscribe()`.
. Subscribe to `SwPush.messages` for foreground messages and show in-app toast/snackbar notifications.
. Subscribe to `SwPush.notificationClicks` and navigate to `payload.url` when present.
. In `ngsw-worker` notification handling, use backend payload fields: `title`, `body`, `tag`, `data.url`/`url`.
. Add UI states for unsupported browsers, disabled backend config, denied permission, and successful subscription.
. Test in Chrome/Edge Android and desktop Chrome; separately verify iOS Safari PWA install-to-home-screen behavior.

== Suggested payload handling
[source,typescript]
----
interface BackendPushPayload {
  title: string;
  body: string;
  url?: string;
  tag?: string;
  data?: Record<string, unknown>;
}
----

== Acceptance checklist
* User can enable notifications from a visible button.
* The browser sends a subscription to `PUT /push/subscriptions`.
* Refresh/re-login does not create duplicate active subscriptions for the same endpoint.
* New level, new hint, timer event, team finish, and game finish notifications open the running game page.
* Logout or disable removes the subscription through `DELETE /push/subscriptions`.

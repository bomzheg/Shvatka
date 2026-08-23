---
name: steward
description: How an agent watches a pull request in this repository — webhooks only, no scheduled check-ins. Read before acting on a CI or review event on a PR you opened or were asked to drive.
---

# Watching a pull request here

**Never schedule a check-in to re-look at a PR.** No `send_later`, no cron, no
`ScheduleWakeup`, no "I'll re-check in an hour". A subscribed PR delivers CI
failures, reviews and comments as webhook events; that is the whole signal, and
waiting for it costs nothing. Polling a quiet PR every hour burns a real share
of the owner's usage budget to learn that nothing changed — that has happened,
and it is why this file exists.

`mcp__Claude_Code_Remote__send_later` is also denied in `.claude/settings.json`.
The deny rule is the backstop; this file is the reason.

## What to do when an event does arrive

Same posture as before, minus the timer:

- **CI red on a PR you opened** — root-cause it and push a fix, or establish it
  is not this PR's failure (red on base too, or a service the diff never
  touches). If it is real but out of scope, say what is failing and why you are
  not fixing it. Then stop; the next push produces the next event.
- **A review comment** — implement and push small, local asks (nits, renames,
  an added test, a one-function refactor). Anything larger, or anything you are
  unsure about, goes to the person who asked for the work — propose, don't push.
- **Green check suite, your own echoed comment, a duplicate of something you
  already handled** — nothing to do. Do not reply to say so.

## What not to do

- Don't re-arm anything after handling an event.
- Don't fetch the whole PR body to learn its status; `get_check_runs` and the
  event payload already say what changed.
- Don't post "still green" or "no change" comments on the PR, and don't message
  the owner to report that nothing happened.
- Don't unsubscribe from the PR — the subscription is what makes the quiet
  waiting free.

## What this file does not change

The rules your harness states as **never** still hold: no skipping, disabling
or quarantining a test to get green; no rewriting history on someone else's
branch; no empty commit or close-and-reopen to kick CI; no approving or merging.
This file governs *pacing*, nothing else.

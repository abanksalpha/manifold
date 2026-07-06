# Sync: self-hosted server + desktop-to-desktop demo

> Assignment 7b. Manifold reuses Anki's built-in sync protocol against a
> self-hosted sync server (D9), so reviews flow between devices with no custom
> sync code. This note records the command that starts the server, the
> desktop-to-desktop sync demo, and the conflict rule. It matches
> [`spec-mobile-sync.md`](spec-mobile-sync.md) section 5.

## Automatic sync: on open/close and at session end

Manifold keeps Anki's built-in two-way sync (D9) and drives it automatically so a
signed-in learner's cards + reviews stay live across their devices on one sync
account (AnkiWeb by default, or a self-hosted server):

- **On profile open/close** — Anki's own auto-sync path
  (`maybe_auto_sync_on_open_close`); the manual sync shortcut is hidden but this
  path is kept. It pulls another device's changes when the app opens and pushes on
  close.
- **At the end of a study session** — when the learner leaves the session with at
  least one review recorded, `ts/routes/manifold-session/+page.svelte` calls
  `triggerCollectionSync()`, which POSTs `/_anki/manifoldSync`; the `manifold_sync`
  mediasrv handler runs `_sync_collection_and_media` on the main thread. This makes
  cross-device sync near-real-time — reviews propagate as soon as a session ends,
  not only on app close — without a per-answer sync, which Anki's full-collection
  protocol is not built for.

The session-end handler is a no-op (not an error) when the learner has not signed
in to sync yet (`sync_auth()` is `None`) or a sync is already running. A genuine
sync failure surfaces through Anki's own sync error UI, and the client-side trigger
rethrows a transport failure rather than swallowing it.

To turn it on, sign in to sync once (AnkiWeb or your server) via **Preferences >
Syncing** and leave "sync on open/close" enabled; on macOS the Preferences menu
item stays on the system menu bar even though Manifold hides its in-app chrome.

## Starting the server

The sync server ships inside `rslib` and is launched through pylib. Set at least
one user (`SYNC_USER1=username:password`) and run it headless. From the repo root,
after a build:

```bash
SYNC_USER1=demo:demo SYNC_HOST=127.0.0.1 SYNC_PORT=27913 SYNC_BASE=/tmp/anki-sync \
    PYTHONPATH=out/pylib out/pyenv/bin/python -m anki.syncserver
```

The desktop build also exposes the same server through the run script, which is
the form quoted in Anki's own docs:

```bash
SYNC_USER1=demo:demo ./run --syncserver
```

Environment variables it reads:

- `SYNC_USER1` (and `SYNC_USER2`, ...): `username:password` pairs; at least one is
  required.
- `SYNC_HOST` / `SYNC_PORT`: bind address and port (default port 8080).
- `SYNC_BASE`: directory for the server's collection data.

### Smoke check (verified)

Started with the first command above, the server logs that it is listening and
answers HTTP:

```
INFO listening addr=127.0.0.1:27913
```

- `GET /` returns `404` (no page at the root), confirming the HTTP server is up.
- `POST /sync/hostKey` returns `400` for an empty body, confirming the sync routes
  exist and are handled by the Anki sync server (an unrelated path would `404`).

Stop it with Ctrl+C (or by killing the process); it leaves the collection in
`SYNC_BASE` intact for the next run.

## Desktop-to-desktop sync demo

Two desktop profiles (A and B) sync through the one self-hosted server.

1. Start the server with `SYNC_USER1=demo:demo` (above).
2. On desktop A, point the client at the server: Preferences > Syncing, set the
   self-hosted sync URL to `http://127.0.0.1:27913/`, and sign in as `demo`. On
   macOS the Preferences item stays on the system menu bar even though Manifold
   hides its in-app chrome; Manifold then syncs through Anki's auto-sync on
   profile open and close (the manual sync shortcut is removed, the auto-sync path
   is not).
3. On A, study some Manifold cards, then let it sync (close the profile or trigger
   sync). The collection uploads to the server.
4. On desktop B, set the same sync URL and sign in as `demo`, then sync. B
   downloads A's collection, including the GRE deck and every `mf::` tag, so both
   shells study the identical deck on the shared engine.
5. Disjoint reviews: study 10 cards on A and 10 different cards on B while each is
   offline, then sync both. All 20 reviews merge and land exactly once, none lost
   or doubled.

## Recording: the automated demo (verified)

The walk-through above is also scripted and captured, so the §7b properties are shown
from a real run rather than described. From the repo root:

```bash
just demo-sync   # or: PYTHONPATH=out/pylib out/pyenv/bin/python manifold/tests/demo_sync.py
```

`manifold/tests/demo_sync.py` starts the self-hosted server, seeds collection A with
the GRE deck, brings up an empty B that full-downloads A (a real common base), then
drives two real collections through the server and checks every outcome against the
merged SQLite `revlog`/card rows. The captured transcript is committed at
[`sync-demo.log`](sync-demo.log); the run ends:

```
[PASS] common base established                           A=519 cards, B=519 cards; revlog baseline A=0, B=0
[PASS] disjoint reviews converge (counts match)          A +20, B +20, expected +20
[PASS] each review present exactly once (no loss/dupes)  A: 20 rows over 20 cards; B: 20 rows over 20 cards
[PASS] conflict: later review wins scheduling state      converged card row == B's later review on both sides
[PASS] conflict: earlier review retained in revlog        both revlog ids present on both sides
RESULT: ALL PASS
```

This is desktop-to-desktop on the shared engine (no phone required) and exercises the
same sync substrate the Android companion would use. The phone APK itself is blocked
by the toolchain (see [`mobile-status.md`](mobile-status.md)), so this stands in for
the phone→desktop shot until the APK is built.

## Conflict rule

The substrate is Anki's collection-level sync; Manifold adds no conflict logic of
its own. The rule is last-write-wins by modification time (mtime):

- When the same object (for Manifold, the same card or its review) was changed on
  both A and B since the last sync, the change with the later modification time
  wins; the earlier one is superseded for scheduling. Every attempt is still
  retained in the revlog, so nothing is silently dropped, but the card's schedule
  reflects only the winning (latest) review rather than double-counting both.
- Clock skew is handled by normalizing review timestamps to the server's clock on
  sync, so a wrong device clock cannot hand a stale review the win.
- If the two collections have diverged too far to merge incrementally (for
  example a schema-level change), Anki falls back to a full one-way sync and the
  user chooses which side to keep, rather than guessing.

To demonstrate it: review the same card on A and B while both are offline, then
sync both. The later-modified review is the one that determines the card's next
due date, and the demo shows a single, deterministic winner. This is the rule
named in [`spec-mobile-sync.md`](spec-mobile-sync.md) section 5.

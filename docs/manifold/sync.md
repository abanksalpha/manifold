# Sync: self-hosted server + desktop-to-desktop demo

> Assignment 7b. Manifold reuses Anki's built-in sync protocol against a
> self-hosted sync server (D9), so reviews flow between devices with no custom
> sync code. This note records the command that starts the server, the
> desktop-to-desktop sync demo, and the conflict rule. It matches
> [`spec-mobile-sync.md`](spec-mobile-sync.md) section 5.

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

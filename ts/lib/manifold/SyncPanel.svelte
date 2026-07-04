<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The cross-device sync prompt + background controller (dashboard body).

Signed out, it shows the "Sync across devices" prompt with Google sign-in (the
flow adapts to the shell: popup in a real browser, a native system-browser
loopback on desktop, a native credential bridge on Android). Signed in, it shows
nothing here — the account lives in the compact chip in the masthead
(SyncChip.svelte), and the scores are the ones already shown under Measurements —
but it still runs the background progress push so other signed-in devices update
in real time. A push failure while signed in surfaces as one small line rather
than the full box, so errors stay loud without cluttering the signed-in view.

All Firebase work is client-only and started in onMount; every failure is
surfaced (no silent fallback).
-->
<script lang="ts">
    import { browser } from "$app/environment";
    import { onDestroy, onMount } from "svelte";

    import Button from "$lib/manifold/Button.svelte";
    import {
        type ManifoldUser,
        onManifoldUser,
        signInWithGoogle,
    } from "$lib/manifold/firebase";
    import { pushProgressSnapshot } from "$lib/manifold/sync";

    let user: ManifoldUser | null = null;
    let ready = false;
    let busy = false;
    let signInError: string | null = null;
    let syncError: string | null = null;

    let unsubAuth: (() => void) | null = null;
    // Guards a single upload per sign-in, so opening the dashboard publishes this
    // device's latest scores once rather than on every reactive tick.
    let pushedForUid: string | null = null;

    onMount(() => {
        if (!browser) {
            return;
        }
        try {
            unsubAuth = onManifoldUser((next) => {
                user = next;
                ready = true;
                if (user) {
                    if (pushedForUid !== user.uid) {
                        pushedForUid = user.uid;
                        void pushProgressSnapshot({ force: true }).catch((e) => {
                            syncError = e instanceof Error ? e.message : String(e);
                        });
                    }
                } else {
                    pushedForUid = null;
                    syncError = null;
                }
            });
        } catch (e) {
            // Config missing / Firebase failed to init: surface it, do not pretend.
            signInError = e instanceof Error ? e.message : String(e);
            ready = true;
        }
    });

    onDestroy(() => {
        unsubAuth?.();
    });

    async function signIn(): Promise<void> {
        busy = true;
        signInError = null;
        try {
            await signInWithGoogle();
        } catch (e) {
            signInError = e instanceof Error ? e.message : String(e);
        } finally {
            busy = false;
        }
    }
</script>

{#if ready && !user}
    <section class="mf-sync" aria-label="Cross-device sync">
        <div class="mf-sync-out">
            <div class="mf-sync-copy">
                <span class="mf-sync-title">Sync across devices</span>
                <span class="mf-sync-sub">
                    Sign in with Google to keep your progress live on every device.
                </span>
            </div>
            <Button on:click={signIn} disabled={busy} ariaLabel="Sign in with Google">
                {busy ? "Signing in…" : "Sign in with Google"}
            </Button>
        </div>
        {#if signInError}
            <p class="mf-sync-error">{signInError}</p>
        {/if}
    </section>
{:else if syncError}
    <section class="mf-sync mf-sync--error" aria-label="Cross-device sync">
        <p class="mf-sync-error">Sync issue: {syncError}</p>
    </section>
{/if}

<style>
    .mf-sync {
        margin-top: var(--mf-space-6);
        border: 3px solid var(--mf-ink, #16131c);
        background: var(--mf-surface, #fff);
        box-shadow: 4px 4px 0 0 var(--mf-ink, #16131c);
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        font-family: "Plus Jakarta Sans Variable", system-ui, sans-serif;
    }
    .mf-sync-out {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .mf-sync-copy {
        display: flex;
        flex-direction: column;
        flex: 1 1 auto;
        min-width: 0;
    }
    .mf-sync-title {
        font-weight: 800;
        letter-spacing: 0.01em;
    }
    .mf-sync-sub {
        font-size: 0.85em;
        opacity: 0.7;
    }
    .mf-sync-error {
        margin: 0;
        color: #b00020;
        font-size: 0.85em;
        font-weight: 700;
    }
</style>

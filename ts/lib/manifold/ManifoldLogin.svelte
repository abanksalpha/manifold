<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The startup sign-in gate for the Manifold app. Manifold requires a Google
account so progress is tied to an identity and mirrored across devices, so this
screen blocks the app until the learner is signed in. The signed-in session
persists (Firebase durable persistence), so this is shown once per device, not
every launch.

`checking` covers the brief window where a persisted session is being restored,
so a returning user sees a spinner rather than a sign-in prompt that flashes away.
Every failure is surfaced, never swallowed.
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import Button from "$lib/manifold/Button.svelte";
    import { signInWithGoogle } from "$lib/manifold/firebase";

    /** Auth state is still resolving (a persisted session is being restored). */
    export let checking = false;
    /** A real error from initializing auth (distinct from a sign-in attempt). */
    export let initError: string | null = null;

    let busy = false;
    let signInError: string | null = null;

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

<div class="manifold mf-page">
    <div class="mf-shell">
        <section class="mf-card">
            <span class="mf-wordmark">Manifold</span>
            {#if checking}
                <div class="mf-checking" aria-live="polite">
                    <span class="mf-spinner" aria-hidden="true"></span>
                    <span class="mf-checking-text">Checking your session</span>
                </div>
            {:else}
                <h1 class="mf-title">Sign in to continue</h1>
                <p class="mf-lede">
                    Manifold keeps your progress on your Google account. Sign in to
                    start studying.
                </p>
                <div class="mf-actions">
                    <Button
                        on:click={signIn}
                        disabled={busy}
                        ariaLabel="Continue with Google"
                    >
                        {busy ? "Signing in…" : "Continue with Google"}
                    </Button>
                </div>
                {#if signInError}
                    <p class="mf-error">{signInError}</p>
                {/if}
                {#if initError}
                    <p class="mf-error">{initError}</p>
                {/if}
            {/if}
        </section>
    </div>
</div>

<style lang="scss">
    /* Centered gate: the one card sits in the middle of the viewport, on the
       app's warm ground with its halftone dot grid behind. */
    .mf-page {
        min-height: 100vh;
        padding: var(--mf-space-7) var(--mf-space-6);
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: clip;
    }

    .mf-shell {
        width: 100%;
        max-width: 460px;
    }

    /* The same sticker card the rest of the app uses, lifted a little more since
       it is the only element on screen. */
    .mf-card {
        display: grid;
        gap: var(--mf-space-4);
        padding: var(--mf-space-7) var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-feature);
        animation: mf-pop-in 200ms var(--mf-ease-out);
    }

    .mf-wordmark {
        position: relative;
        /* Own stacking context so the z-index:-1 highlighter paints above the
           card surface (behind the letters), not behind the whole card as it
           would relative to the page. */
        isolation: isolate;
        width: fit-content;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-2xl);
        font-weight: 800;
        letter-spacing: -0.03em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    /* The amber highlighter sweep under the wordmark, matching every other
       Manifold masthead. */
    .mf-wordmark::after {
        content: "";
        position: absolute;
        left: -0.03em;
        right: -0.03em;
        bottom: 0.08em;
        height: 0.26em;
        background: var(--mf-secondary);
        transform: rotate(-1.5deg);
        transform-origin: left center;
        z-index: -1;
    }

    .mf-title {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xl);
        font-weight: 800;
        letter-spacing: -0.01em;
        line-height: 1.1;
        color: var(--mf-ink);
    }

    .mf-lede {
        margin: 0;
        max-width: 40ch;
        color: var(--mf-ink-muted);
    }

    .mf-actions {
        margin-top: var(--mf-space-2);
    }

    .mf-checking {
        display: flex;
        align-items: center;
        gap: var(--mf-space-3);
    }

    .mf-checking-text {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-sm);
        font-weight: 700;
        letter-spacing: 0.02em;
        color: var(--mf-ink-muted);
    }

    /* A single deliberate spinner: a ring with one ink arc turning steadily,
       identical to the session player's. */
    .mf-spinner {
        flex: none;
        width: 28px;
        height: 28px;
        border: 3px solid color-mix(in srgb, var(--mf-ink) 18%, transparent);
        border-top-color: var(--mf-ink);
        border-radius: var(--mf-radius-full);
        animation: mf-spin 0.8s linear infinite;
    }

    @keyframes mf-spin {
        to {
            transform: rotate(360deg);
        }
    }

    /* Loud-but-honest failure line, same treatment as the session player. */
    .mf-error {
        margin: 0;
        padding: var(--mf-space-3) var(--mf-space-4);
        border: 2px solid var(--mf-accent);
        border-radius: var(--mf-radius);
        font-size: var(--mf-text-sm);
        color: var(--mf-ink);
        background: color-mix(in srgb, var(--mf-accent) 12%, var(--mf-surface));
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-spinner {
            animation-duration: 2.4s;
        }
    }
</style>

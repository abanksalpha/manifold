<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The predict-then-reveal step (D36, Phase 3), shown at New (level 0) BEFORE the
worked example. The learner sees only the stem and is asked to make a quick
prediction, then reveal the worked example. It grades nothing and takes no input:
it is a pretrieval prompt, so the worked solution lands on a mind that has
already tried to guess. Gated by SELF and PREDICT flags in session.ts so it can
be ablated. Dispatches `reveal` when the learner is ready.
-->
<script lang="ts">
    import { createEventDispatcher } from "svelte";

    import Button from "$lib/manifold/Button.svelte";
    import { renderMath } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";
    import type { Problem } from "$lib/manifold/session";

    export let problem: Problem;

    const dispatch = createEventDispatcher<{ reveal: void }>();
</script>

<section class="mf-predict" aria-labelledby="mf-predict-title">
    <p class="mf-predict-eyebrow">
        <span class="mf-predict-mark" aria-hidden="true">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <circle cx="12" cy="12" r="8" />
                <path d="M12 4v3M12 17v3M4 12h3M17 12h3" />
            </svg>
        </span>
        Predict
    </p>
    <h1 id="mf-predict-title" class="mf-predict-title">{problem.topic}</h1>
    <div class="mf-predict-stem">
        <MathText text={renderMath(problem.stem)} />
    </div>
    <p class="mf-predict-note">
        Make a quick prediction, then reveal the worked example.
    </p>
    <Button class="mf-predict-cta" on:click={() => dispatch("reveal")}>
        Reveal worked example
        <svg
            slot="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            stroke-linejoin="round"
        >
            <path d="M5 12h14" />
            <path d="m13 6 6 6-6 6" />
        </svg>
    </Button>
</section>

<style lang="scss">
    /* The predict card: the same reading surface as the problem card, marked by
       the violet teaching rule so it reads as a lesson step, not a question. */
    .mf-predict {
        position: relative;
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: color-mix(in srgb, var(--mf-tertiary) 12%, var(--mf-surface));
        box-shadow: var(--mf-shadow-card);
        overflow: hidden;
    }

    .mf-predict::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: var(--mf-space-2);
        background: var(--mf-tertiary);
    }

    .mf-predict-eyebrow {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        margin: 0 0 var(--mf-space-2);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-tertiary-ink);
    }

    .mf-predict-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-surface);
        color: var(--mf-tertiary-ink);
        /* Nudge to the label's cap-height centre (measured; align skill). */
        position: relative;
        top: 1px;
    }

    .mf-predict-mark svg {
        width: 15px;
        height: 15px;
        display: block;
    }

    .mf-predict-title {
        margin: 0 0 var(--mf-space-3);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xl);
        font-weight: 800;
        letter-spacing: -0.01em;
        line-height: 1.15;
        color: var(--mf-ink);
    }

    .mf-predict-stem {
        font-size: var(--mf-text-lg);
        line-height: 1.5;
        color: var(--mf-ink);
    }

    .mf-predict-note {
        margin: var(--mf-space-4) 0 0;
        max-width: 52ch;
        font-size: var(--mf-text-base);
        line-height: 1.5;
        color: var(--mf-ink-muted);
    }

    :global(.mf-btn.mf-predict-cta) {
        margin-top: var(--mf-space-5);
    }
</style>

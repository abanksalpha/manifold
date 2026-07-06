<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The worked example shown at New (level 0), after the brief lecture intro and
before the learner's own attempt (D36, Phase 1). Manifold does not drop a New
learner into a cold problem: it first shows one full instance solved, the stem,
the five choices with the correct one marked (read-only, never answerable here),
and the verified worked solution. Then "Try one" fetches a FRESH instance of the
same skill so the learner studies one and solves a different one.

This renders the item's OWN verified content and invents nothing; the solution is
rendered here directly (not through AnswerFeedback, which always states a
correct/not-quite outcome that has no meaning before an attempt). Dispatches
`try` when the learner presses "Try one".
-->
<script lang="ts">
    import { createEventDispatcher } from "svelte";

    import Button from "$lib/manifold/Button.svelte";
    import {
        mathToMarkup,
        mathToPlainText,
        renderMath,
    } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";
    import type { Problem } from "$lib/manifold/session";

    export let problem: Problem;

    const dispatch = createEventDispatcher<{ try: void }>();
</script>

<section class="mf-worked" aria-labelledby="mf-worked-title">
    <p class="mf-worked-eyebrow">
        <span class="mf-worked-mark" aria-hidden="true">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M5 5h9M5 10h9M5 15h5" />
                <path d="m15 16 2.5 2.5L22 14" />
            </svg>
        </span>
        Worked example
    </p>
    <h1 id="mf-worked-title" class="mf-worked-title">{problem.topic}</h1>
    <div class="mf-worked-stem">
        <MathText text={renderMath(problem.stem)} />
    </div>

    <ul class="mf-worked-choices">
        {#each problem.choices as choice (choice.id)}
            <li
                class="mf-worked-choice"
                class:is-correct={choice.index === problem.correctIndex}
                aria-label="Choice {choice.id}: {mathToPlainText(
                    choice.text,
                )}{choice.index === problem.correctIndex ? ', the correct answer' : ''}"
            >
                <span class="mf-worked-key">{choice.id}</span>
                <span class="mf-worked-choice-text">
                    <MathText text={mathToMarkup(choice.text)} />
                </span>
                {#if choice.index === problem.correctIndex}
                    <span class="mf-worked-tag">Correct</span>
                {/if}
            </li>
        {/each}
    </ul>

    <div class="mf-worked-solution">
        <h2 class="mf-worked-heading">Worked solution</h2>
        <p class="mf-worked-body">
            <MathText text={renderMath(problem.solution)} />
        </p>
    </div>

    <Button class="mf-worked-cta" on:click={() => dispatch("try")}>
        Try one
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
    /* The worked-example sheet: the problem card's reading surface, marked with
       the violet teaching rule and wash so it reads as instruction. It sits below
       the lecture intro and above the learner's own attempt. */
    .mf-worked {
        position: relative;
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: color-mix(in srgb, var(--mf-tertiary) 12%, var(--mf-surface));
        box-shadow: var(--mf-shadow-card);
        overflow: hidden;
    }

    .mf-worked::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: var(--mf-space-2);
        background: var(--mf-tertiary);
    }

    .mf-worked-eyebrow {
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

    .mf-worked-mark {
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

    .mf-worked-mark svg {
        width: 15px;
        height: 15px;
        display: block;
    }

    .mf-worked-title {
        margin: 0 0 var(--mf-space-3);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xl);
        font-weight: 800;
        letter-spacing: -0.01em;
        line-height: 1.15;
        color: var(--mf-ink);
    }

    .mf-worked-stem {
        font-size: var(--mf-text-lg);
        line-height: 1.5;
        color: var(--mf-ink);
    }

    /* The choices, shown for study only: the same keycap-and-text row as the
       answer tiles, but inert, with the verified answer washed mint and tagged. */
    .mf-worked-choices {
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: var(--mf-space-2);
        margin: var(--mf-space-5) 0 0;
        padding: 0;
    }

    .mf-worked-choice {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
        padding: var(--mf-space-3) var(--mf-space-4);
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        color: var(--mf-ink);
    }

    .mf-worked-choice.is-correct {
        background: color-mix(in srgb, var(--mf-quaternary) 34%, var(--mf-surface));
    }

    .mf-worked-key {
        display: flex;
        align-items: center;
        justify-content: center;
        flex: none;
        width: 32px;
        height: 32px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-base);
        font-weight: 800;
    }

    .mf-worked-choice.is-correct .mf-worked-key {
        background: var(--mf-quaternary);
    }

    .mf-worked-choice-text {
        flex: 1;
        font-size: var(--mf-text-md);
        line-height: 1.4;
    }

    .mf-worked-tag {
        flex: none;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-quaternary-ink);
    }

    .mf-worked-solution {
        margin-top: var(--mf-space-5);
        padding: var(--mf-space-4) var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
    }

    .mf-worked-heading {
        margin: 0 0 var(--mf-space-1);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink-faint);
    }

    .mf-worked-body {
        margin: 0;
        font-size: var(--mf-text-base);
        line-height: 1.6;
        color: var(--mf-ink);
    }

    :global(.mf-btn.mf-worked-cta) {
        width: 100%;
        margin-top: var(--mf-space-5);
    }

    @media (max-width: 460px) {
        .mf-worked {
            padding: var(--mf-space-4);
        }
    }
</style>

<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import { browser } from "$app/environment";

    import Button from "$lib/manifold/Button.svelte";
    import Confetti, { type Origin } from "$lib/manifold/Confetti.svelte";
    import MathText from "$lib/manifold/MathText.svelte";
    import type { Answer, ChoiceId } from "$lib/manifold/session";
    import {
        CHOICE_IDS,
        grade,
        isCorrect,
        levelLabel,
        stepFor,
    } from "$lib/manifold/session";

    import type { PageData } from "./$types";

    export let data: PageData;

    let index = 0;
    let busy = false;
    let confetti: Confetti | undefined;
    let celebrated = false;

    $: step = index < data.queue.length ? stepFor(data.queue[index]) : null;

    // A finished run (every queued skill answered) earns one whole-screen
    // celebration; an empty queue on arrival is not a completion, so it stays calm.
    $: if (browser && step === null && index > 0 && !celebrated) {
        celebrated = true;
        confetti?.celebrate();
    }

    /** The viewport centre of the tile for a letter, so the pop springs from it. */
    function tileCenter(choice: Answer): Origin | null {
        if (!browser) {
            return null;
        }
        const el = document.querySelector(`.mf-choice[aria-label="Answer ${choice}"]`);
        if (!el) {
            return null;
        }
        const rect = el.getBoundingClientRect();
        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
    }

    async function answer(choice: Answer): Promise<void> {
        if (busy || !step) {
            return;
        }
        // Capture the tile before grading advances the queue and swaps the tiles.
        const origin = isCorrect(choice) ? tileCenter(choice) : null;
        busy = true;
        try {
            await grade(step.item, choice);
            index += 1;
            if (origin) {
                confetti?.burst(origin);
            }
        } finally {
            busy = false;
        }
    }

    function onKeydown(event: KeyboardEvent): void {
        if (busy || !step || event.metaKey || event.ctrlKey || event.altKey) {
            return;
        }
        const letter = event.key.toUpperCase();
        if ((CHOICE_IDS as readonly string[]).includes(letter)) {
            event.preventDefault();
            answer(letter as ChoiceId);
        } else if (event.key === "0") {
            event.preventDefault();
            answer("dont-know");
        }
    }
</script>

<svelte:window on:keydown={onKeydown} />

<div class="manifold mf-page">
    <Confetti bind:this={confetti} />
    <div class="mf-shell">
        <header class="mf-masthead">
            <span class="mf-wordmark">Manifold</span>
            {#if step}
                <Button
                    href="/manifold"
                    variant="secondary"
                    ariaLabel="Back to the dashboard"
                >
                    Dashboard
                    <svg
                        slot="icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path d="M19 12H5" />
                        <path d="m11 18-6-6 6-6" />
                    </svg>
                </Button>
            {/if}
        </header>

        {#if step}
            <section
                class="mf-card"
                data-topic={step.item.topicId}
                aria-labelledby="mf-prompt"
            >
                <p id="mf-prompt" class="mf-prompt">
                    A problem about <span class="mf-skill">
                        <MathText text={step.problem.skillName} />
                    </span>
                </p>
                <p class="mf-context">
                    <span
                        class="mf-level mf-level-{step.item.level}"
                        title="Scaffolding level: how much support this problem gives, based on your demonstrated competence"
                    >
                        {levelLabel(step.item.level)}
                    </span>
                </p>

                <div class="mf-choices" class:busy>
                    {#each step.problem.choices as choice (choice.id)}
                        <button
                            class="mf-choice"
                            type="button"
                            disabled={busy}
                            aria-label="Answer {choice.id}"
                            on:click={() => answer(choice.id)}
                        >
                            {choice.id}
                        </button>
                    {/each}
                </div>

                <Button
                    class="mf-dontknow"
                    variant="secondary"
                    disabled={busy}
                    on:click={() => answer("dont-know")}
                >
                    Don't know
                </Button>
            </section>
        {:else}
            <section class="mf-complete">
                <div class="mf-complete-card">
                    <span class="mf-complete-mark" aria-hidden="true">
                        <svg viewBox="0 0 24 24" role="presentation">
                            <circle
                                cx="12"
                                cy="12"
                                r="10.5"
                                fill="var(--mf-quaternary)"
                                stroke="var(--mf-ink)"
                                stroke-width="1.5"
                            />
                            <path
                                d="M7.6 12.5l2.9 3 6-6.6"
                                fill="none"
                                stroke="var(--mf-accent-ink)"
                                stroke-width="2.5"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                        </svg>
                    </span>
                    <h1 class="mf-complete-title">Session complete</h1>
                    <p class="mf-complete-text">
                        No more cards are due in this deck right now.
                    </p>
                    <Button href="/manifold">
                        Back to Manifold
                        <svg
                            slot="icon"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M19 12H5" />
                            <path d="m11 18-6-6 6-6" />
                        </svg>
                    </Button>
                </div>
            </section>
        {/if}
    </div>
</div>

<style lang="scss">
    .mf-page {
        min-height: 100vh;
        padding: var(--mf-space-7) var(--mf-space-6);
    }

    .mf-shell {
        max-width: 640px;
        margin-inline: auto;
    }

    .mf-masthead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
    }

    .mf-wordmark {
        position: relative;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-2xl);
        font-weight: 800;
        letter-spacing: -0.03em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    /* the same yellow highlighter the dashboard sweeps under its wordmark, so the
     * session masthead carries the brand mark. Sat behind the letters, above the
     * ground, and sized in em so it tracks the wordmark. */
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

    /* The stable-grid reading card: a calm surface, chunky ink outline and a soft
       hard shadow, lifted by one slim accent rule along its top edge so the
       problem surface carries a little colour. The tiles below stay neutral. */
    .mf-card {
        position: relative;
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    /* a hot-red accent rule flush inside the top ink border, edge to edge. Pure
       chrome on the card frame; it never touches the answer tiles. */
    .mf-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: var(--mf-space-2);
        background: var(--mf-accent);
    }

    .mf-prompt {
        margin: 0;
        font-size: var(--mf-text-lg);
        font-weight: 400;
        line-height: 1.4;
        /* reserve two lines so the answer tiles keep a fixed position whether the
         * skill name wraps to one line or two */
        min-height: 2.8em;
        color: var(--mf-ink-muted);
    }

    /* the skill under test: plain ink bold, so it reads as the one thing this
     * card is about without any highlighter chrome */
    .mf-skill {
        color: var(--mf-ink);
        font-weight: 800;
    }

    .mf-context {
        margin: var(--mf-space-3) 0 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-faint);
    }

    /* The card's teaching level, a read-only chip. A light tint of the level's
     * palette colour keeps ink text legible on every state. */
    .mf-level {
        display: inline-block;
        padding: 0.05em var(--mf-space-2);
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-ink);
        background: var(--mf-surface);
    }

    .mf-level-0 {
        background: color-mix(in srgb, var(--mf-abstain) 30%, var(--mf-surface));
    }

    .mf-level-1 {
        background: color-mix(in srgb, var(--mf-quaternary) 40%, var(--mf-surface));
    }

    .mf-level-2 {
        background: color-mix(in srgb, var(--mf-signal) 26%, var(--mf-surface));
    }

    .mf-level-3 {
        background: color-mix(in srgb, var(--mf-accent) 34%, var(--mf-surface));
    }

    .mf-choices {
        display: flex;
        gap: var(--mf-space-3);
        margin-top: var(--mf-space-5);
    }

    /* Tactile answer tiles, animated identically to the shared Button: on hover
       the face rises up-left and the ink block grows so its far edge stays put
       (the base is anchored, only the top face moves), and a click presses it
       back down onto the block. The letter is the display face, like a keycap for
       the A-E keyboard shortcuts. */
    .mf-choice {
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 1;
        min-height: 56px;
        border: var(--mf-outline-bold);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        color: var(--mf-ink);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xl);
        font-weight: 800;
        cursor: pointer;
        box-shadow: var(--mf-shadow);
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition);
    }

    /* Anki's global button reset (ts/lib/sass/base.scss) forces
       `transition: color, box-shadow ... !important` on every <button>, which
       drops transform from the transition so the hover lift snaps up-left before
       the shadow eases. Re-assert our transition at higher specificity (and with
       !important, the only way to beat their !important) so transform eases on the
       same bouncy curve as the <a> Button, e.g. Back to Manifold. */
    .mf-choices .mf-choice {
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition) !important;
    }

    /* Re-declare the ink outline in every interactive state. Anki's global
       `button:hover/active/[disabled]` chrome (ts/lib/sass/_button-mixins) is
       more specific than the base `.mf-choice` rule and would otherwise swap our
       4px ink border for a thin grey one on hover, which also snaps the box width
       as it changes untransitioned. Keeping it here wins the cascade. */
    .mf-choice:hover:not(:disabled) {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: var(--mf-hover);
        border: var(--mf-outline-bold);
    }

    .mf-choice:active:not(:disabled) {
        transform: translate(4px, 4px);
        box-shadow: none;
        border: var(--mf-outline-bold);
    }

    /* while grading, dim the row and flatten the tiles with no transform */
    .mf-choices.busy {
        opacity: 0.55;
    }

    .mf-choice:disabled {
        cursor: default;
        transform: none;
        box-shadow: var(--mf-shadow-active);
        border: var(--mf-outline-bold);
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-choice:hover:not(:disabled),
        .mf-choice:active:not(:disabled) {
            transform: none;
        }
    }

    /* the shared candy Button, stretched full width as the low-stakes action */
    :global(.mf-btn.mf-dontknow) {
        width: 100%;
        margin-top: var(--mf-space-4);
    }

    /* Completion: the one loud, celebratory surface. An asymmetric feature shadow,
       a pop-in on mount and a check sticker mark. The copy stays honest. */
    .mf-complete {
        margin-top: var(--mf-space-6);
    }

    .mf-complete-card {
        display: grid;
        justify-items: center;
        gap: var(--mf-space-3);
        padding: var(--mf-space-7) var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-feature);
        text-align: center;
        animation: mf-pop-in var(--mf-transition-bounce) both;
    }

    /* a check sticker: a mint circle with the ink outline and a near-white tick */
    .mf-complete-mark {
        display: block;
        width: 64px;
        height: 64px;
        margin-bottom: var(--mf-space-1);
    }

    .mf-complete-mark svg {
        display: block;
        width: 100%;
        height: 100%;
    }

    .mf-complete-title {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-2xl);
        font-weight: 800;
        letter-spacing: -0.02em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    .mf-complete-text {
        margin: 0 0 var(--mf-space-2);
        max-width: 40ch;
        font-size: var(--mf-text-base);
        color: var(--mf-ink-muted);
    }

    @media (max-width: 460px) {
        .mf-card {
            padding: var(--mf-space-4);
        }

        .mf-choices {
            gap: var(--mf-space-2);
        }

        .mf-choice {
            min-height: 48px;
            font-size: var(--mf-text-md);
        }

        .mf-complete-card {
            padding: var(--mf-space-6) var(--mf-space-4);
        }
    }
</style>

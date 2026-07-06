<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The faded-example scaffold (D36, Phase 2 and 3), shown above the choices at
Guided (level 1) and Revisit (level 3). It reveals the leading steps of the
item's OWN verified worked solution and leaves the trailing step(s) for the
learner to finish by choosing the answer. As competence grows, more of the tail
is faded out (see fadeSteps in scaffold.ts).

The steps are derived from the real solution, never invented. A solution that
cannot be faded (only one step) is not shown here at all: the caller drops the
scaffold (fadedScaffoldFor) and the item is solved cold, so the full answer is
never revealed above the graded choices. All maths is typeset through MathText.
-->
<script lang="ts">
    import { renderMath } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";

    /** The leading steps to reveal, in order (from fadeSteps). */
    export let shown: string[];
    /** How many trailing steps stay hidden for the learner to finish. */
    export let hiddenCount: number;
</script>

<section class="mf-faded" aria-labelledby="mf-faded-title">
    <p class="mf-faded-eyebrow" id="mf-faded-title">
        <span class="mf-faded-mark" aria-hidden="true">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M5 6h11M5 11h11" />
                <path d="M5 16h6" stroke-dasharray="2 2.5" />
            </svg>
        </span>
        Faded example
    </p>

    <ol class="mf-faded-steps">
        {#each shown as step, i (i)}
            <li class="mf-faded-step">
                <span class="mf-faded-num" aria-hidden="true">{i + 1}</span>
                <div class="mf-faded-step-text">
                    <MathText text={renderMath(step)} />
                </div>
            </li>
        {/each}
        {#if hiddenCount > 0}
            <li class="mf-faded-step mf-faded-blank">
                <span class="mf-faded-num" aria-hidden="true">{shown.length + 1}</span>
                <div class="mf-faded-step-text mf-faded-blank-text">
                    {hiddenCount > 1
                        ? "Your turn: finish the last steps"
                        : "Your turn: finish it"}
                </div>
            </li>
        {/if}
    </ol>
</section>

<style lang="scss">
    /* The scaffold tray: a sunken panel inside the problem card with one slim
       violet edge, the same teaching language as the lecture and hint panels. It
       sits above the choices, so the learner reads the method, then finishes it. */
    .mf-faded {
        position: relative;
        margin-top: var(--mf-space-5);
        padding: var(--mf-space-4) var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: color-mix(
            in srgb,
            var(--mf-tertiary) 12%,
            var(--mf-surface-sunken)
        );
        overflow: hidden;
    }

    .mf-faded::before {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: var(--mf-space-1);
        background: var(--mf-tertiary);
    }

    .mf-faded-eyebrow {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        margin: 0 0 var(--mf-space-4);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-tertiary-ink);
    }

    .mf-faded-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 26px;
        height: 26px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-surface);
        color: var(--mf-tertiary-ink);
        /* align-items: center sits the badge ~1px above the label's cap-height
           centre; nudge down to the cap centre (measured; align skill). */
        position: relative;
        top: 1px;
    }

    .mf-faded-mark svg {
        width: 15px;
        height: 15px;
        display: block;
    }

    .mf-faded-steps {
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: var(--mf-space-3);
        margin: 0;
        padding: 0;
    }

    .mf-faded-step {
        display: flex;
        align-items: flex-start;
        gap: var(--mf-space-3);
    }

    /* The blank row's text sits in a padded box; centre its badge to that box so
       the number optically aligns with the "Your turn" line (measured; align). */
    .mf-faded-step.mf-faded-blank {
        align-items: center;
    }

    .mf-faded-num {
        display: flex;
        align-items: center;
        justify-content: center;
        flex: none;
        width: 24px;
        height: 24px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-surface);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 800;
        color: var(--mf-ink);
    }

    /* A flex-start row tops the badge at the row edge, ~1.5px above the first
       line's cap centre; nudge it down to the cap centre (measured; align). */
    .mf-faded-step:not(.mf-faded-blank) .mf-faded-num {
        position: relative;
        top: 1.5px;
    }

    .mf-faded-step-text {
        flex: 1;
        padding-top: 1px;
        font-size: var(--mf-text-base);
        line-height: 1.55;
        color: var(--mf-ink);
    }

    /* The blank the learner finishes: a dashed placeholder that reads as
       deliberately unfinished, with its step number left open. */
    .mf-faded-blank .mf-faded-num {
        border-style: dashed;
        background: transparent;
        color: var(--mf-ink-faint);
    }

    .mf-faded-blank-text {
        padding: var(--mf-space-2) var(--mf-space-3);
        border: 2px dashed
            color-mix(in srgb, var(--mf-tertiary-ink) 55%, var(--mf-surface));
        border-radius: var(--mf-radius);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-sm);
        font-weight: 700;
        letter-spacing: 0.02em;
        color: var(--mf-tertiary-ink);
        background: color-mix(in srgb, var(--mf-tertiary) 10%, var(--mf-surface));
    }
</style>

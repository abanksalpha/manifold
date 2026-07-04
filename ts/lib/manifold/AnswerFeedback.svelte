<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The reveal shown once a problem is answered (D38). It states the outcome with a
distinct cue (a mint check when right, a red mark when wrong, never a streak),
then immediately reveals the worked solution
so the learner reads the reasoning while the attempt is fresh. On a miss it also
shows the verified rationale for the exact choice pressed, which names that
specific error. All maths is typeset through MathText; nothing here grades or
invents, it only renders the bank's verified content. For a New or Guided skill
the solution is framed as a worked example (D36); a cold Independent problem gets
the plain solution.
-->
<script lang="ts">
    import MathText from "$lib/manifold/MathText.svelte";
    import { renderMath } from "$lib/manifold/mathmarkup";
    import type { Problem } from "$lib/manifold/session";

    export let problem: Problem;
    /** The index of the choice the learner pressed, or null for "don't know". */
    export let chosenIndex: number | null;
    export let correct: boolean;
    export let level: number;

    // A New or Guided skill is opened as a worked example; higher levels are
    // cold, so the same reveal reads as a plain solution.
    $: solutionHeading = level <= 1 ? "Worked solution" : "Solution";

    // The rationales cover the four distractors in choice order (the correct one
    // skipped), so the pressed wrong choice maps back by discounting the correct
    // slot. Shown only when that specific rationale exists.
    $: rationale = missRationale(problem, chosenIndex, correct);

    function missRationale(
        p: Problem,
        chosen: number | null,
        wasCorrect: boolean,
    ): string | null {
        if (wasCorrect || chosen === null) {
            return null;
        }
        const rationaleIndex = chosen < p.correctIndex ? chosen : chosen - 1;
        return p.distractorRationales[rationaleIndex] ?? null;
    }
</script>

<div class="mf-feedback" class:correct data-correct={correct} aria-live="polite">
    <p class="mf-feedback-status">
        <span class="mf-feedback-mark" aria-hidden="true">
            {#if correct}
                <svg viewBox="0 0 24 24" role="presentation">
                    <path
                        d="M5 12.5l4 4 10-10.5"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="3"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />
                </svg>
            {:else}
                <svg viewBox="0 0 24 24" role="presentation">
                    <path
                        d="M7 12h10"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="3"
                        stroke-linecap="round"
                    />
                </svg>
            {/if}
        </span>
        {correct ? "Correct" : "Not quite"}
    </p>

    {#if rationale}
        <div class="mf-feedback-block">
            <h3 class="mf-feedback-heading">Your answer</h3>
            <p class="mf-feedback-body"><MathText text={renderMath(rationale)} /></p>
        </div>
    {/if}

    <div class="mf-feedback-block">
        <h3 class="mf-feedback-heading">{solutionHeading}</h3>
        <p class="mf-feedback-body">
            <MathText text={renderMath(problem.solution)} />
        </p>
    </div>
</div>

<style lang="scss">
    /* The reveal panel: a calm sunken surface set inside the card, with one slim
       edge rule that reads mint when right and red when wrong, so the outcome is
       unmistakable at a glance. */
    .mf-feedback {
        position: relative;
        margin-top: var(--mf-space-5);
        padding: var(--mf-space-4) var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
        overflow: hidden;
    }

    .mf-feedback::before {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: var(--mf-space-1);
        background: var(--mf-accent);
    }

    .mf-feedback.correct::before {
        background: var(--mf-quaternary);
    }

    .mf-feedback-status {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-md);
        font-weight: 800;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    /* The status mark rides in a bordered sticker badge like the app's other
       icons, so it optically centres on the label's cap height. The base badge is
       the wrong state (red); the correct override below turns it green. */
    .mf-feedback-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-accent);
        color: var(--mf-accent-ink);
    }

    .mf-feedback.correct .mf-feedback-mark {
        background: var(--mf-quaternary);
        color: var(--mf-ink);
    }

    .mf-feedback-mark svg {
        width: 16px;
        height: 16px;
        display: block;
    }

    .mf-feedback-block {
        margin-top: var(--mf-space-4);
    }

    .mf-feedback-heading {
        margin: 0 0 var(--mf-space-1);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink-faint);
    }

    .mf-feedback-body {
        margin: 0;
        font-size: var(--mf-text-base);
        line-height: 1.6;
        color: var(--mf-ink);
    }
</style>

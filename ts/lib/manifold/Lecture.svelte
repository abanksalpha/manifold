<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The New-skill lecture (Task 1). Before a learner meets the first problem for a
teach ("New") skill, Manifold teaches it: the method's name and when to use it, a
worked walk-through of a VERIFIED banked item, and a key takeaway. The content is
pre-authored and served from lectures.json (never generated live, the same vetted
rule as the teach bank); this component only renders it. All mathematics is
delimited LaTeX typeset through MathText — nothing here grades or invents.

It sits ABOVE the problem card as its own panel (not nested inside it), with a
violet teaching rule so it reads as a lesson, distinct from the hot-red problem
card and the mint/grey answer reveal.
-->
<script lang="ts">
    import type { Lecture } from "$lib/manifold/session";
    import { renderMath } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";

    export let lecture: Lecture;
</script>

<section class="mf-lecture" aria-labelledby="mf-lecture-title">
    <p class="mf-lecture-eyebrow">
        <span class="mf-lecture-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" role="presentation">
                <path
                    d="M4 5.5A1.5 1.5 0 0 1 5.5 4H11v15H5.5A1.5 1.5 0 0 0 4 20.5zM20 5.5A1.5 1.5 0 0 0 18.5 4H13v15h5.5A1.5 1.5 0 0 1 20 20.5z"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linejoin="round"
                />
            </svg>
        </span>
        Lecture
    </p>
    <h1 id="mf-lecture-title" class="mf-lecture-title">{lecture.title}</h1>
    <div class="mf-lecture-body">
        <MathText text={renderMath(lecture.lectureLatex)} fontSize={16} />
    </div>
</section>

<style lang="scss">
    /* A lesson sheet: the same chunky ink outline and hard ink-block shadow as the
       problem card, but marked by a violet teaching rule and a faint violet wash so
       it reads as instruction, not as a second question. It stacks above the problem
       card (a sibling, never a nested card). */
    .mf-lecture {
        position: relative;
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-5) var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: color-mix(in srgb, var(--mf-tertiary) 12%, var(--mf-surface));
        box-shadow: var(--mf-shadow-card);
        overflow: hidden;
    }

    .mf-lecture::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: var(--mf-space-2);
        background: var(--mf-tertiary);
    }

    .mf-lecture-eyebrow {
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

    /* The teaching mark rides in a bordered sticker badge, matching the app's other
       icons so it optically centres on the eyebrow's cap height. */
    .mf-lecture-mark {
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

    .mf-lecture-mark svg {
        width: 15px;
        height: 15px;
        display: block;
    }

    .mf-lecture-title {
        margin: 0 0 var(--mf-space-3);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xl);
        font-weight: 800;
        letter-spacing: -0.01em;
        line-height: 1.15;
        color: var(--mf-ink);
    }

    /* The walk-through itself. pre-line keeps the authored paragraph breaks while
       collapsing incidental whitespace, so \[ … \] display equations from MathText
       sit on their own lines between prose. Capped for a comfortable reading measure. */
    .mf-lecture-body {
        max-width: 62ch;
        font-size: var(--mf-text-md);
        line-height: 1.6;
        color: var(--mf-ink);
        white-space: pre-line;
    }
</style>

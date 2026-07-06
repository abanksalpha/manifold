<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The new-user onboarding wizard. Four phases: set up the deck (import if the
collection is empty), report the courses taken, a short cold placement
diagnostic, and a summary that seeds the learner's starting point. It seeds real
card state through the normal grade path and never produces a readiness number,
so the home gate stays honest: placement sets where you START, not a score.

Chrome (masthead, cards, buttons, choices, eyebrow, pills) reuses the shared
Manifold components and the exact styles the session player uses, so the flow is
of a piece with the rest of the app.
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import { getTopicGraph } from "@generated/backend";
    import { onMount } from "svelte";

    import { goto } from "$app/navigation";
    import Button from "$lib/manifold/Button.svelte";
    import type { TopicNode } from "$lib/manifold/graph";
    import {
        mathToMarkup,
        mathToPlainText,
        renderMath,
    } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";
    import {
        buildPlacementQueue,
        COURSES,
        importSeedDeck,
        knownTopicIds,
        type ProbeTally,
        seedPlacement,
        topicsForCourses,
        type Verdict,
        verdictForTopic,
    } from "$lib/manifold/placement";
    import {
        type Answer,
        grade,
        isCorrect,
        type ServedProblem,
        SessionRunner,
    } from "$lib/manifold/session";

    import type { PageData } from "./$types";

    export let data: PageData;

    type Phase = "setup" | "courses" | "exam" | "summary" | "applying";
    let phase: Phase = "setup";
    let nodes: TopicNode[] = data.nodes as TopicNode[];
    let setupError: string | null = null;

    let selectedList: string[] = [];
    function toggleCourse(id: string): void {
        selectedList = selectedList.includes(id)
            ? selectedList.filter((c) => c !== id)
            : [...selectedList, id];
    }

    let runner: SessionRunner | null = null;
    let served: ServedProblem | null = null;
    let examTotal = 0;
    let examDone = 0;
    let busy = false;
    let tallies = new Map<string, ProbeTally>();

    async function runSetup(): Promise<void> {
        setupError = null;
        phase = "setup";
        // Import the seed deck if this collection has no skill cards yet, so the
        // diagnostic has something to probe. Idempotent; fails loud.
        if (!nodes.some((n) => n.total > 0)) {
            try {
                await importSeedDeck();
                nodes = (await getTopicGraph({})).nodes as TopicNode[];
            } catch (err) {
                setupError = err instanceof Error ? err.message : String(err);
                return;
            }
        }
        phase = "courses";
    }

    onMount(runSetup);

    async function startExam(): Promise<void> {
        const topicIds = topicsForCourses(selectedList);
        if (topicIds.length === 0) {
            phase = "summary";
            return;
        }
        busy = true;
        try {
            const queue = await buildPlacementQueue(topicIds);
            if (queue.length === 0) {
                phase = "summary";
                return;
            }
            runner = new SessionRunner(queue);
            examTotal = queue.length;
            phase = "exam";
            const res = await runner.pull();
            served = res.served;
            if (!served) {
                phase = "summary";
            }
        } finally {
            busy = false;
        }
    }

    async function answerProbe(answer: Answer): Promise<void> {
        if (!served || !runner || busy) {
            return;
        }
        busy = true;
        try {
            const item = served.item;
            const correct = isCorrect(served.problem, answer);
            const prior = tallies.get(item.topicId) ?? { answered: 0, correct: 0 };
            tallies.set(item.topicId, {
                answered: prior.answered + 1,
                correct: prior.correct + (correct ? 1 : 0),
            });
            tallies = tallies; // reassign so the summary readout stays reactive
            examDone += 1;
            // Real Learning-kind evidence for this skill; probes are not timed (0).
            await grade(item, correct, 0);
            const res = await runner.pull();
            served = res.served;
            if (!served) {
                phase = "summary";
            }
        } finally {
            busy = false;
        }
    }

    function endExamEarly(): void {
        runner?.dispose();
        phase = "summary";
    }

    // Summary rows: one per reported topic, with its verdict. Depends on both
    // `selectedList` and `tallies`, so it recomputes as answers land.
    $: reportedTopics = topicsForCourses(selectedList);
    $: titleById = new Map(nodes.map((n) => [n.id, n.title]));
    $: summaryRows = reportedTopics.map((id) => ({
        id,
        title: titleById.get(id) ?? id,
        verdict: verdictForTopic(tallies.get(id), true) as Verdict,
    }));
    $: knownCount = summaryRows.filter((r) => r.verdict === "known").length;

    async function finish(): Promise<void> {
        phase = "applying";
        const prereqsById = new Map(nodes.map((n) => [n.id, n.prereqs]));
        const known = knownTopicIds(selectedList, tallies, prereqsById);
        await seedPlacement(known);
        // Completion is recorded in the local collection flag (the source of
        // truth); Anki's own sync carries it to the account's other devices.
        await goto("/manifold");
    }

    async function skipAll(): Promise<void> {
        phase = "applying";
        await seedPlacement([]); // seeds nothing, but marks onboarding done locally
        await goto("/manifold");
    }

    const verdictCopy: Record<Verdict, string> = {
        known: "Known",
        shaky: "Needs review",
        new: "Start fresh",
    };
</script>

<div class="manifold mf-page">
    <div class="mf-shell">
        <header class="mf-masthead">
            <span class="mf-wordmark">Manifold</span>
            {#if phase === "exam"}
                <div class="mf-masthead-end">
                    <Button variant="secondary" on:click={endExamEarly}>
                        End placement
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
            {/if}
        </header>

        {#if phase === "setup"}
            <section class="mf-card">
                {#if setupError}
                    <p class="mf-eyebrow">Placement</p>
                    <h1 class="mf-title">Could not set up your deck</h1>
                    <p class="mf-error">{setupError}</p>
                    <div class="mf-actions">
                        <Button
                            ariaLabel="Try setting up the deck again"
                            on:click={runSetup}
                        >
                            Try again
                        </Button>
                    </div>
                {:else}
                    <p class="mf-eyebrow">Placement</p>
                    <h1 class="mf-title">Loading the skill set</h1>
                    <p class="mf-lede">
                        Importing the GRE Mathematics topics. One moment.
                    </p>
                    <div class="mf-bar" aria-hidden="true"><span></span></div>
                {/if}
            </section>
        {:else if phase === "courses"}
            <section class="mf-card">
                <p class="mf-eyebrow">Placement, step 1</p>
                <h1 class="mf-title">Which of these have you taken?</h1>
                <p class="mf-lede">
                    Pick every course you have completed. We test a few topics from each
                    to place you, then skip re-teaching what you already know.
                </p>
                <div class="mf-course-grid" role="group" aria-label="Courses taken">
                    {#each COURSES as course (course.id)}
                        <label
                            class="mf-course"
                            class:is-on={selectedList.includes(course.id)}
                        >
                            <input
                                type="checkbox"
                                checked={selectedList.includes(course.id)}
                                on:change={() => toggleCourse(course.id)}
                            />
                            <span class="mf-course-check" aria-hidden="true">
                                <svg
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="3.5"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                >
                                    <path d="M4 12.5 9.5 18 20 6.5" />
                                </svg>
                            </span>
                            <span class="mf-course-name">{course.label}</span>
                        </label>
                    {/each}
                </div>
                <div class="mf-actions">
                    <Button
                        ariaLabel="Start the placement"
                        disabled={busy}
                        on:click={startExam}
                    >
                        {selectedList.length
                            ? "Start placement"
                            : "I've taken none of these"}
                    </Button>
                    <Button
                        variant="secondary"
                        ariaLabel="Skip the placement"
                        on:click={skipAll}
                    >
                        Skip for now
                    </Button>
                </div>
            </section>
        {:else if phase === "exam"}
            {#if served}
                <section class="mf-card" aria-labelledby="mf-stem">
                    <p class="mf-eyebrow">{served.problem.topic}</p>
                    <div id="mf-stem" class="mf-stem">
                        <MathText text={renderMath(served.problem.stem)} />
                    </div>

                    <div class="mf-meta">
                        <span class="mf-pill">Placement</span>
                        <span class="mf-count">Item {examDone + 1} of {examTotal}</span>
                    </div>
                    <div class="mf-progress" aria-hidden="true">
                        <span
                            style="width: {examTotal
                                ? (examDone / examTotal) * 100
                                : 0}%"
                        ></span>
                    </div>

                    <div class="mf-choices">
                        {#each served.problem.choices as choice (choice.id)}
                            <button
                                class="mf-choice"
                                type="button"
                                disabled={busy}
                                aria-label="Answer {choice.id}: {mathToPlainText(
                                    choice.text,
                                )}"
                                on:click={() => answerProbe(choice.id)}
                            >
                                <span class="mf-choice-key">{choice.id}</span>
                                <span class="mf-choice-text">
                                    <MathText text={mathToMarkup(choice.text)} />
                                </span>
                            </button>
                        {/each}
                    </div>

                    <Button
                        class="mf-dontknow"
                        variant="secondary"
                        disabled={busy}
                        on:click={() => answerProbe("dont-know")}
                    >
                        Don't know
                    </Button>
                </section>
            {:else}
                <section class="mf-card" aria-busy="true" aria-live="polite">
                    <p class="mf-eyebrow">Placement</p>
                    <div class="mf-generating-row">
                        <span class="mf-spinner" aria-hidden="true"></span>
                        <div>
                            <h1 class="mf-generating-title">Generating a problem</h1>
                            <p class="mf-generating-note">
                                Writing a fresh question and checking every choice
                                before it is shown.
                            </p>
                        </div>
                    </div>
                </section>
            {/if}
        {:else if phase === "summary"}
            <section class="mf-card">
                <p class="mf-eyebrow">Placement complete</p>
                <h1 class="mf-title">Your starting point</h1>
                {#if summaryRows.length}
                    <p class="mf-lede">
                        {#if knownCount}
                            {knownCount} of {summaryRows.length} topics look solid. We'll
                            skip re-teaching those and start you where the work actually is.
                        {:else}
                            We'll start you at the foundations and build up from there.
                        {/if}
                    </p>
                    <ul class="mf-summary">
                        {#each summaryRows as row (row.id)}
                            <li>
                                <span class="mf-summary-topic">
                                    <MathText text={row.title} />
                                </span>
                                <span class="mf-pill mf-pill-{row.verdict}">
                                    {verdictCopy[row.verdict]}
                                </span>
                            </li>
                        {/each}
                    </ul>
                {:else}
                    <p class="mf-lede">
                        No courses selected. We'll start you at the foundations.
                    </p>
                {/if}
                <p class="mf-note">
                    Readiness stays in mapping until you've done enough cold reviews.
                    Placement sets your starting point, it does not hand out a score.
                </p>
                <div class="mf-actions">
                    <Button
                        ariaLabel="Finish onboarding and open Manifold"
                        on:click={finish}
                    >
                        Go to Manifold
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
                </div>
            </section>
        {:else if phase === "applying"}
            <section class="mf-card">
                <p class="mf-eyebrow">Placement</p>
                <h1 class="mf-title">Saving your placement</h1>
                <div class="mf-bar" aria-hidden="true"><span></span></div>
            </section>
        {/if}
    </div>
</div>

<style lang="scss">
    .mf-page {
        min-height: 100vh;
        padding: var(--mf-space-7) var(--mf-space-6);
        overflow: clip;
    }

    .mf-shell {
        max-width: 760px;
        margin-inline: auto;
    }

    /* Masthead: identical to the session player's — wordmark with the amber
       highlighter sweep, actions pinned to the far end. */
    .mf-masthead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
    }

    .mf-masthead-end {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
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

    /* Card: the same calm surface, chunky ink outline and hard offset shadow the
       rest of the app uses for its panels. */
    .mf-card {
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
        display: grid;
        gap: var(--mf-space-4);
        animation: mf-pop-in 200ms var(--mf-ease-out);
    }

    .mf-eyebrow {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink-faint);
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
        max-width: 60ch;
        color: var(--mf-ink-muted);
    }

    /* Course selection: the same sticker-button grammar as the answer choices
       (bold ink outline, hard shadow, mechanical press). Selected fills amber. */
    .mf-course-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: var(--mf-space-3);
    }

    .mf-course {
        display: flex;
        align-items: center;
        gap: var(--mf-space-3);
        padding: var(--mf-space-3) var(--mf-space-4);
        border: var(--mf-outline-bold);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow);
        cursor: pointer;
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition);
    }

    .mf-course:hover {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: color-mix(in srgb, var(--mf-surface) 86%, var(--mf-ink));
    }

    .mf-course:active {
        transform: translate(4px, 4px);
        box-shadow: none;
    }

    .mf-course.is-on {
        background: var(--mf-secondary);
        color: var(--mf-secondary-ink);
    }

    .mf-course.is-on:hover {
        background: color-mix(in srgb, var(--mf-secondary) 88%, var(--mf-ink));
    }

    .mf-course input {
        position: absolute;
        opacity: 0;
        pointer-events: none;
    }

    /* The tick badge mirrors the choice key square. */
    .mf-course-check {
        flex: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
        color: transparent;
    }

    .mf-course.is-on .mf-course-check {
        background: var(--mf-surface);
        color: var(--mf-ink);
    }

    .mf-course-check svg {
        width: 16px;
        height: 16px;
        display: block;
    }

    .mf-course-name {
        font-family: var(--mf-font-display);
        font-weight: 700;
        font-size: var(--mf-text-sm);
        line-height: 1.2;
    }

    .mf-course input:focus-visible + .mf-course-check {
        outline: 3px solid var(--mf-signal);
        outline-offset: 2px;
    }

    /* Actions group two shared Buttons, exactly like the session player's
       try-again / skip row. */
    .mf-actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
        margin-top: var(--mf-space-2);
    }

    /* Problem stem + choices: copied verbatim from the session player so a probe
       is visually indistinguishable from a real problem. */
    .mf-stem {
        font-size: var(--mf-text-lg);
        line-height: 1.5;
        color: var(--mf-ink);
    }

    /* First-problem generation state, mirroring the session player's spinner
       card so the exam is never blank while a live problem is being written. */
    .mf-generating-row {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
    }

    .mf-generating-title {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-lg);
        font-weight: 800;
        letter-spacing: -0.01em;
        color: var(--mf-ink);
    }

    .mf-generating-note {
        margin: var(--mf-space-1) 0 0;
        max-width: 48ch;
        font-size: var(--mf-text-base);
        line-height: 1.5;
        color: var(--mf-ink-muted);
    }

    /* A single deliberate spinner: a ring with one ink arc turning steadily. */
    .mf-spinner {
        flex: none;
        width: 34px;
        height: 34px;
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

    .mf-meta {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
    }

    .mf-count {
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-faint);
        font-variant-numeric: tabular-nums;
    }

    /* Small ink pill, the app's standard tag treatment (mirrors the session
       level pill and the readiness confidence pill). */
    .mf-pill {
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
        background: var(--mf-surface-sunken);
    }

    .mf-pill-known {
        background: color-mix(in srgb, var(--mf-quaternary) 34%, var(--mf-surface));
    }

    .mf-pill-shaky {
        background: color-mix(in srgb, var(--mf-secondary) 40%, var(--mf-surface));
    }

    .mf-pill-new {
        background: var(--mf-surface-sunken);
        color: var(--mf-ink-muted);
    }

    .mf-progress {
        height: 12px;
        border: var(--mf-outline);
        background: var(--mf-surface-sunken);
        overflow: hidden;
    }

    .mf-progress span {
        display: block;
        height: 100%;
        background: var(--mf-signal);
        transition: width var(--mf-transition);
    }

    .mf-choices {
        display: grid;
        gap: var(--mf-space-3);
    }

    .mf-choice {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
        width: 100%;
        min-height: 56px;
        padding: var(--mf-space-3) var(--mf-space-4);
        border: var(--mf-outline-bold);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        color: var(--mf-ink);
        text-align: left;
        cursor: pointer;
        box-shadow: var(--mf-shadow);
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition);
    }

    /* Anki's global button reset drops transform from the transition; re-assert
       it (as the session player does) so the press eases. */
    .mf-choices .mf-choice {
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition) !important;
    }

    .mf-choice-key {
        display: flex;
        align-items: center;
        justify-content: center;
        flex: none;
        width: 36px;
        height: 36px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-md);
        font-weight: 800;
    }

    .mf-choice-text {
        flex: 1;
        font-size: var(--mf-text-md);
        line-height: 1.4;
    }

    .mf-choice:hover:not(:disabled) {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: color-mix(in srgb, var(--mf-surface) 86%, var(--mf-ink));
        border: var(--mf-outline-bold);
    }

    .mf-choice:active:not(:disabled) {
        transform: translate(4px, 4px);
        box-shadow: none;
        border: var(--mf-outline-bold);
    }

    .mf-choice:disabled {
        border: var(--mf-outline-bold);
    }

    :global(.mf-btn.mf-dontknow) {
        width: 100%;
        margin-top: var(--mf-space-1);
    }

    /* Summary: a plain readout list with the app's ink dividers; verdict as the
       standard ink pill. */
    .mf-summary {
        list-style: none;
        margin: 0;
        padding: 0;
        border: var(--mf-outline);
        box-shadow: var(--mf-shadow-active);
    }

    .mf-summary li {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: var(--mf-space-3);
        padding: var(--mf-space-3) var(--mf-space-4);
    }

    .mf-summary li + li {
        border-top: 2px solid var(--mf-ink);
    }

    .mf-summary-topic {
        font-weight: 600;
        color: var(--mf-ink);
    }

    .mf-note {
        margin: 0;
        max-width: 60ch;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-faint);
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

    /* Indeterminate progress sliver for the setup/apply waits. */
    .mf-bar {
        height: 12px;
        border: var(--mf-outline);
        background: var(--mf-surface-sunken);
        overflow: hidden;
    }

    .mf-bar span {
        display: block;
        height: 100%;
        width: 40%;
        background: var(--mf-signal);
        animation: mf-slide 1.1s var(--mf-ease-out) infinite;
    }

    @keyframes mf-slide {
        from {
            transform: translateX(-100%);
        }
        to {
            transform: translateX(300%);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-course:hover,
        .mf-course:active,
        .mf-choice:hover:not(:disabled),
        .mf-choice:active:not(:disabled) {
            transform: none;
        }

        .mf-spinner {
            animation-duration: 2.4s;
        }
    }

    @media (max-width: 560px) {
        .mf-course-grid {
            grid-template-columns: 1fr;
        }
    }
</style>

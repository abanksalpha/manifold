<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The main page. It opens on the day's action (start a session, and the single
topic worth studying next), then reads out the full readiness dashboard inline:
the three honest scores, the prerequisite graph, and a panel that
reads out whichever topic is selected. One topic is selected on load, the one
worth studying next, so the map opens on an answer rather than a blank panel.
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import Button from "$lib/manifold/Button.svelte";
    import Dag from "$lib/manifold/Dag.svelte";
    import { studyNextWithinPrereqs, type TopicNode } from "$lib/manifold/graph";
    import Legend from "$lib/manifold/Legend.svelte";
    import MathText from "$lib/manifold/MathText.svelte";
    import Metric from "$lib/manifold/Metric.svelte";
    import {
        computeScores,
        type Readiness,
        selectStudyNext,
    } from "$lib/manifold/scoring";
    import { PROBLEMS_ARE_PLACEHOLDER } from "$lib/manifold/session";
    import TopicPanel from "$lib/manifold/TopicPanel.svelte";

    import type { PageData } from "./$types";

    export let data: PageData;

    $: nodes = data.nodes as TopicNode[];
    $: scores = computeScores(nodes, data.scoringConfig);
    $: memory = scores.memory;
    $: performance = scores.performance;
    $: readiness = scores.readiness;
    $: byId = new Map(nodes.map((node) => [node.id, node]));

    // Card counts by teaching (scaffolding) level — competence-driven, not
    // CardType — summed across the graph, for the mastery-progression readout.
    // "new" is a reserved word, hence `nw`.
    $: levelTotals = nodes.reduce(
        (acc, node) => ({
            nw: acc.nw + node.levelNew,
            guided: acc.guided + node.levelGuided,
            independent: acc.independent + node.levelIndependent,
            revisited: acc.revisited + node.levelRevisited,
        }),
        { nw: 0, guided: 0, independent: 0, revisited: 0 },
    );
    $: levelSum =
        levelTotals.nw +
        levelTotals.guided +
        levelTotals.independent +
        levelTotals.revisited;

    $: memoryEvidence = memory ? memory.contributingTopics / memory.totalTopics : 0;
    $: performanceEvidence = performance
        ? performance.contributingTopics / performance.totalTopics
        : 0;

    $: studyNext = readiness.state === "abstaining" ? readiness.studyNext : null;

    let selectedId: string | null = null;
    // Open the map on the topic worth studying next; fall back to the first topic
    // so the panel is never empty. Re-resolve only while nothing has been picked.
    $: if (selectedId === null || !byId.has(selectedId)) {
        selectedId = selectStudyNext(nodes)?.id ?? nodes[0].id;
    }
    $: selectedTopic = selectedId ? (byId.get(selectedId) ?? null) : null;
    $: advice = selectedTopic ? studyNextWithinPrereqs(selectedTopic, byId) : null;

    const memorySymbolTex = "\\bar{R}";
    const performanceSymbolTex = "\\hat{p}";

    type Abstaining = Extract<Readiness, { state: "abstaining" }>;

    function abstainNote(r: Abstaining): string {
        const parts: string[] = [];
        if (r.reviewsNeeded > 0) {
            parts.push(`${r.reviewsNeeded} more independent reviews`);
        }
        if (r.coverageNeeded > 0) {
            parts.push(`${Math.ceil(r.coverageNeeded * 100)}% more coverage`);
        }
        return parts.length ? `Held until ${parts.join(" and ")}.` : "Held.";
    }

    function memoryCaption(): string {
        if (!memory) {
            return "No authored skills in the collection yet.";
        }
        return `Weighted mean recall across ${memory.contributingTopics} of ${memory.totalTopics} topics.`;
    }

    function performanceCaption(): string {
        if (!performance) {
            return "Waits on independent attempts at graduated skills.";
        }
        return `Unsupported accuracy across ${performance.contributingTopics} of ${performance.totalTopics} topics.`;
    }

    function onSelect(event: CustomEvent<string>): void {
        selectedId = event.detail;
    }
</script>

<div class="manifold mf-page">
    <div class="mf-shell">
        <div class="mf-hero">
            <div class="mf-hero-inner">
                <header class="mf-masthead">
                    <h1 class="mf-wordmark">Manifold</h1>
                </header>

                <section
                    class="mf-today"
                    style="--label-accent: var(--mf-accent)"
                    aria-labelledby="mf-today-label"
                >
                    <h2 id="mf-today-label" class="mf-section-label">Today</h2>
                    <div class="mf-today-body">
                        <Button
                            href="/manifold-session"
                            ariaLabel="Start a study session"
                        >
                            Start session
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
                        {#if readiness.state === "abstaining"}
                            <p class="mf-nextup">
                                <span class="mf-nextup-dot" aria-hidden="true"></span>
                                {#if studyNext}
                                    Next up: <strong>
                                        <MathText text={studyNext.title} />
                                    </strong>
                                {:else}
                                    No topics are open to study yet.
                                {/if}
                            </p>
                        {/if}
                    </div>
                </section>
            </div>
        </div>

        <section
            class="mf-measurements"
            style="--label-accent: var(--mf-secondary)"
            aria-labelledby="mf-measure-label"
        >
            <h2 id="mf-measure-label" class="mf-section-label">Measurements</h2>
            <div class="mf-score">
                <Metric
                    label="Memory"
                    symbolTex={memorySymbolTex}
                    symbolLabel="mean recall R"
                    value={memory ? memory.value : null}
                    low={memory ? memory.low : null}
                    high={memory ? memory.high : null}
                    evidence={memoryEvidence}
                    accent="var(--mf-accent)"
                    caption={memoryCaption()}
                />
                <Metric
                    label="Performance"
                    symbolTex={performanceSymbolTex}
                    symbolLabel="estimated accuracy"
                    value={performance ? performance.value : null}
                    low={performance ? performance.low : null}
                    high={performance ? performance.high : null}
                    evidence={performanceEvidence}
                    accent="var(--mf-secondary)"
                    caption={performanceCaption()}
                />
                <div
                    class="mf-readiness-cell"
                    class:is-projected={readiness.state === "projected"}
                >
                    <div class="mf-rc-head">
                        <span class="mf-rc-mark" aria-hidden="true"></span>
                        <span class="mf-rc-label">Readiness</span>
                    </div>
                    {#if readiness.state === "projected"}
                        <span class="mf-rc-range">
                            {readiness.scaledLow}
                            <span class="mf-rc-dash" aria-hidden="true">–</span>
                            {readiness.scaledHigh}
                        </span>
                        <p class="mf-rc-note">
                            Point {readiness.scaledPoint} · {readiness.confidence}
                            confidence · {Math.round(readiness.coverage * 100)}% covered{#if readiness.drivers.length}
                                · driver: {readiness.drivers[0].title}{/if}
                        </p>
                        {#if PROBLEMS_ARE_PLACEHOLDER}
                            <p class="mf-rc-placeholder">
                                Estimate from placeholder problems, not a validated
                                score yet.
                            </p>
                        {/if}
                    {:else}
                        <span class="mf-rc-state">Abstaining</span>
                        <p class="mf-rc-note">{abstainNote(readiness)}</p>
                    {/if}
                </div>
            </div>
        </section>

        <section
            class="mf-levels"
            style="--label-accent: var(--mf-quaternary)"
            aria-labelledby="mf-levels-label"
        >
            <h2 id="mf-levels-label" class="mf-section-label">Levels</h2>
            {#if levelSum > 0}
                <div
                    class="mf-levelbar"
                    role="img"
                    aria-label="{levelTotals.nw} New, {levelTotals.guided} Guided, {levelTotals.independent} Independent, {levelTotals.revisited} Revisit"
                >
                    {#if levelTotals.revisited}
                        <span
                            class="mf-lv mf-lv-revisited"
                            style="flex: {levelTotals.revisited}"
                        ></span>
                    {/if}
                    {#if levelTotals.independent}
                        <span
                            class="mf-lv mf-lv-independent"
                            style="flex: {levelTotals.independent}"
                        ></span>
                    {/if}
                    {#if levelTotals.guided}
                        <span
                            class="mf-lv mf-lv-guided"
                            style="flex: {levelTotals.guided}"
                        ></span>
                    {/if}
                    {#if levelTotals.nw}
                        <span
                            class="mf-lv mf-lv-new"
                            style="flex: {levelTotals.nw}"
                        ></span>
                    {/if}
                </div>
                <ul class="mf-level-legend">
                    <li>
                        <span class="mf-lv-dot mf-lv-new" aria-hidden="true"></span>
                        New
                        <b>{levelTotals.nw}</b>
                    </li>
                    <li>
                        <span class="mf-lv-dot mf-lv-guided" aria-hidden="true"></span>
                        Guided
                        <b>{levelTotals.guided}</b>
                    </li>
                    <li>
                        <span
                            class="mf-lv-dot mf-lv-independent"
                            aria-hidden="true"
                        ></span>
                        Independent
                        <b>{levelTotals.independent}</b>
                    </li>
                    <li>
                        <span
                            class="mf-lv-dot mf-lv-revisited"
                            aria-hidden="true"
                        ></span>
                        Revisit
                        <b>{levelTotals.revisited}</b>
                    </li>
                </ul>
            {:else}
                <p class="mf-levels-empty">No skill cards in the collection yet.</p>
            {/if}
        </section>

        <section
            class="mf-map"
            style="--label-accent: var(--mf-tertiary)"
            aria-labelledby="mf-map-label"
        >
            <h2 id="mf-map-label" class="mf-section-label">Prerequisite map</h2>
            <div class="mf-board">
                <div class="mf-board-graph mf-dot-grid">
                    <Dag {nodes} {selectedId} on:select={onSelect} />
                    <Legend />
                </div>
                <div class="mf-board-side">
                    {#if selectedTopic && advice}
                        <TopicPanel topic={selectedTopic} {advice} />
                    {/if}
                </div>
            </div>
        </section>
    </div>
</div>

<style lang="scss">
    .mf-page {
        min-height: 100vh;
        padding: var(--mf-space-7) var(--mf-space-6);
        /* keep any shape that pokes past the viewport edge from adding scroll */
        overflow: clip;
    }

    .mf-shell {
        max-width: 1280px;
        margin-inline: auto;
    }

    .mf-masthead {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: var(--mf-space-3);
    }

    .mf-wordmark {
        position: relative;
        margin: 0;
        width: fit-content;
        font-family: var(--mf-font-display);
        font-size: var(--mf-display);
        font-weight: 800;
        line-height: 0.9;
        letter-spacing: -0.03em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    /* a chunky yellow highlighter swept under the wordmark, above the confetti
     * but behind the letters, so the name stays legible. Sized in em so it
     * tracks the clamped display size. */
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

    .mf-today {
        margin-top: var(--mf-space-6);
    }

    .mf-section-label {
        display: inline-flex;
        align-items: center;
        gap: var(--mf-space-2);
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    /* a rotated sticker square keys each section to a palette colour */
    .mf-section-label::before {
        content: "";
        width: 12px;
        height: 12px;
        background: var(--label-accent, var(--mf-accent));
        border: 2px solid var(--mf-ink);
        transform: rotate(-8deg);
    }

    .mf-today-body {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: var(--mf-space-4);
        margin-top: var(--mf-space-3);
    }

    .mf-nextup {
        margin: 0;
        font-size: var(--mf-text-base);
        color: var(--mf-ink-muted);
    }

    /* a small sticker dot marks the "next up" nudge (chrome, not a reading) */
    .mf-nextup-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        margin-right: var(--mf-space-2);
        border-radius: var(--mf-radius-full);
        background: var(--mf-quaternary);
        border: 2px solid var(--mf-ink);
        vertical-align: middle;
    }

    .mf-nextup strong {
        color: var(--mf-ink);
        font-weight: 700;
    }

    .mf-measurements {
        margin-top: var(--mf-space-7);
    }

    .mf-score {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--mf-space-5);
        margin-top: var(--mf-space-4);
    }

    /* The readiness cell shares the Metric sticker frame, but its reading stays
     * honest: no confetti accent, a grey header mark, and the withheld state and
     * note in calm slate rather than an alarm colour. */
    .mf-readiness-cell {
        display: grid;
        gap: var(--mf-space-3);
        align-content: start;
        padding: var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    .mf-rc-head {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        min-height: 20px;
    }

    /* the withheld-reading marker stays a plain grey square: no rotation, no pop
     * colour, so it reads as "no answer yet" rather than a cheerful sticker */
    .mf-rc-mark {
        flex: none;
        width: 16px;
        height: 16px;
        border-radius: 0;
        background: var(--mf-abstain);
        border: 2.5px solid var(--mf-ink);
    }

    .mf-rc-label {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-rc-state {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-lg);
        font-weight: 700;
        line-height: 1.1;
        color: var(--mf-abstain);
    }

    .mf-rc-note {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
        max-width: 34ch;
    }

    /* Once Readiness can speak, it is a real answer: the marker takes the mastery
     * signal colour and the reading is drawn in ink, not the grey abstain slate. */
    .mf-readiness-cell.is-projected .mf-rc-mark {
        background: var(--mf-signal);
    }

    .mf-rc-range {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-2xl);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.01em;
        color: var(--mf-ink);
    }

    .mf-rc-dash {
        margin: 0 0.15em;
        color: var(--mf-ink-faint);
    }

    /* The honesty flag: this estimate rides on placeholder problems until real
     * generated items exist, so it is never presented as a validated score. */
    .mf-rc-placeholder {
        margin: 0;
        font-size: var(--mf-text-xs);
        line-height: 1.4;
        color: var(--mf-ink-faint);
        max-width: 34ch;
    }

    .mf-levels {
        margin-top: var(--mf-space-7);
    }

    /* A single stacked bar of the collection's cards by teaching level, so the
     * mastery progression from New to Independent is legible at a glance. */
    .mf-levelbar {
        display: flex;
        height: 20px;
        margin-top: var(--mf-space-4);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-full);
        overflow: clip;
        box-shadow: var(--mf-shadow);
    }

    .mf-lv {
        display: block;
        min-width: 3px;
    }

    /* A card not yet attempted stays grey; Guided and Revisited take warm working
     * colours; Independent (the goal) takes the mastery signal. */
    .mf-lv-new {
        background: var(--mf-abstain);
    }

    .mf-lv-guided {
        background: var(--mf-quaternary);
    }

    .mf-lv-independent {
        background: var(--mf-signal);
    }

    .mf-lv-revisited {
        background: var(--mf-accent);
    }

    .mf-level-legend {
        display: flex;
        flex-wrap: wrap;
        gap: var(--mf-space-2) var(--mf-space-5);
        margin: var(--mf-space-3) 0 0;
        padding: 0;
        list-style: none;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
    }

    .mf-level-legend li {
        display: inline-flex;
        align-items: center;
        gap: var(--mf-space-2);
    }

    .mf-level-legend b {
        color: var(--mf-ink);
        font-weight: 700;
    }

    .mf-lv-dot {
        width: 12px;
        height: 12px;
        border: 2px solid var(--mf-ink);
        transform: rotate(-8deg);
    }

    .mf-levels-empty {
        margin: var(--mf-space-3) 0 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
    }

    .mf-map {
        margin-top: var(--mf-space-7);
    }

    /* One column: the graph card and the readout panel each span the shell, so
     * every block on the page shares the same left and right margin. The graph
     * itself centres inside its card (see .mf-graph-inner). */
    .mf-board {
        display: grid;
        gap: var(--mf-space-6);
        margin-top: var(--mf-space-4);
    }

    /* The graph rides in a big sticker card with a faint dot grid behind it for a
     * graph-paper feel; the card stays --mf-surface so the node label halos keep
     * masking the edges. background-color is a longhand so the dot-grid utility's
     * background-image is not clobbered. */
    .mf-board-graph {
        display: grid;
        gap: var(--mf-space-5);
        padding: var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background-color: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    @media (max-width: 900px) {
        .mf-score {
            grid-template-columns: 1fr 1fr;
        }
    }

    @media (max-width: 480px) {
        .mf-score {
            grid-template-columns: 1fr;
        }
    }
</style>

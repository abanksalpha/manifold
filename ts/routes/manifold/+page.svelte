<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The main page. It opens on the day's action (start a session), then reads out the
full readiness dashboard inline: the two measured inputs (memory, performance),
the readiness instrument that projects them onto the ETS scale, the prerequisite
graph, and a panel that reads out whichever topic is selected. One topic is
selected on load, the one worth studying next, so the map opens on an answer
rather than a blank panel.

Readiness is never a bare number. Above the give-up line it shows the projected
scaled range and point, how sure it is, how much of the exam it covers, when it
was read, what is dragging it down, a target ladder with the logarithmic hours to
each rung, and the maturity residue it refuses to promise past. Below the line it
shows the missing evidence and the topic to study next, never a score. Every
value here is read from scoring.ts; this page renders, it does not compute.
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import { onMount } from "svelte";

    import { goto } from "$app/navigation";
    import Button from "$lib/manifold/Button.svelte";
    import Dag from "$lib/manifold/Dag.svelte";
    import { currentManifoldUser } from "$lib/manifold/firebase";
    import Formula from "$lib/manifold/Formula.svelte";
    import { studyNextWithinPrereqs, type TopicNode } from "$lib/manifold/graph";
    import Legend from "$lib/manifold/Legend.svelte";
    import MathText from "$lib/manifold/MathText.svelte";
    import Meter from "$lib/manifold/Meter.svelte";
    import Metric from "$lib/manifold/Metric.svelte";
    import { claimAccount, fetchPlacementState } from "$lib/manifold/placement";
    import {
        computeScores,
        READINESS_MIN_COVERAGE,
        READINESS_MIN_INDEPENDENT_REVIEWS,
        selectStudyNext,
    } from "$lib/manifold/scoring";
    import { prewarmSession, PROBLEMS_ARE_PLACEHOLDER } from "$lib/manifold/session";
    import SyncChip from "$lib/manifold/SyncChip.svelte";
    import SyncPanel from "$lib/manifold/SyncPanel.svelte";
    import TopicPanel from "$lib/manifold/TopicPanel.svelte";

    import type { PageData } from "./$types";

    export let data: PageData;

    $: nodes = data.nodes as TopicNode[];
    $: config = data.scoringConfig;
    $: scores = computeScores(nodes, config);
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

    // Narrow the readiness union once, so the template reads either the projected
    // instrument or the abstain state without re-checking the tag each time.
    $: projected = readiness.state === "projected" ? readiness : null;
    $: abstaining = readiness.state === "abstaining" ? readiness : null;
    $: studyNext = abstaining ? abstaining.studyNext : null;

    // The target ladder rung the projection is read against (D29/D30). Default to
    // the evolved goal, the top-decile "strong" band, not the median; kept valid
    // if the ladder ever changes shape rather than guessing a missing rung.
    let selectedTargetId = "strong";
    $: if (projected && !projected.targets.some((t) => t.id === selectedTargetId)) {
        selectedTargetId = projected.targets[0].id;
    }
    $: selectedTarget =
        projected?.targets.find((t) => t.id === selectedTargetId) ?? null;

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
    const readinessSymbolTex = "\\hat{s}";

    const updatedFormat = new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    });
    function formatUpdated(ms: number): string {
        return updatedFormat.format(new Date(ms));
    }
    function isoStamp(ms: number): string {
        return new Date(ms).toISOString();
    }
    function asPercent(fraction: number): number {
        return Math.round(fraction * 100);
    }
    // Whole hours once the estimate is coarse, one decimal while it is small, so a
    // short target does not round away to a misleading zero.
    function formatHours(hours: number): string {
        if (hours <= 0) {
            return "0";
        }
        return hours < 10 ? hours.toFixed(1) : String(Math.round(hours));
    }
    // Position of a scaled score on the axis (scaleMin..scaleMax), as a percent.
    function scalePercent(scaled: number): number {
        return ((scaled - config.scaleMin) / (config.scaleMax - config.scaleMin)) * 100;
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

    // Placement is gated locally, but bound to the signed-in Google account.
    // First we claim the collection for this account: if a DIFFERENT account
    // signs in on this device, the engine wipes the local Manifold deck and
    // clears onboarding, so this fresh account is routed to placement rather than
    // inheriting the previous account's progress. Then the local onboarding flag
    // (synced by Anki's own protocol across the account's devices) decides the
    // gate. Firebase gates *login* (the root layout), not placement. An overlay
    // covers the page until the check resolves so no stale data flashes; a
    // genuine backend failure surfaces rather than silently showing the dashboard.
    let checkingOnboarding = true;
    let onboardingError: string | null = null;

    onMount(async () => {
        try {
            const user = currentManifoldUser();
            if (user && (await claimAccount(user.uid))) {
                // A different Google account signed in: local progress was reset,
                // so start this account at placement.
                await goto("/manifold-onboarding");
                return;
            }
            if (!(await fetchPlacementState())) {
                await goto("/manifold-onboarding");
                return;
            }
        } catch (e) {
            onboardingError = e instanceof Error ? e.message : String(e);
            return;
        }
        checkingOnboarding = false;
        // Start generating the first session problem now, so a template-less
        // leading skill's live generation overlaps the time spent here instead of
        // stalling the session's first screen when "Start session" is pressed.
        prewarmSession();
    });
</script>

<div class="manifold mf-page">
    <div class="mf-shell">
        <div class="mf-hero">
            <div class="mf-hero-inner">
                <header class="mf-masthead">
                    <h1 class="mf-wordmark">Manifold</h1>
                    <SyncChip />
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
                        <Button
                            href="/manifold-onboarding"
                            variant="secondary"
                            ariaLabel="Retake the placement"
                        >
                            Retake placement
                        </Button>
                    </div>
                </section>

                <SyncPanel />
            </div>
        </div>

        <section
            class="mf-measurements"
            style="--label-accent: var(--mf-secondary)"
            aria-labelledby="mf-measure-label"
        >
            <h2 id="mf-measure-label" class="mf-section-label">Measurements</h2>

            <!-- The two measured inputs sit together; readiness is the projection
                 drawn from them, so it takes its own wider instrument below. -->
            <div class="mf-inputs">
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
            </div>

            <div class="mf-readiness" class:is-projected={projected !== null}>
                <div class="mf-rc-head">
                    <span class="mf-rc-mark" aria-hidden="true"></span>
                    <span class="mf-rc-label">Readiness</span>
                    <span class="mf-rc-symbol">
                        <Formula
                            tex={readinessSymbolTex}
                            label="projected scaled score"
                            fontSize={13}
                        />
                    </span>
                    {#if projected}
                        <span
                            class="mf-rc-conf"
                            class:mf-rc-conf-confident={projected.confidence ===
                                "confident"}
                        >
                            {projected.confidence}
                        </span>
                    {:else}
                        <span class="mf-rc-state">Abstaining</span>
                    {/if}
                    <time
                        class="mf-rc-updated"
                        datetime={isoStamp(readiness.lastUpdated)}
                    >
                        Updated {formatUpdated(readiness.lastUpdated)}
                    </time>
                </div>

                {#if projected}
                    <div class="mf-rc-reading">
                        <span
                            class="mf-rc-range"
                            aria-label="projected {projected.scaledLow} to {projected.scaledHigh}"
                        >
                            {projected.scaledLow}
                            <span class="mf-rc-dash" aria-hidden="true">–</span>
                            {projected.scaledHigh}
                        </span>
                        <span class="mf-rc-point">point {projected.scaledPoint}</span>
                    </div>

                    <div
                        class="mf-gauge"
                        style="--conf: {projected.confidence === 'confident' ? 1 : 0.5}"
                        role="img"
                        aria-label="Projected {projected.scaledLow} to {projected.scaledHigh}, point {projected.scaledPoint}, on the {config.scaleMin} to {config.scaleMax} scale"
                    >
                        <div class="mf-gauge-track">
                            <div
                                class="mf-gauge-residue"
                                style="left: {scalePercent(
                                    projected.residue.promisedCeiling,
                                )}%"
                            ></div>
                            <div
                                class="mf-gauge-band"
                                style="left: {scalePercent(
                                    projected.scaledLow,
                                )}%; width: {Math.max(
                                    0.8,
                                    scalePercent(projected.scaledHigh) -
                                        scalePercent(projected.scaledLow),
                                )}%"
                            ></div>
                            <div
                                class="mf-gauge-point"
                                style="left: {scalePercent(projected.scaledPoint)}%"
                            ></div>
                            {#each projected.targets as t (t.id)}
                                <div
                                    class="mf-gauge-target"
                                    class:is-active={t.id === selectedTargetId}
                                    style="left: {scalePercent(t.scaledPoint)}%"
                                ></div>
                            {/each}
                        </div>
                        <div class="mf-gauge-scale" aria-hidden="true">
                            <span>{config.scaleMin}</span>
                            <span>{config.scaleMax}</span>
                        </div>
                    </div>

                    <dl class="mf-rc-facts">
                        <div class="mf-rc-fact">
                            <dt>Covered</dt>
                            <dd>{asPercent(projected.coverage)}% of the exam</dd>
                        </div>
                        <div class="mf-rc-fact">
                            <dt>Evidence</dt>
                            <dd>{projected.independentReviews} independent reviews</dd>
                        </div>
                    </dl>

                    {#if projected.drivers.length}
                        <p class="mf-rc-drivers">
                            Held back by{#each projected.drivers as d, i (d.id)}{i > 0
                                    ? ", "
                                    : " "}<MathText text={d.title} /> ({asPercent(
                                    d.performance,
                                )}%){/each}.
                        </p>
                    {/if}

                    {#if projected.lapseRate > 0}
                        <p class="mf-rc-lapse">
                            {asPercent(projected.lapseRate)}% of graduated cards have
                            lapsed, widening the range.
                        </p>
                    {/if}

                    <div class="mf-rc-ladder">
                        <div class="mf-target-select" role="group" aria-label="Target">
                            {#each projected.targets as t (t.id)}
                                <button
                                    type="button"
                                    class="mf-target-btn"
                                    class:is-active={t.id === selectedTargetId}
                                    aria-pressed={t.id === selectedTargetId}
                                    on:click={() => (selectedTargetId = t.id)}
                                >
                                    <span class="mf-target-name">{t.label}</span>
                                    <span class="mf-target-band">
                                        {t.scaledLow}–{t.scaledHigh}
                                    </span>
                                </button>
                            {/each}
                        </div>

                        {#if selectedTarget}
                            <p class="mf-target-detail">
                                {#if selectedTarget.reached}
                                    {selectedTarget.label} reached. The projection sits at
                                    or above {selectedTarget.scaledPoint}.
                                {:else}
                                    {selectedTarget.gapPoints} scaled points to
                                    {selectedTarget.label}, about
                                    {formatHours(selectedTarget.hoursToTarget)} h of focused
                                    practice on the logarithmic effort curve.
                                {/if}
                            </p>
                        {/if}
                    </div>

                    <p class="mf-rc-residue">
                        Capped at {projected.residue.promisedCeiling}. The top
                        {projected.residue.scaledPoints} scaled points ({projected
                            .residue.items} deep-proof items) are not promised.
                    </p>

                    {#if PROBLEMS_ARE_PLACEHOLDER}
                        <p class="mf-rc-placeholder">
                            Estimate from placeholder problems, not a validated score
                            yet.
                        </p>
                    {/if}
                {:else if abstaining}
                    <p class="mf-rc-lead">Not enough evidence to project a score.</p>

                    <div class="mf-gate">
                        <div class="mf-gate-row">
                            <div class="mf-gate-head">
                                <span class="mf-gate-label">Independent reviews</span>
                                <span class="mf-gate-count">
                                    {abstaining.independentReviews} / {READINESS_MIN_INDEPENDENT_REVIEWS}
                                </span>
                            </div>
                            <Meter
                                value={Math.min(
                                    1,
                                    abstaining.independentReviews /
                                        READINESS_MIN_INDEPENDENT_REVIEWS,
                                )}
                                evidence={Math.min(
                                    1,
                                    abstaining.independentReviews /
                                        READINESS_MIN_INDEPENDENT_REVIEWS,
                                )}
                                showRange={false}
                                label="independent reviews, {abstaining.independentReviews} of {READINESS_MIN_INDEPENDENT_REVIEWS}"
                            />
                        </div>
                        <div class="mf-gate-row">
                            <div class="mf-gate-head">
                                <span class="mf-gate-label">Coverage</span>
                                <span class="mf-gate-count">
                                    {asPercent(abstaining.coverage)}% / {asPercent(
                                        READINESS_MIN_COVERAGE,
                                    )}%
                                </span>
                            </div>
                            <Meter
                                value={Math.min(
                                    1,
                                    abstaining.coverage / READINESS_MIN_COVERAGE,
                                )}
                                evidence={Math.min(
                                    1,
                                    abstaining.coverage / READINESS_MIN_COVERAGE,
                                )}
                                showRange={false}
                                label="coverage, {asPercent(
                                    abstaining.coverage,
                                )} percent of the {asPercent(
                                    READINESS_MIN_COVERAGE,
                                )} percent needed"
                            />
                        </div>
                    </div>

                    <p class="mf-rc-next">
                        {#if studyNext}
                            Study <strong><MathText text={studyNext.title} /></strong>
                            next to close the gap.
                        {:else}
                            No topics are open to study yet.
                        {/if}
                    </p>
                {/if}
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

{#if checkingOnboarding}
    <div class="manifold mf-gate-cover" aria-live="polite">
        {#if onboardingError}
            <p class="mf-gate-cover-error">
                Couldn't reach your account: {onboardingError}
            </p>
        {:else}
            <span class="mf-gate-cover-spinner" aria-hidden="true"></span>
        {/if}
    </div>
{/if}

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

    /* Covers the dashboard while the Google-account onboarding check runs, so the
       returning-vs-new decision resolves before any local data is shown. */
    .mf-gate-cover {
        position: fixed;
        inset: 0;
        z-index: 50;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: var(--mf-space-6);
        background: var(--mf-bg);
    }

    .mf-gate-cover-spinner {
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

    .mf-gate-cover-error {
        margin: 0;
        max-width: 52ch;
        padding: var(--mf-space-3) var(--mf-space-4);
        border: 2px solid var(--mf-accent);
        border-radius: var(--mf-radius);
        font-size: var(--mf-text-sm);
        color: var(--mf-ink);
        background: color-mix(in srgb, var(--mf-accent) 12%, var(--mf-surface));
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-gate-cover-spinner {
            animation-duration: 2.4s;
        }
    }

    .mf-masthead {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
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

    .mf-measurements {
        margin-top: var(--mf-space-7);
    }

    /* The two measured inputs, side by side; they collapse to one column before
     * the readiness instrument does, since each is a compact single reading. */
    .mf-inputs {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--mf-space-5);
        margin-top: var(--mf-space-4);
    }

    /* The readiness instrument: same sticker frame as a Metric, but roomier,
     * because it carries the projection, the target ladder and the honest
     * caveats rather than a single reading. Saturated colour is spent only on
     * the confidence and coverage signals inside it; the frame stays ink. */
    .mf-readiness {
        display: grid;
        gap: var(--mf-space-4);
        align-content: start;
        margin-top: var(--mf-space-5);
        padding: var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    .mf-rc-head {
        display: flex;
        align-items: center;
        gap: var(--mf-space-3);
        min-height: 20px;
    }

    /* the reading marker: a plain grey square while abstaining ("no answer yet"),
     * taking the measured signal colour once a projection exists. */
    .mf-rc-mark {
        flex: none;
        width: 16px;
        height: 16px;
        border-radius: 0;
        background: var(--mf-abstain);
        border: 2.5px solid var(--mf-ink);
    }

    .mf-readiness.is-projected .mf-rc-mark {
        background: var(--mf-signal);
    }

    .mf-rc-label {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-rc-symbol {
        display: inline-flex;
        align-items: center;
        opacity: 0.85;
    }

    /* status sits after the label; the timestamp is pushed to the far edge so the
     * "when" always lands in the same place across both states. */
    .mf-rc-state {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-sm);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-abstain);
    }

    /* confidence as an outlined pill: provisional stays quiet, confident earns
     * the measured signal fill (a how-sure signal, so it may carry colour). */
    .mf-rc-conf {
        padding: 2px 10px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
        background: var(--mf-surface);
    }

    .mf-rc-conf-confident {
        color: var(--mf-accent-ink);
        background: color-mix(in srgb, var(--mf-signal) 30%, var(--mf-surface));
    }

    .mf-rc-updated {
        margin-left: auto;
        font-size: var(--mf-text-xs);
        color: var(--mf-ink-faint);
        white-space: nowrap;
    }

    /* the headline reading: the range in the big display face, the point beside
     * it in plain type so the range leads and the point supports it. */
    .mf-rc-reading {
        display: flex;
        align-items: baseline;
        gap: var(--mf-space-3);
        flex-wrap: wrap;
    }

    .mf-rc-range {
        font-family: var(--mf-font-display);
        font-size: var(--mf-readout);
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.02em;
        color: var(--mf-ink);
        font-variant-numeric: tabular-nums;
    }

    .mf-rc-dash {
        margin: 0 0.12em;
        color: var(--mf-ink-faint);
    }

    .mf-rc-point {
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-md);
        font-weight: 600;
        color: var(--mf-ink-muted);
        font-variant-numeric: tabular-nums;
    }

    /* The scale instrument: the projected band and point drawn on the real
     * 200..990 axis, with the three targets ticked and the residue it will not
     * promise hatched off at the top. A gauge, not a progress bar. */
    .mf-gauge {
        display: grid;
        gap: var(--mf-space-2);
    }

    .mf-gauge-track {
        position: relative;
        height: 22px;
        border: var(--mf-border-width) solid var(--mf-ink);
        background: var(--mf-surface);
        overflow: hidden;
    }

    /* the maturity residue: a hatched dead zone from the promised ceiling to the
     * scale top, so the "not promised" region is visible, not implied. */
    .mf-gauge-residue {
        position: absolute;
        top: 0;
        bottom: 0;
        right: 0;
        background-image: repeating-linear-gradient(
            -45deg,
            var(--mf-abstain) 0,
            var(--mf-abstain) 2px,
            transparent 2px,
            transparent 7px
        );
        opacity: 0.5;
    }

    /* the projected band, its chroma scaled by confidence so a provisional
     * projection reads greyer than a confident one. */
    .mf-gauge-band {
        position: absolute;
        top: 0;
        bottom: 0;
        min-width: 3px;
        background: oklch(
            var(--mf-signal-l) calc(var(--mf-signal-c) * var(--conf, 1))
                var(--mf-signal-h)
        );
    }

    .mf-gauge-point {
        position: absolute;
        top: -2px;
        bottom: -2px;
        width: 3px;
        margin-left: -1.5px;
        background: var(--mf-ink);
    }

    /* target rungs: thin ink ticks; the selected rung grows and takes the action
     * colour, tying the gauge to the selector below it. */
    .mf-gauge-target {
        position: absolute;
        top: 3px;
        bottom: 3px;
        width: 2px;
        margin-left: -1px;
        background: var(--mf-ink);
        opacity: 0.45;
    }

    .mf-gauge-target.is-active {
        top: -2px;
        bottom: -2px;
        width: 3px;
        margin-left: -1.5px;
        background: var(--mf-accent);
        opacity: 1;
    }

    .mf-gauge-scale {
        display: flex;
        justify-content: space-between;
        font-size: var(--mf-text-xs);
        color: var(--mf-ink-faint);
        font-variant-numeric: tabular-nums;
    }

    /* the honest facts, in a two-up definition grid: coverage and the evidence
     * that cleared the give-up gate. */
    .mf-rc-facts {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: var(--mf-space-2) var(--mf-space-5);
        margin: 0;
    }

    .mf-rc-fact {
        display: grid;
        gap: 2px;
    }

    .mf-rc-fact dt {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-rc-fact dd {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink);
        font-variant-numeric: tabular-nums;
    }

    .mf-rc-drivers,
    .mf-rc-lapse {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
        max-width: 60ch;
    }

    .mf-rc-drivers :global(.mf-mathtext) {
        color: var(--mf-ink);
        font-weight: 600;
    }

    /* the target ladder: a segmented selector and the detail for the chosen rung,
     * inset so it reads as the controllable part of the instrument. */
    .mf-rc-ladder {
        display: grid;
        gap: var(--mf-space-3);
        padding: var(--mf-space-4);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
    }

    .mf-target-select {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: var(--mf-space-2);
    }

    .mf-target-btn {
        display: grid;
        gap: 2px;
        padding: var(--mf-space-2) var(--mf-space-3);
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        cursor: pointer;
        text-align: left;
        transition: background-color var(--mf-transition);
    }

    .mf-target-btn:hover {
        background: var(--mf-hover);
    }

    .mf-target-btn.is-active {
        background: var(--mf-accent);
        color: var(--mf-accent-ink);
    }

    .mf-target-name {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-sm);
        font-weight: 700;
        letter-spacing: 0.02em;
        color: inherit;
    }

    .mf-target-band {
        font-size: var(--mf-text-xs);
        color: inherit;
        opacity: 0.75;
        font-variant-numeric: tabular-nums;
    }

    .mf-target-detail {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink);
        font-variant-numeric: tabular-nums;
    }

    .mf-rc-residue {
        margin: 0;
        font-size: var(--mf-text-xs);
        line-height: 1.5;
        color: var(--mf-ink-faint);
        max-width: 60ch;
    }

    /* the honesty flag: this estimate rides on placeholder problems until real
     * generated items exist, so it is never presented as a validated score. */
    .mf-rc-placeholder {
        margin: 0;
        font-size: var(--mf-text-xs);
        line-height: 1.4;
        color: var(--mf-ink-faint);
        max-width: 60ch;
    }

    /* --- Abstaining state --- */

    .mf-rc-lead {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-lg);
        font-weight: 700;
        line-height: 1.15;
        color: var(--mf-ink);
    }

    /* the give-up gate made visible: two bars showing how close each condition is
     * to letting readiness speak, with the real counts alongside. */
    .mf-gate {
        display: grid;
        gap: var(--mf-space-4);
    }

    .mf-gate-row {
        display: grid;
        gap: var(--mf-space-2);
    }

    .mf-gate-head {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: var(--mf-space-3);
    }

    .mf-gate-label {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-gate-count {
        font-size: var(--mf-text-sm);
        color: var(--mf-ink);
        font-variant-numeric: tabular-nums;
    }

    .mf-rc-next {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
        max-width: 60ch;
    }

    .mf-rc-next strong {
        color: var(--mf-ink);
        font-weight: 700;
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
        .mf-inputs {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 560px) {
        .mf-target-select {
            grid-template-columns: 1fr;
        }

        .mf-rc-facts {
            grid-template-columns: 1fr;
        }
    }
</style>

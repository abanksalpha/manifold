<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The readout for one selected topic. Recall and performance get their own
meters; the rest of the engine numbers sit in a tight definition list. A
topic with no studied cards reports "not yet measured" rather than a hollow
zero, matching how the home page treats an unevidenced score. The note says what
to study next, read from the engine lock states, never recomputed.
-->
<script lang="ts">
    import Formula from "./Formula.svelte";
    import { percent } from "./format";
    import GlyphSwatch from "./GlyphSwatch.svelte";
    import { tierLabel, type PrereqAdvice, type TopicNode } from "./graph";
    import MathText from "./MathText.svelte";
    import Meter from "./Meter.svelte";

    export let topic: TopicNode;
    export let advice: PrereqAdvice;

    const recallTex = "\\bar{R}";
    const performanceTex = "\\hat{p}";
    const stabilityTex = "\\bar{S}";

    const lockLabels: Record<string, string> = {
        locked: "Locked",
        unlocked: "Unlocked",
        in_progress: "In progress",
        mastered: "Mastered",
    };

    $: studied = topic.avgStability > 0;
    $: gradedPerformance = topic.gradedReviews > 0;
    $: tierText = tierLabel(topic.tier);
    $: lockLabel = lockLabels[topic.lockState] ?? topic.lockState;
    $: blockedTarget = advice.kind === "blocked" ? advice.target : null;
</script>

<aside class="mf-panel" aria-live="polite">
    <header class="mf-panel-head">
        <GlyphSwatch
            class="mf-panel-glyph"
            tier={topic.tier}
            lockState={topic.lockState}
            size={28}
        />
        <div class="mf-panel-headtext">
            <h2 class="mf-panel-title"><MathText text={topic.title} /></h2>
            <span class="mf-panel-chip">{lockLabel}</span>
        </div>
    </header>

    <div class="mf-panel-meters">
        <div class="mf-pm">
            <div class="mf-pm-head">
                <span class="mf-pm-label">Memory</span>
                <span class="mf-pm-symbol">
                    <Formula tex={recallTex} label="mean recall R" fontSize={12} />
                </span>
                <span class="mf-pm-value" class:muted={!studied}>
                    {studied ? percent(topic.avgRecall) : "not yet measured"}
                </span>
            </div>
            <Meter
                value={topic.avgRecall}
                evidence={topic.coverage}
                showRange={false}
                unmeasured={!studied}
                label="topic recall"
            />
        </div>

        <div class="mf-pm">
            <div class="mf-pm-head">
                <span class="mf-pm-label">Performance</span>
                <span class="mf-pm-symbol">
                    <Formula
                        tex={performanceTex}
                        label="estimated accuracy"
                        fontSize={12}
                    />
                </span>
                <span class="mf-pm-value" class:muted={!gradedPerformance}>
                    {gradedPerformance
                        ? percent(topic.performance)
                        : "not yet measured"}
                </span>
            </div>
            <Meter
                value={topic.performance}
                evidence={topic.coverage}
                showRange={false}
                unmeasured={!gradedPerformance}
                label="topic performance"
            />
        </div>
    </div>

    <dl class="mf-stats">
        <div class="mf-stat">
            <dt class="mf-stat-key">Mastered</dt>
            <dd class="mf-stat-val">{topic.mastered} / {topic.total}</dd>
        </div>
        <div class="mf-stat">
            <dt class="mf-stat-key">
                Stability <span class="mf-stat-symbol">
                    <Formula
                        tex={stabilityTex}
                        label="mean stability S"
                        fontSize={11}
                    />
                </span>
            </dt>
            <dd class="mf-stat-val" class:muted={!studied}>
                {studied ? `${topic.avgStability.toFixed(1)} d` : "not yet measured"}
            </dd>
        </div>
        <div class="mf-stat">
            <dt class="mf-stat-key">Graded reviews</dt>
            <dd class="mf-stat-val">{topic.gradedReviews}</dd>
        </div>
        <div class="mf-stat">
            <dt class="mf-stat-key">Tier</dt>
            <dd class="mf-stat-val">{tierText}</dd>
        </div>
        <div class="mf-stat">
            <dt class="mf-stat-key">Blueprint weight</dt>
            <dd class="mf-stat-val">{topic.weight}</dd>
        </div>
    </dl>

    <p class="mf-panel-note">
        {#if advice.kind === "open"}
            Open to study now.
        {:else if advice.kind === "mastered"}
            Mastered. Reviews keep it from fading.
        {:else if blockedTarget}
            Locked. Study <strong>{blockedTarget.title}</strong>
            next to open it.
        {:else}
            Locked until its prerequisites are mastered.
        {/if}
    </p>
</aside>

<style lang="scss">
    .mf-panel {
        position: sticky;
        top: var(--mf-space-5);
        display: grid;
        gap: var(--mf-space-5);
        align-content: start;
        padding: var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    /* a colour-blocked card header: the head pulls out to the panel's inner
     * edges and is cut off by a hard ink rule. A soft yellow, for variety against
     * the map's violet (mastered/selected) and green (in progress). */
    .mf-panel-head {
        display: flex;
        align-items: flex-start;
        gap: var(--mf-space-3);
        margin: calc(-1 * var(--mf-space-5)) calc(-1 * var(--mf-space-5)) 0;
        padding: var(--mf-space-4) var(--mf-space-5);
        background: color-mix(in srgb, var(--mf-secondary) 72%, var(--mf-surface));
        border-bottom: var(--mf-outline);
    }

    .mf-panel-head :global(.mf-panel-glyph) {
        flex: none;
        margin-top: 1px;
    }

    .mf-panel-headtext {
        display: grid;
        gap: var(--mf-space-2);
    }

    .mf-panel-title {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-lg);
        font-weight: 700;
        line-height: 1.15;
        letter-spacing: -0.01em;
        color: var(--mf-ink);
    }

    /* lock state as a neutral outlined pill; a status label, not a reading */
    .mf-panel-chip {
        width: fit-content;
        padding: 3px 12px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-surface);
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-panel-meters {
        display: grid;
        gap: var(--mf-space-4);
    }

    .mf-pm {
        display: grid;
        gap: var(--mf-space-2);
    }

    .mf-pm-head {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
    }

    .mf-pm-label {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-pm-symbol {
        display: inline-flex;
        align-items: center;
        opacity: 0.85;
    }

    .mf-pm-value {
        margin-left: auto;
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-sm);
        font-variant-numeric: tabular-nums;
        color: var(--mf-ink);

        &.muted {
            font-family: var(--mf-font-sans);
            color: var(--mf-ink-faint);
        }
    }

    /* the secondary numbers sit in a hard-bordered inset block: tactile and
     * clearly framed, but with no shadow so it never reads as a nested card */
    .mf-stats {
        display: grid;
        gap: var(--mf-space-3);
        margin: 0;
        padding: var(--mf-space-4);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
    }

    .mf-stat {
        display: grid;
        grid-template-columns: 1fr auto;
        align-items: baseline;
        gap: var(--mf-space-4);
    }

    .mf-stat-key {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
    }

    .mf-stat-symbol {
        display: inline-flex;
        align-items: center;
        opacity: 0.8;
    }

    .mf-stat-val {
        margin: 0;
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-sm);
        font-variant-numeric: tabular-nums;
        color: var(--mf-ink);

        &.muted {
            font-family: var(--mf-font-sans);
            color: var(--mf-ink-faint);
        }
    }

    .mf-panel-note {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-muted);
    }

    .mf-panel-note strong {
        color: var(--mf-ink);
        font-weight: 700;
    }
</style>

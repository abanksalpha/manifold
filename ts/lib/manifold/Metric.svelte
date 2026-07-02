<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
One score, framed as a sticker card. The frame is decoration (a 2px ink outline,
a hard offset shadow, a small accent shape by the label); the reading inside
stays honest: the number is plain, and the Meter's fill still greys out with
weak evidence. `accent` rotates the header colour across cards for the confetti
effect. A missing reading reads "not yet measured" rather than a hollow zero.
-->
<script lang="ts">
    import Formula from "./Formula.svelte";
    import Meter from "./Meter.svelte";
    import { percent } from "./format";

    export let label: string;
    /** Optional typeset definition shown beside the label, e.g. mean recall. */
    export let symbolTex: string | null = null;
    export let symbolLabel = "";
    /** The reading in [0, 1], or null when it cannot be measured yet. */
    export let value: number | null;
    export let low: number | null = null;
    export let high: number | null = null;
    export let evidence = 1;
    export let showRange = true;
    export let caption: string;
    /** Header accent colour; pass a palette token to rotate across cards. */
    export let accent = "var(--mf-accent)";

    $: measured = value !== null;
</script>

<div class="metric" style="--accent: {accent}">
    <div class="metric-head">
        <span class="metric-mark" aria-hidden="true"></span>
        <span class="metric-label">{label}</span>
        {#if symbolTex}
            <span class="metric-symbol">
                <Formula tex={symbolTex} label={symbolLabel} fontSize={13} />
            </span>
        {/if}
    </div>

    <div class="metric-readout" class:muted={!measured}>
        {#if measured}
            <span class="num">{percent(value ?? 0)}</span>
        {:else}
            not yet measured
        {/if}
    </div>

    <Meter
        value={value ?? 0}
        low={low ?? value ?? 0}
        high={high ?? value ?? 0}
        {evidence}
        {showRange}
        unmeasured={!measured}
        {label}
    />

    <p class="metric-caption">{caption}</p>
</div>

<style lang="scss">
    .metric {
        display: grid;
        gap: var(--mf-space-3);
        align-content: start;
        padding: var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    .metric-head {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        min-height: 20px;
    }

    /* the pop: a small outlined sticker square in the card's rotating accent,
     * slapped on at a slight angle */
    .metric-mark {
        flex: none;
        width: 16px;
        height: 16px;
        border-radius: 0;
        background: var(--accent);
        border: 2.5px solid var(--mf-ink);
        transform: rotate(-8deg);
    }

    .metric-label {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .metric-symbol {
        display: inline-flex;
        align-items: center;
        margin-left: auto;
        opacity: 0.85;
    }

    .metric-readout {
        font-family: var(--mf-font-display);
        font-size: var(--mf-readout);
        font-weight: 800;
        line-height: 1;
        color: var(--mf-ink);
        font-variant-numeric: tabular-nums;

        .num {
            letter-spacing: -0.02em;
        }

        &.muted {
            font-family: var(--mf-font-sans);
            font-size: var(--mf-text-md);
            font-weight: 600;
            color: var(--mf-ink-faint);
        }
    }

    .metric-caption {
        margin: 0;
        font-size: var(--mf-text-sm);
        color: var(--mf-ink-faint);
        max-width: 30ch;
    }
</style>

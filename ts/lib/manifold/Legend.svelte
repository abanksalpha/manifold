<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
Reads the graph back to the user: which fill means which lock state, which
shape means which tier. The swatches are the same NodeGlyph the graph draws, so
the key cannot fall out of step with the marks it describes.
-->
<script lang="ts">
    import GlyphSwatch from "./GlyphSwatch.svelte";
    import { LOCK_ORDER, tierLabel, TIER_ORDER } from "./graph";

    const lockLabels: Record<string, string> = {
        locked: "Locked",
        unlocked: "Unlocked",
        in_progress: "In progress",
        mastered: "Mastered",
    };
</script>

<div class="mf-legend">
    <div class="mf-legend-group">
        <span class="mf-legend-title">Lock state</span>
        <ul class="mf-legend-items">
            {#each LOCK_ORDER as state (state)}
                <li class="mf-legend-item">
                    <GlyphSwatch
                        class="mf-legend-swatch"
                        tier="relearn"
                        lockState={state}
                    />
                    <span class="mf-legend-label">{lockLabels[state]}</span>
                </li>
            {/each}
        </ul>
    </div>

    <div class="mf-legend-group">
        <span class="mf-legend-title">Tier</span>
        <ul class="mf-legend-items">
            {#each TIER_ORDER as tier (tier)}
                <li class="mf-legend-item">
                    <GlyphSwatch class="mf-legend-swatch" {tier} lockState="unlocked" />
                    <span class="mf-legend-label">{tierLabel(tier)}</span>
                </li>
            {/each}
        </ul>
    </div>
</div>

<style lang="scss">
    .mf-legend {
        display: flex;
        flex-wrap: wrap;
        gap: var(--mf-space-5) var(--mf-space-6);
    }

    .mf-legend-group {
        display: grid;
        gap: var(--mf-space-3);
        align-content: start;
    }

    .mf-legend-title {
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-legend-items {
        display: flex;
        flex-wrap: wrap;
        gap: var(--mf-space-2) var(--mf-space-3);
        margin: 0;
        padding: 0;
        list-style: none;
    }

    /* each key entry is a small outlined chip so the marks read as a tidy set */
    .mf-legend-item {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        padding: var(--mf-space-1) var(--mf-space-3);
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-surface);
    }

    .mf-legend-item :global(.mf-legend-swatch) {
        flex: none;
    }

    .mf-legend-label {
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-sm);
        font-weight: 600;
        line-height: 1.3;
        color: var(--mf-ink-muted);
    }
</style>

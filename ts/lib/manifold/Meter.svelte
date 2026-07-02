<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
A horizontal reading: a fill from zero to the value, the observed spread as a
lighter band, and a tick at the point estimate. Fill colour saturation is scaled
by `evidence` (how much data backs the reading) via the signal hue's chroma, so a
thinly-evidenced value shows up greyer. When `unmeasured`, the track stays empty
and striped. The track is deliberately calm: no width animation, so a reading
never slides around or dresses itself up.
-->
<script lang="ts">
    export let value: number;
    export let low: number = value;
    export let high: number = value;
    /** 0..1: fraction of evidence behind the reading; scales fill chroma. */
    export let evidence = 1;
    /** Draw the observed-range band, not just the value tick. */
    export let showRange = true;
    export let unmeasured = false;
    export let label: string;

    const clamp01 = (n: number): number => Math.max(0, Math.min(1, n));

    $: v = clamp01(value);
    $: lo = clamp01(Math.min(low, high));
    $: hi = clamp01(Math.max(low, high));
    $: ev = clamp01(evidence);
    $: valueText = unmeasured ? "not yet measured" : `${Math.round(v * 100)}%`;
</script>

<div
    class="meter"
    class:unmeasured
    role="meter"
    aria-valuemin={0}
    aria-valuemax={100}
    aria-valuenow={unmeasured ? undefined : Math.round(v * 100)}
    aria-valuetext={valueText}
    aria-label={label}
    style="--mf-evidence: {ev}"
>
    <div class="track">
        {#if !unmeasured}
            <div class="fill" style="width: {v * 100}%"></div>
            {#if showRange && hi > lo}
                <div
                    class="band"
                    style="left: {lo * 100}%; width: {(hi - lo) * 100}%"
                ></div>
                <div class="tick" style="left: {v * 100}%"></div>
            {/if}
        {/if}
    </div>
</div>

<style lang="scss">
    .meter {
        --fill: oklch(
            var(--mf-signal-l) calc(var(--mf-signal-c) * var(--mf-evidence))
                var(--mf-signal-h)
        );
    }

    /* a hard-bordered bar, sharp corners, the reading blocked in flat colour: a
     * physical gauge rather than a soft progress pill */
    .track {
        position: relative;
        height: 18px;
        border: var(--mf-border-width) solid var(--mf-ink);
        border-radius: 0;
        background: var(--mf-surface);
        overflow: hidden;
    }

    .fill {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        background: var(--fill);
    }

    /* the observed spread, hatched over the fill so it reads as a range, not a
     * second solid value */
    .band {
        position: absolute;
        top: 0;
        bottom: 0;
        min-width: 2px;
        background-image: repeating-linear-gradient(
            -45deg,
            var(--mf-ink) 0,
            var(--mf-ink) 1.5px,
            transparent 1.5px,
            transparent 6px
        );
        opacity: 0.55;
    }

    .tick {
        position: absolute;
        top: -2px;
        bottom: -2px;
        width: 3px;
        margin-left: -1.5px;
        background: var(--mf-ink);
    }

    .unmeasured .track {
        background:
            repeating-linear-gradient(
                -45deg,
                var(--mf-surface-sunken) 0,
                var(--mf-surface-sunken) 5px,
                transparent 5px,
                transparent 10px
            ),
            var(--mf-surface-sunken);
    }
</style>

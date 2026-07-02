<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
A single topic mark rendered as a standalone SVG, for use in HTML contexts (the
legend, the panel header). The same shape rules and fills the graph draws, so a
swatch always matches the node it stands for. Its root is an <svg>, which keeps
the markup unambiguously in the SVG namespace.
-->
<script lang="ts">
    import { diamondPoints, glyphStyle, GLYPH_INSET, GLYPH_SIZE } from "./graph";

    export let tier: string;
    export let lockState: string;
    export let size = 16;

    let klass = "";
    export { klass as class };

    const r = GLYPH_SIZE / 2 - GLYPH_INSET;
    const inner = GLYPH_SIZE - GLYPH_INSET * 2;
</script>

<svg
    class={klass}
    width={size}
    height={size}
    viewBox="0 0 {GLYPH_SIZE} {GLYPH_SIZE}"
    aria-hidden="true"
>
    {#if tier === "relearn"}
        <circle
            cx={GLYPH_SIZE / 2}
            cy={GLYPH_SIZE / 2}
            {r}
            style={glyphStyle(lockState)}
        />
    {:else if tier === "teach"}
        <rect
            x={GLYPH_INSET}
            y={GLYPH_INSET}
            width={inner}
            height={inner}
            rx="8"
            style={glyphStyle(lockState)}
        />
    {:else}
        <polygon points={diamondPoints()} style={glyphStyle(lockState)} />
    {/if}
</svg>

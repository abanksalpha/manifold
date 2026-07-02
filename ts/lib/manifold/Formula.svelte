<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
Typesets a TeX expression to an SVG using the engine MathJax build, so every
symbol on the page is real typeset maths rather than ASCII. The SVG is rendered
inside an <img> data URL, which sandboxes MathJax's injected colour styles and
lets the result recolour with the page theme.
-->
<script lang="ts">
    import { pageTheme } from "$lib/sveltelib/theme";

    import { convertMathjax } from "../../editable/mathjax";

    export let tex: string;
    export let fontSize = 15;
    /** Accessible text for screen readers, e.g. "mean recall R". */
    export let label: string;

    let converted = "";
    $: [converted] = convertMathjax(tex, $pageTheme.isDark, fontSize);
    $: src = `data:image/svg+xml,${encodeURIComponent(converted)}`;
</script>

<img class="mf-formula" {src} alt={label} />

<style lang="scss">
    .mf-formula {
        vertical-align: middle;
        // MathJax bakes the glyph colour into the SVG, so do not tint the <img>.
    }
</style>

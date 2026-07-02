<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
Renders a label that mixes prose with inline LaTeX, e.g. "Powers of \(i\)
(cyclic reduction)". The plain runs stay as real text nodes (so a caller's
innerText, and screen readers, still read the words), and each \( … \) or
\[ … \] run is typeset with the same engine Formula.svelte uses (MathJax, via
convertMathjax) so no new dependency is pulled in. A string with no delimiters
is emitted unchanged.

Maths is drawn as an SVG data URL inside an <img>, which sandboxes MathJax's
injected colour styles the way Formula does. The SVG's own ex-based width,
height and vertical-align are carried onto the <img> so the maths scales with,
and sits on the baseline of, the surrounding text rather than shifting the line.
-->
<script lang="ts">
    import { pageTheme } from "$lib/sveltelib/theme";

    import { convertMathjax } from "../../editable/mathjax";

    export let text: string;
    /** Point size the maths is rasterised at. The visible size then tracks the
     *  surrounding text through the ex-based dimensions copied off the SVG. */
    export let fontSize = 15;

    type Segment =
        | { kind: "text"; value: string }
        | { kind: "inline" | "display"; value: string; raw: string };

    // \[ … \] is a display block, \( … \) is inline; anything else is literal
    // text. Non-greedy and newline-aware so adjacent runs split cleanly.
    const MATH = /\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)/g;

    function split(input: string): Segment[] {
        const segments: Segment[] = [];
        let last = 0;
        let match: RegExpExecArray | null;
        MATH.lastIndex = 0;
        while ((match = MATH.exec(input)) !== null) {
            if (match.index > last) {
                segments.push({ kind: "text", value: input.slice(last, match.index) });
            }
            const display = match[1] !== undefined;
            segments.push({
                kind: display ? "display" : "inline",
                value: (display ? match[1] : match[2]).trim(),
                raw: match[0],
            });
            last = match.index + match[0].length;
        }
        if (last < input.length) {
            segments.push({ kind: "text", value: input.slice(last) });
        }
        return segments;
    }

    interface Rendered {
        kind: "text" | "inline" | "display";
        /** Text to print: the run itself, or the raw source when maths fails. */
        value: string;
        src?: string;
        width?: string;
        height?: string;
        shift?: string;
    }

    function typeset(
        value: string,
        raw: string,
        kind: "inline" | "display",
        dark: boolean,
    ): Rendered {
        const [svg] = convertMathjax(value, dark, fontSize);
        // convertMathjax returns "Mathjax Error" on a throw, or an <svg> that
        // carries data-mjx-error when the TeX does not parse. Both fall back to
        // the raw source rather than throwing or showing a broken image.
        if (!svg.startsWith("<svg") || svg.includes("data-mjx-error")) {
            return { kind, value: raw };
        }
        return {
            kind,
            value,
            src: `data:image/svg+xml,${encodeURIComponent(svg)}`,
            width: /\bwidth="([^"]+)"/.exec(svg)?.[1],
            height: /\bheight="([^"]+)"/.exec(svg)?.[1],
            shift: /vertical-align:\s*([^;"]+)/.exec(svg)?.[1],
        };
    }

    $: rendered = split(text).map(
        (segment): Rendered =>
            segment.kind === "text"
                ? { kind: "text", value: segment.value }
                : typeset(segment.value, segment.raw, segment.kind, $pageTheme.isDark),
    );
</script>

<!-- prettier-ignore -->
<span class="mf-mathtext">{#each rendered as run}{#if run.kind === "text"}{run.value}{:else if run.src}<img class="mf-math" class:mf-math-display={run.kind === "display"} src={run.src} alt={run.value} style:width={run.width} style:height={run.height} style:vertical-align={run.shift} />{:else}{run.value}{/if}{/each}</span>

<style lang="scss">
    // Sit in the text flow without introducing its own box.
    .mf-mathtext {
        display: inline;
    }

    .mf-math {
        // vertical-align is set per-glyph from the SVG so the baseline matches.
        display: inline-block;
    }

    .mf-math-display {
        display: block;
        margin: var(--mf-space-3, 0.75em) auto;
    }
</style>

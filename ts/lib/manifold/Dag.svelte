<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The prerequisite graph. Topics are laid out by layoutGraph (rows by tier then
prerequisite depth, one band per area) and drawn as an SVG at its intrinsic
pixel size, so a unit is a pixel and the alignment harness measures real
positions. Each node is selectable by pointer or keyboard; selecting one lights
its prerequisite edges and tells the parent which topic to read out.
-->
<script lang="ts">
    import { createEventDispatcher } from "svelte";

    import {
        diamondPoints,
        edgePath,
        GLYPH_INSET,
        glyphStyle,
        LAYOUT,
        layoutGraph,
        tierLabel,
        type TopicNode,
        wrapLabel,
    } from "./graph";

    export let nodes: TopicNode[];
    export let selectedId: string | null = null;

    const dispatch = createEventDispatcher<{ select: string }>();

    const NODE = LAYOUT.node;

    // Backing rect for a node's wrapped label. It paints in the mf-label-bgs
    // layer above the edges, so a connecting line passes behind the name box
    // rather than across it; the label text keeps its ground-coloured halo too,
    // as a second line of defence. Square corners and integer-snapped, even width
    // so the fill lands on the pixel grid. Width is capped to the column slot so a
    // wide label's backing never reaches into a neighbour's slot.
    const LABEL_CHAR_W = 6.5;
    const LABEL_PAD = 3;
    const LABEL_MAX_W = LAYOUT.colW - 8;
    function labelRect(lines: string[]): {
        x: number;
        y: number;
        w: number;
        h: number;
    } {
        const longest = lines.reduce((m, line) => Math.max(m, line.length), 0);
        let w = Math.min(
            Math.round(longest * LABEL_CHAR_W + LABEL_PAD * 2),
            LABEL_MAX_W,
        );
        if (w % 2) {
            w += 1;
        }
        const h = 19 + 13 * (lines.length - 1);
        // Drop the box 3px so it centres on the text block (the first baseline
        // sits 15px below the node) instead of butting against the node above,
        // keeping a snug, balanced margin around every line.
        return { x: NODE / 2 - w / 2, y: NODE + 3, w, h };
    }

    $: layout = layoutGraph(nodes);
    $: prereqsOfSelected = new Set(
        nodes.find((n) => n.id === selectedId)?.prereqs ?? [],
    );
    $: lockById = new Map(nodes.map((n) => [n.id, n.lockState]));

    /** An edge is "mastered" when both of its endpoints are. */
    function edgeMastered(fromId: string, toId: string): boolean {
        return lockById.get(fromId) === "mastered" && lockById.get(toId) === "mastered";
    }

    const areaTitles: Record<string, string> = {
        calculus: "Calculus",
        algebra: "Algebra",
        additional: "Additional",
    };

    // A short underline colour per band, rotated across the confetti palette.
    // Decoration only: the bands' widths and gap are still driven by the layout.
    const headAccents = [
        "var(--mf-accent)",
        "var(--mf-secondary)",
        "var(--mf-tertiary)",
    ];

    const lockLabels: Record<string, string> = {
        locked: "locked",
        unlocked: "unlocked",
        in_progress: "in progress",
        mastered: "mastered",
    };

    function choose(id: string): void {
        dispatch("select", id);
    }

    function onKey(event: KeyboardEvent, id: string): void {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            choose(id);
        }
    }
</script>

<div class="mf-graph-scroll">
    <div class="mf-graph-inner" style="width: {layout.width}px">
        <div
            class="mf-area-heads"
            style="grid-template-columns: {layout.bands
                .map((b) => `${b.w}px`)
                .join(' ')}; gap: {LAYOUT.bandGap}px"
        >
            {#each layout.bands as band, i (band.area)}
                <span
                    class="mf-area-head"
                    style="--head-accent: {headAccents[i % headAccents.length]}"
                >
                    {areaTitles[band.area] ?? band.area}
                </span>
            {/each}
        </div>

        <svg
            class="mf-dag"
            width={layout.width}
            height={layout.height}
            viewBox="0 0 {layout.width} {layout.height}"
            role="group"
            aria-label="Topic prerequisite graph"
        >
            <g class="mf-edges">
                {#each layout.edges as edge (edge.fromId + "->" + edge.toId)}
                    <path
                        class="mf-edge"
                        class:active={edge.toId === selectedId ||
                            edge.fromId === selectedId}
                        class:mastered={edgeMastered(edge.fromId, edge.toId)}
                        d={edgePath(edge)}
                    />
                {/each}
            </g>

            <!-- Name backings paint above the edges, so a dashed line passes
                 behind a topic name rather than across it. The glyphs and label
                 text (in the node groups below) paint above these in turn. -->
            <g class="mf-label-bgs">
                {#each layout.nodes as p (p.node.id)}
                    {@const rect = labelRect(wrapLabel(p.node.title))}
                    <rect
                        class="mf-label-bg"
                        x={p.x + rect.x}
                        y={p.y + rect.y}
                        width={rect.w}
                        height={rect.h}
                    />
                {/each}
            </g>

            {#each layout.nodes as p (p.node.id)}
                {@const lines = wrapLabel(p.node.title)}
                <g
                    class="mf-node"
                    class:selected={p.node.id === selectedId}
                    class:prereq={prereqsOfSelected.has(p.node.id)}
                    transform="translate({p.x},{p.y})"
                    data-topic={p.node.id}
                    role="button"
                    tabindex="0"
                    aria-pressed={p.node.id === selectedId}
                    aria-label="{p.node.title}, {tierLabel(
                        p.node.tier,
                    )} tier, {lockLabels[p.node.lockState] ?? p.node.lockState}"
                    on:click={() => choose(p.node.id)}
                    on:keydown={(event) => onKey(event, p.node.id)}
                >
                    <rect
                        class="mf-ring"
                        x={-5}
                        y={-5}
                        width={NODE + 10}
                        height={NODE + 10}
                        rx="2"
                    />
                    {#if p.node.tier === "relearn"}
                        <circle
                            class="mf-glyph"
                            cx={NODE / 2}
                            cy={NODE / 2}
                            r={NODE / 2 - GLYPH_INSET}
                            style={glyphStyle(
                                p.node.lockState,
                                p.node.id === selectedId,
                            )}
                        />
                    {:else if p.node.tier === "teach"}
                        <rect
                            class="mf-glyph"
                            x={GLYPH_INSET}
                            y={GLYPH_INSET}
                            width={NODE - GLYPH_INSET * 2}
                            height={NODE - GLYPH_INSET * 2}
                            rx="2"
                            style={glyphStyle(
                                p.node.lockState,
                                p.node.id === selectedId,
                            )}
                        />
                    {:else}
                        <polygon
                            class="mf-glyph"
                            points={diamondPoints(NODE)}
                            style={glyphStyle(
                                p.node.lockState,
                                p.node.id === selectedId,
                            )}
                        />
                    {/if}
                    <rect class="mf-node-hit" width={NODE} height={NODE} />
                    <text
                        class="mf-node-label"
                        x={NODE / 2}
                        y={NODE + 15}
                        text-anchor="middle"
                    >
                        {#each lines as line, i (i)}
                            <tspan x={NODE / 2} dy={i === 0 ? 0 : 13}>{line}</tspan>
                        {/each}
                    </text>
                    <title>{p.node.title}</title>
                </g>
            {/each}
        </svg>
    </div>
</div>

<style lang="scss">
    .mf-graph-scroll {
        overflow-x: auto;
        // keep a sub-pixel scaler from ever touching the SVG: it renders at its
        // own pixel size and scrolls on narrow screens instead of shrinking.
    }

    .mf-graph-inner {
        margin: 0 auto;
    }

    .mf-area-heads {
        display: grid;
        margin-bottom: var(--mf-space-3);
    }

    .mf-area-head {
        position: relative;
        text-align: center;
        padding-bottom: var(--mf-space-2);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    /* a short, chunky colour tab under each band head; decoration, not a rule.
     * A hard-edged bar with the ink stroke, so it reads as a sticker, not a line */
    .mf-area-head::after {
        content: "";
        position: absolute;
        left: 50%;
        bottom: 0;
        transform: translateX(-50%);
        width: 32px;
        height: 6px;
        border: 2px solid var(--mf-ink);
        background: var(--head-accent, var(--mf-accent));
    }

    .mf-dag {
        display: block;
    }

    /* prerequisite edges read as dashed ink connectors */
    .mf-edge {
        fill: none;
        stroke: var(--mf-ink);
        stroke-width: 2.25;
        stroke-dasharray: 5 6;
        stroke-linecap: round;
        opacity: 0.55;
        transition:
            stroke var(--mf-transition),
            opacity var(--mf-transition);
    }

    /* an edge whose both ends are mastered goes solid and violet, so a completed
     * chain reads as one continuous coloured path; every other edge stays dashed */
    .mf-edge.mastered {
        stroke: var(--mf-signal);
        stroke-dasharray: none;
        opacity: 0.85;
    }

    /* Selection is a weight + opacity change only. It does not recolour the edge
     * or touch its dash, so solid keeps meaning "mastered" and dashed "not yet". */
    .mf-edge.active {
        stroke-width: 3;
        opacity: 1;
    }

    .mf-node {
        cursor: pointer;
        outline: none;
    }

    .mf-node-hit {
        fill: transparent;
    }

    .mf-label-bg {
        fill: var(--mf-surface);
        stroke: none;
    }

    .mf-ring {
        fill: none;
        stroke: none;
        transition: stroke var(--mf-transition);
    }

    /* The ring is only a keyboard-focus indicator: no box on hover, and a
     * selected topic is shown by its highlighted edges and darker label. */
    .mf-node:focus-visible .mf-ring {
        stroke: var(--mf-signal);
        stroke-width: 3.5;
    }

    .mf-node-label {
        font-family: var(--mf-font-sans);
        font-size: 11px;
        fill: var(--mf-ink-faint);
        // A ground-coloured halo around each glyph, painted under the fill, so
        // any edge that slips past the label backing still cannot touch a letter.
        paint-order: stroke;
        stroke: var(--mf-surface);
        stroke-width: 3.5;
        stroke-linejoin: round;
        transition: fill var(--mf-transition);
    }

    .mf-node.selected .mf-node-label,
    .mf-node.prereq .mf-node-label {
        fill: var(--mf-ink);
    }

    /* Selection colouring lives in glyphStyle (graph.ts): the selected glyph
     * keeps its lock-state colour, just darker, so state stays legible while the
     * highlighted edges + darker label mark the selection. */

    @media (prefers-reduced-motion: reduce) {
        .mf-edge,
        .mf-node-label {
            transition: none;
        }
    }
</style>

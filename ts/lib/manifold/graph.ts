// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Deterministic layout for the Manifold prerequisite DAG.
 *
 * The readiness dashboard draws the 33 blueprint topics as a layered graph:
 * rows run by tier first (relearn, then teach, then recognize) and within a
 * tier by prerequisite depth, so each column reads top to bottom in study
 * order; three columns for the exam areas, each packed to its own height so a
 * sparse column never stretches the graph. Positions are pure functions of the
 * graph returned by `getTopicGraph`, so the same data always renders the same
 * picture and the alignment harness can measure it. Nothing here reads anything
 * the engine did not already compute: an unknown area or a prerequisite cycle is
 * an error, not a best guess.
 */

/**
 * The per-topic node from the `getTopicGraph` RPC (camelCase). Recall,
 * performance and coverage are fractions in [0, 1]; stability is in days.
 */
export interface TopicNode {
    id: string;
    title: string;
    area: string;
    tier: string;
    weight: number;
    prereqs: string[];
    lockState: string;
    mastered: number;
    total: number;
    avgRecall: number;
    avgStability: number;
    coverage: number;
    performance: number;
    gradedReviews: number;
    independentReviews: number;
    levelNew: number;
    levelGuided: number;
    levelIndependent: number;
    levelRevisited: number;
}

/** Exam areas, in the left-to-right column order the dashboard draws them. */
export const AREA_ORDER = ["calculus", "algebra", "additional"] as const;
export type Area = (typeof AREA_ORDER)[number];

/** Study tiers, ordered by how deeply the exam expects a topic to be known. */
export const TIER_ORDER = ["relearn", "teach", "recognize"] as const;
export type Tier = (typeof TIER_ORDER)[number];

/**
 * Display labels for the tiers. The internal ids stay relearn/teach/recognize
 * (blueprint keys, `mf::tier::*` tags, engine); only the UI shows these.
 */
export const TIER_LABELS: Record<string, string> = {
    relearn: "Core",
    teach: "Target",
    recognize: "Reach",
};

/** The display label for a tier id, falling back to the raw id. */
export function tierLabel(tier: string): string {
    return TIER_LABELS[tier] ?? tier;
}

/** The four lock states the engine assigns, ordered from cold to complete. */
export const LOCK_ORDER = ["locked", "unlocked", "in_progress", "mastered"] as const;
export type LockState = (typeof LOCK_ORDER)[number];

/**
 * Geometry, every value a multiple of 4 so node edges land on the pixel grid
 * and the spacing stays on one scale. A node box is square; `colW` is the fixed
 * width of one node-plus-label column slot, wide enough that the longest wrapped
 * label clears its neighbours. An area band holds one slot per peer in its most
 * crowded row, so bands widen only as much as their busiest depth needs.
 */
export const LAYOUT = {
    node: 48,
    colW: 132,
    bandGap: 48,
    rowPitch: 112,
    padTop: 8,
    labelBlock: 56,
} as const;

export interface PositionedNode {
    node: TopicNode;
    /** Row: tier band first, then prerequisite depth. */
    row: number;
    area: Area;
    /** Top-left of the node box. */
    x: number;
    y: number;
    /** Centre of the node box. */
    cx: number;
    cy: number;
}

export interface GraphEdge {
    fromId: string;
    toId: string;
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    /**
     * Signed horizontal offset for routing a same-column edge that skips a row,
     * so it bows out around the nodes stacked between its ends instead of drawing
     * a straight line through them. Undefined for ordinary edges.
     */
    bow?: number;
}

/** How far a skipping same-column edge bows sideways, past the column's labels. */
const EDGE_BOW = 72;

export interface AreaBand {
    area: Area;
    x: number;
    w: number;
    cx: number;
}

export interface GraphLayout {
    nodes: PositionedNode[];
    edges: GraphEdge[];
    bands: AreaBand[];
    width: number;
    height: number;
}

/**
 * Longest-prerequisite-chain depth for every topic. Roots (no prerequisites)
 * are depth 0; every edge therefore points strictly downward. A cycle or a
 * dangling prerequisite is raised, never silently flattened.
 */
export function computeDepths(nodes: TopicNode[]): Map<string, number> {
    const byId = new Map(nodes.map((node) => [node.id, node]));
    const depth = new Map<string, number>();
    const onStack = new Set<string>();

    function visit(id: string): number {
        const seen = depth.get(id);
        if (seen !== undefined) {
            return seen;
        }
        if (onStack.has(id)) {
            throw new Error(`manifold prerequisite cycle through topic '${id}'`);
        }
        const node = byId.get(id);
        if (!node) {
            throw new Error(`manifold references unknown prerequisite topic '${id}'`);
        }
        onStack.add(id);
        let d = 0;
        for (const prereq of node.prereqs) {
            d = Math.max(d, visit(prereq) + 1);
        }
        onStack.delete(id);
        depth.set(id, d);
        return d;
    }

    for (const node of nodes) {
        visit(node.id);
    }
    return depth;
}

/**
 * The tier band a topic sits in, low to high: relearn above teach above
 * recognize. An unknown tier is an error, mirroring the area check.
 */
function tierBand(tier: string): number {
    const index = (TIER_ORDER as readonly string[]).indexOf(tier);
    if (index < 0) {
        throw new Error(`manifold topic has unknown tier '${tier}'`);
    }
    return index;
}

/**
 * Row for every topic: tier first (relearn, then teach, then recognize) and,
 * within a tier, prerequisite depth. Each column then reads top to bottom in
 * study order — single-variable calculus, then multivariable, then differential
 * equations; teach squares before recognize diamonds.
 *
 * Rows are packed per area column, not across the whole graph: distinct
 * (tier, depth) pairs collapse to consecutive rows within their own area, and
 * every column starts at row 0. A sparse tier in one column therefore cannot
 * stretch the others, so the graph is only as tall as its busiest column
 * instead of the union of every column's levels.
 */
export function computeRows(nodes: TopicNode[]): Map<string, number> {
    const depth = computeDepths(nodes);
    const rows = new Map<string, number>();

    const areas = new Map<string, TopicNode[]>();
    for (const node of nodes) {
        const group = areas.get(node.area);
        if (group) {
            group.push(node);
        } else {
            areas.set(node.area, [node]);
        }
    }

    for (const group of areas.values()) {
        const keys = new Set<string>();
        for (const node of group) {
            keys.add(`${tierBand(node.tier)}|${depth.get(node.id)}`);
        }
        const order = [...keys]
            .map((key) => key.split("|").map(Number) as [number, number])
            .sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        const rowByKey = new Map<string, number>();
        order.forEach(([tier, d], row) => rowByKey.set(`${tier}|${d}`, row));
        for (const node of group) {
            rows.set(
                node.id,
                rowByKey.get(`${tierBand(node.tier)}|${depth.get(node.id)}`)!,
            );
        }
    }
    return rows;
}

/**
 * Place every topic. Each area band is as wide as its most crowded row needs:
 * one fixed `colW` slot per peer, so a label never has to share a slot with a
 * sibling and collide. Within a row the slots are centred on the band, so a
 * lone topic sits at the band centre and a pair straddles it symmetrically;
 * input (blueprint) order decides which side, keeping the result stable.
 */
export function layoutGraph(nodes: TopicNode[]): GraphLayout {
    if (nodes.length === 0) {
        throw new Error("getTopicGraph returned no topics");
    }
    const rowOf = computeRows(nodes);
    const { node: NODE, colW, bandGap, rowPitch, padTop, labelBlock } = LAYOUT;

    // Peers share an area and a row: they are the topics drawn on one row of
    // one band, and they are the topics that must not overlap horizontally.
    const peers = new Map<string, TopicNode[]>();
    for (const node of nodes) {
        const key = `${node.area}|${rowOf.get(node.id)}`;
        const group = peers.get(key);
        if (group) {
            group.push(node);
        } else {
            peers.set(key, [node]);
        }
    }

    // A band's width is its busiest row: as many colW slots as that row has
    // peers (at least one). Sparse bands stay narrow instead of padding to the
    // widest band, which keeps the picture compact and every band centred.
    const maxPeersByArea = new Map<Area, number>();
    for (const [key, group] of peers) {
        const area = key.slice(0, key.lastIndexOf("|")) as Area;
        maxPeersByArea.set(area, Math.max(maxPeersByArea.get(area) ?? 1, group.length));
    }

    const bandInfo = new Map<Area, { left: number; w: number; cx: number }>();
    let cursor = 0;
    for (const area of AREA_ORDER) {
        const w = (maxPeersByArea.get(area) ?? 1) * colW;
        bandInfo.set(area, { left: cursor, w, cx: cursor + w / 2 });
        cursor += w + bandGap;
    }
    const width = cursor - bandGap;

    let maxRow = 0;
    const positioned: PositionedNode[] = nodes.map((node) => {
        const d = rowOf.get(node.id) ?? 0;
        maxRow = Math.max(maxRow, d);
        const band = bandInfo.get(node.area as Area);
        if (!band) {
            throw new Error(`manifold topic has unknown area '${node.area}'`);
        }
        const group = peers.get(`${node.area}|${d}`) ?? [node];
        const slot = group.indexOf(node);
        // Centre the row's slots on the band centre: a group of one lands on the
        // centre, a group of two straddles it by half a slot each, and so on.
        const cx = band.cx + colW * (slot + 0.5 - group.length / 2);
        const y = padTop + d * rowPitch;
        return {
            node,
            row: d,
            area: node.area as Area,
            x: cx - NODE / 2,
            y,
            cx,
            cy: y + NODE / 2,
        };
    });

    const byId = new Map(positioned.map((p) => [p.node.id, p]));
    const edges: GraphEdge[] = [];
    for (const p of positioned) {
        for (const prereqId of p.node.prereqs) {
            const from = byId.get(prereqId);
            if (!from) {
                throw new Error(
                    `manifold references unknown prerequisite topic '${prereqId}'`,
                );
            }
            // A vertical edge that skips a row (e.g. elementary algebra → number
            // theory, jumping past the linear-algebra chain in the same column)
            // would draw straight through the nodes between its ends. Bow it out
            // toward the graph's interior so the connection reads on its own.
            const sameColumn = Math.abs(from.cx - p.cx) < 1;
            const skipsRow = p.row - from.row > 1;
            let bow: number | undefined;
            if (sameColumn && skipsRow) {
                bow = from.cx < width / 2 ? EDGE_BOW : -EDGE_BOW;
            }
            edges.push({
                fromId: prereqId,
                toId: p.node.id,
                x1: from.cx,
                y1: from.y + NODE,
                x2: p.cx,
                y2: p.y,
                bow,
            });
        }
    }

    const bands: AreaBand[] = AREA_ORDER.map((area) => {
        const band = bandInfo.get(area)!;
        return { area, x: band.left, w: band.w, cx: band.cx };
    });

    return {
        nodes: positioned,
        edges,
        bands,
        width,
        height: padTop + maxRow * rowPitch + NODE + labelBlock,
    };
}

/**
 * A vertical cubic path from a prerequisite down to the topic that needs it.
 * Control points sit halfway down, giving a calm S when the columns differ and
 * a straight drop when they do not.
 */
export function edgePath(edge: GraphEdge): string {
    // A bowed edge eases out to an offset column, runs vertically past the nodes
    // it skips, then eases back in, so it clears everything stacked between its
    // ends rather than overlapping the straight chain edges.
    if (edge.bow) {
        const bx = edge.x1 + edge.bow;
        const yTop = edge.y1 + 18;
        const yBot = edge.y2 - 18;
        return [
            `M${edge.x1},${edge.y1}`,
            `C${edge.x1},${edge.y1 + 10} ${bx},${yTop - 10} ${bx},${yTop}`,
            `L${bx},${yBot}`,
            `C${bx},${yBot + 10} ${edge.x2},${edge.y2 - 10} ${edge.x2},${edge.y2}`,
        ].join(" ");
    }
    const midY = (edge.y1 + edge.y2) / 2;
    return `M${edge.x1},${edge.y1} C${edge.x1},${midY} ${edge.x2},${midY} ${edge.x2},${edge.y2}`;
}

/** The square box a topic mark is drawn in, and the stroke breathing room. */
export const GLYPH_SIZE = 48;
export const GLYPH_INSET = 2;

/** Points for the recognize-tier diamond, inscribed in the glyph box. */
export function diamondPoints(size = GLYPH_SIZE, inset = GLYPH_INSET): string {
    const mid = size / 2;
    return `${mid},${inset} ${size - inset},${mid} ${mid},${size - inset} ${inset},${mid}`;
}

/**
 * Inline fill and stroke for a topic mark, by lock state. Inlined rather than
 * class-driven so the one source of truth is shared by the graph and the legend
 * without either carrying a class the other might drop.
 *
 * Every state paints an opaque fill so the dashed prerequisite edges (drawn
 * behind the nodes) never show through a glyph: in-progress is the palette
 * green (quaternary), mastered the violet signal, and locked a muted but solid
 * grey. A selected node keeps its own state colour, just darker — the palette's
 * `-ink` variant where one exists, otherwise a mix toward the ink — so the
 * state stays legible while the selection stands out. A selected locked glyph
 * keeps that same faint stroke instead of taking the hard ink border the other
 * states carry, so its frame never hardens to black; the deeper fill alone
 * marks the pick.
 */
export function glyphStyle(lockState: string, selected = false): string {
    // A locked mark keeps its stroke faded whether resting or selected: washed
    // with the surface colour so its frame never hardens to a black ink border.
    const stroke = lockState === "locked"
        ? "color-mix(in srgb, var(--mf-ink-faint) 55%, var(--mf-surface))"
        : "var(--mf-ink)";
    let fill: string;
    switch (lockState) {
        case "mastered":
            fill = selected ? "var(--mf-signal-ink)" : "var(--mf-signal)";
            break;
        case "in_progress":
            // A mid green: the full -ink variant reads too dark as a fill, so the
            // selected state only steps halfway toward it.
            fill = selected
                ? "color-mix(in srgb, var(--mf-quaternary-ink) 55%, var(--mf-quaternary))"
                : "var(--mf-quaternary)";
            break;
        case "unlocked":
            fill = selected
                ? "color-mix(in srgb, var(--mf-surface) 78%, var(--mf-ink))"
                : "var(--mf-surface)";
            break;
        default:
            // The stroke above stays faint whether or not a locked glyph is
            // picked, so selection is carried by a deeper grey fill, kept light
            // enough that it never reads as a dark block.
            fill = selected
                ? "color-mix(in srgb, var(--mf-surface-sunken) 94%, var(--mf-ink))"
                : "color-mix(in srgb, var(--mf-surface-sunken) 55%, var(--mf-surface))";
    }
    return `fill: ${fill}; stroke: ${stroke}; stroke-width: 3;`;
}

/** What to study next for a selected topic, read only from engine lock states. */
export type PrereqAdvice =
    | { kind: "open" }
    | { kind: "mastered" }
    | { kind: "blocked"; target: TopicNode | null };

/**
 * For an open or mastered topic the advice is itself; for a locked topic, the
 * best prerequisite to study next: one that can be studied now (unlocked or in
 * progress) wins over a deeper-locked one, and among those the one leaving the
 * most blueprint points on the table, weight times the recall still missing.
 */
export function studyNextWithinPrereqs(
    topic: TopicNode,
    byId: Map<string, TopicNode>,
): PrereqAdvice {
    if (topic.lockState === "mastered") {
        return { kind: "mastered" };
    }
    if (topic.lockState === "unlocked" || topic.lockState === "in_progress") {
        return { kind: "open" };
    }

    let best: TopicNode | null = null;
    let bestScore = -1;
    for (const prereqId of topic.prereqs) {
        const prereq = byId.get(prereqId);
        if (!prereq) {
            throw new Error(
                `manifold references unknown prerequisite topic '${prereqId}'`,
            );
        }
        if (prereq.lockState === "mastered") {
            continue;
        }
        const studyable = prereq.lockState === "unlocked" || prereq.lockState === "in_progress";
        const score = (studyable ? 1000 : 0) + prereq.weight * (1 - prereq.avgRecall);
        if (score > bestScore) {
            bestScore = score;
            best = prereq;
        }
    }
    return { kind: "blocked", target: best };
}

/**
 * Word-wrap a topic title into at most `maxLines` lines of about `maxChars`
 * each. If words remain after the last line, the last line ends in an ellipsis;
 * the full title is always available in the topic panel and the node tooltip.
 */
export function wrapLabel(title: string, maxChars = 20, maxLines = 3): string[] {
    const words = title.split(/\s+/).filter(Boolean);
    const lines: string[] = [];
    let i = 0;
    while (i < words.length && lines.length < maxLines) {
        let line = words[i];
        i += 1;
        while (i < words.length && `${line} ${words[i]}`.length <= maxChars) {
            line = `${line} ${words[i]}`;
            i += 1;
        }
        lines.push(line);
    }
    if (i < words.length && lines.length > 0) {
        const last = lines[lines.length - 1].replace(/[\s.,&]+$/, "");
        lines[lines.length - 1] = `${last}…`;
    }
    return lines;
}

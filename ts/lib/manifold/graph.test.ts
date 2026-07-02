// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import { computeDepths, computeRows, layoutGraph, studyNextWithinPrereqs, type TopicNode, wrapLabel } from "./graph";

function node(overrides: Partial<TopicNode> = {}): TopicNode {
    return {
        id: "t",
        title: "Topic",
        area: "calculus",
        tier: "relearn",
        weight: 1,
        prereqs: [],
        lockState: "locked",
        mastered: 0,
        total: 0,
        avgRecall: 0,
        avgStability: 0,
        coverage: 0,
        performance: 0,
        gradedReviews: 0,
        independentReviews: 0,
        levelNew: 0,
        levelGuided: 0,
        levelIndependent: 0,
        levelRevisited: 0,
        ...overrides,
    };
}

function byId(nodes: TopicNode[]): Map<string, TopicNode> {
    return new Map(nodes.map((n) => [n.id, n]));
}

test("depth is the longest prerequisite chain, not the shortest", () => {
    const nodes = [
        node({ id: "a", prereqs: [] }),
        node({ id: "b", prereqs: ["a"] }),
        node({ id: "c", prereqs: ["b"] }),
        // d depends on both a (depth 0) and c (depth 2): the longest wins.
        node({ id: "d", prereqs: ["a", "c"] }),
    ];
    const depth = computeDepths(nodes);
    expect(depth.get("a")).toBe(0);
    expect(depth.get("b")).toBe(1);
    expect(depth.get("c")).toBe(2);
    expect(depth.get("d")).toBe(3);
});

test("a prerequisite cycle is raised, never silently flattened", () => {
    const nodes = [
        node({ id: "a", prereqs: ["b"] }),
        node({ id: "b", prereqs: ["a"] }),
    ];
    expect(() => computeDepths(nodes)).toThrow(/cycle/);
});

test("rows band by tier (relearn, teach, recognize), then by prerequisite depth", () => {
    const nodes = [
        node({ id: "root", tier: "relearn", prereqs: [] }),
        node({ id: "deepRelearn", tier: "relearn", prereqs: ["root"] }),
        node({ id: "shallowTeach", tier: "teach", prereqs: ["root"] }),
        node({ id: "recognize", tier: "recognize", prereqs: ["shallowTeach"] }),
    ];
    const rows = computeRows(nodes);
    // Tier wins over raw depth: a deeper relearn topic still sits above the
    // shallowest teach topic, and recognize sits below teach.
    expect(rows.get("root")!).toBeLessThan(rows.get("deepRelearn")!);
    expect(rows.get("deepRelearn")!).toBeLessThan(rows.get("shallowTeach")!);
    expect(rows.get("shallowTeach")!).toBeLessThan(rows.get("recognize")!);
});

test("an unknown area is an error", () => {
    expect(() => layoutGraph([node({ id: "a", area: "geometry" })])).toThrow(/unknown area/);
});

test("a single topic at a depth centres in its area band; a pair splits it", () => {
    const nodes = [
        node({ id: "root", area: "calculus", prereqs: [] }),
        node({ id: "solo", area: "calculus", prereqs: ["root"] }),
        node({ id: "twinA", area: "calculus", prereqs: ["solo"] }),
        node({ id: "twinB", area: "calculus", prereqs: ["solo"] }),
    ];
    const { nodes: placed } = layoutGraph(nodes);
    const at = (id: string) => placed.find((p) => p.node.id === id)!;

    // root and solo are alone at their depth, so they share the band centre.
    expect(at("root").cx).toBe(at("solo").cx);
    // the twins straddle that centre, evenly and in input order.
    expect(at("twinA").cx).toBeLessThan(at("root").cx);
    expect(at("twinB").cx).toBeGreaterThan(at("root").cx);
    expect(at("root").cx - at("twinA").cx).toBeCloseTo(at("twinB").cx - at("root").cx, 5);
});

test("topics at the same depth share a top edge; a centred column shares a left edge", () => {
    const nodes = [
        node({ id: "root", area: "calculus", prereqs: [] }),
        node({ id: "mid", area: "calculus", prereqs: ["root"] }),
        node({ id: "leftPair", area: "calculus", prereqs: ["mid"] }),
        node({ id: "rightPair", area: "calculus", prereqs: ["mid"] }),
    ];
    const { nodes: placed } = layoutGraph(nodes);
    const at = (id: string) => placed.find((p) => p.node.id === id)!;

    // same depth => same row => same y (top edge).
    expect(at("leftPair").y).toBe(at("rightPair").y);
    // both alone at their depth => centred => same x (left edge).
    expect(at("root").x).toBe(at("mid").x);
    // every edge points strictly downward.
    const { edges } = layoutGraph(nodes);
    for (const edge of edges) {
        expect(edge.y2).toBeGreaterThan(edge.y1);
    }
});

test("a same-column edge that skips a row bows out around the topics between", () => {
    const nodes = [
        node({ id: "a", prereqs: [] }),
        node({ id: "b", prereqs: ["a"] }),
        node({ id: "c", prereqs: ["b"] }),
        // a → d skips straight down the same column, through b and c.
        node({ id: "d", prereqs: ["c", "a"] }),
    ];
    const { edges } = layoutGraph(nodes);

    const skip = edges.find((e) => e.fromId === "a" && e.toId === "d")!;
    expect(Math.abs(skip.bow ?? 0)).toBe(72);

    // The plain chain links stay on the straight path.
    const chain = edges.find((e) => e.fromId === "b" && e.toId === "c")!;
    expect(chain.bow).toBeUndefined();
});

test("study-next is the topic itself when it is open", () => {
    const topic = node({ id: "open", lockState: "unlocked" });
    expect(studyNextWithinPrereqs(topic, byId([topic]))).toEqual({ kind: "open" });
});

test("a locked topic points at the studyable prerequisite with the most at risk", () => {
    const nodes = [
        node({ id: "deep", lockState: "locked", weight: 9, avgRecall: 0 }),
        node({ id: "openLow", lockState: "unlocked", weight: 2, avgRecall: 0.1 }),
        node({ id: "openHigh", lockState: "in_progress", weight: 6, avgRecall: 0.2 }),
        node({ id: "child", lockState: "locked", prereqs: ["deep", "openLow", "openHigh"] }),
    ];
    const advice = studyNextWithinPrereqs(nodes[3], byId(nodes));
    // openHigh is studyable (beats the deeper-locked "deep") and carries more
    // points at risk than openLow, so it is the recommendation.
    expect(advice).toEqual({ kind: "blocked", target: nodes[2] });
});

test("wrapLabel keeps the whole title when it fits and trims with an ellipsis when it does not", () => {
    expect(wrapLabel("Linear algebra")).toEqual(["Linear algebra"]);
    const long = wrapLabel("Precalculus, trigonometry & coordinate geometry", 18, 2);
    expect(long.length).toBe(2);
    expect(long[long.length - 1].endsWith("…")).toBe(true);
});

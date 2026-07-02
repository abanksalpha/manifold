// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import {
    computeScores,
    READINESS_MIN_COVERAGE,
    READINESS_MIN_INDEPENDENT_REVIEWS,
    type ScoringConfig,
    selectStudyNext,
    type TopicStat,
} from "./scoring";

function topic(overrides: Partial<TopicStat> = {}): TopicStat {
    return {
        id: "t",
        title: "Topic",
        area: "calculus",
        tier: "relearn",
        weight: 1,
        lockState: "unlocked",
        total: 0,
        avgRecall: 0,
        performance: 0,
        coverage: 0,
        gradedReviews: 0,
        independentReviews: 0,
        ...overrides,
    };
}

/** A ScoringConfig fixture mirroring `rslib/src/manifold/blueprint.json`. */
function config(overrides: Partial<ScoringConfig> = {}): ScoringConfig {
    return {
        scaleMin: 200,
        scaleMax: 990,
        distributionMean: 676,
        distributionSd: 154,
        etsAnchors: [
            { scaled: 900, percentileBelow: 93 },
            { scaled: 860, percentileBelow: 86 },
            { scaled: 820, percentileBelow: 77 },
            { scaled: 800, percentileBelow: 74 },
            { scaled: 780, percentileBelow: 70 },
            { scaled: 740, percentileBelow: 62 },
            { scaled: 700, percentileBelow: 54 },
            { scaled: 680, percentileBelow: 50 },
            { scaled: 660, percentileBelow: 46 },
            { scaled: 620, percentileBelow: 38 },
            { scaled: 580, percentileBelow: 30 },
            { scaled: 540, percentileBelow: 22 },
            { scaled: 500, percentileBelow: 14 },
            { scaled: 460, percentileBelow: 7 },
            { scaled: 420, percentileBelow: 3 },
        ],
        medianRawFraction: 0.5,
        performanceSd: 0.18,
        coverageBandLambda: 0.1,
        ...overrides,
    };
}

test("memory is the blueprint-weighted mean of recall over authored topics", () => {
    const nodes = [
        topic({ id: "a", weight: 3, total: 5, avgRecall: 0.8 }),
        topic({ id: "b", weight: 1, total: 5, avgRecall: 0.4 }),
        // total === 0: no authored skills, so excluded from Memory entirely.
        topic({ id: "c", weight: 10, total: 0, avgRecall: 0.9 }),
    ];

    const { memory } = computeScores(nodes, config());

    expect(memory).not.toBeNull();
    // (3*0.8 + 1*0.4) / (3+1) = 0.7, untouched by the total===0 topic.
    expect(memory!.value).toBeCloseTo(0.7, 5);
    expect(memory!.low).toBeCloseTo(0.4, 5);
    expect(memory!.high).toBeCloseTo(0.8, 5);
    expect(memory!.contributingTopics).toBe(2);
    expect(memory!.totalTopics).toBe(3);
});

test("performance reads not-measured until a topic has independent reviews", () => {
    const unmeasured = computeScores([
        // graded reviews exist, but none are unsupported (Independent): no signal.
        topic({ total: 5, avgRecall: 0.6, performance: 0.5, gradedReviews: 40, independentReviews: 0 }),
    ], config());
    expect(unmeasured.performance).toBeNull();

    const measured = computeScores([
        topic({ id: "a", weight: 2, performance: 0.6, independentReviews: 30 }),
        topic({ id: "b", weight: 2, performance: 0.4, independentReviews: 10 }),
        // independentReviews === 0: excluded from Performance.
        topic({ id: "c", weight: 9, performance: 0.9, independentReviews: 0 }),
    ], config());
    expect(measured.performance).not.toBeNull();
    expect(measured.performance!.value).toBeCloseTo(0.5, 5);
    expect(measured.performance!.contributingTopics).toBe(2);
});

test("coverage is weight*coverage summed over all topics, divided by total weight", () => {
    const { coverage } = computeScores([
        topic({ id: "a", weight: 3, coverage: 1 }),
        topic({ id: "b", weight: 1, coverage: 0 }),
    ], config());
    // (3*1 + 1*0) / (3+1) = 0.75
    expect(coverage).toBeCloseTo(0.75, 5);
});

test("readiness abstains below the give-up line and names the missing evidence", () => {
    const nodes = [
        topic({
            id: "a",
            weight: 3,
            total: 5,
            avgRecall: 0.5,
            coverage: 0.4,
            performance: 0.5,
            independentReviews: 40,
        }),
        topic({
            id: "b",
            weight: 1,
            total: 5,
            avgRecall: 0.5,
            coverage: 0.4,
            performance: 0.5,
            independentReviews: 20,
        }),
    ];

    const { readiness, gate } = computeScores(nodes, config());

    expect(gate.met).toBe(false);
    expect(readiness.state).toBe("abstaining");
    if (readiness.state !== "abstaining") {
        throw new Error("expected abstaining");
    }
    expect(readiness.independentReviews).toBe(60);
    expect(readiness.reviewsNeeded).toBe(READINESS_MIN_INDEPENDENT_REVIEWS - 60);
    expect(readiness.coverage).toBeCloseTo(0.4, 5);
    expect(readiness.coverageNeeded).toBeCloseTo(READINESS_MIN_COVERAGE - 0.4, 5);
});

test("readiness abstains when only supported (learning) attempts exist", () => {
    // 500 graded reviews but zero Independent: this is scaffolded practice, not
    // evidence. Readiness must stay silent (D20/D21).
    const { readiness, gate } = computeScores([
        topic({
            id: "a",
            weight: 1,
            total: 5,
            avgRecall: 0.6,
            coverage: 0.9,
            performance: 0,
            gradedReviews: 500,
            independentReviews: 0,
        }),
    ], config());

    expect(gate.met).toBe(false);
    if (readiness.state !== "abstaining") {
        throw new Error("expected abstaining");
    }
    expect(readiness.reviewsNeeded).toBe(READINESS_MIN_INDEPENDENT_REVIEWS);
});

test("readiness projects an ETS-anchored range once the gate is met", () => {
    // p̄ = 0.5 (the median raw fraction) maps to the 50th-percentile anchor, 680.
    const { readiness, gate } = computeScores([
        topic({ id: "a", weight: 1, total: 5, avgRecall: 0.7, coverage: 1, performance: 0.5, independentReviews: 250 }),
    ], config());

    expect(gate.met).toBe(true);
    expect(readiness.state).toBe("projected");
    if (readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    expect(readiness.scaledPoint).toBe(680);
    // Single topic, full coverage: the band collapses to the point.
    expect(readiness.scaledLow).toBeLessThanOrEqual(readiness.scaledPoint);
    expect(readiness.scaledHigh).toBeGreaterThanOrEqual(readiness.scaledPoint);
    expect(readiness.confidence).toBe("provisional");
    expect(readiness.independentReviews).toBe(250);
});

test("readiness maps stronger performance to a higher scaled score, within scale", () => {
    const strong = computeScores([
        topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.75, independentReviews: 300 }),
    ], config());
    const weak = computeScores([
        topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.35, independentReviews: 300 }),
    ], config());

    if (strong.readiness.state !== "projected" || weak.readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    expect(strong.readiness.scaledPoint).toBeGreaterThan(weak.readiness.scaledPoint);
    expect(strong.readiness.scaledPoint).toBeLessThanOrEqual(990);
    expect(weak.readiness.scaledPoint).toBeGreaterThanOrEqual(200);
});

test("readiness reports confident once the higher evidence bar is cleared", () => {
    const nodes = [
        topic({ id: "a", weight: 3, total: 5, coverage: 0.85, performance: 0.6, independentReviews: 400 }),
        topic({ id: "b", weight: 2, total: 5, coverage: 0.85, performance: 0.5, independentReviews: 300 }),
    ];

    const { readiness } = computeScores(nodes, config());
    if (readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    // 700 independent reviews, coverage 0.85: both above the confident bar.
    expect(readiness.confidence).toBe("confident");
    // A real band and a driver readout are present. Topic a drags hardest:
    // weight 3 * (1 - 0.6) = 1.2 exceeds b's 2 * (1 - 0.5) = 1.0.
    expect(readiness.scaledHigh).toBeGreaterThan(readiness.scaledLow);
    expect(readiness.drivers.length).toBeGreaterThan(0);
    expect(readiness.drivers[0].id).toBe("a");
});

test("study-next picks the open topic with the most blueprint points at risk", () => {
    const nodes = [
        topic({ id: "calc", weight: 8, lockState: "in_progress", avgRecall: 0.9 }),
        topic({ id: "algebra", weight: 5, lockState: "unlocked", avgRecall: 0.2 }),
        topic({ id: "topology", weight: 12, lockState: "locked", avgRecall: 0.0 }),
        topic({ id: "limits", weight: 10, lockState: "mastered", avgRecall: 0.95 }),
    ];

    const studyNext = selectStudyNext(nodes);

    expect(studyNext).not.toBeNull();
    expect(studyNext!.id).toBe("algebra");
    expect(studyNext!.priority).toBeCloseTo(4.0, 5);
});

test("study-next is null when nothing is open to study", () => {
    const nodes = [
        topic({ id: "a", lockState: "locked" }),
        topic({ id: "b", lockState: "mastered" }),
    ];
    expect(selectStudyNext(nodes)).toBeNull();

    const { readiness } = computeScores(nodes, config());
    if (readiness.state !== "abstaining") {
        throw new Error("expected abstaining");
    }
    expect(readiness.studyNext).toBeNull();
});

test("an empty topic graph is an error, not a silent zero", () => {
    expect(() => computeScores([], config())).toThrow();
});

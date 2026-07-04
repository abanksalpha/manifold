// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import {
    computeScores,
    hoursToTarget,
    maturityResidue,
    READINESS_MIN_COVERAGE,
    READINESS_MIN_INDEPENDENT_REVIEWS,
    type ScoringConfig,
    selectStudyNext,
    selectTarget,
    targetLadder,
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
        levelIndependent: 0,
        levelRevisited: 0,
        ...overrides,
    };
}

/**
 * A ScoringConfig fixture mirroring `rslib/src/manifold/blueprint.json`: the
 * current ETS Mathematics anchors (Guide to the Use of Scores, 2021–2024) and
 * the readiness-mapping constants (target ladder, log curve, residue ceiling).
 */
function config(overrides: Partial<ScoringConfig> = {}): ScoringConfig {
    return {
        scaleMin: 200,
        scaleMax: 990,
        distributionMean: 680,
        distributionSd: 161,
        etsAnchors: [
            { scaled: 900, percentileBelow: 91 },
            { scaled: 880, percentileBelow: 88 },
            { scaled: 860, percentileBelow: 84 },
            { scaled: 840, percentileBelow: 79 },
            { scaled: 820, percentileBelow: 75 },
            { scaled: 800, percentileBelow: 71 },
            { scaled: 780, percentileBelow: 68 },
            { scaled: 760, percentileBelow: 64 },
            { scaled: 740, percentileBelow: 61 },
            { scaled: 720, percentileBelow: 56 },
            { scaled: 700, percentileBelow: 53 },
            { scaled: 680, percentileBelow: 49 },
            { scaled: 660, percentileBelow: 46 },
            { scaled: 640, percentileBelow: 41 },
            { scaled: 620, percentileBelow: 38 },
            { scaled: 600, percentileBelow: 34 },
            { scaled: 580, percentileBelow: 30 },
            { scaled: 560, percentileBelow: 25 },
            { scaled: 540, percentileBelow: 22 },
            { scaled: 520, percentileBelow: 18 },
            { scaled: 500, percentileBelow: 14 },
            { scaled: 480, percentileBelow: 11 },
            { scaled: 460, percentileBelow: 8 },
            { scaled: 440, percentileBelow: 6 },
            { scaled: 420, percentileBelow: 4 },
            { scaled: 400, percentileBelow: 3 },
            { scaled: 380, percentileBelow: 2 },
        ],
        medianRawFraction: 0.5,
        performanceSd: 0.18,
        coverageBandLambda: 0.1,
        lapseBandLambda: 0.12,
        targets: [
            { id: "median", label: "Median", scaledPoint: 680, scaledLow: 660, scaledHigh: 700 },
            { id: "strong", label: "Strong", scaledPoint: 800, scaledLow: 780, scaledHigh: 820 },
            {
                id: "exceptional",
                label: "Exceptional",
                scaledPoint: 860,
                scaledLow: 840,
                scaledHigh: 880,
            },
        ],
        hoursCurve: { scaledFloor: 560, pointsPerLogHour: 120, hoursScale: 12 },
        maturityResidue: { items: 3, scaledPoints: 35 },
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
    // p̄ = 0.5 (the median raw fraction) lands at the 50th percentile, which on
    // the ETS 2021–2024 Math table (680 = 49th, 700 = 53rd) interpolates to 685,
    // rounded to the scale's 10-point granularity → 690.
    const { readiness, gate } = computeScores([
        topic({ id: "a", weight: 1, total: 5, avgRecall: 0.7, coverage: 1, performance: 0.5, independentReviews: 250 }),
    ], config());

    expect(gate.met).toBe(true);
    expect(readiness.state).toBe("projected");
    if (readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    expect(readiness.scaledPoint).toBe(690);
    // Single topic, full coverage, no lapses: the band collapses to the point.
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

// --- Readiness upgrades (D29/D30/D26) --------------------------------------

test("the target ladder exposes median, strong and exceptional with scaled bands", () => {
    const ladder = targetLadder(config());
    expect(ladder.map((t) => t.id)).toEqual(["median", "strong", "exceptional"]);
    for (const t of ladder) {
        // Each rung is a band around its point, not a bare number.
        expect(t.scaledLow).toBeLessThanOrEqual(t.scaledPoint);
        expect(t.scaledPoint).toBeLessThanOrEqual(t.scaledHigh);
    }
    // The ladder climbs: each rung sits above the previous.
    expect(ladder[0].scaledPoint).toBeLessThan(ladder[1].scaledPoint);
    expect(ladder[1].scaledPoint).toBeLessThan(ladder[2].scaledPoint);

    // The selector returns a chosen rung and refuses an unknown one.
    expect(selectTarget(config(), "strong").scaledPoint).toBe(800);
    expect(() => selectTarget(config(), "nope")).toThrow();
});

test("an empty target ladder is an error, not a silent empty goal set", () => {
    expect(() => targetLadder(config({ targets: [] }))).toThrow();
});

test("hours-to-target is zero once reached and grows with a farther target", () => {
    const curve = config().hoursCurve!;
    expect(hoursToTarget(800, 700, curve)).toBe(0); // already past it
    expect(hoursToTarget(700, 700, curve)).toBe(0); // exactly at it
    const near = hoursToTarget(620, 700, curve);
    const far = hoursToTarget(620, 800, curve);
    expect(near).toBeGreaterThan(0);
    expect(far).toBeGreaterThan(near);
});

test("hours-to-target shows logarithmic diminishing returns near the top", () => {
    const curve = config().hoursCurve!;
    // The same 60-point climb costs far more hours higher up the scale — the
    // Messick-style top-percentile tax.
    const lowClimb = hoursToTarget(620, 680, curve);
    const highClimb = hoursToTarget(800, 860, curve);
    expect(highClimb).toBeGreaterThan(lowClimb);
    // Concretely (floor 560, 120 pts/e-fold, 12h scale): ~12.8h vs ~57.5h.
    expect(lowClimb).toBeCloseTo(12.83, 1);
    expect(highClimb).toBeCloseTo(57.52, 1);
});

test("the maturity residue is exposed and caps the projected ceiling", () => {
    const residue = maturityResidue(config());
    expect(residue.items).toBe(3);
    expect(residue.scaledPoints).toBe(35);
    expect(residue.promisedCeiling).toBe(955); // 990 − 35

    // A near-perfect in-app performance maps above the raw ceiling, but the app
    // refuses to promise past the residue: the projection is capped at 955.
    const { readiness } = computeScores([
        topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.99, independentReviews: 800 }),
    ], config());
    if (readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    expect(readiness.residue.promisedCeiling).toBe(955);
    expect(readiness.scaledHigh).toBeLessThanOrEqual(955);
    // The cap bites: the uncapped map would clamp to the raw scale max, 990.
    expect(readiness.scaledPoint).toBe(955);
});

test("maturity residue missing from config is an error, not a whole-scale promise", () => {
    expect(() => maturityResidue(config({ maturityResidue: undefined }))).toThrow();
    // The same omission fails loudly on the projected path, never silently.
    expect(() =>
        computeScores([
            topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.5, independentReviews: 250 }),
        ], config({ maturityResidue: undefined }))
    ).toThrow();
});

test("a high lapse rate widens the readiness band (D26)", () => {
    // Identical evidence; the fragile collection has graduated cards that lapsed.
    const base = computeScores([
        topic({
            id: "a",
            weight: 1,
            total: 5,
            coverage: 1,
            performance: 0.5,
            independentReviews: 250,
            levelIndependent: 20,
            levelRevisited: 0,
        }),
    ], config());
    const fragile = computeScores([
        topic({
            id: "a",
            weight: 1,
            total: 5,
            coverage: 1,
            performance: 0.5,
            independentReviews: 250,
            levelIndependent: 10,
            levelRevisited: 10,
        }),
    ], config());

    if (base.readiness.state !== "projected" || fragile.readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    expect(base.readiness.lapseRate).toBe(0);
    expect(fragile.readiness.lapseRate).toBeCloseTo(0.5, 5);
    // No lapses, full coverage, single topic: the base band collapses to a point.
    const baseWidth = base.readiness.scaledHigh - base.readiness.scaledLow;
    const fragileWidth = fragile.readiness.scaledHigh - fragile.readiness.scaledLow;
    expect(baseWidth).toBe(0);
    expect(fragileWidth).toBeGreaterThan(baseWidth);
});

test("projected readiness scores each target with a gap and hours-to-target", () => {
    // A weak-but-gated learner sits below every target, so each rung shows a gap
    // and a positive hours-to-target that climbs with the target height.
    const { readiness } = computeScores([
        topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.4, independentReviews: 300 }),
    ], config());
    if (readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    const byId = new Map(readiness.targets.map((t) => [t.id, t]));
    const median = byId.get("median")!;
    const exceptional = byId.get("exceptional")!;
    expect(median.reached).toBe(false);
    expect(median.gapPoints).toBeGreaterThan(0);
    expect(median.hoursToTarget).toBeGreaterThan(0);
    expect(exceptional.hoursToTarget).toBeGreaterThan(median.hoursToTarget);
});

test("readiness stamps last-updated in both states", () => {
    const when = 1_700_000_000_000;
    const abstaining = computeScores(
        [
            topic({ id: "a", weight: 1, total: 5, coverage: 0.4, performance: 0.5, independentReviews: 10 }),
        ],
        config(),
        when,
    );
    expect(abstaining.readiness.state).toBe("abstaining");
    expect(abstaining.readiness.lastUpdated).toBe(when);

    const projected = computeScores(
        [
            topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.5, independentReviews: 250 }),
        ],
        config(),
        when,
    );
    expect(projected.readiness.state).toBe("projected");
    expect(projected.readiness.lastUpdated).toBe(when);
});

test("projected readiness carries all seven honest fields, never a bare scalar", () => {
    const { readiness } = computeScores(
        [
            topic({ id: "a", weight: 1, total: 5, coverage: 1, performance: 0.6, independentReviews: 250 }),
        ],
        config(),
        42,
    );
    if (readiness.state !== "projected") {
        throw new Error("expected projected");
    }
    // 1 point · 2 range · 3 % covered · 4 how-sure · 5 last-updated · 6
    // reasons/drivers · 7 give-up state.
    expect(typeof readiness.scaledPoint).toBe("number");
    expect(readiness.scaledHigh).toBeGreaterThanOrEqual(readiness.scaledLow);
    expect(readiness.coverage).toBeCloseTo(1, 5);
    expect(["provisional", "confident"]).toContain(readiness.confidence);
    expect(readiness.lastUpdated).toBe(42);
    expect(Array.isArray(readiness.drivers)).toBe(true);
    expect(readiness.state).toBe("projected");
    // plus the D29 additions: an honest target ladder and the residue ceiling.
    expect(readiness.targets.map((t) => t.id)).toEqual(["median", "strong", "exceptional"]);
    expect(readiness.residue.promisedCeiling).toBe(955);
});

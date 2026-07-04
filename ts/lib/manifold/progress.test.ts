// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import { buildProgressData, MAX_MIRRORED_TOPICS } from "./progress";
import type { ScoreReport, TopicStat } from "./scoring";

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

function projectedReport(overrides: Partial<ScoreReport> = {}): ScoreReport {
    return {
        memory: { value: 0.8, low: 0.6, high: 0.95, contributingTopics: 3, totalTopics: 3 },
        performance: null,
        coverage: 0.42,
        totalIndependentReviews: 210,
        gate: { met: true, minIndependentReviews: 200, minCoverage: 0.5 },
        readiness: {
            state: "projected",
            scaledPoint: 720,
            scaledLow: 700,
            scaledHigh: 740,
            coverage: 0.42,
            independentReviews: 210,
            confidence: "provisional",
            drivers: [],
            lastUpdated: 0,
            targets: [],
            lapseRate: 0.1,
            residue: { items: 2, scaledPoints: 30, promisedCeiling: 960 },
        },
        ...overrides,
    };
}

test("maps metrics, coverage, and a projected readiness onto the mirror", () => {
    const nodes = [
        topic({ id: "calc-limits", title: "Limits", avgRecall: 0.8, performance: 0.7, coverage: 0.5 }),
        topic({ id: "alg-groups", area: "algebra", title: "Groups", lockState: "in_progress" }),
    ];
    const data = buildProgressData(projectedReport(), nodes);

    // memory present, performance absent (null) -> present:false with zeroed numbers.
    expect(data.memory).toEqual({ present: true, value: 0.8, low: 0.6, high: 0.95 });
    expect(data.performance).toEqual({ present: false, value: 0, low: 0, high: 0 });

    expect(data.coverage).toBe(0.42);
    expect(data.totalIndependentReviews).toBe(210);
    expect(data.readinessState).toBe("projected");
    expect(data.readiness).toEqual({
        state: "projected",
        scaledPoint: 720,
        scaledLow: 700,
        scaledHigh: 740,
        confidence: "provisional",
        lapseRate: 0.1,
    });

    expect(data.topics).toHaveLength(2);
    expect(data.topics[0]).toEqual({
        id: "calc-limits",
        title: "Limits",
        area: "calculus",
        tier: "relearn",
        lockState: "unlocked",
        avgRecall: 0.8,
        performance: 0.7,
        coverage: 0.5,
    });
});

test("maps an abstaining readiness to the evidence still owed", () => {
    const report = projectedReport({
        readiness: {
            state: "abstaining",
            independentReviews: 40,
            reviewsNeeded: 160,
            coverage: 0.3,
            coverageNeeded: 0.2,
            studyNext: null,
            lastUpdated: 0,
        },
    });
    const data = buildProgressData(report, [topic()]);
    expect(data.readinessState).toBe("abstaining");
    expect(data.readiness).toEqual({
        state: "abstaining",
        reviewsNeeded: 160,
        coverageNeeded: 0.2,
    });
});

test("caps the mirrored topics list at MAX_MIRRORED_TOPICS", () => {
    const nodes = Array.from({ length: MAX_MIRRORED_TOPICS + 5 }, (_v, i) => topic({ id: `t${i}` }));
    const data = buildProgressData(projectedReport(), nodes);
    expect(data.topics).toHaveLength(MAX_MIRRORED_TOPICS);
});

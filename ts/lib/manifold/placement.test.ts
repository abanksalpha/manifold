// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { describe, expect, it } from "vitest";

import { COURSES, knownTopicIds, topicsForCourses, verdictForTopic } from "./placement";

// All 33 blueprint topic ids (rslib/src/manifold/blueprint.json).
const ALL_TOPICS = [
    "elementary_algebra",
    "precalc_functions",
    "trigonometry",
    "coordinate_geometry",
    "limits_continuity",
    "differential_calc",
    "applications_derivatives",
    "integral_calc",
    "integration_techniques",
    "applications_integrals",
    "sequences_series",
    "multivariable_diff",
    "multivariable_int",
    "vector_calc",
    "differential_equations",
    "number_theory",
    "linear_algebra_core",
    "vector_spaces",
    "eigen",
    "group_theory",
    "rings_fields",
    "logic_sets",
    "combinatorics",
    "graph_theory",
    "algorithms",
    "probability",
    "statistics",
    "real_analysis_sequences",
    "real_analysis_topology",
    "metric_topology",
    "complex_analysis",
    "geometry",
    "numerical_analysis",
];

describe("course map", () => {
    it("covers every blueprint topic at least once", () => {
        const covered = new Set(COURSES.flatMap((c) => c.topicIds));
        for (const id of ALL_TOPICS) {
            expect(covered.has(id), `topic ${id} is uncovered`).toBe(true);
        }
    });

    it("maps only known topic ids", () => {
        const known = new Set(ALL_TOPICS);
        for (const c of COURSES) {
            for (const id of c.topicIds) {
                expect(known.has(id), `${c.id} maps unknown ${id}`).toBe(true);
            }
        }
    });

    it("dedupes topics across selected courses", () => {
        const calc1 = COURSES.find((c) => c.id === "calc_1")!;
        const topics = topicsForCourses([calc1.id, calc1.id]);
        expect(topics.length).toBe(new Set(topics).size);
    });
});

describe("verdicts", () => {
    it("known at >=50% probe accuracy", () => {
        expect(verdictForTopic({ answered: 2, correct: 1 }, false)).toBe("known");
    });
    it("shaky between 25% and 50%", () => {
        expect(verdictForTopic({ answered: 4, correct: 1 }, false)).toBe("shaky");
    });
    it("new below 25%", () => {
        expect(verdictForTopic({ answered: 4, correct: 0 }, false)).toBe("new");
    });
    it("self-reported but untested counts as known (labeled prior)", () => {
        expect(verdictForTopic(undefined, true)).toBe("known");
    });
    it("not reported and untested is new", () => {
        expect(verdictForTopic(undefined, false)).toBe("new");
    });
});

describe("known topic ids include the prereq closure", () => {
    it("adds a reported topic's transitive prerequisites", () => {
        // differential_calc <- limits_continuity <- {precalc_functions, trigonometry}
        const prereqs = new Map<string, string[]>([
            ["differential_calc", ["limits_continuity"]],
            ["limits_continuity", ["precalc_functions", "trigonometry"]],
            ["precalc_functions", ["elementary_algebra"]],
            ["trigonometry", ["precalc_functions"]],
            ["elementary_algebra", []],
        ]);
        const tallies = new Map([["differential_calc", { answered: 2, correct: 2 }]]);
        const known = knownTopicIds(["calc_1"], tallies, prereqs);
        // calc_1 maps to differential_calc (known) -> pull in its prereq chain.
        expect(known).toContain("differential_calc");
        expect(known).toContain("limits_continuity");
        expect(known).toContain("elementary_algebra");
    });
});

// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Onboarding placement client logic: the course -> topic map, the per-topic
 * verdict from probe results + self-report, the seed set (known topics plus the
 * transitive prerequisite closure of the reported courses), and thin wrappers
 * over the placement RPCs. Kept free of Svelte so it is unit-testable.
 */

import {
    applyPlacement,
    buildPlacementExam,
    claimAccount as claimAccountRpc,
    getPlacementState,
} from "@generated/backend";

import type { QueueItem } from "$lib/manifold/session";

/** A course the learner may have taken, mapped to the blueprint topics it covers. */
export interface Course {
    id: string;
    label: string;
    topicIds: string[];
}

/**
 * Covers all 33 blueprint topics (rslib/src/manifold/blueprint.json). The engine
 * validates every id server-side, so a drifted id fails loudly rather than
 * silently dropping a topic.
 */
export const COURSES: Course[] = [
    {
        id: "precalc",
        label: "Precalculus",
        topicIds: ["elementary_algebra", "precalc_functions", "trigonometry", "coordinate_geometry"],
    },
    {
        id: "calc_1",
        label: "Calculus I (differential)",
        topicIds: ["limits_continuity", "differential_calc", "applications_derivatives"],
    },
    {
        id: "calc_2",
        label: "Calculus II (integral & series)",
        topicIds: ["integral_calc", "integration_techniques", "applications_integrals", "sequences_series"],
    },
    {
        id: "calc_3",
        label: "Calculus III (multivariable)",
        topicIds: ["multivariable_diff", "multivariable_int", "vector_calc"],
    },
    { id: "odes", label: "Differential equations", topicIds: ["differential_equations"] },
    {
        id: "linear_algebra",
        label: "Linear algebra",
        topicIds: ["linear_algebra_core", "vector_spaces", "eigen"],
    },
    { id: "abstract_algebra", label: "Abstract algebra", topicIds: ["group_theory", "rings_fields"] },
    { id: "number_theory", label: "Number theory", topicIds: ["number_theory"] },
    {
        id: "discrete",
        label: "Discrete math / combinatorics",
        topicIds: ["logic_sets", "combinatorics", "graph_theory", "algorithms"],
    },
    { id: "prob_stats", label: "Probability & statistics", topicIds: ["probability", "statistics"] },
    {
        id: "real_analysis",
        label: "Real analysis",
        topicIds: ["real_analysis_sequences", "real_analysis_topology", "metric_topology"],
    },
    { id: "complex_analysis", label: "Complex analysis", topicIds: ["complex_analysis"] },
    { id: "geometry", label: "Geometry", topicIds: ["geometry"] },
    { id: "numerical", label: "Numerical analysis", topicIds: ["numerical_analysis"] },
];

/** Probe accuracy at/above which a tested topic counts as known. */
export const KNOWN_ACCURACY = 0.5;
/** Probe accuracy at/above which a tested topic counts as shaky (else new). */
export const SHAKY_ACCURACY = 0.25;
/** Default probes drawn per topic. */
export const DEFAULT_PER_TOPIC = 1;

const COURSE_BY_ID = new Map(COURSES.map((c) => [c.id, c]));

/** The deduped union of blueprint topics covered by the selected courses. */
export function topicsForCourses(courseIds: string[]): string[] {
    const out = new Set<string>();
    for (const id of courseIds) {
        const course = COURSE_BY_ID.get(id);
        if (course) {
            for (const t of course.topicIds) {
                out.add(t);
            }
        }
    }
    return [...out];
}

export interface ProbeTally {
    answered: number;
    correct: number;
}

export type Verdict = "known" | "shaky" | "new";

/**
 * Per-topic verdict. A tested topic is graded by probe accuracy; an untested
 * topic (all probes abstained or none drawn) falls back to self-report: reported
 * -> known (a labeled prior confirmed later by study), not reported -> new.
 */
export function verdictForTopic(tally: ProbeTally | undefined, reported: boolean): Verdict {
    if (!tally || tally.answered === 0) {
        return reported ? "known" : "new";
    }
    const accuracy = tally.correct / tally.answered;
    if (accuracy >= KNOWN_ACCURACY) {
        return "known";
    }
    if (accuracy >= SHAKY_ACCURACY) {
        return "shaky";
    }
    return "new";
}

/** Transitive prerequisite closure of a set of topic ids. */
function prereqClosure(topicIds: Iterable<string>, prereqsById: Map<string, string[]>): Set<string> {
    const out = new Set<string>();
    const stack = [...topicIds];
    while (stack.length) {
        const id = stack.pop()!;
        if (out.has(id)) {
            continue;
        }
        out.add(id);
        for (const p of prereqsById.get(id) ?? []) {
            if (!out.has(p)) {
                stack.push(p);
            }
        }
    }
    return out;
}

/**
 * The topics to seed: every topic whose verdict is `known`, plus the transitive
 * prerequisite closure of the reported courses' topics (knowing X implies its
 * prerequisites), so seeding leaves the DAG coherent and the reported topics
 * actually unlock. Shaky/new topics are left to normal teaching.
 */
export function knownTopicIds(
    reportedCourseIds: string[],
    tallies: Map<string, ProbeTally>,
    prereqsById: Map<string, string[]>,
): string[] {
    const reportedSet = new Set(topicsForCourses(reportedCourseIds));
    const known = new Set<string>();
    for (const topicId of reportedSet) {
        if (verdictForTopic(tallies.get(topicId), true) === "known") {
            known.add(topicId);
        }
    }
    // Any topic tested well even if not reported.
    for (const [topicId, tally] of tallies) {
        if (verdictForTopic(tally, reportedSet.has(topicId)) === "known") {
            known.add(topicId);
        }
    }
    return [...prereqClosure(known, prereqsById)];
}

// --- RPC wrappers -------------------------------------------------------------

const IMPORT_SEED_URL = "/_anki/manifoldImportSeed";

/** Whether onboarding is done (or the collection already has study history). */
export async function fetchPlacementState(): Promise<boolean> {
    const res = await getPlacementState({});
    return res.completed;
}

/**
 * Bind the local collection to the signed-in Google account. Returns true when a
 * *different* account signed in on this device, in which case the engine has
 * already wiped the local Manifold deck and cleared onboarding, so the caller
 * routes this fresh account to placement. Claiming an unclaimed collection, or
 * re-confirming the same account, returns false (no reset).
 */
export async function claimAccount(uid: string): Promise<boolean> {
    const res = await claimAccountRpc({ uid });
    return res.reset;
}

/** Build the cold diagnostic queue for the given topics, mapped to QueueItems. */
export async function buildPlacementQueue(
    topicIds: string[],
    perTopic = DEFAULT_PER_TOPIC,
): Promise<QueueItem[]> {
    const res = await buildPlacementExam({ topicIds, perTopic });
    return res.items.map((item) => ({
        cardId: item.cardId,
        skillId: item.skillId,
        skillName: item.skillName,
        topicId: item.topicId,
        topicTitle: item.topicTitle,
        tier: item.tier,
        level: item.level,
    }));
}

/** Seed the known topics and mark onboarding done; returns the seeded count. */
export async function seedPlacement(known: string[]): Promise<number> {
    const res = await applyPlacement({ knownTopicIds: known });
    return res.seededCards;
}

/** Import the GRE seed deck (idempotent). Throws loudly on failure. */
export async function importSeedDeck(): Promise<{ added: number; skipped: number }> {
    const res = await fetch(IMPORT_SEED_URL, {
        method: "POST",
        headers: { "Content-Type": "application/binary" },
        body: new TextEncoder().encode("{}"),
    });
    if (!res.ok) {
        throw new Error(`seed import failed: ${res.status}`);
    }
    const parsed = JSON.parse(await res.text()) as
        | { status: "ok"; added: number; skipped: number }
        | { status: "error"; detail: string };
    if (parsed.status !== "ok") {
        throw new Error(`seed import failed: ${parsed.detail}`);
    }
    return { added: parsed.added, skipped: parsed.skipped };
}

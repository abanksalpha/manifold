// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import type { LiveResponse, QueueItem, SessionStep, StepFetcher } from "./session";
import {
    abstainSummary,
    bigintReplacer,
    bigintReviver,
    CHOICE_IDS,
    choiceFor,
    hintsAllowed,
    isCorrect,
    levelLabel,
    PROBLEMS_ARE_PLACEHOLDER,
    SessionRunner,
    stepFromResponse,
    toLecture,
    toProblem,
} from "./session";

// A verified item as the live `manifoldNextProblem` endpoint returns it (D44):
// generated on the fly and proven by verify.py before it is ever sent here.
const EIGEN_ITEM = {
    stem: "What are the eigenvalues of the matrix [[3, 1], [0, 2]]?",
    choices: ["1, 6", "3, 5", "0, 5", "2, 3", "-2, -3"],
    correct_index: 3,
    solution: "The matrix is upper triangular, so the eigenvalues are the diagonal entries 3 and 2.",
    distractor_rationales: ["off by det", "trace not eigenvalue", "not singular", "sign flip"],
    source_ref: "manifold-live://eigen/eigenvalues_of_an_explicit_small_matrix",
};

function queueItem(overrides: Partial<QueueItem> = {}): QueueItem {
    return {
        cardId: 123n,
        skillId: "eigenvalues_of_an_explicit_small_matrix",
        skillName: "Eigenvalues of a small matrix",
        topicId: "eigen",
        topicTitle: "Eigenvalues & eigenvectors",
        tier: "teach",
        level: 0,
        ...overrides,
    };
}

test("the placeholder era is over: problems are real, verified live items", () => {
    expect(PROBLEMS_ARE_PLACEHOLDER).toBe(false);
});

test("toProblem maps a served item and stamps the skill's display identity", () => {
    const problem = toProblem(queueItem(), EIGEN_ITEM);

    expect(problem.stem).toContain("eigenvalues");
    expect(problem.topic).toBe("Eigenvalues & eigenvectors");
    expect(problem.tier).toBe("teach");
    expect(problem.choices.map((c) => c.id)).toEqual([...CHOICE_IDS]);
    expect(problem.choices).toHaveLength(5);
    expect(problem.correctIndex).toBe(3);
    expect(problem.choices[3].text).toBe("2, 3");
    expect(problem.solution.length).toBeGreaterThan(0);
    expect(problem.sourceRef).toContain("eigen");
});

test("toProblem fails loudly on a served item that breaks its own contract", () => {
    // Verify-before-serve is the invariant: a malformed 'ok' payload is a real bug,
    // not something to render as a broken card.
    expect(() => toProblem(queueItem(), { ...EIGEN_ITEM, choices: ["only", "four", "here", "now"] }))
        .toThrow(/exactly 5 choices/);
    expect(() => toProblem(queueItem(), { ...EIGEN_ITEM, correct_index: 9 }))
        .toThrow(/correct_index out of range/);
});

test("stepFromResponse serves a problem for an ok verdict", () => {
    const step = stepFromResponse(queueItem(), { status: "ok", item: EIGEN_ITEM });
    expect(step.kind).toBe("problem");
    if (step.kind === "problem") {
        expect(step.problem.correctIndex).toBe(3);
    }
});

test("stepFromResponse yields an honest abstain, never a fabricated problem", () => {
    const response: LiveResponse = { status: "abstain", reason: "offline", detail: "no network" };
    const step = stepFromResponse(queueItem(), response);
    expect(step.kind).toBe("abstain");
    if (step.kind === "abstain") {
        expect(step.reason).toBe("offline");
        expect(step.detail).toBe("no network");
    }
});

test("grading is objective: only the verified correct_index is correct", () => {
    const problem = toProblem(queueItem(), EIGEN_ITEM);

    // Correct index 3 is "D".
    expect(isCorrect(problem, "D")).toBe(true);
    for (const wrong of ["A", "B", "C", "E"] as const) {
        expect(isCorrect(problem, wrong)).toBe(false);
    }
    expect(isCorrect(problem, "dont-know")).toBe(false);
});

test("the correct letter differs per item, so 'A' is not a free pass", () => {
    const probItem = {
        ...EIGEN_ITEM,
        choices: ["1/9", "1/12", "1/6", "2/9", "5/36"],
        correct_index: 0,
    };
    const problem = toProblem(queueItem(), probItem);
    // Here the correct answer is "A"; on the eigen item above it was "D". The
    // letter is never a shortcut: it tracks the item's verified correct_index.
    expect(isCorrect(problem, "A")).toBe(true);
    expect(toProblem(queueItem(), EIGEN_ITEM).correctIndex).not.toBe(problem.correctIndex);
});

test("choiceFor maps a letter to its choice, and 'don't know' to null", () => {
    const problem = toProblem(queueItem(), EIGEN_ITEM);
    expect(choiceFor(problem, "C")?.index).toBe(2);
    expect(choiceFor(problem, "dont-know")).toBeNull();
});

test("levelLabel names each scaffolding level and falls back to New", () => {
    expect(levelLabel(0)).toBe("New");
    expect(levelLabel(2)).toBe("Independent");
    expect(levelLabel(99)).toBe("New");
});

test("hintsAllowed offers hints on every level except cold Independent", () => {
    expect(hintsAllowed(0)).toBe(true); // New
    expect(hintsAllowed(1)).toBe(true); // Guided
    expect(hintsAllowed(2)).toBe(false); // Independent: solved cold, no hints
    expect(hintsAllowed(3)).toBe(true); // Revisit
    expect(hintsAllowed(99)).toBe(true); // out of range renders as New
});

test("abstainSummary gives honest, plain-language copy for each reason", () => {
    expect(abstainSummary("no_key")).toMatch(/key/i);
    expect(abstainSummary("offline")).toMatch(/network|reach/i);
    expect(abstainSummary("unverified_after_retries")).toMatch(/verif/i);
    // A conceptual skill that honestly defers has its own plain line.
    expect(abstainSummary("needs_curation")).toMatch(/curat/i);
    // An unknown code still yields an honest, non-empty line (never a fake claim).
    expect(abstainSummary("something_new").length).toBeGreaterThan(0);
});

// --- lectures (Task 1) --------------------------------------------------------

test("toLecture maps a served lecture and stamps the skill's display topic", () => {
    const lecture = toLecture(queueItem(), {
        skill_id: "eigenvalues_of_an_explicit_small_matrix",
        topic_id: "eigen",
        title: "Eigenvalues of a triangular matrix",
        lecture_latex: "For a triangular matrix the eigenvalues are the diagonal "
            + "entries, so \\(\\det(A - \\lambda I) = 0\\) factors immediately.",
        anchored_item_id: "mfteach_abc123",
    });
    expect(lecture.skillId).toBe("eigenvalues_of_an_explicit_small_matrix");
    expect(lecture.topic).toBe("Eigenvalues & eigenvectors");
    expect(lecture.title).toContain("Eigenvalues");
    expect(lecture.lectureLatex).toContain("\\(");
    expect(lecture.anchoredItemId).toBe("mfteach_abc123");
});

test("toLecture fails loudly on a lecture that breaks its own contract", () => {
    expect(() =>
        toLecture(queueItem(), {
            skill_id: "eigenvalues_of_an_explicit_small_matrix",
            title: "",
            lecture_latex: "body",
        })
    ).toThrow(/missing title/);
    expect(() =>
        toLecture(queueItem(), {
            skill_id: "eigenvalues_of_an_explicit_small_matrix",
            title: "A title",
            lecture_latex: "   ",
        })
    ).toThrow(/missing lecture_latex/);
});

// --- SessionRunner: skip-ahead + honest defer (the key UX fix, D44) ------------

function queue(...skillIds: string[]): QueueItem[] {
    return skillIds.map((skillId, i) => queueItem({ cardId: BigInt(i + 1), skillId }));
}

/** A deterministic fetcher: "ok" serves the eigen problem, "abstain" defers, "throw"
 * models a served item that broke its own contract (a loud, recoverable breach). */
function fakeFetcher(plan: Record<string, "ok" | "abstain" | "throw">): StepFetcher {
    return async (item: QueueItem): Promise<SessionStep> => {
        const kind = plan[item.skillId];
        if (kind === "throw") {
            throw new Error(`served item ${item.skillId} broke its own contract`);
        }
        if (kind === "abstain") {
            return { kind: "abstain", item, reason: "needs_curation", detail: "conceptual" };
        }
        return { kind: "problem", item, problem: toProblem(item, EIGEN_ITEM) };
    };
}

test("runner serves verified skills in order and defers abstains, never dead-ending", async () => {
    const runner = new SessionRunner(
        queue("ok1", "defer2", "ok3"),
        { fetchStep: fakeFetcher({ ok1: "ok", defer2: "abstain", ok3: "ok" }), prefetchTarget: 2 },
    );

    const first = await runner.pull();
    expect(first.served?.item.skillId).toBe("ok1");
    expect(first.served?.queuePosition).toBe(1);
    expect(first.deferred).toHaveLength(0);

    // defer2 abstains, so the runner skips ahead to ok3 rather than dead-ending.
    const second = await runner.pull();
    expect(second.served?.item.skillId).toBe("ok3");
    expect(second.served?.queuePosition).toBe(3);
    expect(second.deferred).toHaveLength(1);
    expect(second.deferred[0].skillId).toBe("defer2");
    expect(second.deferred[0].reason).toBe("needs_curation");

    const third = await runner.pull();
    expect(third.served).toBeNull();
    expect(third.deferred).toHaveLength(1);
    expect(runner.served).toBe(2);
});

test("runner skips a leading run of abstains to reach the first verified problem", async () => {
    const runner = new SessionRunner(
        queue("defer1", "defer2", "ok3"),
        { fetchStep: fakeFetcher({ defer1: "abstain", defer2: "abstain", ok3: "ok" }) },
    );
    const first = await runner.pull();
    expect(first.served?.item.skillId).toBe("ok3");
    expect(first.deferred.map((d) => d.skillId)).toEqual(["defer1", "defer2"]);
});

test("when every skill defers, the runner ends honestly with no served problem", async () => {
    const runner = new SessionRunner(
        queue("defer1", "defer2"),
        { fetchStep: fakeFetcher({ defer1: "abstain", defer2: "abstain" }) },
    );
    const result = await runner.pull();
    expect(result.served).toBeNull();
    expect(result.deferred).toHaveLength(2);
    expect(runner.served).toBe(0);
});

test("a malformed served item makes pull() reject loudly, then skipCurrent recovers", async () => {
    const runner = new SessionRunner(
        queue("bad1", "ok2"),
        { fetchStep: fakeFetcher({ bad1: "throw", ok2: "ok" }) },
    );
    await expect(runner.pull()).rejects.toThrow(/broke its own contract/);
    // The failed skill stays current so it can be recovered, not silently dropped.
    expect(runner.currentItem?.skillId).toBe("bad1");

    const recovered = await runner.skipCurrent("served_item_invalid", "was invalid");
    expect(recovered.served?.item.skillId).toBe("ok2");
    expect(recovered.deferred.map((d) => d.skillId)).toEqual(["bad1"]);
});

test("bigintReplacer/reviver round-trip a QueueItem's bigint cardId losslessly", () => {
    // The persisted session snapshot carries QueueItems whose cardId is a bigint;
    // this is the load-bearing bit for resuming a session, and gradeNow needs a real
    // bigint back (a string would silently break grading), so guard the round-trip.
    const items = queue("ok1", "ok2");
    items[0] = { ...items[0], cardId: 90071992547409931n }; // > Number.MAX_SAFE_INTEGER
    const revived = JSON.parse(
        JSON.stringify(items, bigintReplacer),
        bigintReviver,
    ) as QueueItem[];

    expect(revived).toHaveLength(2);
    expect(typeof revived[0].cardId).toBe("bigint");
    expect(revived[0].cardId).toBe(90071992547409931n);
    expect(revived[1].cardId).toBe(items[1].cardId);
    expect(revived[0].skillId).toBe("ok1");
    // Values without the bigint tag pass through unchanged.
    const plain = { a: 1, b: "x", c: [true, null] };
    expect(JSON.parse(JSON.stringify(plain, bigintReplacer), bigintReviver)).toEqual(plain);
});

test("snapshotProgress + resume let a run continue from where it left off", async () => {
    const plan = fakeFetcher({ ok1: "ok", defer2: "abstain", ok3: "ok" });
    const runner = new SessionRunner(
        queue("ok1", "defer2", "ok3"),
        { fetchStep: plan, prefetchTarget: 2 },
    );

    const first = await runner.pull();
    expect(first.served?.item.skillId).toBe("ok1");

    // A snapshot records how far the run has progressed (past ok1) so it can be
    // rebuilt after a trip to the dashboard rather than restarted.
    const snap = runner.snapshotProgress();
    expect(snap.cursor).toBe(1);
    expect(snap.servedCount).toBe(1);
    expect(snap.deferred).toHaveLength(0);

    // Rebuilding on the SAME queue with that snapshot resumes at the next skill
    // (skipping the deferred defer2 to reach ok3) instead of replaying ok1.
    const resumed = new SessionRunner(
        queue("ok1", "defer2", "ok3"),
        { fetchStep: plan, prefetchTarget: 2, resume: snap },
    );
    const next = await resumed.pull();
    expect(next.served?.item.skillId).toBe("ok3");
    expect(next.served?.queuePosition).toBe(3);
    expect(next.deferred.map((d) => d.skillId)).toEqual(["defer2"]);
});

test("dispose aborts in-flight generation so nothing lingers after navigating away", async () => {
    const signals: AbortSignal[] = [];
    // A fetcher whose requests never settle on their own, so the only way they end is
    // via the abort signal the runner threads through.
    const fetchStep: StepFetcher = (_item: QueueItem, signal?: AbortSignal) => {
        if (signal) {
            signals.push(signal);
        }
        return new Promise<SessionStep>(() => {
            // intentionally never resolves; dispose() is what ends it
        });
    };
    const runner = new SessionRunner(queue("ok1", "ok2"), { fetchStep, prefetchTarget: 2 });

    // Start pulling (do not await — the fetches hang) to warm the look-ahead buffer.
    void runner.pull();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(signals.length).toBeGreaterThan(0);
    expect(signals.some((s) => s.aborted)).toBe(false);

    runner.dispose();
    // Every in-flight request is now aborted, so the browser stops waiting on a
    // generation whose result would be discarded once we have left the screen.
    expect(signals.every((s) => s.aborted)).toBe(true);
});

test("disposing mid-pull unwinds without generating the rest of the queue", async () => {
    const items = queue("a", "b", "c", "d");
    let calls = 0;
    // Assigned synchronously by the first fetchStep's Promise executor (which runs
    // during prefetch, before we ever call it), hence the definite-assignment `!`.
    let resolveFirst!: (step: SessionStep) => void;
    const fetchStep: StepFetcher = (item: QueueItem) => {
        calls += 1;
        if (calls === 1) {
            // The first generation is slow, finishing just as the learner leaves.
            return new Promise<SessionStep>((resolve) => {
                resolveFirst = resolve;
            });
        }
        return Promise.resolve<SessionStep>({
            kind: "problem",
            item,
            problem: toProblem(item, EIGEN_ITEM),
        });
    };
    const runner = new SessionRunner(items, { fetchStep, prefetchTarget: 1 });

    const pending = runner.pull();
    await new Promise((resolve) => setTimeout(resolve, 0));
    // The learner navigates away, then the slow first generation resolves.
    runner.dispose();
    resolveFirst({ kind: "abstain", item: items[0], reason: "request_failed", detail: "aborted" });

    const result = await pending;
    // pull() stops instead of marching through b/c/d for the abandoned screen: only
    // the one in-flight generation ever ran.
    expect(result.served).toBeNull();
    expect(calls).toBe(1);
});

test("warmFirst starts the first problem early so a later pull reuses it (dashboard prewarm)", async () => {
    const calls: Record<string, number> = {};
    const fetchStep: StepFetcher = async (item: QueueItem): Promise<SessionStep> => {
        calls[item.skillId] = (calls[item.skillId] ?? 0) + 1;
        return { kind: "problem", item, problem: toProblem(item, EIGEN_ITEM) };
    };
    const runner = new SessionRunner(queue("ok1", "ok2"), { fetchStep, prefetchTarget: 1 });

    // The dashboard prewarm begins generating only the first problem.
    runner.warmFirst();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(calls.ok1).toBe(1);
    expect(calls.ok2).toBeUndefined();

    // The session then pulls it: ok1's generation is reused, not started over.
    const first = await runner.pull();
    expect(first.served?.item.skillId).toBe("ok1");
    expect(calls.ok1).toBe(1);
});

test("retryCurrent re-generates a skill after a transient contract breach", async () => {
    let attempts = 0;
    const fetchStep: StepFetcher = async (item: QueueItem): Promise<SessionStep> => {
        if (item.skillId === "flaky") {
            attempts += 1;
            if (attempts === 1) {
                throw new Error("first attempt broke its contract");
            }
        }
        return { kind: "problem", item, problem: toProblem(item, EIGEN_ITEM) };
    };
    const runner = new SessionRunner(queue("flaky"), { fetchStep });

    await expect(runner.pull()).rejects.toThrow(/first attempt/);
    const recovered = await runner.retryCurrent();
    expect(recovered.served?.item.skillId).toBe("flaky");
    expect(recovered.deferred).toHaveLength(0);
});

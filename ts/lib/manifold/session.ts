// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * The Manifold study session: a thin player over a DAG-aware backend queue and a
 * live, verified problem source (D44).
 *
 * Manifold never shows the raw Anki card. The backend's `BuildSessionQueue`
 * decides which skills to serve and in what order: due skills first (ordered by
 * points-at-stake), then new skills drawn only from topics the prerequisite DAG
 * has unlocked, interleaved across topics. That decision is read-only, so FSRS,
 * intervals, card state, sync and undo are untouched.
 *
 * Every runtime PROBLEM is generated ON THE FLY per review (D44, the owner
 * reversal of the earlier bank-first plan): the player asks the backend
 * `manifoldNextProblem` endpoint for a problem for a due skill, which generates a
 * candidate live and serves it only once `verify.py` has proven it (verification
 * stays in the loop; no fabrication). There is no persisted item bank on the
 * runtime path.
 *
 * `SessionRunner` drives the due queue and NEVER dead-ends on an abstain: a skill
 * the live generator cannot produce a verified problem for is recorded as DEFERRED
 * and the runner skips ahead to the next skill that DID verify, so the learner is
 * served real, verified problems continuously. To hide generation latency it keeps
 * a small in-memory buffer of the next few due skills generating in the background
 * (per session, never persisted). Deferred skills are surfaced only as a small,
 * honest "N skills pending content" note — never a full-screen wall, never a fake.
 *
 * Grading is objective, read from the served item's `correct_index`; it flows
 * through `grade_now`, which feeds Anki's normal answering path from the card's
 * own scheduling states, so FSRS reschedules exactly as it would from a reviewer
 * answer, independent of Anki's queue order.
 *
 * Coverage is honest, never padded (cross-cutting rule; D35, D44). A deferred skill
 * carries no problem and is never graded, so it can never move a score. There is no
 * cached bank to fall back to and no fabricated problem, ever.
 */

import { CardAnswer_Rating } from "@generated/anki/scheduler_pb";
import { buildSessionQueue, getProblemsSolved, gradeNow } from "@generated/backend";

/** The deck the trainer studies. Every skill card lives here. */
export const MANIFOLD_DECK_NAME = "GRE Mathematics";

/**
 * Whether the player is serving placeholder problems. False: problems are
 * generated live and served only once SymPy-verified, so a graded attempt is a
 * solved exam item, not a tap on a placeholder control. The dashboard reads this
 * to clear the readiness provenance banner (spec §7, D18).
 */
export const PROBLEMS_ARE_PLACEHOLDER = false;

/**
 * The teaching (scaffolding) level a card is at, competence-driven rather than
 * tied to Anki's learning-steps calendar (D24). It shapes how the worked
 * solution is revealed (D36): a New skill is opened as a worked example, and the
 * scaffolding fades as competence grows toward a cold Independent problem.
 */
export const LEVEL_LABELS = ["New", "Guided", "Independent", "Revisit"] as const;

/** The human label for a card's numeric level; falls back to "New" out of range. */
export function levelLabel(level: number): string {
    return LEVEL_LABELS[level] ?? LEVEL_LABELS[0];
}

/**
 * The "Independent" scaffolding level (index into {@link LEVEL_LABELS}): a cold
 * problem the learner is meant to solve with no support.
 */
export const INDEPENDENT_LEVEL = 2;

/**
 * Whether the hint assistant is offered for a problem at this level. Every level
 * may ask for a hint EXCEPT Independent, which is solved cold by design: New (0),
 * Guided (1) and Revisit (3) show the "Ask for a hint" affordance; Independent (2)
 * does not. Out-of-range levels default to allowed (they render as New).
 */
export function hintsAllowed(level: number): boolean {
    return level !== INDEPENDENT_LEVEL;
}

/**
 * Whether the predict-then-reveal pretrieval step is offered at New (level 0):
 * before the worked example the learner is shown the stem and asked to make a
 * quick prediction (D36, Phase 3). It grades nothing and sends nothing; it is a
 * pure metacognitive prompt. Exported as a flag so the study feature can be
 * ablated or A/B compared without editing the player.
 */
export const PREDICT_ENABLED = true;

/**
 * Whether the optional self-explanation prompt is offered after an attempt at
 * New (level 0) and Guided (level 1): a one-line "why does this method work?"
 * box (D36, Phase 3). It is never graded and never sent anywhere. Exported as a
 * flag so the study feature can be ablated or A/B compared.
 */
export const SELF_EXPLAIN_ENABLED = true;

/** The five lettered controls. "Don't know" is handled separately, as a miss. */
export const CHOICE_IDS = ["A", "B", "C", "D", "E"] as const;
export type ChoiceId = (typeof CHOICE_IDS)[number];

/** What the learner can press: a lettered choice, or an explicit "don't know". */
export type Answer = ChoiceId | "dont-know";

/**
 * One answer control: its letter, its position in the item's choice list (the
 * index graded against `correct_index`), and the choice text as generated (ASCII
 * maths; the view typesets it through `mathToMarkup`).
 */
export interface Choice {
    id: ChoiceId;
    index: number;
    text: string;
}

/**
 * A real problem for a skill, generated live and verified before serving: a
 * typeset stem, five choices, the index of the correct one, the worked solution
 * revealed after an attempt, the per-distractor rationales, and the named source
 * the item traces to (AC22). Choice and solution text carry ASCII maths that the
 * view typesets.
 */
export interface Problem {
    skillName: string;
    topic: string;
    tier: string;
    stem: string;
    choices: Choice[];
    correctIndex: number;
    solution: string;
    distractorRationales: string[];
    sourceRef: string;
}

/** The skill identity a queue item stands for. */
export interface Skill {
    skillId: string;
    skillName: string;
    topic: string;
    tier: string;
}

/**
 * One entry of the backend session queue: the skill identity plus the card id
 * the answer grades. Mirrors the `SessionItem` proto in camelCase.
 */
export interface QueueItem {
    cardId: bigint;
    skillId: string;
    skillName: string;
    topicId: string;
    topicTitle: string;
    tier: string;
    /** Teaching (scaffolding) level, competence-driven: 0 New … 3 Revisited. */
    level: number;
}

/**
 * One step of the session. Either a real, verified problem to solve, or an
 * ABSTAIN step for a skill the live generator could not produce a verified
 * problem for this time. An abstain step carries no problem and is never graded,
 * so honest coverage is visible instead of papered over with a fake.
 */
export type SessionStep =
    | { kind: "problem"; item: QueueItem; problem: Problem }
    | { kind: "abstain"; item: QueueItem; reason: string; detail?: string };

/** A verified item as returned by the live `manifoldNextProblem` endpoint. */
interface LiveItem {
    stem: string;
    choices: string[];
    correct_index: number;
    solution: string;
    distractor_rationales: string[];
    source_ref: string;
}

/** The verdict from the live endpoint: a verified item, or an honest abstain. */
export type LiveResponse =
    | { status: "ok"; item: LiveItem }
    | { status: "abstain"; reason: string; detail?: string };

/** The whitelisted mediasrv endpoint that generates + verifies one problem (D44). */
const NEXT_PROBLEM_URL = "/_anki/manifoldNextProblem";

/**
 * Ask the backend for a live-generated, verified problem for a skill. The body is
 * JSON but is sent as `application/binary` to satisfy mediasrv's same-origin POST
 * guard, exactly like the generated backend RPCs. A transport failure is turned
 * into an honest abstain (its real message surfaced) rather than a thrown error,
 * so the session degrades to the abstain state instead of crashing; a malformed
 * "ok" payload still throws loudly, since the server claims it was verified.
 */
async function postNextProblem(item: QueueItem, signal?: AbortSignal): Promise<LiveResponse> {
    const body = JSON.stringify({
        skill_id: item.skillId,
        skill_name: item.skillName,
        topic_id: item.topicId,
        topic_title: item.topicTitle,
        tier: item.tier,
        level: item.level,
    });
    const res = await fetch(NEXT_PROBLEM_URL, {
        method: "POST",
        headers: { "Content-Type": "application/binary" },
        body: new TextEncoder().encode(body),
        signal,
    });
    if (!res.ok) {
        let msg = `${res.status}`;
        try {
            msg = `${res.status}: ${await res.text()}`;
        } catch {
            // keep the status-only message
        }
        throw new Error(msg);
    }
    const text = await res.text();
    let parsed: unknown;
    try {
        parsed = JSON.parse(text);
    } catch (err) {
        throw new Error(`live generation returned non-JSON: ${(err as Error).message}`);
    }
    const response = parsed as LiveResponse;
    if (response.status !== "ok" && response.status !== "abstain") {
        throw new Error(`live generation returned an unexpected status: ${text.slice(0, 200)}`);
    }
    return response;
}

/**
 * Map a verified live item onto a `Problem` for the view, stamping the skill's
 * display identity from the queue item. The item was already proven server-side,
 * but its shape is still validated here: a malformed served item is a real
 * invariant violation and raises immediately rather than rendering a broken card.
 */
export function toProblem(item: QueueItem, live: LiveItem): Problem {
    if (!Array.isArray(live.choices) || live.choices.length !== CHOICE_IDS.length) {
        throw new Error(`served item for ${item.skillId}: needs exactly ${CHOICE_IDS.length} choices`);
    }
    if (!live.choices.every((c) => typeof c === "string" && c.trim())) {
        throw new Error(`served item for ${item.skillId}: every choice must be a non-empty string`);
    }
    if (
        typeof live.correct_index !== "number"
        || !Number.isInteger(live.correct_index)
        || live.correct_index < 0
        || live.correct_index >= CHOICE_IDS.length
    ) {
        throw new Error(`served item for ${item.skillId}: correct_index out of range`);
    }
    if (typeof live.stem !== "string" || !live.stem.trim()) {
        throw new Error(`served item for ${item.skillId}: missing stem`);
    }
    if (typeof live.solution !== "string" || !live.solution.trim()) {
        throw new Error(`served item for ${item.skillId}: missing solution`);
    }
    const rationales = Array.isArray(live.distractor_rationales)
        ? live.distractor_rationales.filter((r): r is string => typeof r === "string")
        : [];
    return {
        skillName: item.skillName,
        topic: item.topicTitle,
        tier: item.tier,
        stem: live.stem,
        choices: live.choices.map((text, index) => ({ id: CHOICE_IDS[index], index, text })),
        correctIndex: live.correct_index,
        solution: live.solution,
        distractorRationales: rationales,
        sourceRef: live.source_ref,
    };
}

/** Turn a live verdict into a session step: a real problem, or an honest abstain. */
export function stepFromResponse(item: QueueItem, response: LiveResponse): SessionStep {
    if (response.status === "ok") {
        return { kind: "problem", item, problem: toProblem(item, response.item) };
    }
    return { kind: "abstain", item, reason: response.reason, detail: response.detail };
}

/** A plain-language line for an abstain reason code, for the honest empty state. */
export function abstainSummary(reason: string): string {
    switch (reason) {
        case "no_key":
            return "The problem generator needs an API key, and none is set.";
        case "offline":
            return "The generator could not be reached. Check the network connection.";
        case "unverified_after_retries":
            return "A few problems were generated but none passed verification, so none is shown.";
        case "needs_curation":
            return "This skill needs curated content; no automatic machine-checkable problem fits it yet.";
        case "generation_error":
        case "generation_failed":
        case "generation_timeout":
            return "Generating a problem did not succeed this time.";
        case "request_failed":
            return "The request to generate a problem did not complete.";
        case "serve_live_unavailable":
            return "The problem generator is not available in this build.";
        case "no_fixture":
            return "No test problem is configured for this skill.";
        default:
            return "A verified problem could not be generated this time.";
    }
}

// --- new-skill lectures (Task 1) ----------------------------------------------

/**
 * A pre-authored lecture for a New (teach) skill: the method's name and when to
 * use it, a worked walk-through of a VERIFIED banked item, and a key takeaway, with
 * all mathematics as delimited LaTeX in `lectureLatex`. Served from the static,
 * pre-authored `lectures.json` (never generated live, the same "vetted content, no
 * runtime fabrication" rule as the teach bank). A skill without a lecture simply
 * teaches through its worked solution instead — an honest gap, never a faked one.
 */
export interface Lecture {
    skillId: string;
    topic: string;
    title: string;
    lectureLatex: string;
    anchoredItemId: string | null;
}

/** A lecture as the whitelisted `manifoldLecture` endpoint returns it. */
interface LiveLecture {
    skill_id: string;
    topic_id?: string;
    title: string;
    lecture_latex: string;
    anchored_item_id?: string | null;
}

/** The endpoint verdict: a lecture, or an honest "none" (no lecture authored yet). */
type LectureResponse =
    | { status: "ok"; lecture: LiveLecture }
    | { status: "none"; reason?: string; detail?: string };

/** The whitelisted mediasrv endpoint that returns a pre-authored lecture (Task 1). */
const LECTURE_URL = "/_anki/manifoldLecture";

/**
 * Map a served lecture onto the view's `Lecture`, stamping the skill's display
 * topic. A malformed "ok" (missing title or body) is a real contract breach and
 * throws, exactly like {@link toProblem}; it never renders an empty lecture.
 */
export function toLecture(item: QueueItem, live: LiveLecture): Lecture {
    if (typeof live.title !== "string" || !live.title.trim()) {
        throw new Error(`lecture for ${item.skillId}: missing title`);
    }
    if (typeof live.lecture_latex !== "string" || !live.lecture_latex.trim()) {
        throw new Error(`lecture for ${item.skillId}: missing lecture_latex`);
    }
    return {
        skillId: item.skillId,
        topic: item.topicTitle,
        title: live.title,
        lectureLatex: live.lecture_latex,
        anchoredItemId: live.anchored_item_id ?? null,
    };
}

/**
 * Fetch the pre-authored lecture for a New skill, or null when none is authored
 * yet. The lecture is supplementary teaching, not the graded unit, so a transport
 * failure degrades to null (the problem still shows) rather than crashing; a
 * malformed "ok" payload still throws, since the server claims a real lecture.
 * Never fabricates a lecture.
 */
export async function fetchLecture(item: QueueItem): Promise<Lecture | null> {
    let res: Response;
    try {
        res = await fetch(LECTURE_URL, {
            method: "POST",
            headers: { "Content-Type": "application/binary" },
            body: new TextEncoder().encode(
                JSON.stringify({
                    skill_id: item.skillId,
                    skill_name: item.skillName,
                    topic_id: item.topicId,
                    tier: item.tier,
                }),
            ),
        });
    } catch {
        return null;
    }
    if (!res.ok) {
        return null;
    }
    let parsed: LectureResponse;
    try {
        parsed = JSON.parse(await res.text()) as LectureResponse;
    } catch {
        return null;
    }
    return parsed.status === "ok" ? toLecture(item, parsed.lecture) : null;
}

// --- hint assistant (ask a question about the current problem) ----------------

/**
 * One exchange in the hint conversation: the learner's question and the hint that
 * came back. Kept per problem (never persisted) and sent as context so a follow-up
 * question builds on the previous nudge.
 */
export interface HintTurn {
    question: string;
    hint: string;
}

/** The verdict from the hint endpoint: a hint, or an honest abstain. */
export type HintResponse =
    | { status: "ok"; hint: string }
    | { status: "abstain"; reason: string; detail?: string };

/** The whitelisted mediasrv endpoint that produces one answer-free hint. */
const HINT_URL = "/_anki/manifoldHint";

/**
 * A plain-language line for a hint-abstain reason code, for the honest empty state.
 * Falls back to the endpoint's own detail (then a generic line) so the real reason
 * is always what the learner sees, never a fabricated hint.
 */
export function hintUnavailableMessage(reason: string, detail?: string): string {
    switch (reason) {
        case "no_key":
            return "The hint assistant needs an API key, and none is set.";
        case "offline":
            return "The hint assistant could not be reached. Check the connection and try again.";
        case "hint_unavailable":
            return "The hint assistant is not available in this build.";
        case "hint_timeout":
            return "The hint took too long to come back. Try asking again.";
        case "no_fixture":
            return "No test hint is configured for this skill.";
        default:
            return detail?.trim() || "A hint could not be produced this time.";
    }
}

/**
 * Ask the assistant for a hint about the current problem. The body is JSON sent as
 * `application/binary` to satisfy mediasrv's same-origin POST guard, exactly like
 * the other Manifold endpoints. The assistant is given only the stem and choices
 * the learner already sees (never the correct index or the worked solution), so it
 * cannot leak the answer even by accident.
 *
 * A transport or contract failure throws loudly (the caller surfaces the real
 * message rather than showing a fabricated hint); an honest "abstain" verdict is
 * returned for the caller to render as the real reason.
 */
export async function fetchHint(
    item: QueueItem,
    problem: Problem,
    question: string,
    history: HintTurn[],
    signal?: AbortSignal,
): Promise<HintResponse> {
    const body = JSON.stringify({
        skill_id: item.skillId,
        skill_name: item.skillName,
        topic_title: item.topicTitle,
        stem: problem.stem,
        choices: problem.choices.map((choice) => choice.text),
        question,
        history: history.map((turn) => ({ question: turn.question, hint: turn.hint })),
    });
    const res = await fetch(HINT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/binary" },
        body: new TextEncoder().encode(body),
        signal,
    });
    if (!res.ok) {
        let msg = `${res.status}`;
        try {
            msg = `${res.status}: ${await res.text()}`;
        } catch {
            // keep the status-only message
        }
        throw new Error(msg);
    }
    const text = await res.text();
    let parsed: HintResponse;
    try {
        parsed = JSON.parse(text) as HintResponse;
    } catch (err) {
        throw new Error(`hint request returned non-JSON: ${(err as Error).message}`);
    }
    if (parsed.status === "ok") {
        if (typeof parsed.hint !== "string" || !parsed.hint.trim()) {
            throw new Error("hint response was marked ok but carried no hint text");
        }
        return parsed;
    }
    if (parsed.status === "abstain") {
        return parsed;
    }
    throw new Error(`hint request returned an unexpected status: ${text.slice(0, 200)}`);
}

// --- skip-ahead runner + in-memory prefetch buffer (never persisted) ----------

/**
 * A due skill the live generator could not produce a verified problem for this
 * session. It is DEFERRED, never dead-ended: the runner skips ahead to the next
 * verified skill and surfaces these only as a small, honest "pending content" note.
 */
export interface DeferredSkill {
    skillId: string;
    skillName: string;
    topic: string;
    reason: string;
    detail?: string;
}

/** A verified problem to serve, with its 1-based position in the full due queue. */
export interface ServedProblem {
    item: QueueItem;
    problem: Problem;
    queuePosition: number;
}

/**
 * The outcome of pulling the next verified problem. `served` is the next real
 * problem (null once the queue is exhausted); `deferred` is the honest, growing
 * list of skills skipped because no verified problem could be generated for them.
 */
export interface PullResult {
    served: ServedProblem | null;
    deferred: DeferredSkill[];
}

/** How a step is generated for a queue item; injectable so the runner is testable.
 * The optional `signal` lets the runner abort an in-flight generation when the
 * learner navigates away (e.g. to the dashboard), so a slow live-generation POST
 * does not keep the browser waiting on a request whose result will be discarded. */
export type StepFetcher = (item: QueueItem, signal?: AbortSignal) => Promise<SessionStep>;

/**
 * A runner's progress through the queue, enough to rebuild it mid-session so the
 * learner returns to exactly where they were after a trip to the dashboard (no
 * regeneration, no restart). The queue itself is snapshotted alongside this by the
 * player; together they fully restore the run.
 */
export interface RunnerProgress {
    cursor: number;
    servedCount: number;
    deferred: DeferredSkill[];
}

/**
 * JSON (de)serialization that survives a {@link QueueItem}'s `cardId`, which is a
 * `bigint` and therefore not representable in JSON. Used to persist a session
 * snapshot so the learner resumes exactly where they were across a dashboard
 * round-trip. Pass {@link bigintReplacer} to `JSON.stringify` and
 * {@link bigintReviver} to `JSON.parse`; anything without the tag is untouched.
 */
export function bigintReplacer(_key: string, value: unknown): unknown {
    return typeof value === "bigint" ? { __bigint__: value.toString() } : value;
}

export function bigintReviver(_key: string, value: unknown): unknown {
    if (
        value !== null
        && typeof value === "object"
        && "__bigint__" in (value as Record<string, unknown>)
    ) {
        return BigInt((value as { __bigint__: string }).__bigint__);
    }
    return value;
}

/**
 * Generate + verify one problem for a queue item, turning a transport failure into
 * an honest abstain (its real message surfaced) rather than a thrown error, so the
 * session degrades to a defer instead of crashing. A malformed served "ok" item
 * still throws loudly, since the server claims it was verified.
 */
export async function fetchLiveStep(item: QueueItem, signal?: AbortSignal): Promise<SessionStep> {
    let response: LiveResponse;
    try {
        response = await postNextProblem(item, signal);
    } catch (err) {
        return {
            kind: "abstain",
            item,
            reason: "request_failed",
            detail: err instanceof Error ? err.message : String(err),
        };
    }
    return stepFromResponse(item, response);
}

/**
 * Generate + verify a FRESH instance of the same skill, mapped to a
 * {@link ServedProblem}, or null when none can be served.
 *
 * A New skill is taught on one worked instance and then attempted on a DIFFERENT
 * one (D36), so the player calls this after the worked example to get a new
 * instance of the same skill. It uses the same live endpoint as the runner
 * ({@link postNextProblem}) and the same mapping ({@link toProblem}). An honest
 * abstain or a transport failure returns null so the caller can fall back to the
 * already-served worked instance (real and verified, so honest, not fabricated)
 * rather than crashing; a malformed "ok" payload still throws loudly through
 * {@link toProblem}, since the server claims it was verified. `queuePosition` is
 * carried by the caller, so it is 0 here.
 */
export async function fetchProblem(
    item: QueueItem,
    signal?: AbortSignal,
): Promise<ServedProblem | null> {
    let response: LiveResponse;
    try {
        response = await postNextProblem(item, signal);
    } catch {
        return null;
    }
    if (response.status !== "ok") {
        return null;
    }
    return { item, problem: toProblem(item, response.item), queuePosition: 0 };
}

/**
 * How many upcoming due skills to keep generating ahead of the learner. A small
 * look-ahead buffer hides generation latency: template-backed skills serve in a
 * fraction of a second, but a skill with no template needs a live model round-trip
 * (seconds), so keeping a few generating in the background means the NEXT problem is
 * usually ready the moment the learner presses Continue instead of stalling on a
 * fresh generation each time (D44).
 */
export const PREFETCH_TARGET = 4;

/**
 * Drives a study session over the due queue. The key UX guarantee (D44): it NEVER
 * dead-ends on an abstain. A skill whose live problem cannot be verified is recorded
 * as {@link DeferredSkill} and the runner skips ahead to the next skill that DID
 * verify, so the learner is served real, verified problems back to back. A small
 * in-memory buffer keeps the next few due skills generating in the background to hide
 * latency (per session, never persisted, no bank).
 *
 * A served item that violates its own contract (a malformed "ok" payload) is a real
 * invariant breach, not an ordinary abstain: {@link pull} rejects loudly so the view
 * can surface it, and {@link retryCurrent} / {@link skipCurrent} recover from it
 * without losing the progress already made through the queue.
 */
export class SessionRunner {
    private readonly queue: QueueItem[];
    private readonly fetchStep: StepFetcher;
    private readonly prefetchTarget: number;
    private readonly cache = new Map<number, Promise<SessionStep>>();
    // Abort controllers for in-flight generations, so navigating away can cancel
    // requests whose results would be discarded (see dispose()).
    private readonly controllers = new Map<number, AbortController>();
    private readonly deferred: DeferredSkill[] = [];
    private cursor = 0; // index of the next queue item to classify
    private servedCount = 0;
    // Once torn down, the runner spawns no further generation and any in-flight
    // pull() unwinds without prefetching more (see dispose()).
    private disposed = false;

    constructor(
        queue: QueueItem[],
        options: {
            fetchStep?: StepFetcher;
            prefetchTarget?: number;
            /** Resume a partially-completed run (see {@link snapshotProgress}). */
            resume?: RunnerProgress;
        } = {},
    ) {
        this.queue = queue;
        this.fetchStep = options.fetchStep ?? fetchLiveStep;
        this.prefetchTarget = Math.max(1, options.prefetchTarget ?? PREFETCH_TARGET);
        if (options.resume) {
            this.cursor = Math.max(0, Math.min(options.resume.cursor, queue.length));
            this.servedCount = Math.max(0, options.resume.servedCount);
            this.deferred.push(...options.resume.deferred);
        }
    }

    /**
     * A snapshot of how far the run has progressed, for persisting mid-session and
     * later reconstructing the runner (with the same queue) so the learner resumes
     * exactly where they were rather than starting over.
     */
    snapshotProgress(): RunnerProgress {
        return {
            cursor: this.cursor,
            servedCount: this.servedCount,
            deferred: this.deferredSkills,
        };
    }

    /**
     * Warm the look-ahead buffer now. Used right after a resume, whose rebuilt runner
     * starts with an empty cache, so the first Continue on return finds its problem
     * already generating instead of stalling on a cold start.
     */
    prime(): void {
        this.prefetchAhead();
    }

    /**
     * Begin generating ONLY the current problem now, without consuming it. Used by
     * the dashboard prewarm so a template-less skill's slow live generation starts
     * while the learner is still on the dashboard, instead of stalling the session's
     * first screen.
     */
    warmFirst(): void {
        if (!this.disposed && this.cursor < this.queue.length) {
            this.warm(this.cursor);
        }
    }

    /**
     * Abort every in-flight generation and drop the look-ahead buffer. This cancels
     * the browser's fetch (so the client stops waiting and discards the result) when
     * the player is torn down, e.g. the learner navigates to the dashboard; a fresh
     * runner is built on return. Note it does not kill the server-side generation
     * subprocess, which runs to completion — the widened waitress pool is what keeps
     * those busy workers from starving navigation.
     */
    dispose(): void {
        this.disposed = true;
        for (const controller of this.controllers.values()) {
            controller.abort();
        }
        this.controllers.clear();
        this.cache.clear();
    }

    /** A snapshot of the skills skipped so far for lack of a verified problem. */
    get deferredSkills(): DeferredSkill[] {
        return this.deferred.slice();
    }

    /** How many verified problems have been served so far. */
    get served(): number {
        return this.servedCount;
    }

    /** Total number of due skills in the queue. */
    get total(): number {
        return this.queue.length;
    }

    /** The skill currently being classified (what a loud failure or spinner refers to). */
    get currentItem(): QueueItem | null {
        return this.cursor < this.queue.length ? this.queue[this.cursor] : null;
    }

    /** Warm generation for the next few unclassified skills (the look-ahead buffer). */
    private prefetchAhead(): void {
        if (this.disposed) {
            return;
        }
        const limit = Math.min(this.cursor + this.prefetchTarget, this.queue.length);
        for (let i = this.cursor; i < limit; i++) {
            this.warm(i);
        }
    }

    private warm(index: number): Promise<SessionStep> {
        let pending = this.cache.get(index);
        if (!pending) {
            const controller = new AbortController();
            this.controllers.set(index, controller);
            pending = this.fetchStep(this.queue[index], controller.signal);
            this.cache.set(index, pending);
            // Mark the rejection handled so a background prefetch never trips an
            // unhandledrejection; the cached promise still rejects when awaited.
            pending.catch(() => {
                // Swallowed here only to mark it seen; pull() awaits and surfaces it.
            });
        }
        return pending;
    }

    private recordDeferred(item: QueueItem, reason: string, detail?: string): void {
        this.deferred.push({
            skillId: item.skillId,
            skillName: item.skillName,
            topic: item.topicTitle,
            reason,
            detail,
        });
    }

    /**
     * Pull the next verified problem, skipping (and recording) any abstaining skills
     * on the way. Resolves `{ served: null }` once the queue is exhausted. Rejects
     * only when a served item breaks its own contract (a loud, recoverable breach);
     * the failed skill stays current so it can be retried or skipped.
     */
    async pull(): Promise<PullResult> {
        this.prefetchAhead();
        while (this.cursor < this.queue.length) {
            // Torn down mid-flight (the learner navigated away): stop here rather than
            // prefetching and generating more for a screen that no longer exists.
            if (this.disposed) {
                return { served: null, deferred: this.deferredSkills };
            }
            const index = this.cursor;
            // Do NOT advance the cursor before awaiting: if this throws (a malformed
            // served item), the failed skill remains current for retry/skip.
            const step = await this.warm(index);
            if (step.kind === "problem") {
                this.cursor = index + 1;
                this.servedCount += 1;
                this.prefetchAhead();
                return {
                    served: { item: step.item, problem: step.problem, queuePosition: index + 1 },
                    deferred: this.deferredSkills,
                };
            }
            this.recordDeferred(step.item, step.reason, step.detail);
            this.cursor = index + 1;
            this.prefetchAhead();
        }
        return { served: null, deferred: this.deferredSkills };
    }

    /** Abort and forget the cached generation for one index (so a re-warm starts a
     *  fresh request and no controller is orphaned past cancellation). */
    private drop(index: number): void {
        this.controllers.get(index)?.abort();
        this.controllers.delete(index);
        this.cache.delete(index);
    }

    /**
     * Re-generate the current skill after a loud served-item failure, then continue.
     * Backs the view's "Try again" on the rare malformed-served-item error.
     */
    retryCurrent(): Promise<PullResult> {
        this.drop(this.cursor);
        return this.pull();
    }

    /**
     * Defer the current skill after a loud served-item failure and move on, so a
     * single bad item never dead-ends the session. Backs the view's "Skip skill".
     */
    skipCurrent(reason: string, detail?: string): Promise<PullResult> {
        if (this.cursor < this.queue.length) {
            this.recordDeferred(this.queue[this.cursor], reason, detail);
            this.drop(this.cursor);
            this.cursor += 1;
        }
        return this.pull();
    }
}

/** The skill a queue item stands for. */
export function skillFromItem(item: QueueItem): Skill {
    return {
        skillId: item.skillId,
        skillName: item.skillName,
        topic: item.topicTitle,
        tier: item.tier,
    };
}

/** The choice the learner pressed, or null for "don't know" / an unknown letter. */
export function choiceFor(problem: Problem, answer: Answer): Choice | null {
    if (answer === "dont-know") {
        return null;
    }
    return problem.choices.find((choice) => choice.id === answer) ?? null;
}

/**
 * Objective grading: an answer is correct only when the pressed choice is the
 * item's verified `correct_index`. "Don't know" and every other letter is a
 * miss. There is no "A is always correct" shortcut.
 */
export function isCorrect(problem: Problem, answer: Answer): boolean {
    const choice = choiceFor(problem, answer);
    return choice !== null && choice.index === problem.correctIndex;
}

/**
 * The order to study: due skills first by points-at-stake, then unlocked new
 * skills, interleaved across topics, all decided read-only by the engine. Fails
 * loudly if the backend cannot build the queue rather than serving a guess.
 */
export async function buildQueue(): Promise<QueueItem[]> {
    const response = await buildSessionQueue({});
    return response.items.map((item) => ({
        cardId: item.cardId,
        skillId: item.skillId,
        skillName: item.skillName,
        topicId: item.topicId,
        topicTitle: item.topicTitle,
        tier: item.tier,
        level: item.level,
    }));
}

// --- dashboard prewarm --------------------------------------------------------
// The first problem is instant when the leading due skill has a template, but a
// template-less skill needs a live, verified generation (seconds). To keep the
// session's FIRST screen from stalling on that, the dashboard kicks off the first
// problem's generation early (while the learner reads the dashboard), and the
// session hands off to it. Best-effort and per app-run: if it does not complete,
// the session simply generates on its own, and any real failure still surfaces
// there rather than being swallowed here.

let prewarmed: { queue: QueueItem[]; runner: SessionRunner } | null = null;

/** Start generating the first due problem now, if not already warming. Safe to
 *  call repeatedly (e.g. from the dashboard's mount); a no-op off the browser. */
export function prewarmSession(): void {
    if (prewarmed || typeof window === "undefined") {
        return;
    }
    void (async () => {
        try {
            const queue = await buildQueue();
            if (queue.length === 0) {
                return;
            }
            const runner = new SessionRunner(queue);
            runner.warmFirst();
            prewarmed = { queue, runner };
        } catch {
            // Prewarm is a pure optimization; the session builds its own queue and
            // fails loudly there if the backend genuinely cannot serve one.
        }
    })();
}

/** Consume the prewarmed runner + queue (once), or null if none is ready. */
export function takePrewarmedSession(): { queue: QueueItem[]; runner: SessionRunner } | null {
    const taken = prewarmed;
    prewarmed = null;
    return taken;
}

/**
 * Grade the card and let FSRS reschedule it. A correct answer rates Good, a miss
 * rates Again, exactly as the reviewer would. `grade_now` reads the card's own
 * scheduling states and applies the rating through Anki's normal answering path,
 * so the chosen order does not depend on Anki's queue and intervals are
 * untouched. Only real problems are graded; abstain steps never reach here.
 *
 * `millisecondsTaken` is the measured time on the problem, recorded into the
 * revlog so study-time stats count Manifold reviews (it was dropped as 0 before).
 * The caller caps it; 0 means the answer was not timed.
 */
export async function grade(
    item: QueueItem,
    correct: boolean,
    millisecondsTaken: number,
): Promise<void> {
    const rating = correct ? CardAnswer_Rating.GOOD : CardAnswer_Rating.AGAIN;
    await gradeNow({ cardIds: [item.cardId], rating, millisecondsTaken });
}

/**
 * Read the cumulative count of problems solved (graded reviews across all
 * sessions) from the engine's revlog. A transport failure surfaces to the caller
 * rather than returning a fabricated zero.
 */
export async function fetchProblemsSolved(): Promise<number> {
    const solved = await getProblemsSolved({});
    return solved.total;
}

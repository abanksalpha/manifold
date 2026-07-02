// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * The Manifold study session: a thin player over a DAG-aware backend queue.
 *
 * Manifold never shows the raw Anki card. The backend's `BuildSessionQueue`
 * decides which skills to serve and in what order: due skills first (ordered by
 * points-at-stake), then new skills drawn only from topics the prerequisite DAG
 * has unlocked, interleaved across topics. That decision is read-only, so FSRS,
 * intervals, card state, sync and undo are untouched.
 *
 * The player walks that order. For each skill it puts a problem in front of the
 * learner; today that problem is a placeholder (the skill label and a fixed set
 * of answer controls), and a Phase-2 generator will return real stems and
 * choices through the one seam below (`getProblem`) without the player changing.
 * Grading goes through `grade_now`, which feeds Anki's normal answering path
 * from the card's own scheduling states, so FSRS reschedules exactly as it would
 * from a reviewer answer, without depending on Anki's queue order.
 */

import { CardAnswer_Rating } from "@generated/anki/scheduler_pb";
import { buildSessionQueue, gradeNow } from "@generated/backend";

/** The deck the trainer studies. Every skill card lives here. */
export const MANIFOLD_DECK_NAME = "GRE Mathematics";

/**
 * Whether the player is still serving placeholder problems (no generated stems).
 * While true, graded attempts are taps on the placeholder A-E control, not solved
 * exam items, so the dashboard flags readiness provenance (D18, spec §7). This
 * flips to false only when `getProblem` returns real generated content.
 */
export const PROBLEMS_ARE_PLACEHOLDER = true;

/**
 * The teaching (scaffolding) level a card is at — competence-driven, not tied to
 * Anki's learning-steps calendar, so an Independent (solo) problem is reachable
 * the same day once the learner shows competence. A label only today: the player
 * does not yet vary the slide by level.
 */
export const LEVEL_LABELS = ["New", "Guided", "Independent", "Revisit"] as const;

/** The human label for a card's numeric level; falls back to "New" out of range. */
export function levelLabel(level: number): string {
    return LEVEL_LABELS[level] ?? LEVEL_LABELS[0];
}

/** The five lettered controls. "Don't know" is handled separately, as a miss. */
export const CHOICE_IDS = ["A", "B", "C", "D", "E"] as const;
export type ChoiceId = (typeof CHOICE_IDS)[number];

/** What the learner can press: a lettered choice, or an explicit "don't know". */
export type Answer = ChoiceId | "dont-know";

/** One answer control. Today it carries only its letter; a generated problem
 * will add the choice's text on this same shape. */
export interface Choice {
    id: ChoiceId;
}

/**
 * A problem to put in front of the learner. Today it is a placeholder: the skill
 * it tests, the topic and tier it sits under, and the fixed lettered controls.
 * No stem or choice text exists yet because problems are not generated. The
 * Phase-2 generator populates this same shape with real content.
 */
export interface Problem {
    skillName: string;
    topic: string;
    tier: string;
    choices: Choice[];
}

/** The skill identity the player renders a problem for. */
export interface Skill {
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

/** One step of the session: the queued skill and the problem to render for it. */
export interface SessionStep {
    item: QueueItem;
    problem: Problem;
}

/**
 * The seam. "Get the problem for this skill". Today it returns the label plus
 * the fixed A-E controls; the generator slots in here later and returns real
 * stems and choices, and nothing upstream changes.
 */
export function getProblem(skill: Skill): Problem {
    return {
        skillName: skill.skillName,
        topic: skill.topic,
        tier: skill.tier,
        choices: CHOICE_IDS.map((id) => ({ id })),
    };
}

/** The skill a queue item stands for: its name, the topic title and the tier. */
export function skillFromItem(item: QueueItem): Skill {
    return { skillName: item.skillName, topic: item.topicTitle, tier: item.tier };
}

/** The step to render for a queue item. */
export function stepFor(item: QueueItem): SessionStep {
    return { item, problem: getProblem(skillFromItem(item)) };
}

/**
 * The grading convention while problems are placeholders: A is the correct
 * answer, so the learner drives correctness by choosing A; every other letter
 * and "don't know" is a miss.
 */
export function isCorrect(answer: Answer): boolean {
    return answer === "A";
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

/**
 * Grade the card and let FSRS reschedule it. A correct answer rates Good, a miss
 * rates Again, exactly as the reviewer would. `grade_now` reads the card's own
 * scheduling states and applies the rating through Anki's normal answering path,
 * so the chosen order does not depend on Anki's queue and intervals are
 * untouched.
 */
export async function grade(item: QueueItem, answer: Answer): Promise<void> {
    const rating = isCorrect(answer) ? CardAnswer_Rating.GOOD : CardAnswer_Rating.AGAIN;
    await gradeNow({ cardIds: [item.cardId], rating });
}

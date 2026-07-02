// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import type { QueueItem } from "./session";
import { CHOICE_IDS, getProblem, isCorrect, skillFromItem, stepFor } from "./session";

function queueItem(overrides: Partial<QueueItem> = {}): QueueItem {
    return {
        cardId: 123n,
        skillId: "chain_rule",
        skillName: "Chain rule",
        topicId: "differential_calc",
        topicTitle: "Differential calculus",
        tier: "relearn",
        level: 0,
        ...overrides,
    };
}

test("getProblem returns the skill label and the fixed A-E controls", () => {
    const problem = getProblem({ skillName: "Chain rule", topic: "Differentiation", tier: "relearn" });

    expect(problem.skillName).toBe("Chain rule");
    expect(problem.topic).toBe("Differentiation");
    expect(problem.tier).toBe("relearn");
    expect(problem.choices.map((c) => c.id)).toEqual([...CHOICE_IDS]);
});

test("skillFromItem reads the name, topic title and tier off a queue item", () => {
    const skill = skillFromItem(queueItem());

    expect(skill).toEqual({
        skillName: "Chain rule",
        topic: "Differential calculus",
        tier: "relearn",
    });
});

test("stepFor pairs a queue item with its placeholder problem", () => {
    const item = queueItem();
    const step = stepFor(item);

    expect(step.item).toBe(item);
    expect(step.problem.skillName).toBe("Chain rule");
    expect(step.problem.topic).toBe("Differential calculus");
    expect(step.problem.choices).toHaveLength(CHOICE_IDS.length);
});

test("A is the only correct answer; everything else is a miss", () => {
    expect(isCorrect("A")).toBe(true);
    expect(isCorrect("B")).toBe(false);
    expect(isCorrect("C")).toBe(false);
    expect(isCorrect("D")).toBe(false);
    expect(isCorrect("E")).toBe(false);
    expect(isCorrect("dont-know")).toBe(false);
});

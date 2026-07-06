// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import { fadedScaffoldFor, fadeSteps, splitSolutionSteps } from "./scaffold";

test("splitSolutionSteps splits a multi-sentence solution into ordered steps", () => {
    const steps = splitSolutionSteps(
        "There are 36 outcomes. Four of them sum to 5. So the probability is 1/9.",
    );
    expect(steps).toEqual([
        "There are 36 outcomes.",
        "Four of them sum to 5.",
        "So the probability is 1/9.",
    ]);
});

test("splitSolutionSteps never splits inside an inline \\( ... \\) span", () => {
    // The period inside \(a.b\) must not be read as a sentence boundary.
    const steps = splitSolutionSteps(
        "First factor \\(a.b = c\\) fully. Then read the roots.",
    );
    expect(steps).toEqual([
        "First factor \\(a.b = c\\) fully.",
        "Then read the roots.",
    ]);
});

test("splitSolutionSteps never splits inside a display \\[ ... \\] span", () => {
    // Newlines and a period sit INSIDE the display span and must be protected.
    const steps = splitSolutionSteps(
        "Set up the integral.\n\\[ \\int_0^1 x\\,dx.\n= 1/2 \\]\nEvaluate it.",
    );
    expect(steps).toEqual([
        "Set up the integral.",
        "\\[ \\int_0^1 x\\,dx.\n= 1/2 \\]",
        "Evaluate it.",
    ]);
});

test("splitSolutionSteps also breaks on newlines and drops blank pieces", () => {
    const steps = splitSolutionSteps("Step one\n\nStep two\n");
    expect(steps).toEqual(["Step one", "Step two"]);
});

test("splitSolutionSteps returns a single step when there is no boundary", () => {
    expect(splitSolutionSteps("Just one line with no terminator")).toEqual([
        "Just one line with no terminator",
    ]);
});

test("splitSolutionSteps returns nothing for a blank solution", () => {
    expect(splitSolutionSteps("")).toEqual([]);
    expect(splitSolutionSteps("   \n  ")).toEqual([]);
});

test("fadeSteps hides the final step at Guided (level 1)", () => {
    const steps = ["a.", "b.", "c."];
    expect(fadeSteps(steps, 1)).toEqual({ shown: ["a.", "b."], hiddenCount: 1 });
});

test("fadeSteps hides two trailing steps at Revisit (level 3) when long enough", () => {
    const steps = ["a.", "b.", "c.", "d."];
    expect(fadeSteps(steps, 3)).toEqual({ shown: ["a.", "b."], hiddenCount: 2 });
});

test("fadeSteps at Revisit hides only one when the solution is short", () => {
    const steps = ["a.", "b.", "c."];
    expect(fadeSteps(steps, 3)).toEqual({ shown: ["a.", "b."], hiddenCount: 1 });
});

test("fadeSteps never hides every step, leaving at least one shown", () => {
    const steps = ["only.", "two."];
    const faded = fadeSteps(steps, 3);
    expect(faded.shown).toEqual(["only."]);
    expect(faded.hiddenCount).toBe(1);
    expect(faded.shown.length).toBeGreaterThanOrEqual(1);
});

test("fadeSteps returns hiddenCount 0 for a one-step solution (the caller then shows no scaffold)", () => {
    const steps = ["The whole worked solution, in one step."];
    expect(fadeSteps(steps, 1)).toEqual({
        shown: ["The whole worked solution, in one step."],
        hiddenCount: 0,
    });
    expect(fadeSteps(steps, 3)).toEqual({
        shown: ["The whole worked solution, in one step."],
        hiddenCount: 0,
    });
});

test("fadeSteps handles an empty step list", () => {
    expect(fadeSteps([], 1)).toEqual({ shown: [], hiddenCount: 0 });
});

test("splitSolutionSteps + fadeSteps produce a real scaffold from a dice solution", () => {
    // The e2e/live fixture's solution, verbatim, exercises the real path: three
    // steps, the last (the answer) hidden at Guided.
    const solution = "There are \\(6 \\cdot 6 = 36\\) equally likely ordered outcomes. "
        + "Exactly four of them sum to \\(5\\): \\((1,4), (2,3), (3,2), (4,1)\\). "
        + "So \\(P(\\text{sum} = 5) = \\frac{4}{36} = \\frac{1}{9}\\).";
    const steps = splitSolutionSteps(solution);
    expect(steps).toHaveLength(3);
    const faded = fadeSteps(steps, 1);
    expect(faded.shown).toHaveLength(2);
    expect(faded.hiddenCount).toBe(1);
    // The answer lives in the hidden final step, so the scaffold does not leak it.
    expect(faded.shown.join(" ")).not.toContain("\\frac{1}{9}");
});

test("fadedScaffoldFor drops the scaffold (null) for a one-step solution, so nothing leaks", () => {
    // A one-step solution cannot hide the answer, so NO scaffold is shown and the
    // item is solved cold, rather than revealing the full solution above the live
    // graded choices. This is the gate that stops a trivially-correct attempt.
    expect(fadedScaffoldFor("The whole solution, answer 1/9, in one sentence.", 1)).toBeNull();
    expect(fadedScaffoldFor("The whole solution, answer 1/9, in one sentence.", 3)).toBeNull();
});

test("fadedScaffoldFor drops the scaffold (null) for a blank solution", () => {
    expect(fadedScaffoldFor("", 1)).toBeNull();
    expect(fadedScaffoldFor("   ", 1)).toBeNull();
});

test("fadedScaffoldFor returns a real scaffold when the solution can be faded", () => {
    const faded = fadedScaffoldFor("Set up the sum. Simplify each term. So the total is 6.", 1);
    expect(faded).not.toBeNull();
    expect(faded?.hiddenCount).toBe(1);
    expect(faded?.shown).toEqual(["Set up the sum.", "Simplify each term."]);
    // The answer sits in the hidden final step, never in the shown steps.
    expect(faded?.shown.join(" ")).not.toContain("total is 6");
});

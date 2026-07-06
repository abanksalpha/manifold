// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * The faded-example scaffold (D36, Phase 2 and 3).
 *
 * A Guided (level 1) or Revisit (level 3) skill is not solved cold: the player
 * shows the leading steps of the item's OWN verified worked solution and hides
 * the trailing step(s), so the learner finishes the method by choosing the
 * answer. This module is the pure, view-free half of that: it splits a solution
 * into ordered steps and decides how many trailing steps to hide.
 *
 * It derives everything from the real `solution` text and invents nothing: a
 * solution that will not split into two or more steps is not padded with a
 * fabricated one, it degrades honestly to the full worked solution (see
 * {@link fadeSteps}).
 */

// A delimited-LaTeX math span: display `\[ ... \]` or inline `\( ... \)`,
// matched non-greedily so adjacent spans do not merge. Mirrors the delimiters
// MathText typesets, so the two always agree on what a math run is.
const MATH_SPAN = /\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)/g;

// Private-use sentinels used only inside this module: one stands in for a math
// span while the prose is split (so a period inside maths can never be read as a
// sentence end), the other marks a step boundary. Neither occurs in real content.
const MATH_MARK = "\uE000";
const STEP_MARK = "\uE001";

/**
 * Split a delimited-LaTeX solution into ordered step strings, never splitting
 * inside a `\( ... \)` or `\[ ... \]` span.
 *
 * Maths spans are protected first, then the prose is split on newlines and on
 * sentence-ending punctuation (`.`, `!`, `?`) followed by whitespace; the spans
 * are then restored. Steps are trimmed and empties dropped. A blank or
 * whitespace-only solution yields no steps.
 */
export function splitSolutionSteps(solution: string): string[] {
    if (typeof solution !== "string" || !solution.trim()) {
        return [];
    }
    // 1. Protect maths: replace each span with a sentinel-wrapped index so the
    //    sentence splitter never sees the punctuation or spaces inside it.
    const spans: string[] = [];
    const guarded = solution.replace(MATH_SPAN, (span) => {
        spans.push(span);
        return `${MATH_MARK}${spans.length - 1}${MATH_MARK}`;
    });

    // 2. Mark boundaries: every newline run, and every sentence end followed by
    //    whitespace, becomes a single step boundary.
    const marked = guarded
        .replace(/\r\n?/g, "\n")
        .replace(/\n+/g, STEP_MARK)
        .replace(/([.!?])(\s+)/g, `$1${STEP_MARK}`);

    // 3. Restore the protected maths, trim, and drop empty pieces.
    const restore = new RegExp(`${MATH_MARK}(\\d+)${MATH_MARK}`, "g");
    return marked
        .split(STEP_MARK)
        .map((piece) => piece.replace(restore, (_m, index: string) => spans[Number(index)] ?? ""))
        .map((piece) => piece.trim())
        .filter((piece) => piece.length > 0);
}

/** The steps shown by the scaffold, plus how many trailing steps stay hidden. */
export interface FadedSteps {
    shown: string[];
    hiddenCount: number;
}

/**
 * Decide which solution steps to reveal for a scaffold at this level, hiding the
 * trailing one(s) for the learner to finish.
 *
 * Graduated fade (a simple monotone policy): Guided (level 1) hides the final
 * step; Revisit (level 3) hides the final two once the solution is long enough
 * (four or more steps), so support lessens as competence grows. Any other level
 * hides one. It never hides every step: at least one is always shown when there
 * are two or more.
 *
 * A one-step solution cannot be faded honestly, so it yields `hiddenCount: 0`;
 * the caller then shows NO scaffold and the item is solved cold (see
 * {@link fadedScaffoldFor}). Revealing the whole solution above the graded
 * choices would leak the answer, so it is never shown in that case.
 */
export function fadeSteps(steps: string[], level: number): FadedSteps {
    const total = steps.length;
    if (total === 0) {
        return { shown: [], hiddenCount: 0 };
    }
    if (total < 2) {
        return { shown: steps.slice(), hiddenCount: 0 };
    }
    let hidden = level === 3 && total >= 4 ? 2 : 1;
    // Never hide all steps: always leave at least one shown.
    hidden = Math.min(hidden, total - 1);
    return { shown: steps.slice(0, total - hidden), hiddenCount: hidden };
}

/**
 * The scaffold to show for a Guided (level 1) or Revisit (level 3) attempt, or
 * null when the item cannot be faded safely.
 *
 * The faded example scaffolds the SAME item that is then graded, so it is only
 * honest while at least one trailing step (which carries the answer) stays
 * hidden. A solution that will not split into two or more steps leaves nothing to
 * hide (`hiddenCount === 0`); this returns null so the caller shows no scaffold
 * and the learner solves it cold, instead of reading the full solution, answer
 * included, directly above the live choices. This is the single gate that keeps a
 * scaffolded attempt from feeding FSRS a trivially-correct answer.
 */
export function fadedScaffoldFor(solution: string, level: number): FadedSteps | null {
    const faded = fadeSteps(splitSolutionSteps(solution), level);
    if (faded.hiddenCount < 1 || faded.shown.length === 0) {
        return null;
    }
    return faded;
}

// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Turn the item bank's ASCII maths into typeset maths.
 *
 * The verified bank (`item_bank.json`) stores stems, choices and solutions in a
 * plain, machine-checkable ASCII grammar (`3x^2 + 2x`, `x**3 + 2*x`,
 * `[[3, 1], [0, 2]]`, `det(A - lambda I)`, `1/9`). The session must never show
 * that ASCII to a learner (spec D38: every equation is typeset). This module is
 * the single seam that rewrites the bank grammar into LaTeX and marks the maths
 * runs inside prose, so `MathText.svelte` can typeset them through the engine's
 * MathJax build (the repo's math engine; no ASCII math ever reaches the screen).
 *
 * It converts, never invents: a run it cannot confidently read as maths is left
 * as prose, so a solution's words stay words and only its expressions become
 * symbols. Nothing here grades or trusts content; correctness was settled
 * offline by the SymPy verifier that built the bank.
 */

/** Multi-letter identifiers that are maths, not prose: Greek letters and the
 * standard function/operator names. Everything else with two or more letters is
 * read as an English word and ends a maths run rather than being typeset. */
const MATH_WORDS = new Set([
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "theta",
    "lambda",
    "mu",
    "nu",
    "pi",
    "rho",
    "sigma",
    "tau",
    "phi",
    "chi",
    "psi",
    "omega",
    "infty",
    "infinity",
    "sqrt",
    "sin",
    "cos",
    "tan",
    "sec",
    "csc",
    "cot",
    "log",
    "ln",
    "exp",
    "lim",
    "det",
    "gcd",
    "lcm",
    "min",
    "max",
    "deg",
    "dim",
    "ker",
    "mod",
    "Re",
    "Im",
]);

/** Single letters that read as English words, not variables, so a stray article
 * or pronoun is not italicised mid-sentence. Real variables (x, f, F, n, …) are
 * unaffected; matrix names like A or the identity I only ever appear inside a
 * function call here, where they are typeset regardless. */
const WORD_LETTERS = new Set(["a", "A", "I"]);

/** Convert a `[[a, b], [c, d]]` matrix literal to a LaTeX bmatrix. */
function matrixToLatex(literal: string): string {
    const inner = literal.slice(1, -1).trim();
    const rows = inner
        .split(/\]\s*,\s*\[/)
        .map((row) => row.replace(/^\[|\]$/g, "").trim())
        .filter((row) => row.length > 0);
    const body = rows
        .map((row) => row.split(/\s*,\s*/).join(" & "))
        .join(" \\\\ ");
    return `\\begin{bmatrix} ${body} \\end{bmatrix}`;
}

/**
 * Convert one pure ASCII maths expression to LaTeX. Handles the bank grammar:
 * matrices, `**`/`^` powers, `*` (implicit next to a symbol, `\cdot` between
 * numbers), integer fractions, comparison operators, Greek letters and the
 * named functions. Order matters: matrices and powers are resolved before the
 * multiplication and fraction passes touch the same characters.
 */
export function expressionToLatex(expr: string): string {
    let s = expr.trim();
    s = s.replace(/\[\[.*?\]\]/g, (m) => matrixToLatex(m));
    s = s.replace(/sqrt\s*\(([^()]*)\)/g, "\\sqrt{$1}");
    s = s.replace(/\*\*/g, "^");
    for (const word of MATH_WORDS) {
        if (word === "sqrt") {
            continue;
        }
        s = s.replace(new RegExp(`\\b${word}\\b`, "g"), `\\${word}`);
    }
    // Brace a bare exponent so multi-character powers group correctly.
    s = s.replace(
        /\^\s*(\{[^{}]*\}|-?[0-9A-Za-z]+)/g,
        (_m, g: string) => (g.startsWith("{") ? `^${g}` : `^{${g}}`),
    );
    // Multiplication: drop the star where a coefficient meets a symbol or group
    // (2*x -> 2x), and render it as a centred dot only between bare numbers.
    s = s.replace(/(\d)\s*\*\s*(?=[A-Za-z(\\])/g, "$1");
    s = s.replace(/([A-Za-z)])\s*\*\s*(?=[A-Za-z(\\])/g, "$1");
    s = s.replace(/\s*\*\s*/g, " \\cdot ");
    s = s.replace(/(\d+)\s*\/\s*(\d+)/g, "\\frac{$1}{$2}");
    s = s.replace(/<=/g, " \\le ");
    s = s.replace(/>=/g, " \\ge ");
    s = s.replace(/!=/g, " \\ne ");
    s = s.replace(/->/g, " \\to ");
    return s.replace(/\s+/g, " ").trim();
}

/** Index just past the `)` that closes the `(` at `start`, or -1 if unbalanced. */
function readBalancedParens(s: string, start: number): number {
    let depth = 0;
    for (let i = start; i < s.length; i++) {
        if (s[i] === "(") {
            depth += 1;
        } else if (s[i] === ")") {
            depth -= 1;
            if (depth === 0) {
                return i + 1;
            }
        }
    }
    return -1;
}

/** True when every two-or-more-letter word inside a group is a maths word, so a
 * parenthesised aside of ordinary prose is never typeset as an equation. */
function looksLikeMath(inner: string): boolean {
    const words = inner.match(/[A-Za-z]{2,}/g) ?? [];
    return words.every((word) => MATH_WORDS.has(word));
}

/**
 * Mark the maths runs in a mixed prose/ASCII string and return a string
 * `MathText.svelte` can render: each maths run is converted to LaTeX and wrapped
 * in `\( … \)`, and the prose between runs is left untouched. A run is bounded
 * by any ordinary word (two or more non-maths letters) or sentence punctuation,
 * so words never leak into an equation and equations never bleed into words.
 */
export function mathToMarkup(text: string): string {
    if (!text) {
        return "";
    }
    const out: string[] = [];
    let mathRaw = "";
    let prose = "";
    let pending = "";

    const flushMath = (): void => {
        if (!mathRaw) {
            return;
        }
        const latex = expressionToLatex(mathRaw);
        // A run with no letters or digits (a lone operator or bracket) is not
        // really maths; keep it as prose rather than typesetting a stray symbol.
        out.push(/[0-9A-Za-z]/.test(latex) ? `\\(${latex}\\)` : mathRaw.trim());
        mathRaw = "";
    };
    const flushProse = (): void => {
        if (prose) {
            out.push(prose);
            prose = "";
        }
    };
    const addMath = (token: string): void => {
        if (pending) {
            if (mathRaw) {
                mathRaw += pending;
            } else {
                prose += pending;
                flushProse();
            }
            pending = "";
        }
        flushProse();
        mathRaw += token;
    };
    const addProse = (token: string): void => {
        if (pending) {
            flushMath();
            prose += pending;
            pending = "";
        }
        flushMath();
        prose += token;
    };

    let i = 0;
    const n = text.length;
    while (i < n) {
        const c = text[i];
        if (/\s/.test(c)) {
            let j = i;
            while (j < n && /\s/.test(text[j])) {
                j += 1;
            }
            pending += text.slice(i, j);
            i = j;
            continue;
        }
        if (c === "[" && text[i + 1] === "[") {
            const m = /^\[\[.*?\]\]/.exec(text.slice(i));
            if (m) {
                addMath(m[0]);
                i += m[0].length;
                continue;
            }
        }
        if (c === "(") {
            const end = readBalancedParens(text, i);
            if (end !== -1 && looksLikeMath(text.slice(i + 1, end - 1))) {
                addMath(text.slice(i, end));
                i = end;
                continue;
            }
            addProse(c);
            i += 1;
            continue;
        }
        if (/[A-Za-z]/.test(c)) {
            let j = i;
            while (j < n && /[A-Za-z]/.test(text[j])) {
                j += 1;
            }
            const word = text.slice(i, j);
            let k = j;
            while (k < n && text[k] === "'") {
                k += 1;
            }
            const token = text.slice(i, k);
            const isSymbol = (word.length === 1 && !WORD_LETTERS.has(word))
                || MATH_WORDS.has(word);
            if (isSymbol && text[k] === "(") {
                const end = readBalancedParens(text, k);
                if (end !== -1 && looksLikeMath(text.slice(k + 1, end - 1))) {
                    addMath(text.slice(i, end));
                    i = end;
                    continue;
                }
            }
            if (isSymbol) {
                addMath(token);
            } else {
                addProse(token);
            }
            i = k;
            continue;
        }
        const num = /^\d+(?:\.\d+)?/.exec(text.slice(i));
        if (num) {
            addMath(num[0]);
            i += num[0].length;
            continue;
        }
        const op = /^(\*\*|<=|>=|!=|->|[+*/^=])/.exec(text.slice(i));
        if (op) {
            addMath(op[0]);
            i += op[0].length;
            continue;
        }
        if (c === "-") {
            const prev = text[i - 1];
            const next = text[i + 1];
            if (prev && next && /[A-Za-z]/.test(prev) && /[A-Za-z]/.test(next)) {
                addProse(c);
            } else {
                addMath(c);
            }
            i += 1;
            continue;
        }
        addProse(c);
        i += 1;
    }

    if (pending) {
        flushMath();
        prose += pending;
    }
    flushMath();
    flushProse();
    return out.join("");
}

/** True when a string already carries a LaTeX math delimiter (`\(` or `\[`). */
const HAS_LATEX_DELIMITER = /\\\(|\\\[/;

/**
 * Prepare a DISPLAY field (stem, worked solution, a rationale, a lecture body) for
 * `MathText`.
 *
 * The generator now emits these fields with mathematics already wrapped in
 * `\( … \)` / `\[ … \]` LaTeX and validated at generation time (Task 2), so the
 * view can typeset them directly — running that LaTeX back through `mathToMarkup`
 * (which speaks the ASCII grammar) would mangle the backslashes and show raw
 * source, the exact bug this replaces. So: a field that already carries a LaTeX
 * delimiter is passed through untouched for `MathText` to typeset; a field with no
 * delimiter is either plain prose or a legacy ASCII item from before the switch, so
 * it goes through `mathToMarkup`, which marks any ASCII maths runs. This is a
 * grammar router, never a fabrication: it invents nothing, it only picks which
 * reader the text was written for.
 *
 * CHOICES do not come here — they stay sympy-ASCII (verify.py parses them) and go
 * through `mathToMarkup` / `mathToPlainText` directly at the call site.
 */
export function renderMath(text: string): string {
    if (!text) {
        return "";
    }
    return HAS_LATEX_DELIMITER.test(text) ? text : mathToMarkup(text);
}

/**
 * Render the bank's ASCII maths as a plain-text form for a screen reader.
 *
 * `mathToMarkup` + `MathText` typeset maths into LaTeX images whose only text
 * is the LaTeX source, so an answer control that named itself "Answer A" — or
 * leaned on that LaTeX alt — would read no real option to a non-sighted
 * learner. This speaks the same grammar as words ("x**3 + 2*x" -> "x to the
 * power of 3 plus 2 times x") so the accessible name carries the actual choice.
 * Like `mathToMarkup` it converts, never invents: a token it does not
 * recognise is left as written, and correctness was already settled offline.
 */
export function mathToPlainText(text: string): string {
    if (!text) {
        return "";
    }
    let s = text;
    // Matrices first, before the operator passes touch the inner entries:
    // [[a, b], [c, d]] -> "matrix with rows a, b; c, d".
    s = s.replace(/\[\[.*?\]\]/g, (literal) => {
        const inner = literal.slice(1, -1).trim();
        const rows = inner
            .split(/\]\s*,\s*\[/)
            .map((row) => row.replace(/^\[|\]$/g, "").trim())
            .filter((row) => row.length > 0);
        return `matrix with rows ${rows.join("; ")}`;
    });
    s = s.replace(/sqrt\s*\(([^()]*)\)/g, "square root of ($1)");
    // Powers before the single-star pass, so `**` never reads as "times".
    s = s.replace(/\s*(?:\*\*|\^)\s*/g, " to the power of ");
    s = s.replace(/(\d+)\s*\/\s*(\d+)/g, "$1 over $2");
    s = s.replace(/\s*\*\s*/g, " times ");
    s = s.replace(/<=/g, " less than or equal to ");
    s = s.replace(/>=/g, " greater than or equal to ");
    s = s.replace(/!=/g, " not equal to ");
    s = s.replace(/->/g, " to ");
    s = s.replace(/\s*\+\s*/g, " plus ");
    // Only a spaced hyphen is a binary minus; a leading "-2" stays a sign.
    s = s.replace(/ - /g, " minus ");
    s = s.replace(/\s*=\s*/g, " equals ");
    return s.replace(/\s+/g, " ").trim();
}

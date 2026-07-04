// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "vitest";

import { expressionToLatex, mathToMarkup, mathToPlainText, renderMath } from "./mathmarkup";

test("expressionToLatex converts the bank's power grammar", () => {
    expect(expressionToLatex("x**3 + 2*x")).toBe("x^{3} + 2x");
    expect(expressionToLatex("3*x**3 + 2*x**2")).toBe("3x^{3} + 2x^{2}");
    expect(expressionToLatex("6*x + 2")).toBe("6x + 2");
});

test("expressionToLatex converts fractions, dot products and matrices", () => {
    expect(expressionToLatex("1/9")).toBe("\\frac{1}{9}");
    expect(expressionToLatex("6 * 6 = 36")).toBe("6 \\cdot 6 = 36");
    expect(expressionToLatex("[[3, 1], [0, 2]]")).toBe(
        "\\begin{bmatrix} 3 & 1 \\\\ 0 & 2 \\end{bmatrix}",
    );
});

test("expressionToLatex names Greek letters and functions", () => {
    expect(expressionToLatex("det(A - lambda I)")).toBe("\\det(A - \\lambda I)");
});

test("mathToMarkup typesets the maths in a stem and leaves the prose alone", () => {
    const out = mathToMarkup(
        "Which of the following is an antiderivative of f(x) = 3x^2 + 2x?",
    );
    expect(out).toContain("Which of the following is an antiderivative of ");
    expect(out).toContain("\\(f(x) = 3x^{2} + 2x\\)");
    expect(out.endsWith("?")).toBe(true);
    // No raw ASCII power survives to the screen.
    expect(out).not.toContain("3x^2");
    expect(out).not.toContain("**");
});

test("mathToMarkup typesets a matrix embedded in prose", () => {
    const out = mathToMarkup("the matrix [[3, 1], [0, 2]]?");
    expect(out).toContain("\\(\\begin{bmatrix} 3 & 1 \\\\ 0 & 2 \\end{bmatrix}\\)");
    expect(out).not.toContain("[[3");
});

test("mathToMarkup wraps a whole ASCII choice as one typeset run", () => {
    expect(mathToMarkup("x**3 + 2*x")).toBe("\\(x^{3} + 2x\\)");
});

test("mathToMarkup does not italicise ordinary prose or stray articles", () => {
    // Pure prose passes through untouched.
    expect(mathToMarkup("The matrix is upper triangular.")).toBe(
        "The matrix is upper triangular.",
    );
    // The article "a" is a word here, not a variable, so it is not typeset.
    expect(mathToMarkup("As a check, the trace 5 = 3 + 2 agrees.")).toContain("As a check, ");
    expect(mathToMarkup("As a check, the trace 5 = 3 + 2 agrees.")).toContain("\\(5 = 3 + 2\\)");
});

test("mathToMarkup keeps a parenthesised prose aside as prose", () => {
    const out = mathToMarkup("term by term (raise the exponent by one) so F(x) holds");
    expect(out).toContain("(raise the exponent by one)");
    expect(out).toContain("\\(F(x)\\)");
});

test("renderMath passes delimited LaTeX straight through, untouched", () => {
    // The generator now emits display fields as delimited LaTeX; renderMath must
    // NOT run them through mathToMarkup (which would mangle the backslashes).
    const inline = "By the chain rule, \\(\\frac{dz}{dx} = -\\frac{x}{z}\\).";
    expect(renderMath(inline)).toBe(inline);
    const display = "So \\[\\int 2x\\,dx = x^{2} + C.\\]";
    expect(renderMath(display)).toBe(display);
});

test("renderMath still typesets a legacy ASCII field (no delimiters)", () => {
    // A pre-LaTeX bank item has ASCII maths and no delimiters; renderMath routes it
    // through mathToMarkup so it still typesets instead of showing raw ASCII.
    const out = renderMath("The antiderivative is x**3 + 2*x here.");
    expect(out).toContain("\\(x^{3} + 2x\\)");
    expect(out).not.toContain("x**3");
});

test("renderMath leaves plain prose alone and handles empty input", () => {
    expect(renderMath("The matrix is upper triangular.")).toBe(
        "The matrix is upper triangular.",
    );
    expect(renderMath("")).toBe("");
});

test("mathToPlainText speaks the bank's choice grammar for a screen reader", () => {
    // Powers and multiplication become words, never "star" or "caret".
    expect(mathToPlainText("x**3 + 2*x")).toBe("x to the power of 3 plus 2 times x");
    expect(mathToPlainText("3*x**3 + 2*x**2")).toBe(
        "3 times x to the power of 3 plus 2 times x to the power of 2",
    );
    // Fractions read as "over"; a leading minus stays a sign.
    expect(mathToPlainText("5/36")).toBe("5 over 36");
    expect(mathToPlainText("-2, -3")).toBe("-2, -3");
    // A spaced hyphen is a binary minus.
    expect(mathToPlainText("det(A - lambda I)")).toBe("det(A minus lambda I)");
    // Matrices are named rather than read as brackets.
    expect(mathToPlainText("[[3, 1], [0, 2]]")).toBe("matrix with rows 3, 1; 0, 2");
    // No raw operator survives to the accessible name.
    expect(mathToPlainText("x**3 + 2*x")).not.toContain("*");
});

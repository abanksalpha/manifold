// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

// Pixel-alignment measurement for the teaching-scaffold panels (align skill),
// run against the real rendered mediasrv page in the hermetic harness (so the
// faded example renders deterministically from the 3-step fixture). It mirrors
// the align skill's measure.mjs math: icon/badge optical centering to the text's
// cap-height, shared left edges, and gaps on the 4px spacing scale. Any delta
// over 1px fails, so this is the measure-fix loop as a permanent regression guard.

import type { Page } from "@playwright/test";

import { expect, reachAttempt, test } from "./fixtures";

const TOL = 1;
const SCALE = 4;

// The measurement runs in the page: cap-height optical center (mirrors
// measure.mjs), element box center, a bare text node's cap center via a Range,
// and the box edges. Returns the deltas the align skill checks.
async function measureFaded(page: Page) {
    await page.evaluate(() => (document.fonts ? document.fonts.ready.then(() => true) : true));
    return page.evaluate(() => {
        const capCenterY = (rectTop: number, cs: CSSStyleDeclaration): number => {
            const fontSize = parseFloat(cs.fontSize);
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d")!;
            ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${fontSize}px ${cs.fontFamily}`;
            ctx.textBaseline = "alphabetic";
            const m = ctx.measureText("H");
            const capHeight = m.actualBoundingBoxAscent || fontSize * 0.7;
            const ascent = m.fontBoundingBoxAscent || fontSize * 0.8;
            const descent = m.fontBoundingBoxDescent || fontSize * 0.2;
            const lh = cs.lineHeight === "normal" ? fontSize * 1.2 : parseFloat(cs.lineHeight);
            const baseline = rectTop + (lh - (ascent + descent)) / 2 + ascent;
            return baseline - capHeight / 2;
        };
        const boxCenterY = (el: Element): number => {
            const r = el.getBoundingClientRect();
            return r.top + r.height / 2;
        };
        const elCap = (el: Element): number => {
            const cs = getComputedStyle(el);
            const r = el.getBoundingClientRect();
            const top = r.top + parseFloat(cs.paddingTop || "0") + parseFloat(cs.borderTopWidth || "0");
            return capCenterY(top, cs);
        };
        const textNode = (parent: Element): Text | null => {
            for (const n of Array.from(parent.childNodes)) {
                if (n.nodeType === 3 && (n.textContent || "").trim()) {
                    return n as Text;
                }
            }
            return null;
        };
        const textNodeCap = (parent: Element): number => {
            const n = textNode(parent)!;
            const rng = document.createRange();
            rng.selectNode(n);
            return capCenterY(rng.getBoundingClientRect().top, getComputedStyle(parent));
        };
        const textNodeLeft = (parent: Element): number => {
            const n = textNode(parent)!;
            const rng = document.createRange();
            rng.selectNode(n);
            return rng.getBoundingClientRect().left;
        };
        const left = (el: Element): number => el.getBoundingClientRect().left;
        const right = (el: Element): number => el.getBoundingClientRect().right;

        const eyebrow = document.querySelector(".mf-faded-eyebrow")!;
        const mark = document.querySelector(".mf-faded-mark")!;
        const stepNum = document.querySelector(".mf-faded-step:not(.mf-faded-blank) .mf-faded-num")!;
        const stepText = document.querySelector(
            ".mf-faded-step:not(.mf-faded-blank) .mf-faded-step-text",
        )!;
        const blankNum = document.querySelector(".mf-faded-blank .mf-faded-num")!;
        const blankText = document.querySelector(".mf-faded-blank-text")!;

        // Signed centre deltas (badge centre minus text cap-centre): positive means
        // the badge sits BELOW the cap centre (nudge up), negative means ABOVE it.
        return {
            eyebrowIconVsLabel: boxCenterY(mark) - textNodeCap(eyebrow),
            eyebrowGap: textNodeLeft(eyebrow) - right(mark),
            stepIconVsText: boxCenterY(stepNum) - elCap(stepText),
            stepGap: left(stepText) - right(stepNum),
            markVsStepNumLeft: Math.abs(left(mark) - left(stepNum)),
            blankIconVsText: boxCenterY(blankNum) - elCap(blankText),
        };
    });
}

const onScale = (gap: number): number => Math.abs(gap - Math.round(gap / SCALE) * SCALE);

// The signed centre delta between an eyebrow's icon badge and its label's
// cap-height centre (shared by every teaching panel). Reuses the same cap-height
// math as the align skill's measure.mjs.
async function measureEyebrow(
    page: Page,
    eyebrowSel: string,
    markSel: string,
): Promise<number> {
    await page.evaluate(() => (document.fonts ? document.fonts.ready.then(() => true) : true));
    return page.evaluate(
        ({ eyebrowSel, markSel }) => {
            const capCenterY = (rectTop: number, cs: CSSStyleDeclaration): number => {
                const fontSize = parseFloat(cs.fontSize);
                const canvas = document.createElement("canvas");
                const ctx = canvas.getContext("2d")!;
                ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${fontSize}px ${cs.fontFamily}`;
                ctx.textBaseline = "alphabetic";
                const m = ctx.measureText("H");
                const capHeight = m.actualBoundingBoxAscent || fontSize * 0.7;
                const ascent = m.fontBoundingBoxAscent || fontSize * 0.8;
                const descent = m.fontBoundingBoxDescent || fontSize * 0.2;
                const lh = cs.lineHeight === "normal" ? fontSize * 1.2 : parseFloat(cs.lineHeight);
                return rectTop + (lh - (ascent + descent)) / 2 + ascent - capHeight / 2;
            };
            const eyebrow = document.querySelector(eyebrowSel)!;
            const mark = document.querySelector(markSel)!;
            let cap = 0;
            for (const n of Array.from(eyebrow.childNodes)) {
                if (n.nodeType === 3 && (n.textContent || "").trim()) {
                    const rng = document.createRange();
                    rng.selectNode(n);
                    cap = capCenterY(rng.getBoundingClientRect().top, getComputedStyle(eyebrow));
                    break;
                }
            }
            const r = mark.getBoundingClientRect();
            return r.top + r.height / 2 - cap;
        },
        { eyebrowSel, markSel },
    );
}

// Runs first, on the all-New seeded collection, so the New-skill ladder (and its
// worked-example eyebrow) is reachable before the faded test grades a card into a
// due Guided item that would otherwise head the queue.
test("the worked-example teaching panel eyebrow is aligned to the pixel", async ({ page }) => {
    await page.goto("/manifold-session");
    await expect(page.locator(".mf-predict")).toBeVisible({ timeout: 30000 });
    await page.getByRole("button", { name: "Reveal worked example" }).click();
    await expect(page.locator(".mf-worked")).toBeVisible({ timeout: 30000 });
    const d = await measureEyebrow(page, ".mf-worked-eyebrow", ".mf-worked-mark");
    expect(Math.abs(d), `worked eyebrow icon vs label: ${d.toFixed(3)}px`).toBeLessThanOrEqual(TOL);
});

test("the faded-example teaching panel is aligned to the pixel", async ({ page }) => {
    // Reach a Guided (level 1) item: take the first New item to its attempt, miss
    // it, then round-trip the dashboard so the now-due Guided card is served fresh
    // with its faded scaffold (identical navigation to manifold-scaffold.test).
    await page.goto("/manifold-session");
    await reachAttempt(page);
    await page.getByRole("button", { name: "Don't know" }).click();
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await page.getByRole("link", { name: "Back to the dashboard" }).click();
    await expect(page.locator(".mf-wordmark")).toBeVisible();
    await page.evaluate(() => window.sessionStorage.clear());
    await page.goto("/manifold-session");
    await expect(page.locator(".mf-faded")).toBeVisible({ timeout: 30000 });

    const m = await measureFaded(page);

    // Report every failing check at once (not just the first), so the whole panel
    // can be brought to the pixel in one pass.
    const checks: Array<[string, number]> = [
        ["eyebrow icon vs FADED EXAMPLE label (cap-center)", Math.abs(m.eyebrowIconVsLabel)],
        ["step number badge vs step text (cap-center)", Math.abs(m.stepIconVsText)],
        ["blank number badge vs 'Your turn' text (cap-center)", Math.abs(m.blankIconVsText)],
        ["eyebrow mark vs step number left edge", m.markVsStepNumLeft],
        ["eyebrow gap on 4px scale", onScale(m.eyebrowGap)],
        ["step gap on 4px scale", onScale(m.stepGap)],
    ];
    const failures = checks
        .filter(([, delta]) => delta > TOL)
        .map(([name, delta]) => `${name}: ${delta.toFixed(3)}px`);
    expect(failures, `alignment deltas: ${JSON.stringify(m)}`).toEqual([]);
});

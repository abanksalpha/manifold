// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "./fixtures";

test("manifold home renders the scores from the seeded graph", async ({ page }) => {
    await page.goto("/manifold");

    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The two measured inputs are present.
    await expect(page.locator(".metric-label", { hasText: "Memory" })).toBeVisible();
    await expect(page.locator(".metric-label", { hasText: "Performance" })).toBeVisible();

    // Performance has no graded reviews yet, so it abstains from a number. Scope
    // to the Performance card: on a fresh seed "not yet measured" also shows in
    // the selected topic's unmeasured meters, so the bare text matches several
    // elements. Scoping keeps the assertion's intent (Performance has no number)
    // without tripping strict mode.
    await expect(
        page.locator(".metric", { hasText: "Performance" }).getByText("not yet measured"),
    ).toBeVisible();

    // Readiness is below the give-up line on the seeded, unreviewed collection:
    // it abstains, shows the give-up gate it is waiting on, and names the topic
    // to study next, never a bare score.
    await expect(page.locator(".mf-rc-state")).toHaveText("Abstaining");
    await expect(
        page.locator(".mf-gate-label", { hasText: "Independent reviews" }),
    ).toBeVisible();
    await expect(page.locator(".mf-gate-label", { hasText: "Coverage" })).toBeVisible();
    // No projected reading is rendered below the give-up line.
    await expect(page.locator(".mf-rc-reading")).toHaveCount(0);

    // Study-next is derived from the graph: the only unlocked root on the fresh
    // seed is elementary algebra.
    await expect(page.locator(".mf-rc-next")).toContainText("Elementary algebra");

    // The primary action links onward to a session.
    await expect(
        page.getByRole("link", { name: "Start a study session" }),
    ).toHaveAttribute("href", "/manifold-session");
});

// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "./fixtures";

test("manifold home renders the scores from the seeded graph", async ({ page }) => {
    await page.goto("/manifold");

    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The three measurements are present.
    await expect(page.locator(".metric-label", { hasText: "Memory" })).toBeVisible();
    await expect(page.locator(".metric-label", { hasText: "Performance" })).toBeVisible();

    // Performance has no graded reviews yet, so it abstains from a number.
    await expect(page.getByText("not yet measured")).toBeVisible();

    // Readiness is below the give-up line on the seeded, unreviewed collection.
    await expect(page.locator(".mf-rc-state")).toHaveText("Abstaining");

    // Study-next is derived from the graph, and the primary action links onward.
    await expect(page.locator(".mf-nextup")).toContainText("Next up");
    await expect(
        page.getByRole("link", { name: "Start a study session" }),
    ).toHaveAttribute("href", "/manifold-session");
});

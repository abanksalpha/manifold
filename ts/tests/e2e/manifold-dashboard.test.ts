// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "./fixtures";

test("manifold main page renders the dashboard graph and reads out a selected topic", async ({ page }) => {
    // The readiness dashboard now lives on the main page.
    await page.goto("/manifold");

    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The score strip carries the three honest scores.
    await expect(page.locator(".metric-label", { hasText: "Memory" })).toBeVisible();
    await expect(page.locator(".metric-label", { hasText: "Performance" })).toBeVisible();
    await expect(page.locator(".mf-rc-label")).toHaveText("Readiness");

    // Readiness abstains on the seeded, unreviewed collection.
    await expect(page.locator(".mf-rc-state")).toHaveText("Abstaining");

    // All 33 blueprint topics are drawn as nodes, and the legend explains them.
    await expect(page.locator(".mf-node")).toHaveCount(33);
    await expect(page.locator(".mf-legend-label", { hasText: "In progress" })).toBeVisible();

    // One topic is selected on load, so the panel reads out real stats.
    await expect(page.locator(".mf-panel-title")).not.toBeEmpty();
    await expect(page.locator(".mf-stat-key", { hasText: "Tier" })).toBeVisible();
    await expect(page.locator(".mf-stat-key", { hasText: "Blueprint weight" })).toBeVisible();

    // Selecting another node moves the readout to that topic.
    await page.locator(".mf-node[data-topic='linear_algebra_core']").click();
    await expect(page.locator(".mf-panel-title")).toHaveText("Linear algebra: matrices & systems");
});

// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, test } from "./fixtures";

test("a fresh account is routed into onboarding and can complete it", async ({ page }) => {
    // The seeded collection has skill cards but no study history and no
    // onboarding flag, so the home routes into the placement wizard.
    await page.goto("/manifold");
    await expect(page).toHaveURL(/manifold-onboarding/);
    await expect(page.getByText("Which of these have you taken?")).toBeVisible();

    // Report a course and start the placement.
    await page.getByText("Calculus I (differential)").click();
    await page.getByText("Start placement").click();

    // Now either in the cold diagnostic or, if every probe abstained under the
    // e2e fixtures, already at the summary. End the diagnostic if it is running;
    // either way the wizard lands on the summary and never dead-ends. (Answering
    // individual probes goes through the same grade path the session spec covers.)
    const summary = page.getByRole("heading", { name: "Your starting point" });
    const endButton = page.getByRole("button", { name: "End placement" });
    await expect(summary.or(endButton).first()).toBeVisible({ timeout: 30000 });
    if (await endButton.isVisible().catch(() => false)) {
        await endButton.click();
    }
    await expect(summary).toBeVisible();

    // Finishing seeds the placement and lands on the dashboard, which no longer
    // redirects back to onboarding.
    await page.getByText("Go to Manifold").click();
    await expect(page).not.toHaveURL(/onboarding/);
    await expect(page.getByText("Measurements")).toBeVisible();
});

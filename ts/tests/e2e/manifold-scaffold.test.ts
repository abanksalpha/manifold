// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

// The 3-phase teaching scaffold (D36), driven through the real mediasrv session
// pages on a freshly seeded, throwaway GRE collection (run_e2e_isolated.py). The
// seed is entirely unreviewed, so the first served skill is New (level 0): it
// opens with a prediction, then a worked example, then a fresh attempt. Missing a
// New card once makes it Guided (level 1), whose attempt carries a faded-example
// scaffold above the choices. Nothing is mocked here beyond the model-call
// doubles the isolated runner injects; verify.py still proves every served item.

import { expect, reachAttempt, test } from "./fixtures";

test("a New (level 0) item shows predict, then a worked example, then an attempt", async ({ page }) => {
    await page.goto("/manifold-session");
    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // Phase 1 pretrieval: the prediction step shows the stem and asks for a guess
    // before revealing anything worked. There are no answerable choices yet.
    const predict = page.locator(".mf-predict");
    await expect(predict).toBeVisible({ timeout: 30000 });
    await expect(predict.locator(".mf-predict-stem")).not.toBeEmpty();
    await expect(page.locator(".mf-choice")).toHaveCount(0);
    await page.getByRole("button", { name: "Reveal worked example" }).click();

    // Phase 1 worked example: one full instance solved, with the correct choice
    // marked (read-only, not answerable) and the verified worked solution shown.
    const worked = page.locator(".mf-worked");
    await expect(worked).toBeVisible({ timeout: 30000 });
    await expect(worked.getByText("Worked example")).toBeVisible();
    await expect(worked.getByText("Worked solution")).toBeVisible();
    await expect(worked.locator(".mf-worked-choice")).toHaveCount(5);
    await expect(worked.locator(".mf-worked-choice.is-correct")).toHaveCount(1);
    // The worked example is study-only: its choices are not answer buttons.
    await expect(page.getByRole("button", { name: /^Answer / })).toHaveCount(0);
    await page.getByRole("button", { name: "Try one" }).click();

    // The attempt: a fresh instance of the same skill, now answerable.
    const problem = page.locator(".mf-card:not(.mf-abstain):not(.mf-generating)");
    await expect(problem).toBeVisible({ timeout: 30000 });
    await expect(page.locator(".mf-choice")).toHaveCount(5);
    await expect(page.locator(".mf-level")).toHaveText("New");
    await expect(page.getByRole("button", { name: "Answer A" })).toBeVisible();
    // No faded scaffold at New: the worked example already taught it in full.
    await expect(page.locator(".mf-faded")).toHaveCount(0);
});

test("a Guided (level 1) item shows a faded example scaffold above the choices", async ({ page }) => {
    await page.goto("/manifold-session");

    // The seed is all-new, so the first item is New (level 0). Take it to the
    // attempt and miss it ("Don't know"): a missed new card enters learning with
    // no successes, which is Guided (level 1) and due again within the learn-ahead
    // window, so it heads the next queue build.
    await reachAttempt(page);
    await expect(page.locator(".mf-level")).toHaveText("New");
    await page.getByRole("button", { name: "Don't know" }).click();
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await expect(page.locator(".mf-error")).toHaveCount(0);

    // Leave to the dashboard (which persists the session), drop that snapshot, then
    // start fresh so the now-due Guided card is served from a full queue rebuild
    // rather than resumed in its revealed state.
    await page.getByRole("link", { name: "Back to the dashboard" }).click();
    await expect(page.locator(".mf-wordmark")).toBeVisible();
    await page.evaluate(() => window.sessionStorage.clear());
    await page.goto("/manifold-session");

    // The Guided attempt goes straight to the choices (no predict/worked ladder)
    // and carries the faded-example scaffold ABOVE them.
    const faded = page.locator(".mf-faded");
    await expect(faded).toBeVisible({ timeout: 30000 });
    await expect(page.locator(".mf-level")).toHaveText("Guided");
    await expect(page.locator(".mf-predict, .mf-worked")).toHaveCount(0);

    // The scaffold reveals real leading steps and a clearly marked blank to finish.
    await expect(faded.locator(".mf-faded-step").first()).toBeVisible();
    await expect(faded.locator(".mf-faded-blank-text")).toContainText("Your turn");

    // It sits above the choices: teach the method, then let the learner finish it.
    await expect(page.locator(".mf-choice")).toHaveCount(5);
    const fadedBox = await faded.boundingBox();
    const choicesBox = await page.locator(".mf-choices").boundingBox();
    expect(fadedBox).not.toBeNull();
    expect(choicesBox).not.toBeNull();
    expect(fadedBox!.y).toBeLessThan(choicesBox!.y);

    // Finishing by choosing still grades the same card, unchanged.
    await page.getByRole("button", { name: "Answer A" }).click();
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await expect(page.locator(".mf-error")).toHaveCount(0);
});

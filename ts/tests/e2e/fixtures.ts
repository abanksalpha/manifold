// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { expect, type Page, test as base } from "@playwright/test";

export { expect } from "@playwright/test";

export const test = base.extend({
    // The Manifold app gates every route on Google sign-in. The e2e has no
    // interactive OAuth, so point Firebase at the local Auth emulator (started by
    // run_e2e_isolated.py) before any page script runs; firebase.ts then signs in
    // anonymously so the login gate resolves headlessly.
    page: async ({ page }, use) => {
        await page.addInitScript(() => {
            (globalThis as { __MANIFOLD_FIREBASE_EMULATOR__?: boolean })
                .__MANIFOLD_FIREBASE_EMULATOR__ = true;
        });
        await use(page);
    },
});

/**
 * Advance the New-skill teaching ladder to the learner's own attempt.
 *
 * A New (level 0) item opens with a prediction, then a worked example, before the
 * attempt (D36); other levels go straight to the choices. This clicks through
 * whichever teaching steps are shown and waits for the attempt (its five
 * choices), so a spec can reach the answerable problem regardless of level.
 */
export async function reachAttempt(page: Page): Promise<void> {
    await expect(
        page.locator(".mf-predict, .mf-worked, .mf-choice").first(),
    ).toBeVisible({ timeout: 30000 });
    if (await page.locator(".mf-predict").count()) {
        await page.getByRole("button", { name: "Reveal worked example" }).click();
        await expect(page.locator(".mf-worked")).toBeVisible({ timeout: 30000 });
    }
    if (await page.locator(".mf-worked").count()) {
        await page.getByRole("button", { name: "Try one" }).click();
    }
    await expect(page.locator(".mf-choice")).toHaveCount(5, { timeout: 30000 });
}

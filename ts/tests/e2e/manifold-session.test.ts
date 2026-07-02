// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

// The study session serves skills the prerequisite DAG has unlocked, drawn from
// the seeded "GRE Mathematics" deck, so this test runs against a collection that
// has been seeded with manifold/content/import_seed.py (the same seed the align
// live-render uses). On a fresh seed nothing is due and only the root topic,
// elementary_algebra, is unlocked, so that is all the session serves.

import { expect, test } from "./fixtures";

test("manifold session serves the unlocked root and advances on every answer", async ({ page }) => {
    await page.goto("/manifold-session");

    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The problem is the placeholder wrapper: a labelled prompt, the tier and
    // level context, and six controls. No fabricated stem or choice content.
    await expect(page.locator(".mf-prompt")).toContainText("A problem about");
    await expect(page.locator(".mf-skill")).not.toBeEmpty();
    await expect(page.locator(".mf-level")).not.toBeEmpty();
    await expect(page.locator(".mf-choice")).toHaveCount(5);
    await expect(page.locator(".mf-dontknow")).toHaveCount(1);

    // Prerequisite gating: only the unlocked root contributes, so the first card
    // sits under elementary_algebra and not a locked downstream topic. The card
    // carries its topic as a data attribute (the copy no longer names it).
    await expect(page.locator(".mf-card")).toHaveAttribute(
        "data-topic",
        "elementary_algebra",
    );

    // Answering A (the correct choice) reschedules the card and advances to a
    // different unlocked skill.
    const firstSkill = await page.locator(".mf-skill").innerText();
    await page.getByRole("button", { name: "Answer A" }).click();
    await expect(page.locator(".mf-skill")).toBeVisible();
    await expect(page.locator(".mf-skill")).not.toHaveText(firstSkill);
    await expect(page.locator(".mf-card")).toHaveAttribute(
        "data-topic",
        "elementary_algebra",
    );

    // Answering "Don't know" (a miss) also advances to a new card.
    const secondSkill = await page.locator(".mf-skill").innerText();
    await page.getByRole("button", { name: "Don't know" }).click();
    await expect(page.locator(".mf-skill")).toBeVisible();
    await expect(page.locator(".mf-skill")).not.toHaveText(secondSkill);

    await page.screenshot({ path: "out/manifold-render/manifold-session.png", fullPage: true });
});

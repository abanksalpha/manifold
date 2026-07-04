// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

// The study session generates every problem ON THE FLY per review (D44): the page
// asks the whitelisted `manifoldNextProblem` endpoint, which generates a candidate
// live and serves it only once verify.py has proven it (verification stays in the
// loop; no fabrication, no persisted bank). There is no item_bank.json on the
// runtime path any more.
//
// For a deterministic, offline, free run, the isolated runner points
// MANIFOLD_LIVE_FIXTURES at live_fixtures.e2e.json: a test double that replaces
// ONLY the model call, so verify.py still runs and every served item is really
// verified. The default fixture draft serves a verified problem for any skill, so
// the first step is a real graded problem; a reserved skill id maps to a
// deliberately-unverifiable draft so the honest abstain path can be asserted
// directly against the endpoint.

import { expect, test } from "./fixtures";

test("manifold session generates, verifies, serves and grades a problem live", async ({ page }) => {
    await page.goto("/manifold-session");

    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The placeholder era is over: no generic "A problem about <skill>" wrapper.
    await expect(page.getByText("A problem about")).toHaveCount(0);

    // The first step is generated live. It shows the honest "generating" state and
    // then a real, verified problem (the fixture default verifies through verify.py).
    const problem = page.locator(".mf-card:not(.mf-abstain):not(.mf-generating)");
    await expect(problem).toBeVisible({ timeout: 30000 });

    await expect(page.locator("#mf-stem")).not.toBeEmpty();
    await expect(page.locator(".mf-choice")).toHaveCount(5);

    // The queue-position chrome ("Skill 3 of 98") was removed: it never appears.
    await expect(page.getByText(/Skill \d+ of \d+/)).toHaveCount(0);
    // The scaffolding-level description and its hover tooltip were removed: only the
    // bare level badge remains, with no descriptive prose or title beside it.
    await expect(page.locator(".mf-prequestion")).toHaveCount(0);

    await page.getByRole("button", { name: "Answer A" }).click();

    // Exactly one choice is marked correct, the item's verified correct_index,
    // proving grading is objective and not "A is always right".
    await expect(page.locator(".mf-choice.is-correct")).toHaveCount(1);
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await expect(page.locator(".mf-feedback")).toContainText(/solution/i);
    await expect(page.getByRole("button", { name: "Continue" })).toBeVisible();

    await page.screenshot({ path: "out/manifold-render/manifold-session.png", fullPage: true });

    // The abstain path is honest and never fabricates: a skill whose live draft
    // fails verification (the reserved fixture) yields an explicit ABSTAIN, with
    // verify.py still in the loop, not an unverified item. Assert it directly
    // against the endpoint so the outcome is deterministic.
    const abstain = await page.request.post("/_anki/manifoldNextProblem", {
        headers: { "Content-Type": "application/binary" },
        data: JSON.stringify({
            skill_id: "mf_e2e_force_abstain",
            skill_name: "Reserved abstain probe",
            topic_id: "elementary_algebra",
            tier: "relearn",
        }),
    });
    expect(abstain.ok()).toBe(true);
    const verdict = JSON.parse(await abstain.text());
    expect(verdict.status).toBe("abstain");
    // It was rejected by the verifier (in the loop), not silently dropped.
    expect(verdict.reason).toBe("unverified_after_retries");
});

test("the answered problem persists across a dashboard round-trip, then grading resumes", async ({ page }) => {
    await page.goto("/manifold-session");

    const problem = page.locator(".mf-card:not(.mf-abstain):not(.mf-generating)");
    await expect(problem).toBeVisible({ timeout: 30000 });

    // Capture the exact problem the learner is on, then answer it so we are in the
    // revealed state with the worked solution and Continue shown.
    const stem = ((await page.locator("#mf-stem").textContent()) ?? "").trim();
    expect(stem.length).toBeGreaterThan(0);
    await page.getByRole("button", { name: "Answer A" }).click();
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await expect(page.getByRole("button", { name: "Continue" })).toBeVisible();
    // The grade write landed (no honest failure banner), proving gradeNow ran.
    await expect(page.locator(".mf-error")).toHaveCount(0);

    // Leave for the dashboard, then come back to the session.
    await page.getByRole("link", { name: "Back to the dashboard" }).click();
    await expect(page.locator(".mf-wordmark")).toBeVisible();
    await page.goto("/manifold-session");

    // The REVEALED state is restored: the same stem, still showing the worked
    // solution and Continue — not a fresh asking-phase card. A restart-from-the-top
    // would have discarded the answer and shown a new asking problem, so this
    // distinguishes a true resume from a regeneration (issue: the problem should
    // persist when you return to the dashboard and go back).
    const restored = page.locator(".mf-card:not(.mf-abstain):not(.mf-generating)");
    await expect(restored).toBeVisible({ timeout: 30000 });
    await expect(page.locator("#mf-stem")).toHaveText(stem);
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await expect(page.getByRole("button", { name: "Continue" })).toBeVisible();

    // Continue to the NEXT problem, drawn from the restored queue whose card ids were
    // revived from the bigint-tagged snapshot, and grade it: the write must land,
    // proving the card id round-tripped through JSON and back into gradeNow.
    await page.getByRole("button", { name: "Continue" }).click();
    const next = page.locator(".mf-card:not(.mf-abstain):not(.mf-generating)");
    await expect(next).toBeVisible({ timeout: 30000 });
    await page.getByRole("button", { name: "Answer A" }).click();
    await expect(page.locator(".mf-feedback")).toBeVisible();
    await expect(page.locator(".mf-error")).toHaveCount(0);
});

test("manifold serves a pre-authored New-skill lecture, grounded in a verified item", async ({ page }) => {
    await page.goto("/manifold-session");
    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The New-skill lecture (Task 1) is served from a pre-authored, static file via
    // the whitelisted manifoldLecture endpoint — never generated live. POST it for a
    // seeded teach skill and confirm it returns a real lecture: a title plus a body
    // whose mathematics is delimited LaTeX (the Task 2 convention MathText typesets),
    // anchored to a VERIFIED teach_bank item so it teaches proven content, not a fake.
    const lecture = await page.request.post("/_anki/manifoldLecture", {
        headers: { "Content-Type": "application/binary" },
        data: JSON.stringify({
            skill_id: "implicit_differentiation_for_a_partial_derivative",
            topic_id: "multivariable_diff",
            tier: "teach",
        }),
    });
    expect(lecture.ok()).toBe(true);
    const lectureVerdict = JSON.parse(await lecture.text());
    expect(lectureVerdict.status).toBe("ok");
    expect(lectureVerdict.lecture.title).toContain("Implicit differentiation");
    expect(lectureVerdict.lecture.lecture_latex).toContain("\\(");
    expect(lectureVerdict.lecture.lecture_latex).toContain("\\frac{\\partial z}{\\partial x}");
    expect(lectureVerdict.lecture.anchored_item_id).toBe("mfteach_95baa092e4252c15");

    // A teach skill with no authored lecture is an honest "none", never a faked one.
    const none = await page.request.post("/_anki/manifoldLecture", {
        headers: { "Content-Type": "application/binary" },
        data: JSON.stringify({ skill_id: "mf_no_such_lecture", tier: "teach" }),
    });
    expect(none.ok()).toBe(true);
    expect(JSON.parse(await none.text()).status).toBe("none");
});

test("manifold hint assistant answers a question without revealing the answer", async ({ page }) => {
    await page.goto("/manifold-session");
    await expect(page.locator(".mf-wordmark")).toHaveText("Manifold");

    // The hint endpoint is a live model path; the isolated runner injects a fixtures
    // double (MANIFOLD_HINT_FIXTURES) that replaces ONLY the model call, so this is
    // deterministic. Assert it against the endpoint directly first: a real, typeset
    // (delimited-LaTeX) hint comes back for the problem context the page posts.
    const hint = await page.request.post("/_anki/manifoldHint", {
        headers: { "Content-Type": "application/binary" },
        data: JSON.stringify({
            skill_id: "dice_sum",
            skill_name: "Dice sum probability",
            topic_title: "Probability",
            stem: "Two fair dice are rolled. What is P(sum = 5)?",
            choices: ["1/9", "1/12", "1/6", "2/9", "5/36"],
            question: "Where should I start?",
            history: [],
        }),
    });
    expect(hint.ok()).toBe(true);
    const hintVerdict = JSON.parse(await hint.text());
    expect(hintVerdict.status).toBe("ok");
    expect(hintVerdict.hint).toContain("\\(");

    // Now drive it through the UI on a live problem. The hint assistant is offered on
    // New / Guided / Revisit, but never on a cold Independent problem, so the toggle's
    // presence must match the served level.
    const problem = page.locator(".mf-card:not(.mf-abstain):not(.mf-generating)");
    await expect(problem).toBeVisible({ timeout: 30000 });

    const level = ((await page.locator(".mf-level").first().textContent()) ?? "").trim();
    const toggle = page.getByRole("button", { name: "Ask for a hint" });

    if (level === "Independent") {
        // Solved cold, with no hints: the affordance is absent entirely.
        await expect(toggle).toHaveCount(0);
        return;
    }

    // The panel is collapsed by default (it never nudges the learner to lean on it),
    // so open it, ask, and read the typeset hint back.
    await toggle.click();
    const input = page.getByRole("textbox", { name: "Ask a question about this problem" });
    await expect(input).toBeVisible();
    // The question contains the letters A-E on purpose: typing it must NOT trigger the
    // player's A-E answer shortcuts (the field guard), so no answer is graded.
    await input.fill("Can you explain where to begin, and any edge cases?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();

    await expect(page.locator(".mf-hint-answer-text")).toContainText(
        "Translate the given information",
        { timeout: 30000 },
    );

    // The hint did NOT reveal the outcome: the problem is still in the asking phase
    // (no feedback panel), and typing the question never answered it for the learner.
    await expect(page.locator(".mf-feedback")).toHaveCount(0);
    await expect(page.locator(".mf-choice")).toHaveCount(5);
});

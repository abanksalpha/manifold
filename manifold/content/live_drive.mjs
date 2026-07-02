// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

// Live end-to-end driver for the REAL Manifold app.
//
// Points a Playwright Chromium at the mediasrv of an already-running `./run`
// instance (a real, freshly-seeded desktop app, launched by live_drive.py) and
// asserts every Manifold feature end to end, capturing a screenshot of each
// surface. Every /_anki/* response is recorded so the run can prove that every
// backend RPC (getTopicGraph / buildSessionQueue / gradeNow) returned 2xx, and
// any uncaught page exception or 4xx/5xx RPC is a hard failure.
//
// Env:
//   MF_BASE_URL  base URL of the running app's mediasrv (e.g. http://127.0.0.1:PORT)
//   MF_SHOT_DIR  directory to write screenshots into
//   MF_CDP       (optional) QtWebEngine remote-debugging URL, to also screenshot
//                the *actual* Qt web view and confirm its booted URL.

import fs from "node:fs";
import path from "node:path";

import { chromium } from "playwright";

const BASE = process.env.MF_BASE_URL;
const SHOTS = process.env.MF_SHOT_DIR ?? "out/manifold-live/shots";
const CDP = process.env.MF_CDP ?? "";

if (!BASE) {
    console.error("MF_BASE_URL is required");
    process.exit(2);
}
fs.mkdirSync(SHOTS, { recursive: true });

const results = [];
function check(name, ok, detail = "") {
    results.push({ name, ok: !!ok, detail });
    console.log(`${ok ? "ok  " : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
}

const rpc = [];
const consoleErrors = [];
const pageErrors = [];

function wire(page) {
    page.on("response", (r) => {
        try {
            const u = new URL(r.url());
            if (u.pathname.startsWith("/_anki/")) {
                rpc.push({ method: r.request().method(), path: u.pathname, status: r.status() });
            }
        } catch {
            /* ignore non-URL responses */
        }
    });
    page.on("pageerror", (e) => {
        pageErrors.push(String(e));
        console.error("PAGEERROR:", String(e));
    });
    page.on("console", (m) => {
        if (m.type() === "error") {
            consoleErrors.push(m.text());
            console.error("CONSOLE.ERROR:", m.text());
        }
    });
}

const shot = (page, name) => page.screenshot({ path: path.join(SHOTS, name), fullPage: true });

async function driveHome(page) {
    console.log("\n--- (b) Home /manifold ---");
    await page.goto(`${BASE}/manifold`, { waitUntil: "networkidle" });
    check("home.wordmark", (await page.locator(".mf-wordmark").textContent())?.trim() === "Manifold");
    const labels = await page.locator(".metric-label").allTextContents();
    check("home.memory.metric", labels.includes("Memory"));
    check("home.performance.metric", labels.includes("Performance"));
    // getTopicGraph succeeded iff the scores rendered (the loader throws otherwise).
    check("home.readiness.abstaining", (await page.locator(".mf-chip").first().textContent())?.trim() === "Abstaining");
    check("home.evidence.rule", (await page.locator(".mf-r-rule-label").textContent())?.trim() === "Evidence rule");
    check("home.performance.abstains", (await page.getByText("not yet measured").count()) > 0);
    check("home.start.href", (await page.locator(".mf-start").getAttribute("href")) === "/manifold-session");
    check(
        "home.dashboard.link",
        (await page.locator(".mf-link", { hasText: "Open readiness dashboard" }).getAttribute("href"))
            === "/manifold-dashboard",
    );
    await shot(page, "live-home.png");
}

async function driveDashboard(page) {
    console.log("\n--- (c) Dashboard /manifold-dashboard ---");
    await page.goto(`${BASE}/manifold-dashboard`, { waitUntil: "networkidle" });
    check("dash.nodes.33", (await page.locator(".mf-node").count()) === 33);
    check("dash.readiness.abstaining", (await page.locator(".mf-rc-state").textContent())?.trim() === "Abstaining");
    check("dash.legend.inprogress", (await page.locator(".mf-legend-label", { hasText: "In progress" }).count()) > 0);
    const initial = (await page.locator(".mf-panel-title").textContent())?.trim() ?? "";
    check("dash.panel.selectedOnLoad", initial.length > 0, `panel=${initial}`);
    await page.locator(".mf-node[data-topic='linear_algebra_core']").click();
    await page.waitForFunction(
        () => document.querySelector(".mf-panel-title")?.textContent?.trim() === "Linear algebra: matrices & systems",
        undefined,
        { timeout: 5000 },
    );
    check(
        "dash.select.updatesPanel",
        (await page.locator(".mf-panel-title").textContent())?.trim() === "Linear algebra: matrices & systems",
    );
    await shot(page, "live-dashboard.png");
}

async function driveSession(page) {
    console.log("\n--- (d) Session /manifold-session ---");
    await page.goto(`${BASE}/manifold-session`, { waitUntil: "networkidle" });
    await page.waitForSelector(".mf-prompt", { timeout: 10000 });
    check("sess.prompt", (await page.locator(".mf-prompt").textContent())?.includes("A problem about"));
    check("sess.skill.nonempty", ((await page.locator(".mf-skill").textContent())?.trim().length ?? 0) > 0);
    check("sess.context.level", ((await page.locator(".mf-level").textContent()) ?? "").trim().length > 0);
    check("sess.choices.5", (await page.locator(".mf-choice").count()) === 5);
    check("sess.dontknow.1", (await page.locator(".mf-dontknow").count()) === 1);
    await shot(page, "live-session.png");

    let allEA = true;
    let graded = 0;
    let aAdvanced = false;
    let dkAdvanced = false;
    for (let i = 0; i < 50; i++) {
        if ((await page.locator(".mf-complete-title").count()) > 0) {
            break;
        }
        // The card copy no longer names the topic; read it off the data attribute.
        const cardTopic = await page.locator(".mf-card").getAttribute("data-topic");
        if (cardTopic !== "elementary_algebra") {
            allEA = false;
        }
        const skill = (await page.locator(".mf-skill").textContent())?.trim() ?? "";
        const label = i === 1 ? "Don't know" : "Answer A"; // exercise A and Don't know
        await page.getByRole("button", { name: label }).click();
        graded += 1;
        await page.waitForFunction(
            (prev) => {
                if (document.querySelector(".mf-complete-title")) {
                    return true;
                }
                const s = document.querySelector(".mf-skill");
                return s && s.textContent.trim() !== prev;
            },
            skill,
            { timeout: 10000 },
        );
        const advanced = (await page.locator(".mf-complete-title").count()) > 0
            || (await page.locator(".mf-skill").textContent())?.trim() !== skill;
        if (i === 0) {
            aAdvanced = advanced;
        }
        if (i === 1) {
            dkAdvanced = advanced;
        }
    }
    check("sess.gating.onlyElementaryAlgebra", allEA, `cards graded=${graded}`);
    check("sess.answerA.advances", aAdvanced);
    check("sess.dontknow.advances", dkAdvanced);
    check("sess.complete.shown", (await page.locator(".mf-complete-title").count()) > 0);
    check(
        "sess.complete.title",
        (await page.locator(".mf-complete-title").textContent())?.trim() === "Session complete",
    );
    const backHref = await page.locator(".mf-complete .mf-link").getAttribute("href");
    check("sess.back.href", backHref === "/manifold");
    await shot(page, "live-session-complete.png");
    await page.locator(".mf-complete .mf-link").click();
    await page.waitForSelector(".mf-start", { timeout: 10000 });
    check("sess.back.linkWorks", (await page.locator(".mf-wordmark").textContent())?.trim() === "Manifold");
    return graded;
}

async function driveReflected(page, graded) {
    console.log("\n--- (e) Reflected numbers after grading ---");
    await page.goto(`${BASE}/manifold-dashboard`, { waitUntil: "networkidle" });
    await page.locator(".mf-node[data-topic='elementary_algebra']").click();
    await page.waitForFunction(
        () => document.querySelector(".mf-panel-title")?.textContent?.trim() === "Elementary algebra",
        undefined,
        { timeout: 5000 },
    );
    const gradedText = await page
        .locator(".mf-stat", { hasText: "Graded reviews" })
        .locator(".mf-stat-val")
        .textContent();
    const gradedNum = parseInt((gradedText ?? "0").trim(), 10);
    check("reflect.gradedReviews>0", gradedNum > 0, `dashboard shows ${gradedNum} graded reviews (drove ${graded})`);
    // Home now measures Performance (previously "not yet measured").
    await page.goto(`${BASE}/manifold`, { waitUntil: "networkidle" });
    await shot(page, "live-reflected.png");
}

async function grabRealWebview() {
    if (!CDP) {
        return;
    }
    console.log("\n--- (a bonus) Screenshot of the real Qt web view over CDP ---");
    try {
        const b = await chromium.connectOverCDP(CDP);
        let real = null;
        for (const c of b.contexts()) {
            for (const p of c.pages()) {
                if (p.url().endsWith("/manifold")) {
                    real = p;
                }
            }
        }
        if (real) {
            check("realapp.webview.bootedIntoManifold", true, real.url());
            await real.screenshot({ path: path.join(SHOTS, "live-realapp-webview.png") });
        } else {
            check("realapp.webview.bootedIntoManifold", false, "no /manifold page found over CDP");
        }
        await b.close();
    } catch (e) {
        // Non-fatal: the orchestrator independently proves boot via /json.
        console.error("CDP screenshot skipped (non-fatal):", e.message);
    }
}

function summarise() {
    console.log("\n=== /_anki RPC responses ===");
    const agg = {};
    for (const r of rpc) {
        const k = `${r.method} ${r.path}`;
        agg[k] = agg[k] ?? { n: 0, bad: 0, statuses: new Set() };
        agg[k].n += 1;
        agg[k].statuses.add(r.status);
        if (r.status < 200 || r.status >= 400) {
            agg[k].bad += 1;
        }
    }
    for (const [k, v] of Object.entries(agg)) {
        console.log(`  ${k}  x${v.n}  statuses={${[...v.statuses].join(",")}}${v.bad ? "  BAD=" + v.bad : ""}`);
    }
    const anyBadRpc = rpc.some((r) => r.status < 200 || r.status >= 400);
    check("rpc.getTopicGraph.served", rpc.some((r) => r.path === "/_anki/getTopicGraph"));
    check("rpc.buildSessionQueue.served", rpc.some((r) => r.path === "/_anki/buildSessionQueue"));
    check("rpc.gradeNow.served", rpc.some((r) => r.path === "/_anki/gradeNow"));
    check("rpc.all2xx", !anyBadRpc);
    check("no.pageerrors", pageErrors.length === 0, `${pageErrors.length} page error(s)`);
    check("no.consoleErrors", consoleErrors.length === 0, `${consoleErrors.length} console error(s)`);
}

const browser = await chromium.launch({ headless: true });
try {
    const context = await browser.newContext({ baseURL: BASE });
    const page = await context.newPage();
    wire(page);
    await driveHome(page);
    await driveDashboard(page);
    const graded = await driveSession(page);
    await driveReflected(page, graded);
    await grabRealWebview();
    summarise();
} finally {
    await browser.close();
}

const failed = results.filter((r) => !r.ok);
console.log("\n=== live-drive summary ===");
console.log(`  checks: ${results.length}, passed: ${results.length - failed.length}, failed: ${failed.length}`);
if (failed.length) {
    console.log("  FAILED CHECKS:");
    for (const f of failed) {
        console.log(`   - ${f.name} ${f.detail}`);
    }
    process.exit(1);
}
console.log("  ALL LIVE-DRIVE CHECKS PASSED");
process.exit(0);

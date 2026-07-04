// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * The progress-mirror push pipeline: read the engine's topic graph, derive the
 * three scores, and write the compact snapshot to Firestore for the signed-in
 * user, so every other device sees the update in real time.
 *
 * This is the one place that stitches the read-only engine RPC to the Firestore
 * mirror, so both the dashboard (on load) and the session player (after each
 * graded answer) push through it. It is deliberately additive and read-only with
 * respect to the collection: it only READS `getTopicGraph`, exactly like the
 * dashboard, and never writes scheduling state.
 *
 * A tiny in-flight guard + minimum interval keep per-answer pushes from piling up
 * during fast study, without hiding failures: an attempted push that fails still
 * rejects with the real error for the caller to surface (no silent fallback).
 */

import { getTopicGraph } from "@generated/backend";

import { currentManifoldUser, writeProgress } from "./firebase";
import { buildProgressData } from "./progress";
import { computeScores, type TopicStat } from "./scoring";

/** The outcome of a push attempt, so callers can distinguish "synced" from
 * "nothing to sync (signed out)" from "coalesced with a recent push". */
export type PushResult = "pushed" | "signed-out" | "throttled";

let inFlight = false;
let lastPushMs = 0;

/** Minimum spacing between pushes when not forced, so a burst of quick answers
 * coalesces into at most one write every ~1.5s instead of one per keystroke. */
export const MIN_PUSH_INTERVAL_MS = 1500;

/**
 * Derive and upload the current progress snapshot for the signed-in user.
 *
 * Returns "signed-out" when nobody is signed in (there is simply nothing to
 * mirror — not a masked error), "throttled" when a push happened very recently
 * (unless `force` is set), and "pushed" once the write lands. Any real failure
 * (engine RPC, scoring, or Firestore rules) rejects with the underlying error.
 */
export async function pushProgressSnapshot(
    opts: { force?: boolean } = {},
): Promise<PushResult> {
    if (!currentManifoldUser()) {
        return "signed-out";
    }
    const now = Date.now();
    if (!opts.force && (inFlight || now - lastPushMs < MIN_PUSH_INTERVAL_MS)) {
        return "throttled";
    }
    inFlight = true;
    try {
        const graph = await getTopicGraph({});
        if (!graph.scoringConfig) {
            throw new Error("getTopicGraph returned no scoring config");
        }
        const nodes = graph.nodes as unknown as TopicStat[];
        const report = computeScores(nodes, graph.scoringConfig);
        await writeProgress(buildProgressData(report, nodes));
        lastPushMs = Date.now();
        return "pushed";
    } finally {
        inFlight = false;
    }
}

// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * The derived progress snapshot Manifold mirrors to Firestore for cross-device
 * sync.
 *
 * Manifold keeps the Anki collection (cards + revlog) as the scheduling source of
 * truth, synced by Anki's own protocol. Firestore carries ONLY this small,
 * derived read-model — the three honest scores + per-topic mastery — so a
 * signed-in learner sees the same live progress on every device (a second desktop,
 * the phone, or the web dashboard). It is a mirror, never the schedule: nothing
 * here feeds back into FSRS.
 *
 * This module is pure data shaping (no Firebase imports), so it is unit-testable
 * and the exact object it produces is what the Firestore security rules validate.
 * The transport fields (uid, updatedAt, platform, deviceId, appVersion) are added
 * by `firebase.ts::writeProgress`; everything derived from the scores is here.
 */

import type { ScoreReport, TopicStat } from "./scoring";

/** A three-number metric estimate, always present as a map so the security rules
 * can type it (present=false when there is no evidence yet, instead of a null). */
export interface MetricMirror {
    present: boolean;
    value: number;
    low: number;
    high: number;
}

/** One per-topic mastery entry, the subset the dashboard renders on any device. */
export interface TopicMirror {
    id: string;
    title: string;
    area: string;
    tier: string;
    lockState: string;
    avgRecall: number;
    performance: number;
    coverage: number;
}

/**
 * The compact readiness read-model. Readiness is never a bare number (D11/D12):
 * `projected` carries the ETS-anchored scaled range + confidence; `abstaining`
 * carries the evidence still owed. Kept to a handful of scalar keys so the rules
 * can bound it.
 */
export type ReadinessMirror =
    | {
        state: "projected";
        scaledPoint: number;
        scaledLow: number;
        scaledHigh: number;
        confidence: string;
        lapseRate: number;
    }
    | {
        state: "abstaining";
        reviewsNeeded: number;
        coverageNeeded: number;
    };

/** The derived payload (everything computed from the scores). Transport fields
 * are added at write time. */
export interface ProgressData {
    coverage: number;
    totalIndependentReviews: number;
    readinessState: "projected" | "abstaining";
    memory: MetricMirror;
    performance: MetricMirror;
    readiness: ReadinessMirror;
    topics: TopicMirror[];
}

/** The maximum topics mirrored, matching the security-rules list cap. The
 * blueprint has ~33 topics, so this is headroom, not a truncation in practice. */
export const MAX_MIRRORED_TOPICS = 64;

function metricMirror(
    metric: { value: number; low: number; high: number } | null,
): MetricMirror {
    if (!metric) {
        return { present: false, value: 0, low: 0, high: 0 };
    }
    return { present: true, value: metric.value, low: metric.low, high: metric.high };
}

function readinessMirror(report: ScoreReport): ReadinessMirror {
    const r = report.readiness;
    if (r.state === "projected") {
        return {
            state: "projected",
            scaledPoint: r.scaledPoint,
            scaledLow: r.scaledLow,
            scaledHigh: r.scaledHigh,
            confidence: r.confidence,
            lapseRate: r.lapseRate,
        };
    }
    return {
        state: "abstaining",
        reviewsNeeded: r.reviewsNeeded,
        coverageNeeded: r.coverageNeeded,
    };
}

/**
 * Build the derived progress payload from the already-computed scores and the
 * topic graph. Deterministic and side-effect free; the object it returns matches
 * the Firestore document schema (minus the transport fields added on write).
 */
export function buildProgressData(report: ScoreReport, nodes: TopicStat[]): ProgressData {
    const topics: TopicMirror[] = nodes.slice(0, MAX_MIRRORED_TOPICS).map((node) => ({
        id: node.id,
        title: node.title,
        area: node.area,
        tier: node.tier,
        lockState: node.lockState,
        avgRecall: node.avgRecall,
        performance: node.performance,
        coverage: node.coverage,
    }));
    return {
        coverage: report.coverage,
        totalIndependentReviews: report.totalIndependentReviews,
        readinessState: report.readiness.state,
        memory: metricMirror(report.memory),
        performance: metricMirror(report.performance),
        readiness: readinessMirror(report),
        topics,
    };
}

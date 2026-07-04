// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Manifold's three honest scores, derived from the topic graph.
 *
 * Manifold reports Memory, Performance and Readiness separately, never blended
 * into one number. Readiness refuses to answer until it has enough evidence (the
 * "give-up rule"), and the evidence it counts is *unsupported* performance only:
 * attempts made cold, once a card has graduated to the Independent level (revlog
 * Review-kind), never scaffolded Learning/Relearning taps (D20/D21). Above the
 * line it maps that evidence to an ETS-anchored scaled range (D13/D19); it never
 * emits a bare number. This module computes; it never invents.
 */

/**
 * The per-topic shape this module reads: the structural subset of the
 * `getTopicGraph` proto node (camelCase) that the scores depend on. Recall,
 * performance and coverage are fractions in [0, 1]. `performance` is accuracy on
 * unsupported (Independent) attempts only; `independentReviews` is their count.
 */
export interface TopicStat {
    id: string;
    title: string;
    area: string;
    tier: string;
    weight: number;
    lockState: string;
    total: number;
    avgRecall: number;
    performance: number;
    coverage: number;
    gradedReviews: number;
    independentReviews: number;
    // Card counts by teaching level, read only for the lapse-rate signal below:
    // Independent = graduated cold-capable, Revisited = lapsed and relearning.
    // Their ratio proxies how fragile the graduated knowledge is (D26).
    levelIndependent: number;
    levelRevisited: number;
}

/** One rung of the target ladder: a named goal and the scaled band that defines
 * it (D29/D30), sourced from the blueprint. */
export interface ReadinessTargetConfig {
    id: string;
    label: string;
    scaledPoint: number;
    scaledLow: number;
    scaledHigh: number;
}

/** Logarithmic hours-to-target curve constants (D29), sourced from the
 * blueprint. `scaled(hours) = scaledFloor + pointsPerLogHour · ln(1 + hours /
 * hoursScale)`; chosen and tunable, not a cited hour count. */
export interface HoursCurveConfig {
    scaledFloor: number;
    pointsPerLogHour: number;
    hoursScale: number;
}

/** The maturity-residue the app does not promise (D29/D30), sourced from the
 * blueprint: the deep-proof items and the scaled points at the top it withholds. */
export interface MaturityResidueConfig {
    items: number;
    scaledPoints: number;
}

/**
 * The static readiness-scale reference data, sourced from the blueprint and
 * delivered over the topic-graph RPC (camelCase). Kept as the single source of
 * truth in `blueprint.json` rather than duplicated here. Singular sub-messages
 * (`hoursCurve`, `maturityResidue`) are optional on the wire (proto3), so they
 * are validated at the point of use and never silently defaulted.
 */
export interface ScoringConfig {
    scaleMin: number;
    scaleMax: number;
    distributionMean: number;
    distributionSd: number;
    etsAnchors: { scaled: number; percentileBelow: number }[];
    medianRawFraction: number;
    performanceSd: number;
    coverageBandLambda: number;
    lapseBandLambda: number;
    targets: ReadinessTargetConfig[];
    hoursCurve?: HoursCurveConfig;
    maturityResidue?: MaturityResidueConfig;
}

/**
 * The give-up rule (PRD D12, refined by D20). Readiness emits no estimate until
 * BOTH conditions hold, counting only unsupported (Independent) attempts.
 */
// Independent (Review-kind) attempts, summed across topics, before Readiness speaks.
export const READINESS_MIN_INDEPENDENT_REVIEWS = 200;
// Blueprint coverage, as a weighted fraction in [0, 1], before Readiness speaks.
export const READINESS_MIN_COVERAGE = 0.5;
// Above these, confidence rises from "provisional" to "confident" (spec §10).
export const READINESS_CONFIDENT_INDEPENDENT_REVIEWS = 600;
export const READINESS_CONFIDENT_COVERAGE = 0.8;

/**
 * A weighted-mean score with the spread it was drawn from. `value` is the
 * blueprint-weight-weighted mean; `low`/`high` are the observed minimum and
 * maximum across the topics that contributed, so the honest range is visible
 * rather than hidden behind the point estimate.
 */
export interface MetricEstimate {
    value: number;
    low: number;
    high: number;
    contributingTopics: number;
    totalTopics: number;
}

/** The best topic to study next when Readiness is abstaining. */
export interface StudyNext {
    id: string;
    title: string;
    area: string;
    tier: string;
    weight: number;
    avgRecall: number;
    /** weight * (1 - avgRecall): blueprint points left on the table here. */
    priority: number;
}

/** A topic dragging the readiness estimate down: weak, and heavily weighted. */
export interface ReadinessDriver {
    id: string;
    title: string;
    weight: number;
    performance: number;
    /** weight * (1 - performance): blueprint points at risk from this topic. */
    priority: number;
}

/** A target ladder rung with the current standing against it (D29/D30). */
export interface TargetProjection {
    id: string;
    label: string;
    scaledPoint: number;
    scaledLow: number;
    scaledHigh: number;
    /** Scaled points from the current point estimate up to this target; 0 once met. */
    gapPoints: number;
    /** Estimated study hours to close the gap on the logarithmic curve; 0 once met. */
    hoursToTarget: number;
    /** True once the current point estimate is at or above the target point. */
    reached: boolean;
}

/** The explicit ceiling the app refuses to promise past (D29/D30). */
export interface MaturityResidue {
    /** Deep-proof items the app cannot drill (~2–3). */
    items: number;
    /** Scaled points at the top the app does not promise (~30–40). */
    scaledPoints: number;
    /** The highest scaled score the app will ever project: scaleMax − residue. */
    promisedCeiling: number;
}

/**
 * Readiness is a refusal or an honest projected range, never a bare scalar. Both
 * states carry `lastUpdated` so the reading is always stamped. `abstaining`:
 * below the give-up line, with the missing evidence and a nudge. `projected`:
 * above the line, mapped to an ETS-anchored scaled range (D13/D19) and carrying
 * the seven honest fields — point, range, %covered, confidence, last-updated,
 * drivers, and the give-up state itself — plus the target ladder, the fragility
 * (lapse) that widened its band (D26), and the residue ceiling it will not
 * promise past (D29).
 */
export type Readiness =
    | {
        state: "abstaining";
        independentReviews: number;
        reviewsNeeded: number;
        coverage: number;
        coverageNeeded: number;
        studyNext: StudyNext | null;
        /** Epoch millis the scores were derived (the "last updated" field). */
        lastUpdated: number;
    }
    | {
        state: "projected";
        scaledPoint: number;
        scaledLow: number;
        scaledHigh: number;
        coverage: number;
        independentReviews: number;
        confidence: "provisional" | "confident";
        drivers: ReadinessDriver[];
        /** Epoch millis the scores were derived (the "last updated" field). */
        lastUpdated: number;
        /** The honest target ladder with hours-to-target and gap per rung. */
        targets: TargetProjection[];
        /** Aggregate lapse rate that widened the band; 0 when nothing has lapsed. */
        lapseRate: number;
        /** The maturity residue the app does not promise past (D29/D30). */
        residue: MaturityResidue;
    };

export interface ScoreReport {
    /** Weighted-mean FSRS recall over topics with at least one authored skill. */
    memory: MetricEstimate | null;
    /** Weighted-mean unsupported accuracy over topics with independent reviews. */
    performance: MetricEstimate | null;
    /** Blueprint-weighted coverage of the exam, in [0, 1]. */
    coverage: number;
    /** Independent (Review-kind) attempts summed across topics. */
    totalIndependentReviews: number;
    gate: {
        met: boolean;
        minIndependentReviews: number;
        minCoverage: number;
    };
    readiness: Readiness;
}

function weightedMean(
    nodes: TopicStat[],
    value: (node: TopicStat) => number,
    include: (node: TopicStat) => boolean,
): MetricEstimate | null {
    let weightSum = 0;
    let weightedValueSum = 0;
    let low = Infinity;
    let high = -Infinity;
    let contributingTopics = 0;

    for (const node of nodes) {
        if (!include(node)) {
            continue;
        }
        const v = value(node);
        weightSum += node.weight;
        weightedValueSum += node.weight * v;
        low = Math.min(low, v);
        high = Math.max(high, v);
        contributingTopics += 1;
    }

    if (contributingTopics === 0 || weightSum === 0) {
        return null;
    }

    return {
        value: weightedValueSum / weightSum,
        low,
        high,
        contributingTopics,
        totalTopics: nodes.length,
    };
}

function coverageScore(nodes: TopicStat[]): number {
    let weightSum = 0;
    let weightedCoverageSum = 0;
    for (const node of nodes) {
        weightSum += node.weight;
        weightedCoverageSum += node.weight * node.coverage;
    }
    if (weightSum === 0) {
        throw new Error("topic graph has zero total blueprint weight");
    }
    return weightedCoverageSum / weightSum;
}

/**
 * The single best topic to study next: among topics the learner can study now
 * (unlocked or in progress), the one with the most blueprint points at risk,
 * weight * (1 - avgRecall). Returns null when nothing is open to study.
 */
export function selectStudyNext(nodes: TopicStat[]): StudyNext | null {
    let best: StudyNext | null = null;
    for (const node of nodes) {
        if (node.lockState !== "unlocked" && node.lockState !== "in_progress") {
            continue;
        }
        const priority = node.weight * (1 - node.avgRecall);
        if (best === null || priority > best.priority) {
            best = {
                id: node.id,
                title: node.title,
                area: node.area,
                tier: node.tier,
                weight: node.weight,
                avgRecall: node.avgRecall,
                priority,
            };
        }
    }
    return best;
}

// --- Readiness mapping numerics (D19) --------------------------------------
// ETS never publishes raw→scaled tables, so this is an explicit approximation:
// expected performance → percentile (a chosen normal) → scaled (ETS anchors).

/** Error function, Abramowitz & Stegun 7.1.26 (max abs error ~1.5e-7). */
function erf(x: number): number {
    const sign = x < 0 ? -1 : 1;
    const ax = Math.abs(x);
    const t = 1 / (1 + 0.3275911 * ax);
    const y = 1
        - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
                + 0.254829592) * t * Math.exp(-ax * ax);
    return sign * y;
}

/** Standard normal CDF. */
function normalCdf(x: number): number {
    return 0.5 * (1 + erf(x / Math.SQRT2));
}

/** Inverse standard normal CDF (Acklam's rational approximation). */
function normalInvCdf(p: number): number {
    const clamped = Math.min(1 - 1e-12, Math.max(1e-12, p));
    const a = [
        -3.969683028665376e+01,
        2.209460984245205e+02,
        -2.759285104469687e+02,
        1.383577518672690e+02,
        -3.066479806614716e+01,
        2.506628277459239e+00,
    ];
    const b = [
        -5.447609879822406e+01,
        1.615858368580409e+02,
        -1.556989798598866e+02,
        6.680131188771972e+01,
        -1.328068155288572e+01,
    ];
    const c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e+00,
        -2.549732539343734e+00,
        4.374664141464968e+00,
        2.938163982698783e+00,
    ];
    const d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00];
    const plow = 0.02425;
    const phigh = 1 - plow;
    if (clamped < plow) {
        const q = Math.sqrt(-2 * Math.log(clamped));
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
    }
    if (clamped <= phigh) {
        const q = clamped - 0.5;
        const r = q * q;
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
            / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
    }
    const q = Math.sqrt(-2 * Math.log(1 - clamped));
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
        / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1);
}

/** Round to the nearest 10 (the real scale's granularity) and clamp to range. */
function clampToScale(scaled: number, config: ScoringConfig): number {
    const rounded = Math.round(scaled / 10) * 10;
    return Math.max(config.scaleMin, Math.min(config.scaleMax, rounded));
}

/**
 * Percentile (0..1) → scaled score. Interpolates the ETS anchor table where it
 * is dense; beyond the outermost anchors, falls back to the normal fit
 * `mean + sd·Φ⁻¹(pct)`. Monotone in `pct`.
 */
function percentileToScaled(pct: number, config: ScoringConfig): number {
    const anchors = config.etsAnchors
        .map((a) => ({ pct: a.percentileBelow / 100, scaled: a.scaled }))
        .sort((x, y) => x.pct - y.pct);
    if (anchors.length === 0) {
        return config.distributionMean + config.distributionSd * normalInvCdf(pct);
    }
    const lo = anchors[0];
    const hi = anchors[anchors.length - 1];
    if (pct <= lo.pct || pct >= hi.pct) {
        return config.distributionMean + config.distributionSd * normalInvCdf(pct);
    }
    for (let i = 0; i < anchors.length - 1; i++) {
        const left = anchors[i];
        const right = anchors[i + 1];
        if (pct >= left.pct && pct <= right.pct) {
            const span = right.pct - left.pct;
            const frac = span === 0 ? 0 : (pct - left.pct) / span;
            return left.scaled + frac * (right.scaled - left.scaled);
        }
    }
    return hi.scaled;
}

/**
 * Expected blueprint-weighted performance (0..1) → scaled score. The chosen
 * approximation (D19): treat the fraction as a normal ability with the median
 * test-taker at `medianRawFraction`, spread `performanceSd`, then read its
 * percentile onto the ETS scale.
 */
function performanceToScaled(pBar: number, config: ScoringConfig): number {
    const pct = normalCdf((pBar - config.medianRawFraction) / config.performanceSd);
    return clampToScale(percentileToScaled(pct, config), config);
}

// --- Target ladder, hours-to-target, residue ceiling (D29/D30) -------------

/**
 * The honest target ladder — median, strong, exceptional — each with its scaled
 * band, sourced from the blueprint (single source of truth). Throws on an empty
 * ladder rather than inventing goals.
 */
export function targetLadder(config: ScoringConfig): ReadinessTargetConfig[] {
    if (config.targets.length === 0) {
        throw new Error("scoring config has no readiness targets");
    }
    return config.targets;
}

/**
 * Select one target by id (`median` | `strong` | `exceptional`). Throws on an
 * unknown id rather than guessing a fallback.
 */
export function selectTarget(config: ScoringConfig, id: string): ReadinessTargetConfig {
    const found = config.targets.find((t) => t.id === id);
    if (!found) {
        throw new Error(`unknown readiness target '${id}'`);
    }
    return found;
}

/**
 * The maturity-residue ceiling: the ~2–3 deep-proof items and the ~30–40 scaled
 * points at the very top the app does NOT promise, and the highest scaled score
 * it will therefore ever project (`scaleMax − residue`). Throws if the config
 * omits it rather than promising the whole scale.
 */
export function maturityResidue(config: ScoringConfig): MaturityResidue {
    const residue = config.maturityResidue;
    if (!residue) {
        throw new Error("scoring config missing maturity residue");
    }
    return {
        items: residue.items,
        scaledPoints: residue.scaledPoints,
        promisedCeiling: config.scaleMax - residue.scaledPoints,
    };
}

/**
 * Cumulative targeted-prep hours the logarithmic curve places at a scaled score:
 * `H(s) = hoursScale · (exp((s − scaledFloor) / pointsPerLogHour) − 1)`.
 * Monotone and convex, so each further scaled point costs more hours than the
 * last — the Messick-style diminishing-returns / top-percentile tax.
 */
function curveHoursAt(scaled: number, curve: HoursCurveConfig): number {
    return curve.hoursScale
        * (Math.exp((scaled - curve.scaledFloor) / curve.pointsPerLogHour) - 1);
}

/**
 * Estimated study hours to move from `current` up to `target` on the log curve;
 * zero once the current estimate already meets the target. Because the curve is
 * convex, the same scaled gain costs progressively more hours the higher the
 * starting point (D29).
 */
export function hoursToTarget(
    current: number,
    target: number,
    curve: HoursCurveConfig,
): number {
    if (current >= target) {
        return 0;
    }
    return curveHoursAt(target, curve) - curveHoursAt(current, curve);
}

/**
 * Aggregate lapse rate: of the cards that have graduated to cold-capable
 * (Independent) or fallen back from it (Revisited), the fraction currently
 * lapsed. A proxy for how fragile the graduated knowledge is; `0` when nothing
 * has graduated yet (an absence of signal, not a failure). Feeds the readiness
 * confidence band (D26): fragile knowledge → a wider, less certain range.
 */
function lapseRate(nodes: TopicStat[]): number {
    let independent = 0;
    let revisited = 0;
    for (const node of nodes) {
        independent += node.levelIndependent;
        revisited += node.levelRevisited;
    }
    const graduated = independent + revisited;
    return graduated === 0 ? 0 : revisited / graduated;
}

/** The top few weak, heavily-weighted topics dragging the estimate down. */
function readinessDrivers(nodes: TopicStat[]): ReadinessDriver[] {
    return nodes
        .filter((node) => node.independentReviews > 0)
        .map((node) => ({
            id: node.id,
            title: node.title,
            weight: node.weight,
            performance: node.performance,
            priority: node.weight * (1 - node.performance),
        }))
        .sort((a, b) => b.priority - a.priority)
        .slice(0, 2);
}

/**
 * Derive Manifold's three scores from the topic graph. `computedAt` stamps the
 * reading's "last updated" field; it defaults to the wall-clock moment of
 * computation (the honest value — the scores are derived now), and is injectable
 * so callers and tests can supply a cached or fixed timestamp.
 */
export function computeScores(
    nodes: TopicStat[],
    config: ScoringConfig,
    computedAt: number = Date.now(),
): ScoreReport {
    if (nodes.length === 0) {
        throw new Error("getTopicGraph returned no topics");
    }

    const memory = weightedMean(
        nodes,
        (node) => node.avgRecall,
        (node) => node.total > 0,
    );
    // Performance is unsupported-only: it aggregates topics with Independent
    // (Review-kind) evidence, never scaffolded practice.
    const performance = weightedMean(
        nodes,
        (node) => node.performance,
        (node) => node.independentReviews > 0,
    );
    const coverage = coverageScore(nodes);
    const totalIndependentReviews = nodes.reduce(
        (sum, node) => sum + node.independentReviews,
        0,
    );

    const gateMet = totalIndependentReviews >= READINESS_MIN_INDEPENDENT_REVIEWS
        && coverage >= READINESS_MIN_COVERAGE;

    let readiness: Readiness;
    if (gateMet && performance !== null) {
        const curve = config.hoursCurve;
        if (!curve) {
            throw new Error("scoring config missing readiness hours curve");
        }
        const residue = maturityResidue(config);
        const confident = totalIndependentReviews >= READINESS_CONFIDENT_INDEPENDENT_REVIEWS
            && coverage >= READINESS_CONFIDENT_COVERAGE;
        // Band = observed per-topic spread, widened as coverage falls and as
        // graduated knowledge proves fragile (a high lapse rate ⇒ less certain).
        const lapse = lapseRate(nodes);
        const halfWidth = config.coverageBandLambda * (1 - coverage)
            + config.lapseBandLambda * lapse
            + 0.5 * (performance.high - performance.low);
        const pLow = Math.max(0, performance.value - halfWidth);
        const pHigh = Math.min(1, performance.value + halfWidth);
        // The app never projects past the promised ceiling: the residue (the
        // deep-proof items + top-percentile tax) is honestly withheld (D29/D30).
        const cap = (scaled: number): number => Math.min(scaled, residue.promisedCeiling);
        const scaledPoint = cap(performanceToScaled(performance.value, config));
        const scaledLow = cap(performanceToScaled(pLow, config));
        const scaledHigh = cap(performanceToScaled(pHigh, config));
        const targets: TargetProjection[] = targetLadder(config).map((t) => ({
            id: t.id,
            label: t.label,
            scaledPoint: t.scaledPoint,
            scaledLow: t.scaledLow,
            scaledHigh: t.scaledHigh,
            gapPoints: Math.max(0, t.scaledPoint - scaledPoint),
            hoursToTarget: hoursToTarget(scaledPoint, t.scaledPoint, curve),
            reached: scaledPoint >= t.scaledPoint,
        }));
        readiness = {
            state: "projected",
            scaledPoint,
            scaledLow,
            scaledHigh,
            coverage,
            independentReviews: totalIndependentReviews,
            confidence: confident ? "confident" : "provisional",
            drivers: readinessDrivers(nodes),
            lastUpdated: computedAt,
            targets,
            lapseRate: lapse,
            residue,
        };
    } else {
        readiness = {
            state: "abstaining",
            independentReviews: totalIndependentReviews,
            reviewsNeeded: Math.max(
                0,
                READINESS_MIN_INDEPENDENT_REVIEWS - totalIndependentReviews,
            ),
            coverage,
            coverageNeeded: Math.max(0, READINESS_MIN_COVERAGE - coverage),
            studyNext: selectStudyNext(nodes),
            lastUpdated: computedAt,
        };
    }

    return {
        memory,
        performance,
        coverage,
        totalIndependentReviews,
        gate: {
            met: gateMet,
            minIndependentReviews: READINESS_MIN_INDEPENDENT_REVIEWS,
            minCoverage: READINESS_MIN_COVERAGE,
        },
        readiness,
    };
}

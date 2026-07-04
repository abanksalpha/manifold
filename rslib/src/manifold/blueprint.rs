// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

//! Static reference data describing the GRE Mathematics blueprint: the topic
//! DAG, blueprint weights, mastery thresholds and per-tier targets.
//!
//! The data is embedded at compile time via [`include_str!`] and parsed once
//! into an in-memory [`BlueprintGraph`] stored in a [`OnceLock`]. It is static
//! content, not per-user state, so it is loaded lazily on first access and
//! shared for the lifetime of the process.

use std::collections::HashMap;
use std::sync::OnceLock;

use serde::Deserialize;

/// The raw blueprint, deserialised from `blueprint.json`.
///
/// Several fields (the scale, score distribution and ETS anchors) are part of
/// the data contract and parsed for completeness, but are only consumed by the
/// scoring layer that builds on this module, so they are not yet read here.
#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub(crate) struct Blueprint {
    pub version: u32,
    pub exam: String,
    pub scale: Scale,
    pub distribution: Distribution,
    pub readiness_mapping: ReadinessMapping,
    pub thresholds: Thresholds,
    pub tier_targets: TierValues,
    pub tier_stability: TierValues,
    pub ets_anchors: EtsAnchors,
    pub topics: Vec<Topic>,
}

/// Readiness raw→scaled mapping constants (D19/D26/D29). Chosen, not derived:
/// the median test-taker's assumed blueprint-weighted raw fraction, the
/// performance SD that turns a fraction into a percentile, the coverage and
/// lapse band wideners, the honest target ladder, the logarithmic
/// hours-to-target curve, and the maturity-residue ceiling.
#[derive(Debug, Deserialize)]
pub(crate) struct ReadinessMapping {
    pub median_raw_fraction: f64,
    pub performance_sd: f64,
    pub coverage_band_lambda: f64,
    pub lapse_band_lambda: f64,
    pub targets: Vec<ReadinessTarget>,
    pub hours_curve: HoursCurve,
    pub maturity_residue: MaturityResidue,
}

/// One rung of the readiness target ladder: a named goal (median / strong /
/// exceptional) with the scaled band that defines it (D29/D30).
#[derive(Debug, Deserialize)]
pub(crate) struct ReadinessTarget {
    pub id: String,
    pub label: String,
    pub scaled_point: i32,
    pub scaled_low: i32,
    pub scaled_high: i32,
}

/// Logarithmic effort→score curve constants (Messick-style diminishing
/// returns, D29). Chosen and tunable, not a cited hour count: the scaled floor
/// at zero targeted prep, the points gained per e-fold of effort, and the
/// hours scale (the curve's knee).
#[derive(Debug, Deserialize)]
pub(crate) struct HoursCurve {
    pub scaled_floor: i32,
    pub points_per_log_hour: f64,
    pub hours_scale: f64,
}

/// The maturity-residue ceiling the app does not promise (D29/D30): the
/// live-proof items no drill can manufacture and the scaled points at the top
/// it therefore withholds.
#[derive(Debug, Deserialize)]
pub(crate) struct MaturityResidue {
    pub items: f64,
    pub scaled_points: i32,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub(crate) struct Scale {
    pub min: i32,
    pub max: i32,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub(crate) struct Distribution {
    pub mean: f64,
    pub sd: f64,
    pub n: u32,
    pub source: String,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub(crate) struct Thresholds {
    pub new_per_day: u32,
    /// Correct retrievals (button ≥ Good) after which a skill's problem is
    /// shown solo (the Independent teaching level); scaffolding fades once
    /// competence is shown, decoupled from Anki's learning-steps
    /// graduation.
    pub independent_successes: u32,
    /// Fraction of a prerequisite topic's skills that must be *answered
    /// correctly* (the mastery-learning criterion) before its dependents
    /// unlock. Competence-now, not durable mastery — reachable in a
    /// session, unlike the weeks-long stability bar (D28).
    pub unlock_competent_fraction: f32,
}

/// A per-tier value (relearn / teach / recognize). Used for both the
/// mastered-fraction *targets* (breadth) and the per-tier *recall bars*
/// (depth).
#[derive(Debug, Deserialize)]
pub(crate) struct TierValues {
    pub relearn: f32,
    pub teach: f32,
    pub recognize: f32,
}

impl TierValues {
    /// The value for the given tier, or `None` if the tier is not one of the
    /// known blueprint tiers.
    pub(crate) fn for_tier(&self, tier: &str) -> Option<f32> {
        match tier {
            "relearn" => Some(self.relearn),
            "teach" => Some(self.teach),
            "recognize" => Some(self.recognize),
            _ => None,
        }
    }
}

/// The ETS percentile anchor table plus its citation. Structured as a block
/// (like `distribution`) so the source travels with the numbers: the anchors
/// are only trustworthy because they carry the named table they came from.
#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub(crate) struct EtsAnchors {
    pub source: String,
    pub anchors: Vec<EtsAnchor>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
pub(crate) struct EtsAnchor {
    pub scaled: i32,
    pub percentile_below: f64,
}

#[derive(Debug, Deserialize)]
pub(crate) struct Topic {
    pub id: String,
    pub title: String,
    pub area: String,
    pub tier: String,
    pub weight: f32,
    pub expected_skills: u32,
    pub prereqs: Vec<String>,
}

/// The parsed blueprint plus an id → index map for O(1) topic lookups.
pub(crate) struct BlueprintGraph {
    blueprint: Blueprint,
    index_by_id: HashMap<String, usize>,
}

impl BlueprintGraph {
    /// Topics in authored (blueprint) order.
    pub(crate) fn topics(&self) -> &[Topic] {
        &self.blueprint.topics
    }

    pub(crate) fn thresholds(&self) -> &Thresholds {
        &self.blueprint.thresholds
    }

    /// The per-tier mastered-fraction targets (breadth: how much of a topic
    /// must be mastered for the topic itself to count as mastered).
    pub(crate) fn tier_targets(&self) -> &TierValues {
        &self.blueprint.tier_targets
    }

    /// The per-tier stability bars, in days (depth: the mean per-card FSRS
    /// stability at or above which a skill counts as mastered — durable memory,
    /// not momentary recall). Relearn/teach demand mature-level stability;
    /// recognize a lower bar, since the recognition tail needs less durability.
    pub(crate) fn tier_stability(&self) -> &TierValues {
        &self.blueprint.tier_stability
    }

    /// The topic with the given id, if it is part of the blueprint.
    pub(crate) fn topic(&self, id: &str) -> Option<&Topic> {
        self.index_by_id.get(id).map(|&i| &self.blueprint.topics[i])
    }

    /// The prerequisite topic ids of the given topic, if it is known.
    pub(crate) fn prereqs(&self, id: &str) -> Option<&[String]> {
        self.topic(id).map(|t| t.prereqs.as_slice())
    }

    /// The static scoring reference data the TS readiness map reads, so the ETS
    /// anchors + mapping constants have a single source of truth (this file).
    pub(crate) fn scoring_config(&self) -> anki_proto::manifold::ScoringConfig {
        let b = &self.blueprint;
        anki_proto::manifold::ScoringConfig {
            scale_min: b.scale.min,
            scale_max: b.scale.max,
            distribution_mean: b.distribution.mean,
            distribution_sd: b.distribution.sd,
            ets_anchors: b
                .ets_anchors
                .anchors
                .iter()
                .map(|a| anki_proto::manifold::EtsAnchor {
                    scaled: a.scaled,
                    percentile_below: a.percentile_below,
                })
                .collect(),
            median_raw_fraction: b.readiness_mapping.median_raw_fraction,
            performance_sd: b.readiness_mapping.performance_sd,
            coverage_band_lambda: b.readiness_mapping.coverage_band_lambda,
            lapse_band_lambda: b.readiness_mapping.lapse_band_lambda,
            targets: b
                .readiness_mapping
                .targets
                .iter()
                .map(|t| anki_proto::manifold::ReadinessTarget {
                    id: t.id.clone(),
                    label: t.label.clone(),
                    scaled_point: t.scaled_point,
                    scaled_low: t.scaled_low,
                    scaled_high: t.scaled_high,
                })
                .collect(),
            hours_curve: Some(anki_proto::manifold::ReadinessHoursCurve {
                scaled_floor: b.readiness_mapping.hours_curve.scaled_floor,
                points_per_log_hour: b.readiness_mapping.hours_curve.points_per_log_hour,
                hours_scale: b.readiness_mapping.hours_curve.hours_scale,
            }),
            maturity_residue: Some(anki_proto::manifold::MaturityResidue {
                items: b.readiness_mapping.maturity_residue.items,
                scaled_points: b.readiness_mapping.maturity_residue.scaled_points,
            }),
        }
    }
}

static GRAPH: OnceLock<BlueprintGraph> = OnceLock::new();

/// The shared, lazily-parsed blueprint graph.
///
/// The blueprint is embedded at compile time, so a parse failure is a build
/// (programmer) error rather than user input: we surface it loudly via a panic
/// with the underlying serde message instead of silently degrading.
pub(crate) fn graph() -> &'static BlueprintGraph {
    GRAPH.get_or_init(|| {
        let json = include_str!("blueprint.json");
        let blueprint: Blueprint = serde_json::from_str(json)
            .unwrap_or_else(|e| panic!("manifold blueprint.json failed to parse: {e}"));
        let index_by_id = blueprint
            .topics
            .iter()
            .enumerate()
            .map(|(i, t)| (t.id.clone(), i))
            .collect();
        BlueprintGraph {
            blueprint,
            index_by_id,
        }
    })
}

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn blueprint_parses_and_is_self_consistent() {
        let g = graph();
        assert!(!g.topics().is_empty());
        // Every prerequisite must reference a topic that exists in the graph,
        // otherwise the lock-state rollup could never resolve.
        for topic in g.topics() {
            assert!(
                g.tier_targets().for_tier(&topic.tier).is_some()
                    && g.tier_stability().for_tier(&topic.tier).is_some(),
                "topic {} has unknown tier {}",
                topic.id,
                topic.tier
            );
            for prereq in &topic.prereqs {
                assert!(
                    g.topic(prereq).is_some(),
                    "topic {} references unknown prereq {}",
                    topic.id,
                    prereq
                );
            }
        }
    }

    #[test]
    fn scoring_config_exposes_readiness_mapping() {
        let config = graph().scoring_config();
        // The ETS anchor curve must be present, strictly monotone (higher scaled
        // ⇒ higher percentile), and carry percentiles in [0, 100]. Authored
        // order is irrelevant — the scoring layer sorts before interpolating —
        // so sort a copy by scaled score and check the invariant there.
        assert!(!config.ets_anchors.is_empty());
        for anchor in &config.ets_anchors {
            assert!((0.0..=100.0).contains(&anchor.percentile_below));
        }
        let mut sorted = config.ets_anchors.clone();
        sorted.sort_by_key(|a| a.scaled);
        for pair in sorted.windows(2) {
            assert!(
                pair[0].scaled < pair[1].scaled,
                "ets_anchors must have distinct scaled scores"
            );
            assert!(
                pair[0].percentile_below <= pair[1].percentile_below,
                "ets_anchors percentile must be monotone in scaled score"
            );
        }

        // The target ladder, hours curve and residue ceiling all reach the
        // scoring layer as data (single source of truth), never hard-coded in TS.
        assert_eq!(config.targets.len(), 3);
        let ids: Vec<&str> = config.targets.iter().map(|t| t.id.as_str()).collect();
        assert_eq!(ids, vec!["median", "strong", "exceptional"]);
        for target in &config.targets {
            assert!(target.scaled_low <= target.scaled_point);
            assert!(target.scaled_point <= target.scaled_high);
        }

        let curve = config.hours_curve.expect("hours curve present");
        assert!(curve.points_per_log_hour > 0.0);
        assert!(curve.hours_scale > 0.0);

        let residue = config.maturity_residue.expect("maturity residue present");
        assert!(residue.items > 0.0);
        assert!(residue.scaled_points > 0);
        // The promised ceiling (scale max − residue) must stay below the raw max.
        assert!(residue.scaled_points < config.scale_max);
    }
}

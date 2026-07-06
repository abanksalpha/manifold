// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

//! Manifold layers a GRE-Mathematics skill/DAG model on top of Anki's existing
//! notes, cards and tags. A skill is an Anki note tagged
//! `mf::topic::<topic_id>`, `mf::skill::<skill_id>` and `mf::tier::<tier>`. The
//! topic DAG, blueprint weights and thresholds are static reference data
//! embedded from [`blueprint.json`].
//!
//! This module only ever *reads* FSRS state; it never retunes parameters or
//! touches scheduling intervals.

pub(crate) mod blueprint;
pub(crate) mod mastery;
pub(crate) mod placement;
mod service;
pub(crate) mod session;
#[cfg(test)]
mod test;

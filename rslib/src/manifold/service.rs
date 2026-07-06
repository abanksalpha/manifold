// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

use crate::collection::Collection;
use crate::error;

impl crate::services::ManifoldService for Collection {
    fn get_topic_graph(&mut self) -> error::Result<anki_proto::manifold::TopicGraphResponse> {
        let nodes = crate::manifold::mastery::compute_topic_graph(self)?;
        let scoring_config = Some(crate::manifold::blueprint::graph().scoring_config());
        Ok(anki_proto::manifold::TopicGraphResponse {
            nodes,
            scoring_config,
        })
    }

    fn build_session_queue(
        &mut self,
        input: anki_proto::manifold::SessionQueueRequest,
    ) -> error::Result<anki_proto::manifold::SessionQueueResponse> {
        // Default on: an unset field means interleave (the full-Manifold
        // behavior), so callers that send an empty request are unchanged. Only
        // an explicit `interleave: false` selects blocked practice (WS5).
        let interleave = input.interleave.unwrap_or(true);
        let items = crate::manifold::session::build_session_queue(self, interleave)?;
        Ok(anki_proto::manifold::SessionQueueResponse { items })
    }

    fn get_problems_solved(
        &mut self,
    ) -> error::Result<anki_proto::manifold::ProblemsSolvedResponse> {
        // Cumulative count of graded reviews across all sessions (the all-time
        // analog of Anki's studied-today count).
        Ok(anki_proto::manifold::ProblemsSolvedResponse {
            total: self.storage.total_studied()?,
        })
    }

    fn get_placement_state(
        &mut self,
    ) -> error::Result<anki_proto::manifold::PlacementStateResponse> {
        let completed = crate::manifold::placement::placement_completed(self)?;
        Ok(anki_proto::manifold::PlacementStateResponse { completed })
    }

    fn build_placement_exam(
        &mut self,
        input: anki_proto::manifold::PlacementExamRequest,
    ) -> error::Result<anki_proto::manifold::SessionQueueResponse> {
        let items = crate::manifold::placement::build_placement_exam(
            self,
            &input.topic_ids,
            input.per_topic,
        )?;
        Ok(anki_proto::manifold::SessionQueueResponse { items })
    }

    fn apply_placement(
        &mut self,
        input: anki_proto::manifold::ApplyPlacementRequest,
    ) -> error::Result<anki_proto::manifold::ApplyPlacementResponse> {
        let seeded_cards =
            crate::manifold::placement::apply_placement(self, &input.known_topic_ids)?;
        Ok(anki_proto::manifold::ApplyPlacementResponse { seeded_cards })
    }

    fn claim_account(
        &mut self,
        input: anki_proto::manifold::ClaimAccountRequest,
    ) -> error::Result<anki_proto::manifold::ClaimAccountResponse> {
        let reset = crate::manifold::placement::claim_account(self, &input.uid)?;
        Ok(anki_proto::manifold::ClaimAccountResponse { reset })
    }
}

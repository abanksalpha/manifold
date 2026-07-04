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
}

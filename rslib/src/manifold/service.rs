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

    fn build_session_queue(&mut self) -> error::Result<anki_proto::manifold::SessionQueueResponse> {
        let items = crate::manifold::session::build_session_queue(self)?;
        Ok(anki_proto::manifold::SessionQueueResponse { items })
    }
}

// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getTopicGraph } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async () => {
    const graph = await getTopicGraph({});
    if (!graph.scoringConfig) {
        throw new Error("getTopicGraph returned no scoring config");
    }
    return { nodes: graph.nodes, scoringConfig: graph.scoringConfig };
}) satisfies PageLoad;

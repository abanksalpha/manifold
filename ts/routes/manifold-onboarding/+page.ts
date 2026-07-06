// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { getTopicGraph } from "@generated/backend";

import type { PageLoad } from "./$types";

export const load = (async () => {
    // Nodes give per-topic totals (is the deck imported?) and prereqs (for the
    // seed closure). No placement gate here — this page IS the onboarding.
    const graph = await getTopicGraph({});
    return { nodes: graph.nodes };
}) satisfies PageLoad;

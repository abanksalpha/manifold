// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { buildQueue } from "$lib/manifold/session";

import type { PageLoad } from "./$types";

export const load = (async () => {
    const queue = await buildQueue();
    return { queue };
}) satisfies PageLoad;

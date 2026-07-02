// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { redirect } from "@sveltejs/kit";

import type { PageLoad } from "./$types";

// The readiness dashboard was merged into the main page. Keep this path working
// by sending anyone who lands on it there.
export const load = (() => {
    redirect(307, "/manifold");
}) satisfies PageLoad;

<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import "./base.scss";

    import { browser } from "$app/environment";
    import { page } from "$app/stores";
    import { onDestroy, setContext } from "svelte";

    import { modalsKey, touchDeviceKey } from "$lib/components/context-keys";
    import { type ManifoldUser, onManifoldUser } from "$lib/manifold/firebase";
    import ManifoldLogin from "$lib/manifold/ManifoldLogin.svelte";

    setContext(modalsKey, new Map());
    setContext(touchDeviceKey, "ontouchstart" in document.documentElement);

    // Only the Manifold app requires Google sign-in. Anki's own web pages (stats
    // graphs, deck options, card info, congrats) render through this same root
    // layout and must never be gated, so the gate keys off the /manifold prefix.
    $: isManifoldApp = $page.url.pathname.startsWith("/manifold");

    let user: ManifoldUser | null = null;
    let authResolved = false;
    let authError: string | null = null;
    let unsubAuth: (() => void) | null = null;

    // Subscribe the first time a Manifold route is shown, so Firebase is never
    // initialized for the non-Manifold pages. A failed init surfaces on the login
    // screen rather than silently letting the app through.
    $: if (browser && isManifoldApp && !unsubAuth) {
        try {
            unsubAuth = onManifoldUser((next) => {
                user = next;
                authResolved = true;
            });
        } catch (e) {
            authError = e instanceof Error ? e.message : String(e);
            authResolved = true;
        }
    }

    onDestroy(() => unsubAuth?.());
</script>

{#if isManifoldApp && !user}
    <ManifoldLogin checking={!authResolved && !authError} initError={authError} />
{:else}
    <slot />
{/if}

<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The readiness dashboard now lives on the main page. The load in +page.ts
redirects here, so this route renders nothing; the link below is only a manual
fallback if the redirect has not run yet.
-->
<a class="mf-redirect" href="/manifold">Continue to Manifold</a>

<style>
    /* Only shown if the 307 redirect has not run yet, so it carries its own
       neo-brutalist styling rather than depending on the shared tokens. */
    .mf-redirect {
        display: inline-block;
        margin: 24px;
        padding: 14px 26px;
        border: 4px solid #16131c;
        background: #ff6b6b;
        box-shadow: 4px 4px 0 0 #16131c;
        color: #16131c;
        font-family: Outfit, system-ui, sans-serif;
        font-weight: 800;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        text-decoration: none;
    }
</style>

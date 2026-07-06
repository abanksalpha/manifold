<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The optional self-explanation prompt (D36, Phase 3), shown after an attempt at
New (level 0) and Guided (level 1). The learner writes one line on why the method
works, which strengthens understanding. It is deliberately inert: nothing is
graded, and nothing is sent anywhere or saved. It stays entirely on the client as
a metacognitive nudge. Gated by SELF_EXPLAIN_ENABLED in session.ts so it can be
ablated or A/B compared.
-->
<script lang="ts">
    let value = "";

    // Keep keystrokes from reaching the player's A-E / Enter shortcuts while the
    // learner is typing here (the player also ignores textarea targets).
    function onKeydown(event: KeyboardEvent): void {
        event.stopPropagation();
    }
</script>

<section class="mf-selfexplain">
    <label class="mf-selfexplain-label" for="mf-selfexplain-input">
        In one line, why does this method work?
    </label>
    <textarea
        id="mf-selfexplain-input"
        class="mf-selfexplain-input"
        rows="2"
        bind:value
        placeholder="Write a sentence for yourself"
        on:keydown={onKeydown}
    ></textarea>
    <p class="mf-selfexplain-note">Optional. It is not graded or saved.</p>
</section>

<style lang="scss">
    /* A quiet reflection box in the revealed phase, tied to the teaching family
       by a slim violet edge but calmer than the mint/red answer feedback. */
    .mf-selfexplain {
        position: relative;
        margin-top: var(--mf-space-4);
        padding: var(--mf-space-4) var(--mf-space-5);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
        overflow: hidden;
    }

    .mf-selfexplain::before {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: var(--mf-space-1);
        background: var(--mf-tertiary);
    }

    .mf-selfexplain-label {
        display: block;
        margin-bottom: var(--mf-space-2);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink-faint);
    }

    .mf-selfexplain-input {
        width: 100%;
        min-height: 48px;
        padding: var(--mf-space-3) var(--mf-space-4);
        border: var(--mf-outline);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        color: var(--mf-ink);
        font-family: var(--mf-font-sans);
        font-size: var(--mf-text-base);
        line-height: 1.5;
        resize: vertical;
    }

    .mf-selfexplain-input::placeholder {
        color: var(--mf-ink-faint);
    }

    .mf-selfexplain-note {
        margin: var(--mf-space-2) 0 0;
        font-size: var(--mf-text-sm);
        line-height: 1.5;
        color: var(--mf-ink-muted);
    }
</style>

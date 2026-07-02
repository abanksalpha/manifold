<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The shared "candy button". Primary is a filled violet pill with a 2px ink
outline and a hard offset shadow that presses in on click; secondary is an
outlined pill that fills amber on hover. Renders an <a> when given an href and a
<button> otherwise, so navigation and actions share one look. An optional `icon`
slot is set in a circular badge, per the design's "icon inside a shape" rule.
Click events forward to the caller; the loud focus ring comes from tokens.scss.
-->
<script lang="ts">
    export let href: string | null = null;
    export let variant: "primary" | "secondary" = "primary";
    export let type: "button" | "submit" = "button";
    export let disabled = false;
    /** Placed after the label; use for a trailing chevron etc. */
    export let ariaLabel: string | null = null;

    let klass = "";
    export { klass as class };
</script>

{#if href}
    <a class="mf-btn {variant} {klass}" {href} aria-label={ariaLabel} on:click>
        <span class="mf-btn-label"><slot /></span>
        {#if $$slots.icon}
            <span class="mf-btn-icon"><slot name="icon" /></span>
        {/if}
    </a>
{:else}
    <button
        class="mf-btn {variant} {klass}"
        {type}
        {disabled}
        aria-label={ariaLabel}
        on:click
    >
        <span class="mf-btn-label"><slot /></span>
        {#if $$slots.icon}
            <span class="mf-btn-icon"><slot name="icon" /></span>
        {/if}
    </button>
{/if}

<style lang="scss">
    .mf-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: var(--mf-space-2);
        min-height: 52px;
        padding: 12px 26px;
        border: var(--mf-outline-bold);
        border-radius: var(--mf-radius);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-md);
        font-weight: 800;
        line-height: 1;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        text-decoration: none;
        cursor: pointer;
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition);
    }

    /* Anki's global button reset (ts/lib/sass/base.scss) forces
       `transition: color, box-shadow ... !important` on every <button>, dropping
       transform so the lift snaps on <button> variants (the <a> variant escapes
       it). Re-assert ours with higher specificity + !important so transform eases
       for every variant alike. */
    .mf-btn.primary,
    .mf-btn.secondary {
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition) !important;
    }

    .mf-btn-label {
        white-space: nowrap;
    }

    /* primary is the hot-red action key: black stroke, ink block shadow, and a
     * mechanical press that drops it onto its own shadow */
    .primary {
        background: var(--mf-accent);
        color: var(--mf-accent-ink);
        box-shadow: var(--mf-shadow);
    }

    .primary:hover:not(:disabled) {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: color-mix(in oklch, var(--mf-accent) 88%, var(--mf-ink));
    }

    .primary:active:not(:disabled) {
        transform: translate(4px, 4px);
        box-shadow: none;
    }

    /* secondary is the outlined key: washes slightly blue on hover and presses
     * the same way, so both actions feel like the same physical switch */
    .secondary {
        background: var(--mf-surface);
        color: var(--mf-ink);
        box-shadow: var(--mf-shadow);
    }

    .secondary:hover:not(:disabled) {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: var(--mf-hover);
    }

    .secondary:active:not(:disabled) {
        transform: translate(4px, 4px);
        box-shadow: none;
    }

    /* Keep the ink outline in every state. When rendered as a <button>, Anki's
       global `button:hover/active/[disabled]` chrome (ts/lib/sass/_button-mixins)
       outspecifies the base `.mf-btn` rule and would swap our 4px ink border for
       a thin grey one; this wins the cascade so the border never changes. */
    .mf-btn:hover:not(:disabled),
    .mf-btn:active:not(:disabled),
    .mf-btn:disabled {
        border: var(--mf-outline-bold);
    }

    /* the icon rides in a bordered sticker badge, never floating bare */
    .mf-btn-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        margin-right: -8px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-surface);
        color: var(--mf-ink);
    }

    .mf-btn-icon :global(svg) {
        width: 16px;
        height: 16px;
        display: block;
    }

    .mf-btn:disabled {
        cursor: default;
        opacity: 0.55;
        transform: none;
        box-shadow: var(--mf-shadow-active);
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-btn:hover:not(:disabled),
        .mf-btn:active:not(:disabled) {
            transform: none;
        }
    }
</style>

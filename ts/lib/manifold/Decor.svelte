<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
A decorative layer of primitive shapes (the "wild decoration" half of the skin):
circles, rings, triangles, squares, plus marks and squiggles, placed behind the
content. It is purely ornamental, so the whole layer is aria-hidden and never
takes pointer events; it hides on small screens by default so a floating shape
can never land on top of text, and its optional idle float is neutralised under
prefers-reduced-motion. Shapes are data-driven so every page decorates from the
same vocabulary and palette rather than hand-rolling one-off divs.
-->
<script context="module" lang="ts">
    export type MfShapeType =
        | "circle"
        | "ring"
        | "triangle"
        | "square"
        | "plus"
        | "squiggle";

    export interface MfShape {
        type: MfShapeType;
        /** rendered size in px */
        size: number;
        /** any CSS colour; pass a palette token e.g. "var(--mf-secondary)" */
        color: string;
        top?: string;
        left?: string;
        right?: string;
        bottom?: string;
        /** degrees */
        rotate?: number;
        /** draw the 2px ink "sticker" outline on filled shapes */
        outline?: boolean;
        /** opt this shape into a slow idle bob */
        float?: boolean;
        opacity?: number;
    }

    /** The rotational confetti palette, in order. */
    export const MF_PALETTE = [
        "var(--mf-accent)",
        "var(--mf-secondary)",
        "var(--mf-tertiary)",
        "var(--mf-quaternary)",
    ];
</script>

<script lang="ts">
    export let shapes: MfShape[] = [];
    export let hideOnMobile = true;

    let klass = "";
    export { klass as class };

    function pos(s: MfShape): string {
        const parts: string[] = [];
        if (s.top != null) {
            parts.push(`top:${s.top}`);
        }
        if (s.left != null) {
            parts.push(`left:${s.left}`);
        }
        if (s.right != null) {
            parts.push(`right:${s.right}`);
        }
        if (s.bottom != null) {
            parts.push(`bottom:${s.bottom}`);
        }
        parts.push(`width:${s.size}px`, `height:${s.size}px`);
        parts.push(`--rot:${s.rotate ?? 0}deg`);
        parts.push(`opacity:${s.opacity ?? 1}`);
        return parts.join(";");
    }
</script>

<div class="mf-decor {klass}" class:hide-mobile={hideOnMobile} aria-hidden="true">
    {#each shapes as s, i (i)}
        <span class="mf-shape" style={pos(s)}>
            <span class="mf-shape-inner" class:float={s.float} style="--i:{i}">
                <svg viewBox="0 0 100 100" role="presentation">
                    {#if s.type === "circle"}
                        <circle
                            cx="50"
                            cy="50"
                            r="46"
                            fill={s.color}
                            stroke={s.outline ? "var(--mf-ink)" : "none"}
                            stroke-width={s.outline ? 6 : 0}
                        />
                    {:else if s.type === "ring"}
                        <circle
                            cx="50"
                            cy="50"
                            r="40"
                            fill="none"
                            stroke={s.color}
                            stroke-width="13"
                        />
                    {:else if s.type === "triangle"}
                        <polygon
                            points="50,7 93,90 7,90"
                            fill={s.color}
                            stroke={s.outline ? "var(--mf-ink)" : "none"}
                            stroke-width={s.outline ? 6 : 0}
                            stroke-linejoin="round"
                        />
                    {:else if s.type === "square"}
                        <rect
                            x="7"
                            y="7"
                            width="86"
                            height="86"
                            rx="4"
                            fill={s.color}
                            stroke={s.outline ? "var(--mf-ink)" : "none"}
                            stroke-width={s.outline ? 6 : 0}
                        />
                    {:else if s.type === "plus"}
                        <path
                            d="M38 6 h24 v32 h32 v24 h-32 v32 h-24 v-32 h-32 v-24 h32 z"
                            fill={s.color}
                            stroke={s.outline ? "var(--mf-ink)" : "none"}
                            stroke-width={s.outline ? 6 : 0}
                            stroke-linejoin="round"
                        />
                    {:else}
                        <path
                            d="M6 62 q18 -46 36 -20 t36 -8"
                            fill="none"
                            stroke={s.color}
                            stroke-width="13"
                            stroke-linecap="round"
                        />
                    {/if}
                </svg>
            </span>
        </span>
    {/each}
</div>

<style lang="scss">
    .mf-decor {
        position: absolute;
        inset: 0;
        z-index: 0;
        pointer-events: none;
    }

    .mf-shape {
        position: absolute;
        display: block;
        transform: rotate(var(--rot, 0deg));
    }

    .mf-shape-inner {
        display: block;
        width: 100%;
        height: 100%;
    }

    .mf-shape-inner.float {
        animation: mf-float 7s ease-in-out infinite;
        animation-delay: calc(var(--i) * 0.8s);
    }

    .mf-shape-inner svg {
        display: block;
        width: 100%;
        height: 100%;
        overflow: visible;
    }

    @media (max-width: 640px) {
        .hide-mobile {
            display: none;
        }
    }
</style>

<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
Confetti ported from the brilliant-clone repo's frontend/src/lib/confetti.ts,
which drives the canvas-confetti library. The same physics (spray angle and
spread, a startVelocity that decays each frame, gravity, per-piece wobble and a
tumbling tilt, and a linear opacity fade over a fixed lifetime) is reimplemented
inline on a single <canvas> so the Anki build gains no dependency. celebrate()
reproduces that file's five layered bursts for finishing a lesson; burst() is its
lighter single pop. Both now bloom from the centre of the screen. The paper squares and circles
keep the source's motion and shape, recoloured to Manifold's pop palette so they
fit the neo-brutalist skin. The layer is a fixed, click-through overlay, and
nothing is drawn when the learner has asked for reduced motion.
-->
<script lang="ts" context="module">
    export interface Origin {
        x: number;
        y: number;
    }

    type Shape = "square" | "circle";

    interface FireOptions {
        particleCount: number;
        angle: number;
        spread: number;
        startVelocity: number;
        decay: number;
        gravity: number;
        drift: number;
        ticks: number;
        scalar: number;
    }

    interface Fetti {
        x: number;
        y: number;
        wobble: number;
        wobbleSpeed: number;
        wobbleX: number;
        wobbleY: number;
        velocity: number;
        angle2D: number;
        tiltAngle: number;
        tiltSin: number;
        tiltCos: number;
        color: string;
        shape: Shape;
        tick: number;
        totalTicks: number;
        decay: number;
        drift: number;
        gravity: number;
        random: number;
        ovalScalar: number;
        scalar: number;
    }

    // canvas-confetti's defaults, the baseline every burst layers overrides onto.
    const DEFAULTS: FireOptions = {
        particleCount: 50,
        angle: 90,
        spread: 45,
        startVelocity: 45,
        decay: 0.9,
        gravity: 1,
        drift: 0,
        ticks: 200,
        scalar: 1,
    };

    // Seed one piece with the source's randomised launch: half its start speed
    // plus a random half again, a heading inside the spread cone, and a random
    // spin phase so the sheet tumbles on its own clock.
    function randomPhysics(
        x: number,
        y: number,
        color: string,
        shape: Shape,
        o: FireOptions,
    ): Fetti {
        const radAngle = o.angle * (Math.PI / 180);
        const radSpread = o.spread * (Math.PI / 180);
        return {
            x,
            y,
            wobble: Math.random() * 10,
            wobbleSpeed: Math.min(0.11, Math.random() * 0.1 + 0.05),
            wobbleX: 0,
            wobbleY: 0,
            velocity: o.startVelocity * 0.5 + Math.random() * o.startVelocity,
            angle2D: -radAngle + (0.5 * radSpread - Math.random() * radSpread),
            tiltAngle: (Math.random() * 0.5 + 0.25) * Math.PI,
            tiltSin: 0,
            tiltCos: 0,
            color,
            shape,
            tick: 0,
            totalTicks: o.ticks,
            decay: o.decay,
            drift: o.drift,
            gravity: o.gravity * 3,
            random: Math.random() + 2,
            ovalScalar: 0.6,
            scalar: o.scalar,
        };
    }

    // Advance one piece a frame and paint it. Velocity decays while gravity
    // keeps pulling it down; the wobble and tilt shear the quad so the paper
    // flutters, and opacity fades linearly to nothing over the piece's life.
    // Returns false once the piece has run out its ticks.
    function updateFetti(context: CanvasRenderingContext2D, fetti: Fetti): boolean {
        fetti.x += Math.cos(fetti.angle2D) * fetti.velocity + fetti.drift;
        fetti.y += Math.sin(fetti.angle2D) * fetti.velocity + fetti.gravity;
        fetti.velocity *= fetti.decay;

        fetti.wobble += fetti.wobbleSpeed;
        fetti.wobbleX = fetti.x + 10 * fetti.scalar * Math.cos(fetti.wobble);
        fetti.wobbleY = fetti.y + 10 * fetti.scalar * Math.sin(fetti.wobble);
        fetti.tiltAngle += 0.1;
        fetti.tiltSin = Math.sin(fetti.tiltAngle);
        fetti.tiltCos = Math.cos(fetti.tiltAngle);
        fetti.random = Math.random() + 2;

        const progress = fetti.tick++ / fetti.totalTicks;

        const x1 = fetti.x + fetti.random * fetti.tiltCos;
        const y1 = fetti.y + fetti.random * fetti.tiltSin;
        const x2 = fetti.wobbleX + fetti.random * fetti.tiltCos;
        const y2 = fetti.wobbleY + fetti.random * fetti.tiltSin;

        context.globalAlpha = 1 - progress;
        context.fillStyle = fetti.color;
        context.beginPath();
        if (fetti.shape === "circle") {
            context.ellipse(
                fetti.x,
                fetti.y,
                Math.abs(x2 - x1) * fetti.ovalScalar,
                Math.abs(y2 - y1) * fetti.ovalScalar,
                (Math.PI / 10) * fetti.wobble,
                0,
                2 * Math.PI,
            );
        } else {
            context.moveTo(Math.floor(fetti.x), Math.floor(fetti.y));
            context.lineTo(Math.floor(fetti.wobbleX), Math.floor(y1));
            context.lineTo(Math.floor(x2), Math.floor(y2));
            context.lineTo(Math.floor(x1), Math.floor(fetti.wobbleY));
        }
        context.closePath();
        context.fill();

        return fetti.tick < fetti.totalTicks;
    }
</script>

<script lang="ts">
    import { onDestroy, onMount } from "svelte";

    // The source's three flat hues become Manifold's pop palette so the spray
    // reads on-brand. Kept as tokens so light/dark and any palette change follow.
    const PALETTE = [
        "var(--mf-accent)",
        "var(--mf-secondary)",
        "var(--mf-tertiary)",
        "var(--mf-quaternary)",
    ];

    let layer: HTMLDivElement | undefined;
    let canvas: HTMLCanvasElement | undefined;
    let ctx: CanvasRenderingContext2D | null = null;

    // Live pieces, mutated in place so the render loop never triggers reactivity.
    const particles: Fetti[] = [];
    let raf = 0;
    let cssW = 0;
    let cssH = 0;

    function prefersReducedMotion(): boolean {
        return (
            typeof window !== "undefined" &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches
        );
    }

    // Back the canvas at device resolution and scale the context so the physics
    // stays in CSS pixels while the paper renders crisp on hi-dpi screens.
    function resize(): void {
        if (!canvas || !ctx) {
            return;
        }
        const dpr = window.devicePixelRatio || 1;
        cssW = window.innerWidth;
        cssH = window.innerHeight;
        canvas.width = Math.floor(cssW * dpr);
        canvas.height = Math.floor(cssH * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    // Only fire in a browser that can actually paint, and never under reduced
    // motion. Mirrors the source's canFire guard.
    function canFire(): boolean {
        return !!ctx && cssW > 0 && cssH > 0 && !prefersReducedMotion();
    }

    // A canvas fill cannot read CSS custom properties, so resolve the palette
    // tokens to concrete colors through the browser's own colour pipeline. Run
    // per call so a light/dark switch is always reflected.
    function resolveColors(): string[] {
        if (!layer) {
            return [];
        }
        const probe = document.createElement("span");
        probe.style.display = "none";
        layer.appendChild(probe);
        const colors = PALETTE.map((token) => {
            probe.style.color = token;
            return getComputedStyle(probe).color;
        });
        probe.remove();
        return colors;
    }

    function frame(): void {
        const context = ctx;
        if (!context) {
            raf = 0;
            return;
        }
        context.clearRect(0, 0, cssW, cssH);
        let write = 0;
        for (let read = 0; read < particles.length; read++) {
            const fetti = particles[read];
            if (updateFetti(context, fetti)) {
                particles[write++] = fetti;
            }
        }
        particles.length = write;
        raf = particles.length > 0 ? requestAnimationFrame(frame) : 0;
    }

    // One canvas-confetti cannon: seed particleCount pieces at the launch point,
    // given in screen pixels, and keep the loop alive.
    function fire(
        startX: number,
        startY: number,
        colors: string[],
        overrides: Partial<FireOptions>,
    ): void {
        const o: FireOptions = { ...DEFAULTS, ...overrides };
        for (let i = 0; i < o.particleCount; i++) {
            const color = colors[i % colors.length];
            const shape: Shape = Math.random() < 0.5 ? "square" : "circle";
            particles.push(randomPhysics(startX, startY, color, shape, o));
        }
        if (raf === 0) {
            raf = requestAnimationFrame(frame);
        }
    }

    // The viewport centre in screen pixels: the launch point for every burst.
    function screenCenter(): Origin {
        return { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    }

    /**
     * A focused pop that leaps up from the centre of the screen. Ports the
     * source's celebrateSmall. The origin (the answered tile) is kept in the
     * signature for callers but ignored, so the pop always fires from centre.
     */
    export function burst(origin: Origin): void {
        if (!canFire()) {
            return;
        }
        void origin;
        const { x, y } = screenCenter();
        fire(x, y, resolveColors(), {
            particleCount: 50,
            spread: 55,
            startVelocity: 40,
            scalar: 0.9,
        });
    }

    /**
     * A whole-screen celebration. Ports the source's celebrate: five layered
     * cannons from the centre of the screen, from a tight fast core out to a
     * slow wide drift, so the spray blooms and lingers rather than firing as one
     * volley.
     */
    export function celebrate(): void {
        if (!canFire()) {
            return;
        }
        const colors = resolveColors();
        const total = 160;
        const { x, y } = screenCenter();
        fire(x, y, colors, {
            particleCount: Math.floor(total * 0.25),
            spread: 26,
            startVelocity: 55,
        });
        fire(x, y, colors, { particleCount: Math.floor(total * 0.2), spread: 60 });
        fire(x, y, colors, {
            particleCount: Math.floor(total * 0.35),
            spread: 100,
            decay: 0.91,
            scalar: 0.9,
        });
        fire(x, y, colors, {
            particleCount: Math.floor(total * 0.1),
            spread: 120,
            startVelocity: 25,
            decay: 0.92,
            scalar: 1.2,
        });
        fire(x, y, colors, {
            particleCount: Math.floor(total * 0.1),
            spread: 120,
            startVelocity: 45,
        });
    }

    onMount(() => {
        if (!canvas) {
            return;
        }
        ctx = canvas.getContext("2d");
        resize();
        window.addEventListener("resize", resize);
    });

    onDestroy(() => {
        if (typeof window !== "undefined") {
            window.removeEventListener("resize", resize);
        }
        if (raf !== 0) {
            cancelAnimationFrame(raf);
            raf = 0;
        }
    });
</script>

<div class="mf-confetti" bind:this={layer} aria-hidden="true">
    <canvas bind:this={canvas} class="mf-confetti-canvas"></canvas>
</div>

<style lang="scss">
    .mf-confetti {
        position: fixed;
        inset: 0;
        z-index: 60;
        overflow: hidden;
        pointer-events: none;
    }

    .mf-confetti-canvas {
        display: block;
        width: 100%;
        height: 100%;
    }
</style>

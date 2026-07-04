<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The hint assistant on the problem player (asking phase only). A stuck learner opens
it, asks a question in their own words, and gets one hint back that points at the
method without giving the answer. It is deliberately quiet: collapsed by default so
it never nudges the learner to lean on it, and the assistant is sent only the stem
and choices the learner already sees (never the correct index or worked solution),
so it cannot leak the answer.

Every exchange is kept in a per-problem conversation (never persisted) and passed
back as context so a follow-up builds on the last nudge. A failed request fails
loudly with its real message; an honest "abstain" (no key, offline) shows the real
reason, never a fabricated hint. All maths in a hint is typeset through MathText.
-->
<script lang="ts">
    import { onDestroy, tick } from "svelte";

    import Button from "$lib/manifold/Button.svelte";
    import MathText from "$lib/manifold/MathText.svelte";
    import { renderMath } from "$lib/manifold/mathmarkup";
    import {
        fetchHint,
        type HintTurn,
        hintUnavailableMessage,
        type Problem,
        type QueueItem,
    } from "$lib/manifold/session";

    export let problem: Problem;
    export let item: QueueItem;

    let open = false;
    let question = "";
    let turns: HintTurn[] = [];
    let pending = false;
    // A loud transport/contract failure (the request itself broke): show it.
    let error: string | null = null;
    // An honest abstain from the assistant (no key, offline): the real reason, not a hint.
    let unavailable: string | null = null;
    let controller: AbortController | null = null;
    let inputEl: HTMLTextAreaElement | undefined;

    async function toggle(): Promise<void> {
        open = !open;
        if (open) {
            await tick();
            inputEl?.focus();
        }
    }

    async function ask(): Promise<void> {
        const q = question.trim();
        if (!q || pending) {
            return;
        }
        pending = true;
        error = null;
        unavailable = null;
        controller = new AbortController();
        try {
            const response = await fetchHint(
                item,
                problem,
                q,
                turns,
                controller.signal,
            );
            if (response.status === "ok") {
                turns = [...turns, { question: q, hint: response.hint }];
                question = "";
                await tick();
                inputEl?.focus();
            } else {
                unavailable = hintUnavailableMessage(response.reason, response.detail);
            }
        } catch (e) {
            // The learner navigated away mid-request: the abort is expected, not an error.
            if (e instanceof DOMException && e.name === "AbortError") {
                return;
            }
            error = e instanceof Error ? e.message : String(e);
        } finally {
            pending = false;
            controller = null;
        }
    }

    // Enter sends; Shift+Enter inserts a newline. Stop the keypress here so the
    // player's global A-E / Enter shortcuts never fire while the learner is typing.
    function onInputKeydown(event: KeyboardEvent): void {
        event.stopPropagation();
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            void ask();
        }
    }

    onDestroy(() => controller?.abort());
</script>

<div class="mf-hint" class:open>
    <button
        type="button"
        class="mf-hint-toggle"
        class:open
        aria-expanded={open}
        aria-controls="mf-hint-body"
        on:click={toggle}
    >
        <span class="mf-hint-badge" aria-hidden="true">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M9 18h6" />
                <path d="M10 21.5h4" />
                <path
                    d="M12 3a6 6 0 0 0-3.5 10.9c.5.4.8 1 .9 1.6l.1.5h5l.1-.5c.1-.6.4-1.2.9-1.6A6 6 0 0 0 12 3Z"
                />
            </svg>
        </span>
        <span class="mf-hint-toggle-label">Ask for a hint</span>
        <span class="mf-hint-chevron" class:open aria-hidden="true">
            <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="m6 9 6 6 6-6" />
            </svg>
        </span>
    </button>

    {#if open}
        <div id="mf-hint-body" class="mf-hint-body">
            <p class="mf-hint-note">
                Ask where you're stuck. The assistant points you toward the method, not
                the answer.
            </p>

            {#if turns.length > 0}
                <div class="mf-hint-log" aria-live="polite">
                    {#each turns as turn, i (i)}
                        <div class="mf-hint-turn">
                            <p class="mf-hint-turn-label">You asked</p>
                            <p class="mf-hint-turn-question">{turn.question}</p>
                            <div class="mf-hint-turn-answer">
                                <span class="mf-hint-answer-badge" aria-hidden="true">
                                    <svg
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        stroke-width="2"
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                    >
                                        <path d="M9 18h6" />
                                        <path d="M10 21.5h4" />
                                        <path
                                            d="M12 3a6 6 0 0 0-3.5 10.9c.5.4.8 1 .9 1.6l.1.5h5l.1-.5c.1-.6.4-1.2.9-1.6A6 6 0 0 0 12 3Z"
                                        />
                                    </svg>
                                </span>
                                <div class="mf-hint-answer-text">
                                    <MathText text={renderMath(turn.hint)} />
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}

            {#if pending}
                <p class="mf-hint-pending" aria-live="polite">
                    <span class="mf-hint-spinner" aria-hidden="true"></span>
                    Thinking of a hint
                </p>
            {/if}

            {#if unavailable}
                <p class="mf-hint-unavailable">{unavailable}</p>
            {/if}
            {#if error}
                <p class="mf-hint-error">Could not get a hint: {error}</p>
            {/if}

            <form class="mf-hint-form" on:submit|preventDefault={ask}>
                <textarea
                    bind:this={inputEl}
                    bind:value={question}
                    class="mf-hint-input"
                    rows="2"
                    placeholder="e.g. Where should I start?"
                    aria-label="Ask a question about this problem"
                    disabled={pending}
                    on:keydown={onInputKeydown}
                ></textarea>
                <Button
                    type="submit"
                    class="mf-hint-send"
                    disabled={pending || question.trim().length === 0}
                >
                    Ask
                    <svg
                        slot="icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2.5"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path d="M12 19V5" />
                        <path d="m5 12 7-7 7 7" />
                    </svg>
                </Button>
            </form>
        </div>
    {/if}
</div>

<style lang="scss">
    .mf-hint {
        margin-top: var(--mf-space-4);
    }

    /* The disclosure control: a bordered bar with the app's mechanical press and a
       violet assistant badge, so it reads as help, not a fifth answer. */
    .mf-hint-toggle {
        display: flex;
        align-items: center;
        gap: var(--mf-space-3);
        width: 100%;
        padding: var(--mf-space-3) var(--mf-space-4);
        border: var(--mf-outline-bold);
        border-radius: var(--mf-radius);
        background: var(--mf-surface);
        color: var(--mf-ink);
        text-align: left;
        cursor: pointer;
        box-shadow: var(--mf-shadow);
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition);
    }

    /* Anki's global button reset forces its own transition with !important and drops
       transform; re-assert ours at higher specificity so the lift eases (as the
       shared Button and choice tiles do). */
    .mf-hint .mf-hint-toggle {
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition) !important;
    }

    /* Only the collapsed bar lifts and presses like a button; once open it is a
       header, so it flattens and connects to the tray it reveals. */
    .mf-hint-toggle:not(.open):hover:not(:disabled) {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: color-mix(in srgb, var(--mf-tertiary) 22%, var(--mf-surface));
    }

    .mf-hint-toggle:not(.open):active:not(:disabled) {
        transform: translate(4px, 4px);
        box-shadow: none;
    }

    .mf-hint-toggle.open {
        transform: none;
        box-shadow: none;
        background: color-mix(in srgb, var(--mf-tertiary) 14%, var(--mf-surface));
    }

    /* Keep the ink outline through every state (Anki's global button chrome would
       otherwise swap it for a thin grey border on hover/active). */
    .mf-hint-toggle:hover:not(:disabled),
    .mf-hint-toggle:active:not(:disabled) {
        border: var(--mf-outline-bold);
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-hint-toggle:not(.open):hover:not(:disabled),
        .mf-hint-toggle:not(.open):active:not(:disabled) {
            transform: none;
        }
    }

    .mf-hint-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: none;
        width: 32px;
        height: 32px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-tertiary);
        color: var(--mf-tertiary-ink);
    }

    .mf-hint-badge svg {
        width: 18px;
        height: 18px;
        display: block;
    }

    .mf-hint-toggle-label {
        flex: 1;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-md);
        font-weight: 800;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .mf-hint-chevron {
        display: inline-flex;
        flex: none;
        color: var(--mf-ink-muted);
        transition: transform var(--mf-transition);
    }

    .mf-hint-chevron.open {
        transform: rotate(180deg);
    }

    .mf-hint-chevron svg {
        width: 20px;
        height: 20px;
        display: block;
    }

    /* The tray: a sunken surface set under the bar, with one slim violet edge, the
       same reveal language as the answer feedback panel. */
    .mf-hint-body {
        position: relative;
        margin-top: calc(-1 * var(--mf-border-width-bold));
        padding: var(--mf-space-4) var(--mf-space-5);
        border: var(--mf-outline-bold);
        border-top: none;
        background: var(--mf-surface-sunken);
    }

    .mf-hint-body::before {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: var(--mf-space-1);
        background: var(--mf-tertiary);
    }

    .mf-hint-note {
        margin: 0 0 var(--mf-space-4);
        max-width: 56ch;
        font-size: var(--mf-text-sm);
        line-height: 1.5;
        color: var(--mf-ink-muted);
    }

    .mf-hint-log {
        display: flex;
        flex-direction: column;
        gap: var(--mf-space-5);
        margin-bottom: var(--mf-space-4);
    }

    .mf-hint-turn-label {
        margin: 0 0 var(--mf-space-1);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink-faint);
    }

    .mf-hint-turn-question {
        margin: 0;
        font-size: var(--mf-text-base);
        line-height: 1.5;
        color: var(--mf-ink-muted);
    }

    .mf-hint-turn-answer {
        display: flex;
        align-items: flex-start;
        gap: var(--mf-space-3);
        margin-top: var(--mf-space-3);
    }

    /* The hint rides behind the same bordered sticker badge the app uses for icons,
       here filled violet to mark it as the assistant's voice. */
    .mf-hint-answer-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: none;
        width: 28px;
        height: 28px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        background: var(--mf-tertiary);
        color: var(--mf-tertiary-ink);
    }

    .mf-hint-answer-badge svg {
        width: 16px;
        height: 16px;
        display: block;
    }

    .mf-hint-answer-text {
        flex: 1;
        font-size: var(--mf-text-base);
        line-height: 1.6;
        color: var(--mf-ink);
    }

    .mf-hint-pending {
        display: flex;
        align-items: center;
        gap: var(--mf-space-3);
        margin: 0 0 var(--mf-space-4);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-sm);
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        color: var(--mf-ink-muted);
    }

    .mf-hint-spinner {
        flex: none;
        width: 18px;
        height: 18px;
        border: 3px solid color-mix(in srgb, var(--mf-ink) 18%, transparent);
        border-top-color: var(--mf-ink);
        border-radius: var(--mf-radius-full);
        animation: mf-spin 0.8s linear infinite;
    }

    @keyframes mf-spin {
        to {
            transform: rotate(360deg);
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-hint-spinner {
            animation-duration: 2.4s;
        }
    }

    /* An honest, quiet line when the assistant abstains (no key, offline): the real
       reason, in the system's one grey, never a fabricated hint. */
    .mf-hint-unavailable {
        margin: 0 0 var(--mf-space-4);
        padding: var(--mf-space-3) var(--mf-space-4);
        border: 2px solid color-mix(in srgb, var(--mf-abstain) 60%, var(--mf-ink));
        border-radius: var(--mf-radius);
        font-size: var(--mf-text-sm);
        line-height: 1.5;
        color: var(--mf-ink-muted);
        background: color-mix(in srgb, var(--mf-abstain) 20%, var(--mf-surface));
    }

    /* A loud-but-honest failure line if the request itself broke. */
    .mf-hint-error {
        margin: 0 0 var(--mf-space-4);
        padding: var(--mf-space-3) var(--mf-space-4);
        border: 2px solid var(--mf-accent);
        border-radius: var(--mf-radius);
        font-size: var(--mf-text-sm);
        line-height: 1.5;
        color: var(--mf-ink);
        background: color-mix(in srgb, var(--mf-accent) 12%, var(--mf-surface));
    }

    .mf-hint-form {
        display: flex;
        align-items: flex-end;
        gap: var(--mf-space-3);
    }

    .mf-hint-input {
        flex: 1;
        min-height: 52px;
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

    .mf-hint-input::placeholder {
        color: var(--mf-ink-faint);
    }

    .mf-hint-input:disabled {
        opacity: 0.6;
        cursor: default;
    }

    :global(.mf-btn.mf-hint-send) {
        flex: none;
    }

    @media (max-width: 460px) {
        .mf-hint-form {
            flex-direction: column;
            align-items: stretch;
        }

        :global(.mf-btn.mf-hint-send) {
            width: 100%;
        }
    }
</style>

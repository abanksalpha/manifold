<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<script lang="ts">
    import "@fontsource-variable/outfit/wght.css";
    import "@fontsource-variable/plus-jakarta-sans/wght.css";
    import "$lib/manifold/tokens.scss";

    import { browser } from "$app/environment";
    import { onDestroy, onMount } from "svelte";

    import AnswerFeedback from "$lib/manifold/AnswerFeedback.svelte";
    import Button from "$lib/manifold/Button.svelte";
    import Confetti from "$lib/manifold/Confetti.svelte";
    import HintPanel from "$lib/manifold/HintPanel.svelte";
    import Lecture from "$lib/manifold/Lecture.svelte";
    import {
        mathToMarkup,
        mathToPlainText,
        renderMath,
    } from "$lib/manifold/mathmarkup";
    import MathText from "$lib/manifold/MathText.svelte";
    import type {
        Answer,
        ChoiceId,
        DeferredSkill,
        Lecture as LectureData,
        PullResult,
        QueueItem,
        RunnerProgress,
        ServedProblem,
    } from "$lib/manifold/session";
    import {
        abstainSummary,
        bigintReplacer,
        bigintReviver,
        choiceFor,
        CHOICE_IDS,
        fetchLecture,
        grade,
        hintsAllowed,
        isCorrect,
        levelLabel,
        SessionRunner,
        takePrewarmedSession,
    } from "$lib/manifold/session";
    import { pushProgressSnapshot } from "$lib/manifold/sync";

    import type { PageData } from "./$types";

    export let data: PageData;

    // One runner per session: it drives the due queue, skips ahead past skills that
    // can't be verified (recording them as deferred), and keeps a small buffer of
    // upcoming problems generating in the background so real problems arrive back to
    // back (D44). It never dead-ends on an abstain. Built from the queue the loader
    // fetched, but rebuilt from a persisted snapshot on mount when the learner is
    // resuming an in-progress session after a trip to the dashboard.
    let queue: QueueItem[] = data.queue;
    let runner = new SessionRunner(queue);

    // The current verified problem, or null while generating / when the run is done.
    let served: ServedProblem | null = null;
    // The New-skill lecture for the current problem, or null (higher level, or none
    // authored yet — an honest gap, never a fabricated lecture). Task 1.
    let lecture: LectureData | null = null;
    let deferred: DeferredSkill[] = [];
    let done = false;
    let loading = false;
    // A loud failure ONLY for a served item that violates its own contract (a
    // malformed "ok" payload); the ordinary "couldn't generate" case is a silent
    // skip-ahead recorded as a deferred skill, not this.
    let loadError: { item: QueueItem | null; message: string } | null = null;
    let generatingItem: QueueItem | null = null;

    let phase: "asking" | "revealed" = "asking";
    let chosenIndex: number | null = null;
    let correct = false;
    let busy = false;
    let answered = 0;
    let error: string | null = null;
    // Non-fatal: a failed progress-mirror push (Firebase) surfaces here without
    // interrupting study, since the review itself is already saved to the engine.
    let syncError: string | null = null;
    let confetti: Confetti | undefined;
    let celebrated = false;
    // Guards against a stale pull resolving after the learner has moved on.
    let loadToken = 0;
    // Persistence is armed only after mount has had a chance to restore, so an
    // init-time reactive save can never clobber a snapshot before it is read.
    let mounted = false;

    // --- session persistence (resume across a dashboard round-trip) --------------
    // The learner can leave the session for the dashboard and come back to the SAME
    // problem in the SAME state instead of losing it to a fresh generation. The live
    // player state (the queue, how far through it we are, the current verified
    // problem and the answer already given) is snapshotted to sessionStorage — scoped
    // to this app run, not persisted to disk, and cleared when the run completes, so
    // it is session continuity, never a fabricated or stale problem bank.
    const SESSION_KEY = "manifold.session.v1";

    interface PersistedSession {
        v: 1;
        queue: QueueItem[];
        progress: RunnerProgress;
        served: ServedProblem | null;
        phase: "asking" | "revealed";
        chosenIndex: number | null;
        correct: boolean;
        answered: number;
    }

    // QueueItem.cardId is a bigint, which JSON cannot represent; bigintReplacer /
    // bigintReviver (shared, unit-tested in session.ts) tag it out and revive it so
    // the whole session round-trips losslessly.
    function saveSnapshot(): void {
        if (!browser) {
            return;
        }
        // A finished run is not resumable: clear it so the next Start begins fresh.
        if (done) {
            clearSnapshot();
            return;
        }
        const snapshot: PersistedSession = {
            v: 1,
            queue,
            progress: runner.snapshotProgress(),
            served,
            phase,
            chosenIndex,
            correct,
            answered,
        };
        // Serialize OUTSIDE the guard: the snapshot shape is fully controlled, so a
        // stringify failure would be a real bug and must surface, not be swallowed.
        // Only the storage write is wrapped, since sessionStorage itself can be
        // unavailable (private mode / quota); resume then degrades but the session
        // keeps running.
        const serialized = JSON.stringify(snapshot, bigintReplacer);
        try {
            sessionStorage.setItem(SESSION_KEY, serialized);
        } catch {
            // sessionStorage unavailable: skip persistence, do not fail the session.
        }
    }

    function clearSnapshot(): void {
        if (!browser) {
            return;
        }
        try {
            sessionStorage.removeItem(SESSION_KEY);
        } catch {
            // ignore — see saveSnapshot
        }
    }

    function loadSnapshot(): PersistedSession | null {
        if (!browser) {
            return null;
        }
        let raw: string | null = null;
        try {
            raw = sessionStorage.getItem(SESSION_KEY);
        } catch {
            return null;
        }
        if (!raw) {
            return null;
        }
        let parsed: PersistedSession;
        try {
            parsed = JSON.parse(raw, bigintReviver) as PersistedSession;
        } catch {
            // A corrupt snapshot is treated as none rather than crashing the session.
            return null;
        }
        if (
            parsed?.v !== 1 ||
            !Array.isArray(parsed.queue) ||
            parsed.queue.length === 0
        ) {
            return null;
        }
        return parsed;
    }

    onMount(() => {
        const snapshot = loadSnapshot();
        if (snapshot) {
            // Resume the in-progress run: rebuild the runner on the SAME queue at the
            // same position, and restore the counters and deferred list.
            queue = snapshot.queue;
            runner = new SessionRunner(queue, { resume: snapshot.progress });
            deferred = snapshot.progress.deferred;
            answered = snapshot.answered;
            if (snapshot.served) {
                // The learner left mid-problem: show that exact problem and answer.
                served = snapshot.served;
                phase = snapshot.phase;
                chosenIndex = snapshot.chosenIndex;
                correct = snapshot.correct;
                loading = false;
                // Warm the next problem now so the first Continue after returning is
                // not a cold start (the rebuilt runner's buffer is otherwise empty).
                runner.prime();
                if (served.item.level === 0) {
                    void loadLecture(served.item, loadToken);
                }
            } else {
                // They had already continued past the last problem (it was still
                // generating when they left): pull the next one for this position.
                void advance();
            }
        } else {
            // Fresh session: adopt the dashboard's prewarmed runner if it started
            // generating the first problem already, so a template-less first skill
            // has a head start instead of stalling this screen.
            const warm = takePrewarmedSession();
            if (warm) {
                queue = warm.queue;
                runner = warm.runner;
            }
            void advance();
        }
        mounted = true;
        // Persist the restored/started state immediately so a very fast round-trip
        // still finds a snapshot.
        saveSnapshot();
    });

    onDestroy(() => {
        // Leaving the session (e.g. to the dashboard): abort any in-flight generation
        // so a slow live request does not linger, and persist where we are so coming
        // back resumes here instead of regenerating from the top.
        // Ordering matters: dispose() aborts synchronously but the aborted fetch
        // rejects on a later microtask, and Svelte fires no reactive saves after
        // destroy, so this saveSnapshot() captures the pre-abort state (the problem
        // the learner was on) rather than the discarded runner's post-abort result.
        runner.dispose();
        saveSnapshot();
    });

    // Persist on every change to the resumable state, once mount has armed it.
    $: if (mounted) {
        void [served, phase, chosenIndex, correct, answered, deferred, done];
        saveSnapshot();
    }

    // A finished run that actually solved something earns one whole-screen
    // celebration; a run that only met deferred skills, or an empty queue on
    // arrival, stays calm rather than cheering nothing.
    $: if (browser && done && answered > 0 && !celebrated) {
        celebrated = true;
        confetti?.celebrate();
    }

    // The dominant defer reason, for the honest end-of-session line when nothing at
    // all could be generated (e.g. no API key): the real reason, never a fake item.
    $: dominantReason =
        deferred.length > 0
            ? [
                  ...deferred.reduce(
                      (counts, d) =>
                          counts.set(d.reason, (counts.get(d.reason) ?? 0) + 1),
                      new Map<string, number>(),
                  ),
              ].sort((a, b) => b[1] - a[1])[0][0]
            : null;

    async function settle(pull: Promise<PullResult>, token: number): Promise<void> {
        try {
            const result = await pull;
            if (token !== loadToken) {
                return;
            }
            served = result.served;
            deferred = result.deferred;
            done = result.served === null;
            loading = false;
            // A New (level 0) skill is taught before its first problem: fetch its
            // pre-authored lecture in the background. It is supplementary, so it
            // never blocks the problem, and a skill without one stays null.
            if (served && served.item.level === 0) {
                void loadLecture(served.item, token);
            }
        } catch (e) {
            if (token !== loadToken) {
                return;
            }
            // Verify-before-serve is the invariant the server just broke: surface it
            // loudly instead of rendering a broken card. Retry/skip recover from here.
            deferred = runner.deferredSkills;
            loadError = {
                item: runner.currentItem,
                message: e instanceof Error ? e.message : String(e),
            };
            loading = false;
        }
    }

    async function advance(): Promise<void> {
        const token = ++loadToken;
        phase = "asking";
        chosenIndex = null;
        correct = false;
        error = null;
        loadError = null;
        served = null;
        lecture = null;
        generatingItem = runner.currentItem;
        loading = true;
        await settle(runner.pull(), token);
    }

    // Load the New-skill lecture for a served item, guarding against a stale pull
    // resolving after the learner has moved on. A missing lecture (null) is honest:
    // the skill simply teaches through its worked solution instead.
    async function loadLecture(item: QueueItem, token: number): Promise<void> {
        const loaded = await fetchLecture(item);
        if (token === loadToken) {
            lecture = loaded;
        }
    }

    function retry(): void {
        const token = ++loadToken;
        loadError = null;
        served = null;
        lecture = null;
        generatingItem = runner.currentItem;
        loading = true;
        void settle(runner.retryCurrent(), token);
    }

    function skip(): void {
        const token = ++loadToken;
        const message = loadError?.message ?? "served item was invalid";
        loadError = null;
        served = null;
        lecture = null;
        loading = true;
        void settle(runner.skipCurrent("served_item_invalid", message), token);
    }

    function screenCenter(): { x: number; y: number } {
        return { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    }

    async function answer(choice: Answer): Promise<void> {
        if (busy || phase !== "asking" || !served) {
            return;
        }
        const problem = served.problem;
        const item = served.item;
        const pressed = choiceFor(problem, choice);
        // Reveal immediately so feedback and animation land promptly; the grade
        // write happens in the background and never blocks the screen.
        chosenIndex = pressed?.index ?? null;
        correct = isCorrect(problem, choice);
        phase = "revealed";
        if (correct && browser) {
            confetti?.burst(screenCenter());
        }
        busy = true;
        error = null;
        try {
            await grade(item, correct);
            // Count the review only once the grade write lands, so a failed save
            // surfaces its error instead of inflating the worked tally.
            answered += 1;
            // Mirror the updated progress to Firestore in the background so other
            // signed-in devices update live. The engine review is already saved, so
            // a sync failure is non-fatal: record it, never block the session.
            void pushProgressSnapshot()
                .then(() => {
                    syncError = null;
                })
                .catch((e) => {
                    syncError = e instanceof Error ? e.message : String(e);
                });
        } catch (e) {
            // Fail loudly: surface the real reason the reschedule did not save
            // instead of pretending the answer was recorded.
            error = e instanceof Error ? e.message : String(e);
        } finally {
            busy = false;
        }
    }

    function onKeydown(event: KeyboardEvent): void {
        // Typing in the hint box (or any field) must never trigger the A-E / Enter
        // answer shortcuts, so ignore keystrokes that originate from a form control.
        const target = event.target as HTMLElement | null;
        if (
            target &&
            (target.tagName === "TEXTAREA" ||
                target.tagName === "INPUT" ||
                target.isContentEditable)
        ) {
            return;
        }
        if (
            event.metaKey ||
            event.ctrlKey ||
            event.altKey ||
            loading ||
            done ||
            loadError
        ) {
            return;
        }
        if (!served) {
            return;
        }
        if (phase === "revealed") {
            if (!busy && (event.key === "Enter" || event.key === " ")) {
                event.preventDefault();
                advance();
            }
            return;
        }
        if (busy) {
            return;
        }
        const letter = event.key.toUpperCase();
        if ((CHOICE_IDS as readonly string[]).includes(letter)) {
            event.preventDefault();
            answer(letter as ChoiceId);
        } else if (event.key === "0") {
            event.preventDefault();
            answer("dont-know");
        }
    }
</script>

<svelte:window on:keydown={onKeydown} />

<div class="manifold mf-page">
    <Confetti bind:this={confetti} />
    <div class="mf-shell">
        <header class="mf-masthead">
            <span class="mf-wordmark">Manifold</span>
            {#if !done}
                <div class="mf-masthead-end">
                    {#if deferred.length > 0}
                        <span
                            class="mf-pending"
                            title="These due skills had no verifiable problem this session. Manifold defers them rather than show an unverified item; they were not scored."
                        >
                            {deferred.length}
                            {deferred.length === 1 ? "skill" : "skills"} pending content
                        </span>
                    {/if}
                    <Button
                        href="/manifold"
                        variant="secondary"
                        ariaLabel="Back to the dashboard"
                    >
                        Dashboard
                        <svg
                            slot="icon"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M19 12H5" />
                            <path d="m11 18-6-6 6-6" />
                        </svg>
                    </Button>
                </div>
            {/if}
        </header>

        {#if done}
            <section class="mf-complete">
                <div class="mf-complete-card">
                    <span class="mf-complete-mark" aria-hidden="true">
                        <svg viewBox="0 0 24 24" role="presentation">
                            <circle
                                cx="12"
                                cy="12"
                                r="10.5"
                                fill="var(--mf-quaternary)"
                                stroke="var(--mf-ink)"
                                stroke-width="1.5"
                            />
                            <path
                                d="M7.6 12.5l2.9 3 6-6.6"
                                fill="none"
                                stroke="var(--mf-accent-ink)"
                                stroke-width="2.5"
                                stroke-linecap="round"
                                stroke-linejoin="round"
                            />
                        </svg>
                    </span>
                    <h1 class="mf-complete-title">Session complete</h1>
                    <p class="mf-complete-text">
                        {#if answered > 0}
                            You worked {answered}
                            {answered === 1 ? "problem" : "problems"}. FSRS has
                            rescheduled each one.
                        {:else}
                            No problems were completed this session.
                        {/if}
                    </p>
                    {#if deferred.length > 0}
                        <p class="mf-complete-pending">
                            {#if answered > 0}
                                {deferred.length}
                                {deferred.length === 1 ? "skill is" : "skills are"}
                                pending content and {deferred.length === 1
                                    ? "was"
                                    : "were"} not scored.
                            {:else}
                                {abstainSummary(dominantReason ?? "")}
                            {/if}
                        </p>
                    {/if}
                    {#if syncError}
                        <p class="mf-complete-pending" style="opacity:0.75">
                            Progress saved on this device, but cross-device sync did not
                            complete: {syncError}
                        </p>
                    {/if}
                    <Button href="/manifold">
                        Back to Manifold
                        <svg
                            slot="icon"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M19 12H5" />
                            <path d="m11 18-6-6 6-6" />
                        </svg>
                    </Button>
                </div>
            </section>
        {:else if loading}
            <section class="mf-card mf-generating" aria-busy="true" aria-live="polite">
                {#if generatingItem}
                    <p class="mf-eyebrow">{generatingItem.topicTitle}</p>
                {/if}
                <div class="mf-generating-row">
                    <span class="mf-spinner" aria-hidden="true"></span>
                    <div>
                        <h1 class="mf-generating-title">Generating a problem</h1>
                        <p class="mf-generating-note">
                            Writing a fresh question for this skill and checking every
                            choice before it is shown.
                        </p>
                    </div>
                </div>
            </section>
        {:else if loadError}
            <section class="mf-card mf-abstain" data-topic={loadError.item?.topicId}>
                <p class="mf-eyebrow">{loadError.item?.topicTitle ?? "Manifold"}</p>
                <h1 class="mf-abstain-title">Something went wrong</h1>
                <p class="mf-abstain-note">
                    A generated problem failed its own checks before it could be shown.
                    It was not scored.
                </p>
                <p class="mf-abstain-detail">{loadError.message}</p>
                <div class="mf-abstain-actions">
                    <Button on:click={retry}>Try again</Button>
                    <Button variant="secondary" on:click={skip}>Skip skill</Button>
                </div>
            </section>
        {:else if served}
            {#if served.item.level === 0 && lecture}
                <Lecture {lecture} />
            {/if}
            <section
                class="mf-card"
                data-topic={served.item.topicId}
                aria-labelledby="mf-stem"
            >
                <p class="mf-eyebrow">{served.problem.topic}</p>
                <div id="mf-stem" class="mf-stem">
                    <MathText text={renderMath(served.problem.stem)} />
                </div>

                <div class="mf-meta">
                    <span class="mf-level mf-level-{served.item.level}">
                        {levelLabel(served.item.level)}
                    </span>
                </div>

                <div class="mf-choices" class:revealed={phase === "revealed"}>
                    {#each served.problem.choices as choice (choice.id)}
                        <button
                            class="mf-choice"
                            class:is-correct={phase === "revealed" &&
                                choice.index === served.problem.correctIndex}
                            class:is-chosen={phase === "revealed" &&
                                chosenIndex === choice.index &&
                                choice.index !== served.problem.correctIndex}
                            type="button"
                            disabled={busy}
                            aria-disabled={phase === "revealed"}
                            aria-label="Answer {choice.id}: {mathToPlainText(
                                choice.text,
                            )}"
                            on:click={() => answer(choice.id)}
                        >
                            <span class="mf-choice-key">{choice.id}</span>
                            <span class="mf-choice-text">
                                <MathText text={mathToMarkup(choice.text)} />
                            </span>
                            {#if phase === "revealed" && choice.index === served.problem.correctIndex}
                                <span class="mf-choice-tag">Correct</span>
                            {:else if phase === "revealed" && chosenIndex === choice.index}
                                <span class="mf-choice-tag muted">Your pick</span>
                            {/if}
                        </button>
                    {/each}
                </div>

                {#if phase === "asking"}
                    {#if hintsAllowed(served.item.level)}
                        {#key served.problem}
                            <HintPanel problem={served.problem} item={served.item} />
                        {/key}
                    {/if}
                    <Button
                        class="mf-dontknow"
                        variant="secondary"
                        disabled={busy}
                        on:click={() => answer("dont-know")}
                    >
                        Don't know
                    </Button>
                {:else}
                    <AnswerFeedback
                        problem={served.problem}
                        {chosenIndex}
                        {correct}
                        level={served.item.level}
                    />
                    {#if error}
                        <p class="mf-error">Could not save your answer: {error}</p>
                    {/if}
                    <Button class="mf-continue" disabled={busy} on:click={advance}>
                        Continue
                        <svg
                            slot="icon"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2.5"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M5 12h14" />
                            <path d="m13 6 6 6-6 6" />
                        </svg>
                    </Button>
                {/if}
            </section>
        {/if}
    </div>
</div>

<style lang="scss">
    .mf-page {
        min-height: 100vh;
        padding: var(--mf-space-7) var(--mf-space-6);
    }

    .mf-shell {
        max-width: 680px;
        margin-inline: auto;
    }

    .mf-masthead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
    }

    .mf-masthead-end {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
    }

    /* An honest, quiet note that some due skills had no verifiable problem this
       session. It is a small count, never a full-screen wall and never a fake
       item: those skills are deferred, not scored. */
    .mf-pending {
        display: inline-flex;
        align-items: center;
        gap: var(--mf-space-2);
        padding: 0.15em var(--mf-space-3);
        border: 2px solid color-mix(in srgb, var(--mf-abstain) 60%, var(--mf-ink));
        border-radius: var(--mf-radius-full);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.02em;
        color: var(--mf-ink-muted);
        background: color-mix(in srgb, var(--mf-abstain) 22%, var(--mf-surface));
    }

    .mf-wordmark {
        position: relative;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-2xl);
        font-weight: 800;
        letter-spacing: -0.03em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    .mf-wordmark::after {
        content: "";
        position: absolute;
        left: -0.03em;
        right: -0.03em;
        bottom: 0.08em;
        height: 0.26em;
        background: var(--mf-secondary);
        transform: rotate(-1.5deg);
        transform-origin: left center;
        z-index: -1;
    }

    /* The reading card: a calm surface, chunky ink outline and a soft hard
       shadow, lifted by one slim accent rule along its top edge. */
    .mf-card {
        position: relative;
        margin-top: var(--mf-space-6);
        padding: var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-card);
    }

    .mf-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: var(--mf-space-2);
        background: var(--mf-accent);
    }

    /* The topic the problem sits under: a small orienting eyebrow above the
       stem, never louder than the question itself. */
    .mf-eyebrow {
        margin: 0 0 var(--mf-space-2);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--mf-ink-faint);
    }

    /* The problem itself: the one prominent thing on the card. Typeset maths
       sits inline with the prose through MathText. */
    .mf-stem {
        font-size: var(--mf-text-lg);
        line-height: 1.5;
        color: var(--mf-ink);
    }

    .mf-meta {
        display: flex;
        align-items: baseline;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
        margin-top: var(--mf-space-4);
    }

    .mf-level {
        display: inline-block;
        padding: 0.05em var(--mf-space-2);
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius-full);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-ink);
        background: var(--mf-surface);
    }

    .mf-level-0 {
        background: color-mix(in srgb, var(--mf-abstain) 30%, var(--mf-surface));
    }

    .mf-level-1 {
        background: color-mix(in srgb, var(--mf-quaternary) 40%, var(--mf-surface));
    }

    .mf-level-2 {
        background: color-mix(in srgb, var(--mf-signal) 26%, var(--mf-surface));
    }

    .mf-level-3 {
        background: color-mix(in srgb, var(--mf-accent) 34%, var(--mf-surface));
    }

    .mf-choices {
        display: flex;
        flex-direction: column;
        gap: var(--mf-space-3);
        margin-top: var(--mf-space-5);
    }

    /* A tactile answer row: the letter rides in a keycap on the left, the
       typeset choice fills the rest. On hover the face lifts up-left and presses
       back down on click, the same mechanical switch as the shared Button. */
    .mf-choice {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
        width: 100%;
        min-height: 56px;
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

    /* Anki's global button reset forces its own transition with !important and
       drops transform; re-assert ours at higher specificity so the lift eases. */
    .mf-choices .mf-choice {
        transition:
            transform var(--mf-transition-bounce),
            box-shadow var(--mf-transition-bounce),
            background-color var(--mf-transition) !important;
    }

    .mf-choice-key {
        display: flex;
        align-items: center;
        justify-content: center;
        flex: none;
        width: 36px;
        height: 36px;
        border: 2px solid var(--mf-ink);
        border-radius: var(--mf-radius);
        background: var(--mf-surface-sunken);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-md);
        font-weight: 800;
    }

    .mf-choice-text {
        flex: 1;
        font-size: var(--mf-text-md);
        line-height: 1.4;
    }

    /* A small state tag pinned to the right of a revealed choice. */
    .mf-choice-tag {
        flex: none;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xs);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mf-quaternary-ink);
    }

    .mf-choice-tag.muted {
        color: var(--mf-ink-faint);
    }

    /* Asking-phase hover: the shared Button's mechanical lift, with the face
       darkening the neutral tile toward ink (a warm grey) rather than washing to
       an off-brand tint. Scoped to :not(.revealed) so a revealed tile never
       lifts once the answer is in. */
    .mf-choices:not(.revealed) .mf-choice:hover:not(:disabled) {
        transform: translate(-2px, -2px);
        box-shadow: var(--mf-shadow-hover);
        background: color-mix(in srgb, var(--mf-surface) 86%, var(--mf-ink));
        border: var(--mf-outline-bold);
    }

    .mf-choices:not(.revealed) .mf-choice:active:not(:disabled) {
        transform: translate(4px, 4px);
        box-shadow: none;
        border: var(--mf-outline-bold);
    }

    /* Revealed tiles are inert and flat: no lift, no shadow travel, and a uniform
       ink border on all four sides (no lighter bottom edge). The correct row is
       washed mint; the learner's wrong pick is washed red, the same conventional
       wrong signal the feedback panel now carries. */
    .mf-choices.revealed .mf-choice {
        cursor: default;
        transform: none;
        box-shadow: var(--mf-shadow-active);
        border: var(--mf-outline-bold);
    }

    .mf-choice.is-correct {
        background: color-mix(in srgb, var(--mf-quaternary) 34%, var(--mf-surface));
        border: var(--mf-outline-bold);
    }

    .mf-choice.is-correct .mf-choice-key {
        background: var(--mf-quaternary);
    }

    .mf-choice.is-chosen {
        background: color-mix(in srgb, var(--mf-accent) 34%, var(--mf-surface));
        border: var(--mf-outline-bold);
    }

    .mf-choice.is-chosen .mf-choice-key {
        background: var(--mf-accent);
    }

    /* Revealed-phase hover deepens each tile's OWN colour in place instead of
       lifting: the neutral tile darkens toward ink, the correct tile to a deeper
       green, the wrong pick to a deeper red. These out-specify the base state
       fills so the reveal reads "pressed and darker", never washed grey. */
    .mf-choices.revealed .mf-choice:hover {
        background: color-mix(in srgb, var(--mf-surface) 86%, var(--mf-ink));
    }

    .mf-choices.revealed .mf-choice.is-correct:hover {
        background: color-mix(
            in srgb,
            color-mix(in srgb, var(--mf-quaternary) 40%, var(--mf-surface)),
            var(--mf-ink) 12%
        );
    }

    .mf-choices.revealed .mf-choice.is-chosen:hover {
        background: color-mix(
            in srgb,
            color-mix(in srgb, var(--mf-accent) 40%, var(--mf-surface)),
            var(--mf-ink) 12%
        );
    }

    .mf-choice:disabled {
        border: var(--mf-outline-bold);
    }

    @media (prefers-reduced-motion: reduce) {
        .mf-choices:not(.revealed) .mf-choice:hover:not(:disabled),
        .mf-choices:not(.revealed) .mf-choice:active:not(:disabled) {
            transform: none;
        }
    }

    :global(.mf-btn.mf-dontknow) {
        width: 100%;
        margin-top: var(--mf-space-4);
    }

    :global(.mf-btn.mf-continue) {
        width: 100%;
        margin-top: var(--mf-space-5);
    }

    /* A loud-but-honest failure line if the grade write did not land. */
    .mf-error {
        margin: var(--mf-space-4) 0 0;
        padding: var(--mf-space-3) var(--mf-space-4);
        border: 2px solid var(--mf-accent);
        border-radius: var(--mf-radius);
        font-size: var(--mf-text-sm);
        color: var(--mf-ink);
        background: color-mix(in srgb, var(--mf-accent) 12%, var(--mf-surface));
    }

    /* Generating: the honest live-generation state. Manifold writes and verifies
       a fresh problem per review (D44); this says so while that runs. */
    .mf-generating::before {
        background: var(--mf-signal);
    }

    .mf-generating-row {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
    }

    .mf-generating-title {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-lg);
        font-weight: 800;
        letter-spacing: -0.01em;
        color: var(--mf-ink);
    }

    .mf-generating-note {
        margin: var(--mf-space-1) 0 0;
        max-width: 48ch;
        font-size: var(--mf-text-base);
        line-height: 1.5;
        color: var(--mf-ink-muted);
    }

    /* A single deliberate spinner: a ring with one ink arc turning steadily. */
    .mf-spinner {
        flex: none;
        width: 34px;
        height: 34px;
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
        .mf-spinner {
            animation-duration: 2.4s;
        }
    }

    /* Abstain / loud error: an honest, quiet state. Calm grey, no alarm, and
       nothing gradeable. */
    .mf-abstain::before {
        background: var(--mf-abstain);
    }

    .mf-abstain-title {
        margin: 0 0 var(--mf-space-3);
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-xl);
        font-weight: 800;
        letter-spacing: -0.01em;
        color: var(--mf-ink);
    }

    .mf-abstain-note {
        margin: var(--mf-space-3) 0 0;
        max-width: 52ch;
        font-size: var(--mf-text-base);
        line-height: 1.55;
        color: var(--mf-ink-muted);
    }

    .mf-abstain-detail {
        margin: var(--mf-space-3) 0 0;
        max-width: 52ch;
        font-size: var(--mf-text-sm);
        line-height: 1.5;
        color: var(--mf-ink-faint);
    }

    .mf-abstain-actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--mf-space-3);
        margin-top: var(--mf-space-5);
    }

    .mf-complete {
        margin-top: var(--mf-space-6);
    }

    .mf-complete-card {
        display: grid;
        justify-items: center;
        gap: var(--mf-space-3);
        padding: var(--mf-space-7) var(--mf-space-6);
        border: var(--mf-outline);
        border-radius: var(--mf-radius-lg);
        background: var(--mf-surface);
        box-shadow: var(--mf-shadow-feature);
        text-align: center;
        animation: mf-pop-in var(--mf-transition-bounce) both;
    }

    .mf-complete-mark {
        display: block;
        width: 64px;
        height: 64px;
        margin-bottom: var(--mf-space-1);
    }

    .mf-complete-mark svg {
        display: block;
        width: 100%;
        height: 100%;
    }

    .mf-complete-title {
        margin: 0;
        font-family: var(--mf-font-display);
        font-size: var(--mf-text-2xl);
        font-weight: 800;
        letter-spacing: -0.02em;
        text-transform: uppercase;
        color: var(--mf-ink);
    }

    .mf-complete-text {
        margin: 0 0 var(--mf-space-2);
        max-width: 44ch;
        font-size: var(--mf-text-base);
        color: var(--mf-ink-muted);
    }

    /* The honest pending-content line on the finish screen: quiet, factual, and
       never dressed up as anything other than skills that were not scored. */
    .mf-complete-pending {
        margin: 0 0 var(--mf-space-2);
        max-width: 46ch;
        font-size: var(--mf-text-sm);
        line-height: 1.5;
        color: var(--mf-ink-faint);
    }

    @media (max-width: 460px) {
        .mf-card {
            padding: var(--mf-space-4);
        }

        .mf-choice {
            min-height: 48px;
        }

        .mf-complete-card {
            padding: var(--mf-space-6) var(--mf-space-4);
        }
    }
</style>

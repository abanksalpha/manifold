<!--
Copyright: Ankitects Pty Ltd and contributors
License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
-->
<!--
The signed-in account chip, top-right in the masthead. Deliberately minimal: the
avatar, the name, and Sign out — no scores (those are the Measurements below).
Renders nothing when signed out (the body SyncPanel shows the sign-in prompt).
Client-only; a sign-out error surfaces inline rather than silently.
-->
<script lang="ts">
    import { browser } from "$app/environment";
    import { onDestroy, onMount } from "svelte";

    import Button from "$lib/manifold/Button.svelte";
    import {
        type ManifoldUser,
        onManifoldUser,
        signOutManifold,
    } from "$lib/manifold/firebase";

    let user: ManifoldUser | null = null;
    let busy = false;
    let error: string | null = null;
    let unsub: (() => void) | null = null;

    onMount(() => {
        if (!browser) {
            return;
        }
        try {
            unsub = onManifoldUser((next) => {
                user = next;
            });
        } catch (e) {
            error = e instanceof Error ? e.message : String(e);
        }
    });

    onDestroy(() => {
        unsub?.();
    });

    async function signOutNow(): Promise<void> {
        busy = true;
        try {
            await signOutManifold();
        } catch (e) {
            error = e instanceof Error ? e.message : String(e);
        } finally {
            busy = false;
        }
    }

    function initial(u: ManifoldUser): string {
        return (u.displayName ?? u.email ?? "?").trim().slice(0, 1).toUpperCase();
    }
</script>

{#if user}
    <div class="mf-account" title={user.email ?? undefined}>
        <div class="mf-account-id">
            {#if user.photoURL}
                <img
                    class="mf-account-avatar"
                    src={user.photoURL}
                    alt=""
                    referrerpolicy="no-referrer"
                />
            {:else}
                <span class="mf-account-avatar mf-account-avatar--fallback">
                    {initial(user)}
                </span>
            {/if}
            <span class="mf-account-name">{user.displayName ?? user.email}</span>
        </div>
        <Button
            class="mf-account-signout"
            variant="secondary"
            on:click={signOutNow}
            disabled={busy}
            ariaLabel="Sign out"
        >
            Sign out
        </Button>
    </div>
    {#if error}
        <p class="mf-account-error">{error}</p>
    {/if}
{/if}

<style>
    /* No container: the account control is just identity + one action. Wrapping
       avatar+name+button in a bordered, shadowed box nested a second bordered,
       shadowed button inside it — the double elevation is what read as cramped.
       Here the avatar circle and the Sign-out button are the only bordered
       elements, each with room to breathe. Rhythm: avatar and name sit tight as
       one identity, with a wider step to the action. */
    .mf-account {
        display: flex;
        align-items: center;
        gap: var(--mf-space-4);
        font-family: "Plus Jakarta Sans Variable", system-ui, sans-serif;
    }
    .mf-account-id {
        display: flex;
        align-items: center;
        gap: var(--mf-space-2);
        min-width: 0;
    }
    .mf-account-avatar {
        display: block;
        width: 34px;
        height: 34px;
        border-radius: 50%;
        border: 2px solid var(--mf-ink, #16131c);
        object-fit: cover;
        flex: none;
    }
    .mf-account-avatar--fallback {
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--mf-secondary, #ffd93d);
        color: var(--mf-ink, #16131c);
        font-weight: 800;
        font-size: 0.95rem;
    }
    .mf-account-name {
        font-weight: 700;
        font-size: 0.95rem;
        color: var(--mf-ink, #16131c);
        max-width: 12rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    /* Sign out is the shared Button (secondary/white variant): white fill, ink
       border, offset shadow, amber hover, mechanical press. With no wrapping box
       it now has room to lift and press. Nudged just under the default size. */
    .mf-account :global(.mf-account-signout) {
        min-height: 42px;
        padding: 9px 18px;
        font-size: var(--mf-text-sm, 0.85rem);
    }
    .mf-account-error {
        margin: var(--mf-space-2) 0 0;
        color: #b00020;
        font-size: 0.8rem;
        font-weight: 700;
        text-align: right;
    }
</style>

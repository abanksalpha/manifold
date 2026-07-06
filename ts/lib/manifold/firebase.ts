// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Manifold's Firebase layer: Google identity + a real-time progress mirror.
 *
 * One shared module drives all three surfaces (desktop Qt webview, Android
 * AnkiDroid webview, and the web dashboard), because they render the same Svelte
 * pages. Firebase carries ONLY the derived progress read-model (see `progress.ts`)
 * — the Anki collection stays the scheduling source of truth, synced by Anki's own
 * protocol. So this is additive: it never touches FSRS, cards, or the revlog.
 *
 * Google sign-in is environment-aware because Google blocks its OAuth consent
 * screen inside embedded webviews ("disallowed_useragent"):
 *   - real browser (web dashboard) → `signInWithPopup`.
 *   - desktop Qt webview          → a native system-browser loopback (mediasrv
 *                                    endpoint) returns a Google ID token, then
 *                                    `signInWithCredential`.
 *   - Android webview             → a native Credential-Manager bridge returns a
 *                                    Google ID token, then `signInWithCredential`.
 *
 * Everything fails loud (no silent fallbacks): a missing config, a sign-in the
 * environment cannot service, or a Firestore error surfaces a real message.
 */

import { type FirebaseApp, getApps, initializeApp } from "firebase/app";
import {
    type Auth,
    browserLocalPersistence,
    connectAuthEmulator,
    getAuth,
    GoogleAuthProvider,
    indexedDBLocalPersistence,
    initializeAuth,
    inMemoryPersistence,
    onAuthStateChanged,
    signInAnonymously,
    signInWithCredential,
    signInWithPopup,
    signOut,
    type User,
} from "firebase/auth";
import {
    connectFirestoreEmulator,
    doc,
    type Firestore,
    getDoc,
    getFirestore,
    onSnapshot,
    serverTimestamp,
    setDoc,
    type Timestamp,
} from "firebase/firestore";

import { requireFirebaseConfig } from "./firebase.config";
import type { ProgressData } from "./progress";

/** A trimmed view of the signed-in user the UI needs. */
export interface ManifoldUser {
    uid: string;
    email: string | null;
    displayName: string | null;
    photoURL: string | null;
}

/** Which shell is rendering these pages, and thus how Google sign-in must run. */
export type ManifoldShell = "browser" | "desktop" | "android";

/** The remote progress document as stored in Firestore (transport fields + the
 * derived payload). `updatedAt` is a Firestore server Timestamp. */
export interface RemoteProgress extends ProgressData {
    uid: string;
    schemaVersion: number;
    updatedAt: Timestamp | null;
    platform: string;
    deviceId: string;
    appVersion: string;
}

const APP_VERSION = "1.0.0";

// The whitelisted desktop mediasrv endpoint that runs the system-browser loopback
// OAuth and returns a Google ID token (implemented in qt/aqt/mediasrv.py).
const DESKTOP_SIGNIN_URL = "/_anki/manifoldGoogleSignIn";

let appSingleton: FirebaseApp | null = null;
let authSingleton: Auth | null = null;
let dbSingleton: Firestore | null = null;

/**
 * Detect the shell. Android injects a `ManifoldAndroidAuth` JS interface, so it is
 * caught first; otherwise a loopback/localhost origin is the embedded desktop
 * webview (served by mediasrv), and anything else is a real browser (the hosted
 * web dashboard). Off the browser entirely (SSR) it reports "browser".
 */
export function detectShell(): ManifoldShell {
    const w = globalThis as unknown as { ManifoldAndroidAuth?: unknown };
    if (w.ManifoldAndroidAuth && typeof w.ManifoldAndroidAuth === "object") {
        return "android";
    }
    if (typeof location === "undefined") {
        return "browser";
    }
    const host = location.hostname;
    return host === "127.0.0.1" || host === "localhost" ? "desktop" : "browser";
}

function shellPlatform(): string {
    switch (detectShell()) {
        case "android":
            return "android";
        case "desktop":
            return "desktop";
        default:
            return "web";
    }
}

/** Lazily initialize the Firebase app + auth + firestore. Throws loudly if the
 * config is incomplete. Connects to the local emulators when a dev flag is set. */
function ensure(): { app: FirebaseApp; auth: Auth; db: Firestore } {
    if (typeof window === "undefined") {
        throw new Error("Firebase can only be initialized in the browser");
    }
    if (!appSingleton) {
        const config = requireFirebaseConfig();
        appSingleton = getApps()[0] ?? initializeApp(config);
        authSingleton = initializeManifoldAuth(appSingleton);
        dbSingleton = getFirestore(appSingleton);
        maybeConnectEmulators(authSingleton, dbSingleton);
    }
    return { app: appSingleton, auth: authSingleton!, db: dbSingleton! };
}

/**
 * Initialize auth with durable persistence so a signed-in session survives
 * closing and reopening the app: IndexedDB first, then localStorage, with
 * in-memory only as a last resort. Falls back to the already-created instance if
 * auth was initialized earlier in this page (the only case `initializeAuth`
 * throws) — not a failure fallback, just re-using the existing singleton.
 */
function initializeManifoldAuth(app: FirebaseApp): Auth {
    try {
        return initializeAuth(app, {
            persistence: [indexedDBLocalPersistence, browserLocalPersistence, inMemoryPersistence],
        });
    } catch {
        return getAuth(app);
    }
}

let emulatorsConnected = false;
function maybeConnectEmulators(auth: Auth, db: Firestore): void {
    const w = globalThis as unknown as { __MANIFOLD_FIREBASE_EMULATOR__?: boolean };
    if (emulatorsConnected || !w.__MANIFOLD_FIREBASE_EMULATOR__) {
        return;
    }
    emulatorsConnected = true;
    connectAuthEmulator(auth, "http://127.0.0.1:9399", { disableWarnings: true });
    connectFirestoreEmulator(db, "127.0.0.1", 8399);
    // The e2e harness has no interactive Google sign-in, so authenticate against
    // the Auth emulator anonymously — enough for the login gate and the owner-only
    // Firestore rules (which key on request.auth.uid). A failure surfaces in the
    // console and leaves the login screen up, never silently letting the app in.
    void signInAnonymously(auth).catch((err) => {
        console.error("Manifold e2e emulator sign-in failed:", err);
    });
}

function toManifoldUser(user: User): ManifoldUser {
    return {
        uid: user.uid,
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
    };
}

/**
 * Subscribe to auth state. Fires immediately with the current user (or null) and
 * on every sign-in/sign-out. Returns an unsubscribe function.
 */
export function onManifoldUser(cb: (user: ManifoldUser | null) => void): () => void {
    const { auth } = ensure();
    return onAuthStateChanged(auth, (user) => cb(user ? toManifoldUser(user) : null));
}

/** The current signed-in user, or null. */
export function currentManifoldUser(): ManifoldUser | null {
    const { auth } = ensure();
    return auth.currentUser ? toManifoldUser(auth.currentUser) : null;
}

// --- sign-in (environment-aware) ---------------------------------------------

/** Sign in with Google, choosing the flow the current shell supports. Rejects
 * with a real error if the shell's native bridge is missing or the user cancels. */
export async function signInWithGoogle(): Promise<ManifoldUser> {
    const { auth } = ensure();
    const shell = detectShell();

    if (shell === "browser") {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        return toManifoldUser(result.user);
    }

    // Embedded webview: a native shell brokers the Google credential.
    const idToken = shell === "android"
        ? await androidGoogleIdToken()
        : await desktopGoogleIdToken();
    const credential = GoogleAuthProvider.credential(idToken);
    const result = await signInWithCredential(auth, credential);
    return toManifoldUser(result.user);
}

/** Ask the desktop shell to run the system-browser loopback OAuth and return a
 * Google ID token. Fails loud on any non-ok verdict. */
async function desktopGoogleIdToken(): Promise<string> {
    let res: Response;
    try {
        res = await fetch(DESKTOP_SIGNIN_URL, {
            method: "POST",
            headers: { "Content-Type": "application/binary" },
            body: new TextEncoder().encode(JSON.stringify({})),
        });
    } catch (err) {
        throw new Error(
            `Desktop Google sign-in could not reach the app: ${(err as Error).message}`,
        );
    }
    if (!res.ok) {
        throw new Error(`Desktop Google sign-in failed: HTTP ${res.status} ${await safeText(res)}`);
    }
    const parsed = JSON.parse(await res.text()) as
        | { status: "ok"; id_token: string }
        | { status: string; reason?: string; detail?: string };
    if (parsed.status !== "ok" || !("id_token" in parsed) || !parsed.id_token) {
        const why = "reason" in parsed ? `${parsed.reason ?? ""} ${parsed.detail ?? ""}`.trim() : "";
        throw new Error(`Desktop Google sign-in did not return a token${why ? `: ${why}` : ""}`);
    }
    return parsed.id_token;
}

/**
 * Ask the Android shell (a `ManifoldAndroidAuth` JS interface injected by the
 * AnkiDroid Kotlin side) for a Google ID token. The bridge starts the native
 * Credential Manager flow and resolves this promise via the two globals below.
 */
function androidGoogleIdToken(): Promise<string> {
    const bridge = (globalThis as unknown as {
        ManifoldAndroidAuth?: { startGoogleSignIn?: () => void };
    }).ManifoldAndroidAuth;
    if (!bridge || typeof bridge.startGoogleSignIn !== "function") {
        throw new Error("Android Google sign-in bridge is unavailable in this build");
    }
    return new Promise<string>((resolve, reject) => {
        const w = globalThis as unknown as {
            __manifoldAndroidResolveIdToken?: (token: string) => void;
            __manifoldAndroidRejectIdToken?: (message: string) => void;
        };
        w.__manifoldAndroidResolveIdToken = (token: string) => {
            cleanup();
            token ? resolve(token) : reject(new Error("Android sign-in returned an empty token"));
        };
        w.__manifoldAndroidRejectIdToken = (message: string) => {
            cleanup();
            reject(new Error(message || "Android Google sign-in failed"));
        };
        function cleanup() {
            delete w.__manifoldAndroidResolveIdToken;
            delete w.__manifoldAndroidRejectIdToken;
        }
        bridge.startGoogleSignIn!();
    });
}

async function safeText(res: Response): Promise<string> {
    try {
        return await res.text();
    } catch {
        return "";
    }
}

/** Sign the user out on this device. */
export async function signOutManifold(): Promise<void> {
    const { auth } = ensure();
    await signOut(auth);
}

// --- per-account onboarding state (Firestore-backed) -------------------------

/**
 * Whether the signed-in Google account has finished onboarding/placement. This
 * lives in Firestore, not the local collection, so it follows the account: a new
 * Google account has no doc and is sent to placement on any device. Throws if no
 * user is signed in (the app gates on sign-in before this runs).
 */
export async function getOnboardingComplete(): Promise<boolean> {
    const { auth, db } = ensure();
    const user = auth.currentUser;
    if (!user) {
        throw new Error("getOnboardingComplete called with no signed-in user");
    }
    const snap = await getDoc(doc(db, "users", user.uid, "state", "onboarding"));
    return snap.exists() && snap.data().complete === true;
}

/**
 * Mark onboarding/placement complete for the signed-in Google account, so every
 * device signed into it skips placement. Throws if no user is signed in.
 */
export async function setOnboardingComplete(): Promise<void> {
    const { auth, db } = ensure();
    const user = auth.currentUser;
    if (!user) {
        throw new Error("setOnboardingComplete called with no signed-in user");
    }
    await setDoc(doc(db, "users", user.uid, "state", "onboarding"), {
        complete: true,
        updatedAt: serverTimestamp(),
    });
}

// --- progress mirror (write + real-time read) --------------------------------

function deviceId(): string {
    const key = "manifold.deviceId";
    let id = localStorage.getItem(key);
    if (!id) {
        id = crypto.randomUUID?.() ?? `dev-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        localStorage.setItem(key, id);
    }
    return id;
}

/**
 * Write the derived progress snapshot for the signed-in user. Overwrites the
 * single `users/{uid}` document (a mirror, not an append log), stamping the
 * transport fields the security rules validate. Throws if no user is signed in or
 * the write is rejected.
 */
export async function writeProgress(data: ProgressData): Promise<void> {
    const { auth, db } = ensure();
    const user = auth.currentUser;
    if (!user) {
        throw new Error("writeProgress called with no signed-in user");
    }
    await setDoc(doc(db, "users", user.uid), {
        uid: user.uid,
        schemaVersion: 1,
        updatedAt: serverTimestamp(),
        platform: shellPlatform(),
        deviceId: deviceId(),
        appVersion: APP_VERSION,
        ...data,
    });
}

/**
 * Subscribe to the signed-in user's progress document in real time. `onChange`
 * fires with the remote snapshot (or null when none exists yet) on every write
 * from any device; `onError` surfaces a Firestore error (e.g. rules rejection)
 * rather than swallowing it. Returns an unsubscribe function.
 */
export function subscribeProgress(
    uid: string,
    onChange: (progress: RemoteProgress | null) => void,
    onError: (error: Error) => void,
): () => void {
    const { db } = ensure();
    return onSnapshot(
        doc(db, "users", uid),
        (snap) => onChange(snap.exists() ? (snap.data() as RemoteProgress) : null),
        (error) => onError(error),
    );
}

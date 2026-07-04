// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

/**
 * Manifold's Firebase web configuration.
 *
 * These values identify the Firebase project (`manifold-gre`) to the client SDK.
 * They are NOT secrets: a Firebase web apiKey is shipped in every web/app client
 * by design, and access is gated by Firestore security rules + Authorized Domains,
 * not by hiding this config (see Firebase docs on "is the apiKey a secret"). So
 * this module is committed and shared verbatim by the desktop shell, the Android
 * shell, and the web dashboard — one project, one config.
 *
 * The one genuine secret in the sync stack — the Google OAuth client secret used
 * by the desktop loopback sign-in — lives in `.env` (gitignored), never here.
 */

export interface FirebaseWebConfig {
    apiKey: string;
    authDomain: string;
    projectId: string;
    storageBucket: string;
    messagingSenderId: string;
    appId: string;
}

export const firebaseConfig: FirebaseWebConfig = {
    apiKey: "AIzaSyBI__PYNZ29WGUkk5nm6Y8Qay4sBQE-sAU",
    authDomain: "manifold-gre.firebaseapp.com",
    projectId: "manifold-gre",
    storageBucket: "manifold-gre.firebasestorage.app",
    messagingSenderId: "451162963698",
    appId: "1:451162963698:web:7a00e66f0866fab4709a6b",
};

/**
 * Fail loud if the config was blanked or left as a placeholder rather than
 * silently initializing a broken Firebase app (honors Manifold's no-silent-
 * fallback rule). Returns the config so callers can use it inline.
 */
export function requireFirebaseConfig(): FirebaseWebConfig {
    const missing = (Object.keys(firebaseConfig) as (keyof FirebaseWebConfig)[])
        .filter((k) => !firebaseConfig[k] || firebaseConfig[k].trim() === "");
    if (missing.length > 0) {
        throw new Error(
            `Firebase config is incomplete (missing: ${missing.join(", ")}). `
                + "Set ts/lib/manifold/firebase.config.ts from `firebase apps:sdkconfig web`.",
        );
    }
    return firebaseConfig;
}

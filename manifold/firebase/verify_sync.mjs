// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
//
// End-to-end verification of the Manifold progress mirror against the Firebase
// emulator suite (Auth + Firestore, using the REAL firestore.rules).
//
// Run it under the emulators, e.g. (from manifold/firebase/):
//   JAVA_HOME=/opt/homebrew/opt/openjdk@21 PATH="$JAVA_HOME/bin:$PATH" \
//   npx -y firebase-tools@latest emulators:exec --only auth,firestore \
//     --project manifold-gre \
//     "/path/to/out/extracted/node/bin/node verify_sync.mjs"
//
// It proves the four properties the design depends on:
//   1. real-time propagation: a write by one client is delivered to a second
//      client (a second "device") of the SAME user via onSnapshot;
//   2. cross-user denial: user B cannot read user A's progress document;
//   3. schema enforcement: an invalid snapshot (extra field) is rejected;
//   4. ownership: a user cannot write to another user's document.

import { deleteApp, initializeApp } from "firebase/app";
import {
    connectAuthEmulator,
    createUserWithEmailAndPassword,
    getAuth,
    signInWithEmailAndPassword,
} from "firebase/auth";
import {
    connectFirestoreEmulator,
    doc,
    getDoc,
    getFirestore,
    onSnapshot,
    serverTimestamp,
    setDoc,
} from "firebase/firestore";

const CONFIG = { apiKey: "emulator", projectId: "manifold-gre", authDomain: "localhost" };
const AUTH_HOST = "http://127.0.0.1:9399";
const FS_HOST = ["127.0.0.1", 8399];

let passed = 0;
let failed = 0;
function check(name, ok, detail = "") {
    if (ok) {
        passed += 1;
        console.log(`  PASS  ${name}`);
    } else {
        failed += 1;
        console.log(`  FAIL  ${name}${detail ? ` — ${detail}` : ""}`);
    }
}

function makeClient(label) {
    const app = initializeApp(CONFIG, label);
    const auth = getAuth(app);
    connectAuthEmulator(auth, AUTH_HOST, { disableWarnings: true });
    const db = getFirestore(app);
    connectFirestoreEmulator(db, FS_HOST[0], FS_HOST[1]);
    return { app, auth, db };
}

function validSnapshot(uid, deviceId) {
    return {
        uid,
        schemaVersion: 1,
        updatedAt: serverTimestamp(),
        platform: "web",
        deviceId,
        appVersion: "1.0.0",
        coverage: 0.42,
        totalIndependentReviews: 210,
        readinessState: "projected",
        memory: { present: true, value: 0.8, low: 0.6, high: 0.95 },
        performance: { present: true, value: 0.7, low: 0.5, high: 0.85 },
        readiness: {
            state: "projected",
            scaledPoint: 720,
            scaledLow: 700,
            scaledHigh: 740,
            confidence: "provisional",
            lapseRate: 0.1,
        },
        topics: [{
            id: "calc-limits",
            title: "Limits",
            area: "calculus",
            tier: "relearn",
            lockState: "in_progress",
            avgRecall: 0.8,
            performance: 0.7,
            coverage: 0.5,
        }],
    };
}

async function isDenied(promise) {
    try {
        await promise;
        return false;
    } catch (e) {
        return String(e?.code || e?.message || e).includes("permission-denied");
    }
}

async function main() {
    const emailA = `a-${Date.now()}@example.com`;
    const emailB = `b-${Date.now()}@example.com`;
    const password = "verify-password-123";

    // Two clients (two "devices") for user A, one client for user B.
    const a1 = makeClient("A1");
    const a2 = makeClient("A2");
    const b = makeClient("B");

    const credA = await createUserWithEmailAndPassword(a1.auth, emailA, password);
    const uidA = credA.user.uid;
    await signInWithEmailAndPassword(a2.auth, emailA, password); // same user, 2nd device
    const credB = await createUserWithEmailAndPassword(b.auth, emailB, password);
    const uidB = credB.user.uid;

    console.log(`\nManifold sync verification (uidA=${uidA.slice(0, 8)}…, uidB=${uidB.slice(0, 8)}…)\n`);

    // 1. Real-time propagation across two devices of the same user.
    const propagation = new Promise((resolve) => {
        let firstSkipped = false;
        const unsub = onSnapshot(doc(a2.db, "users", uidA), (snap) => {
            // The first callback is the initial (empty) state; wait for the write.
            if (!snap.exists()) {
                firstSkipped = true;
                return;
            }
            if (firstSkipped || snap.exists()) {
                unsub();
                resolve(snap.data());
            }
        });
    });
    await setDoc(doc(a1.db, "users", uidA), validSnapshot(uidA, "device-A1"));
    const received = await Promise.race([
        propagation,
        new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), 8000)),
    ]).catch((e) => ({ __error: e.message }));
    check(
        "real-time: device A2 receives device A1's write via onSnapshot",
        received && received.uid === uidA && received.totalIndependentReviews === 210,
        received?.__error ?? JSON.stringify(received)?.slice(0, 80),
    );

    // 2. Cross-user read denial.
    check(
        "security: user B cannot read user A's progress",
        await isDenied(getDoc(doc(b.db, "users", uidA))),
    );

    // 3. Schema enforcement: an extra/unknown field is rejected.
    const polluted = { ...validSnapshot(uidA, "device-A1"), isAdmin: true };
    check(
        "security: schema pollution (extra field) is rejected",
        await isDenied(setDoc(doc(a1.db, "users", uidA), polluted)),
    );

    // 4. Ownership: user A cannot write into user B's document.
    check(
        "security: user A cannot write user B's document",
        await isDenied(setDoc(doc(a1.db, "users", uidB), validSnapshot(uidB, "device-A1"))),
    );

    // 5. Owner can read their own document back.
    const own = await getDoc(doc(a1.db, "users", uidA));
    check("owner can read their own progress", own.exists() && own.data().uid === uidA);

    await Promise.all([deleteApp(a1.app), deleteApp(a2.app), deleteApp(b.app)]);

    console.log(`\n${passed} passed, ${failed} failed\n`);
    process.exit(failed === 0 ? 0 : 1);
}

main().catch((e) => {
    console.error("verification crashed:", e);
    process.exit(2);
});

# Mobile status: WS7 spike (D31 cap-breaker attempt)

> WS7 is the last phase. Its grading cap: no phone companion sharing the engine
> **and** syncing = 70% max. This note records exactly how far the mobile build got
> on this machine, with the real commands and their real output. It is honest by
> construction: no faked APK, no faked sync, no faked pass. Where something is
> blocked, the blocker is named and the command to clear it is given.
>
> **Owner:** this file only. No rslib/ts/build config was changed. The cross-compile
> below succeeds through a build-invocation flag, not a source or manifest edit.
>
> Companions: [`spec-mobile-sync.md`](spec-mobile-sync.md), [`sync.md`](sync.md),
> [`plan-buildout.md`](plan-buildout.md) WS7, decision **D31**.

## Verdict first

**The shared Rust engine (`rslib`, the `anki` crate, carrying the Manifold change)
cross-compiles cleanly for `aarch64-linux-android`.** That retires the single risk
the spec calls the make-or-break of mobile (`spec-mobile-sync.md` §9: getting the
modified `rslib` to build for Android).

**It is not shippable as a phone build tonight.** Three things are missing from this
machine and none can be honestly faked:

1. No AnkiDroid application and no JNI bridge crate (`rsdroid`) in this repo, so there
   is no Android app shell to host the engine and no `.so` to load.
2. No Java runtime, so the Android app build and the SDK packaging tools cannot run,
   so no APK can be produced here.
3. With no phone app, the two-way sync test (assignment 7b) has nothing to sync
   against, so it was not run and is not claimed.

Per **D31**, the fallback stands: ship the honest desktop build (capped at 70% for
the missing phone half) rather than a faked phone build. The engine cross-compile is
real progress toward the cap-breaker and is documented below so the remaining work is
a wiring job, not a research job.

## 1. Toolchain assessment

Checked on macOS (arm64, `aarch64-apple-darwin` host), repo at
`/Users/adambanks/Desktop/manifold`.

| Component                                                                         | State      | Detail                                                              |
| --------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| Rust target `aarch64-linux-android`                                               | Present    | `rustup target list --installed` lists it                           |
| Rust toolchain                                                                    | Present    | 1.92.0, pinned by `rust-toolchain.toml`                             |
| `cargo-ndk`                                                                       | Present    | 4.1.2, at `~/.cargo/bin/cargo-ndk`                                  |
| Android NDK                                                                       | Present    | r29 (`29.0.14206865`) under the Homebrew SDK                        |
| Android SDK (cmdline-tools, platform-tools, emulator, build-tools, system-images) | Present    | `/opt/homebrew/share/android-commandlinetools`                      |
| Generated build inputs (`protoc`, `descriptors.bin`, `_fluent.py`, `ftl.ts`)      | Present    | already built in `out/` by the green desktop build                  |
| Free disk                                                                         | OK         | ~116 GiB                                                            |
| NDK env vars (`ANDROID_NDK_HOME`, `ANDROID_HOME`)                                 | Not set    | exported manually for the build; see below                          |
| Java runtime                                                                      | **Absent** | `java -version` returns "Unable to locate a Java Runtime"           |
| `adb`, `emulator`, `gradle` on PATH                                               | Absent     | SDK binaries exist on disk but are not wired to PATH, and need Java |
| AnkiDroid app checkout or submodule                                               | **Absent** | see §3                                                              |

Someone provisioned most of the Android toolchain here (NDK, `cargo-ndk`, SDK). The
gaps are a Java runtime and the AnkiDroid app itself.

## 2. Cross-compile attempt (the real output)

The NDK path used for every build below:

```bash
export ANDROID_NDK_HOME=/opt/homebrew/share/android-commandlinetools/ndk/29.0.14206865
export ANDROID_HOME=/opt/homebrew/share/android-commandlinetools
```

### 2a. The command from the plan, as written

```bash
cargo ndk -t arm64-v8a build -p anki --target aarch64-linux-android
```

Result: the entire dependency tree compiled (200+ crates, including native C such as
`libsqlite3-sys`, `zstd-sys`, `zlib-rs`, and the crypto stack), then the final `anki`
crate failed with 9 errors, all the same root cause:

```
error[E0432]: unresolved import `tokio::io::AsyncReadExt`
  --> rslib/src/sync/request/header_and_stream.rs:20:5
   note: the item is gated behind the `io-util` feature
error[E0599]: no method named `write_all` found for struct `tokio::fs::File`
  --> rslib/src/updates.rs:72:14
error[E0599]: no method named `flush` found for struct `tokio::fs::File`
  --> rslib/src/updates.rs:79:10
error: could not compile `anki` (lib) due to 9 previous errors
```

### 2b. Diagnosis: this is not a mobile problem

Running the host equivalent reproduces the identical 9 errors:

```bash
cargo build -p anki   # aarch64-apple-darwin, no Android involved -> same 9 errors
```

Root cause is Cargo feature unification, not cross-compilation. `rslib` uses
`tokio::io` extension traits (`AsyncReadExt`, `AsyncWriteExt`, and `read_to_end`,
`write_all`, `flush`, `take`) that live behind tokio's `io-util` feature. The
workspace declares tokio with `["fs", "rt-multi-thread", "macros", "signal"]` and
`tokio-util` with `["io"]`; neither turns on tokio's own `io-util`. In a full build or
a test build, `io-util` arrives by unification from other crates (for example the
dev-dependency `reqwest` with `native-tls`, which pulls `hyper-tls` then
`hyper-util` `client-legacy` then tokio `io-util`). Building `anki` alone as a library,
without dev-dependencies, leaves `io-util` off, so it fails the same way on both
platforms.

### 2c. The command that succeeds

Enabling that one feature on the invocation, with no file edited, compiles the engine
for Android:

```bash
cargo ndk -t arm64-v8a build -p anki --features tokio/io-util --target aarch64-linux-android
```

Output:

```
 Building arm64-v8a (aarch64-linux-android)
Compiling anki v0.0.0 (/Users/adambanks/Desktop/manifold/rslib)
Compiling axum v0.8.4
Compiling reqwest v0.12.23
 Finished `dev` profile [unoptimized + debuginfo] target(s) in 14.45s
```

### 2d. Artifact and proof it is real ARM64

```
target/aarch64-linux-android/debug/libanki.rlib          104 MB, "current ar archive"
target/aarch64-linux-android/debug/deps/*.rlib           335 crates compiled for Android
```

A sampled native object from a C dependency confirms the architecture:

```
$ file target/aarch64-linux-android/debug/build/zstd-sys-*/out/*zstd_compress_sequences.o
ELF 64-bit LSB relocatable, ARM aarch64, version 1 (SYSV), not stripped
```

So `rslib` and every native dependency it needs produce real ARM64 Android objects.
The Manifold engine code (`rslib/src/manifold/`, 6 source files) is inside that
`libanki.rlib`.

### 2e. Note on the `.rlib`

`libanki.rlib` is a Rust static archive, not a loadable Android library. `rslib`
declares no `crate-type`, so it emits an `rlib` only. A phone loads a `cdylib` `.so`.
The only `cdylib` in this workspace is `pylib/rsbridge` (the desktop Python
extension). Producing the Android `.so` needs the JNI bridge described in §4, which is
not in this repo. The cross-compile proves the code and its dependencies build for the
target; it does not by itself produce a phone-loadable binary.

## 3. AnkiDroid: present versus absent

Present in this repo (upstream Anki's Android-facing backend, inside `rslib`):

- `rslib/src/ankidroid/service.rs`, `rslib/src/ankidroid/db.rs`
- `rslib/src/backend/ankidroid.rs`
- `proto/anki/ankidroid.proto`

These are the RPC and DB-proxy surface that an AnkiDroid app calls into. They are part
of the engine that just cross-compiled, so the phone-facing API is already on the
Android build.

Absent (confirmed):

- No AnkiDroid application. No `.gradle`/`.gradle.kts` anywhere, no `com.ichi2`
  package, and no AnkiDroid entry in `.gitmodules` (submodules are only the two `ftl`
  translation repos and the two Briefcase desktop templates).
- No JNI bridge. The `jni` crate is not in `Cargo.lock`, and there is no Android
  `cdylib` crate, so nothing here builds `librsdroid.so`.

## 4. Concrete path to finish

The engine builds. The remaining work is assembly against the AnkiDroid projects,
which live outside this repo. Steps, in order, with the commands.

### Step 0: install a Java runtime (unblocks the Android app build and the SDK tools)

```bash
brew install --cask temurin@17
export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
```

Without this, `gradle` and `sdkmanager` cannot run, so no APK can be assembled on this
machine regardless of the rest.

### Step 1: make `cargo build -p anki` self-contained (recommended one-line fix)

Add `"io-util"` to the workspace tokio features in `Cargo.toml` so the engine builds
standalone without the invocation flag from §2c:

```toml
# Cargo.toml (workspace)
tokio = { version = "1.45", features = ["fs", "rt-multi-thread", "macros", "signal", "io-util"] }
```

This is additive and cannot change the desktop build, which already resolves `io-util`
by unification. It was left unapplied tonight to keep this spike to the one file it
owns; apply it when the mobile build is wired for real.

### Step 2: obtain AnkiDroid and its Rust backend bridge

AnkiDroid is split across two AGPL repositories:

- `github.com/ankidroid/Anki-Android`: the Kotlin/Java app and its gradle build.
- `github.com/ankidroid/Anki-Android-Backend` (the `rsdroid` bridge): a Rust crate
  that depends on the upstream `anki` crate (this `rslib`), adds the JNI layer, sets
  `crate-type = ["cdylib"]`, and builds `librsdroid.so` with `cargo-ndk` (the same
  tool used in §2). It packages the `.so` into an `.aar` the app consumes.

```bash
git clone https://github.com/ankidroid/Anki-Android
git clone https://github.com/ankidroid/Anki-Android-Backend
```

### Step 3: point the bridge at this repo's engine

The backend bridge pulls the Anki engine in as a git submodule and depends on it by
path (`anki = { path = "../anki/rslib" }` or similar in `rsdroid/Cargo.toml`). Anki is
`publish = false`, so it is not on crates.io and a `[patch.crates-io]` override does
not apply. Repoint the path dependency at this checkout instead, so the Manifold change
ships to the phone by construction rather than by a parallel rewrite. Two ways:

```bash
# Option A: replace the backend's anki submodule contents with this fork
#   (align the checkout to the Anki release the backend expects, then copy/symlink).
# Option B: edit the path dependency in the bridge manifest to point here:
```

```toml
# Anki-Android-Backend rsdroid/Cargo.toml
anki = { path = "/Users/adambanks/Desktop/manifold/rslib" }
anki_proto = { path = "/Users/adambanks/Desktop/manifold/rslib/proto" }
```

Match the bridge's expected engine version first to avoid a proto or API drift; if the
upstream backend tracks a different Anki release than this fork's base, align to that
tag before repointing.

### Step 4: build the `.so` and the app

From the backend bridge, build the Android library for the phone ABI (this is the
step §2 already proved works for the engine, now producing a `cdylib` instead of an
`rlib`):

```bash
export ANDROID_NDK_HOME=/opt/homebrew/share/android-commandlinetools/ndk/29.0.14206865
cargo ndk -t arm64-v8a -o ./rsdroid/src/main/jniLibs build --release   # emits librsdroid.so
./gradlew :rsdroid:assembleRelease                                     # packages the .aar
```

Then build the app against that `.aar`:

```bash
# in Anki-Android
./gradlew assembleDebug     # or assembleRelease with a signing config for a real APK
adb install -r AnkiDroid/build/outputs/apk/**/AnkiDroid-*.apk
```

### Step 5: reuse the dashboard in a WebView

Manifold's dashboard is a mediasrv page (`ts/routes/manifold`, the `dashboard.html`
surface in `spec-mobile-sync.md` §8). AnkiDroid already embeds mediasrv-backed
WebViews. Host the same Manifold page in an AnkiDroid WebView so the three scores plus
the give-up rule render from the same code as desktop (D8, D11), rather than a second
UI. No engine change is needed; the scores come from the RPCs already in the Android
build (§3).

### Step 6: run the two-way sync test (assignment 7b) against the self-hosted server

Sync needs no phone-specific code; it reuses Anki's protocol against the self-hosted
server documented in [`sync.md`](sync.md). Once the app runs on a device or emulator:

```bash
# start the server (from sync.md)
SYNC_USER1=demo:demo SYNC_HOST=0.0.0.0 SYNC_PORT=27913 SYNC_BASE=/tmp/anki-sync \
    PYTHONPATH=out/pylib out/pyenv/bin/python -m anki.syncserver
```

Point both desktop and the AnkiDroid build at `http://<host-lan-ip>:27913/` and sign
in as `demo` on both. Then run the test from `spec-mobile-sync.md` §11:

1. Review 10 cards on the phone offline and 10 different cards on desktop offline.
2. Reconnect and sync both. All 20 land exactly once, none lost or doubled.
3. Review the same card on both offline, then sync. The conflict rule from
   [`sync.md`](sync.md) picks a single deterministic winner: the later real-world
   review timestamp wins, normalized to the server clock, and the loser stays in the
   revlog without double-counting the schedule.

Record the run for the deliverable. Do not report a pass until this has actually run
end to end on a device.

## 5. What is proven, what is not

Proven on this machine tonight:

- The Android toolchain is complete except for Java: NDK r29, `cargo-ndk` 4.1.2, and
  the `aarch64-linux-android` Rust target all work together.
- `rslib` (the shared engine with the Manifold change) and its full native dependency
  tree cross-compile to ARM64 Android. Exact command in §2c, artifact in §2d.
- The `io-util` failure from the plan's literal command is a feature-unification
  quirk, reproducible on the desktop host, not a mobile blocker.

Not done, and not faked:

- No `librsdroid.so`, because the JNI bridge crate is not in this repo (§3).
- No APK, because there is no AnkiDroid app project here and no Java runtime to build
  one (§1, §3).
- No on-device review and no two-way sync run, because there is no phone app to run
  them on (§4 step 6).

**Not shippable as a phone build tonight if the AnkiDroid app plus its JNI bridge and
a Java runtime are absent, which on this machine they are.** The desktop build stands
on its own at the documented 70% cap (D31). The hard part of the cap-breaker, building
the shared engine for Android, is done and reproducible; the rest is the wiring in §4.

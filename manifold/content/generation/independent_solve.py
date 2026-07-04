# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""independent_solve.py — blind cross-solve gate that closes the stem-faithfulness
hole in Manifold's verifier (WS1, D32 gate 5).

**Why this exists.** :mod:`verify` proves internal consistency: that exactly one of
the five choices matches the item's own ``check`` block, and that it is the claimed
one. For the *recompute* check types (``det``/``rank``/``eigen``/``count``+brute/
``prob_exact``+brute/``antiderivative``/``smt``) the check derives ground truth from a
spec, so a pass is strong. But for the *stated-value* types (``numeric`` and
``equiv``) the ``check.expr`` **is the answer the generator asserts** — the SymPy pass
is then tautological with respect to the *stem*: a model that miswrites its own
problem produces a self-consistent-but-wrong (stem, choices, check) triple that sails
through. ``crosscheck.ts`` already blind-solves items, but it was scoped to the
*undecidable tail* on the assumption a "machine-proved" item needs no second opinion.
That assumption is false for the stated-value types. This module applies the same
blind solve to *positively-verified* items so the runtime never serves, and the bank
never anchors a lesson on, an item whose stem an independent solver does not agree
resolves to the claimed choice.

**What it does.** A *different, stronger* model (default ``gpt-4o`` — deliberately not
the cheap generator) solves each item **blind**: given only the stem and the five
choices, never the ``solution``, ``check``, ``correct_index``, or rationales. It votes
``samples`` times; agreement requires a >=2-way (or, for one sample, a single) blind
consensus that **also matches** the item's ``correct_index``. Anything else is a
disagreement — the item is not confirmed. Mirrors ``crosscheck.ts`` exactly so the two
paths give the same verdict.

**Honesty / no fabrication (user rule + D32).** This gate never invents a verdict and
never silently passes an unconfirmable item. If the model call cannot run (no key,
network down, or the solver returns garbage), the caller is told loudly via a raised
error and must abstain / skip — it must **never** serve or bank an unconfirmed item.
The correctness signal is the *disagreement of an independent solver with the label*,
never the drafting model's say-so.

The model call is injectable. In production it is a direct structured-output call to an
OpenAI-compatible chat API. For tests and offline e2e, point ``MANIFOLD_SOLVE_FIXTURES``
at a JSON file (a deterministic **test double** that replaces only the model call — the
agreement logic still runs), or pass a ``solve`` callable directly to
:func:`check_agreement`. Shares the generation venv (see ``verify.py`` header).
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import verify  # noqa: E402  (import after sys.path fix-up; reused for value comparison)

# A deliberately different / stronger model than the cheap generator, so the solve is
# genuinely independent (a self-check by the same weak model would be worthless).
DEFAULT_SOLVE_MODEL = "gpt-4o"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_SAMPLES = 2  # independent blind solves per item (mirrors crosscheck.ts)
DEFAULT_REQUEST_TIMEOUT = 45.0
DEFAULT_SOLVE_ATTEMPTS = 3  # per-call transient retries before giving up
CHOICE_COUNT = 5
# The solver may report that its computed answer equals NONE of the listed choices
# (i.e. the item is broken: the true answer isn't even an option). That is a decisive
# DISAGREEMENT, never a match — it catches generator errors where the real answer is
# absent from the choices, which "force-pick an index 0-4" would miss.
NONE_INDEX = -1

# A blind solver is a genuine second opinion only for check types whose SymPy/Z3 pass
# does not already derive ground truth from a spec. These two restate the answer, so
# their "proof" is tautological w.r.t. the stem and MUST be cross-solved.
TAUTOLOGICAL_CHECK_TYPES = frozenset({"numeric", "equiv"})


# --- errors ---------------------------------------------------------------------


class SolverConfigError(Exception):
    """A setup/programming error (bad request, malformed fixtures). Fails loudly."""


class SolverAuthError(Exception):
    """The key was rejected (401/403). Retrying will not help; caller abstains no_key."""


class SolverTransientError(Exception):
    """A retryable network/server condition (offline, timeout, 429, 5xx)."""


class SolverProtocolError(Exception):
    """The solver returned unusable output (no content, bad JSON, out-of-range index)."""


# --- value matching (derive the vote from the solver's COMPUTED answer) ----------
# The model computes reliably but picks indices lazily (it will force-pick the nearest
# choice when the true answer is absent). So we don't trust its chosen_index: we take
# its computed_answer and match it to the choices ourselves with SymPy (numeric AND
# symbolic, via verify.py). If it matches no choice, the vote is NONE_INDEX — which is
# exactly how "the true answer isn't even a choice" (the 20-not-in-choices bug) is caught.


_VALUE_MATCH_RTOL = 1e-3  # tolerate human rounding (e.g. 0.707 vs sqrt(2)/2) without
# collapsing GRE choices, which are separated by far more than 0.1%.


def _values_match(a_text: str, b_text: str) -> bool:
    """True iff two answer strings denote the same value (numeric or symbolic).

    Numeric comparison is loose (``_VALUE_MATCH_RTOL``) so a solver's rounded decimal
    still matches an exact choice; symbolic answers use SymPy equivalence. Anything
    unparseable falls back to normalized text equality. Never raises."""
    try:
        a = verify._sympify(a_text)
        b = verify._sympify(b_text)
    except Exception:
        return a_text.strip() == b_text.strip()
    try:
        if a.free_symbols or b.free_symbols:
            try:
                return verify._equivalent(a, b)
            except Exception:
                return a_text.strip() == b_text.strip()
        av = verify._to_complex(a)
        bv = verify._to_complex(b)
        return abs(av - bv) <= _VALUE_MATCH_RTOL * (1 + abs(bv))
    except Exception:
        return a_text.strip() == b_text.strip()


def _vote_from_computed(item: dict[str, Any], computed: str) -> int:
    """Index of the choice equal to the solver's computed answer, or NONE_INDEX."""
    for i, choice in enumerate(item["choices"]):
        if _values_match(computed, str(choice)):
            return i
    return NONE_INDEX


def _derive_vote(item: dict[str, Any], sample: Any) -> int:
    """Turn one solver result into a vote (a choice index, or NONE_INDEX for 'none').

    The real solver returns ``{"computed_answer", "chosen_index"}``: we prefer the
    value (matched to the choices ourselves) so a lazy/forced index cannot mask a
    wrong or absent answer, falling back to the model's index only if the computed
    value is unusable. A plain int (test doubles / fixtures) is trusted as the index.
    """
    if isinstance(sample, bool):
        raise SolverProtocolError(f"solver returned a bool, not an index/result: {sample!r}")
    if isinstance(sample, int):
        if not NONE_INDEX <= sample < CHOICE_COUNT:
            raise SolverProtocolError(f"solver returned out-of-range index {sample!r}")
        return sample
    if isinstance(sample, dict):
        computed = sample.get("computed_answer")
        if isinstance(computed, str) and computed.strip():
            return _vote_from_computed(item, computed)
        idx = sample.get("chosen_index")
        if isinstance(idx, int) and not isinstance(idx, bool) and NONE_INDEX <= idx < CHOICE_COUNT:
            return idx
        raise SolverProtocolError(f"solver result has no usable computed_answer or chosen_index: {sample!r}")
    raise SolverProtocolError(f"solver returned unexpected type {type(sample).__name__}")


# --- prompt (kept faithful to crosscheck.ts solvePrompt) ------------------------


_SOLVE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "computed_answer": {"type": "string"},
        "chosen_index": {"type": "integer", "minimum": -1, "maximum": 4},
        "reasoning": {"type": "string"},
    },
    "required": ["computed_answer", "chosen_index", "reasoning"],
}


def _solve_prompt(item: dict[str, Any]) -> str:
    lettered = "\n".join(f"{i}: {choice}" for i, choice in enumerate(item["choices"]))
    return "\n".join(
        [
            "Solve this GRE Mathematics multiple-choice problem. Choose the single best answer.",
            "Answer independently from first principles; do not assume any listed order is correct.",
            "",
            f"Problem: {item['stem']}",
            "",
            "Choices (0-indexed):",
            lettered,
            "",
            "Work out the answer yourself FIRST, from first principles.",
            "Return: computed_answer = your own final value as a bare number or exact "
            "expression (e.g. \"20\", \"sqrt(2)/2\", \"3/8\"), independent of the choices; "
            "then chosen_index = the 0-based index of the choice equal to it, or -1 if NONE "
            "of the choices equals your computed answer (do NOT force-pick the nearest one); "
            "plus brief reasoning.",
        ]
    )


# --- OpenAI solver (mirrors serve_live._make_openai_generator plumbing) ---------


def _make_openai_solver(cfg: "SolveConfig") -> Callable[[dict[str, Any]], int]:
    url = f"{cfg.base_url.rstrip('/')}/chat/completions"

    def solve(item: dict[str, Any]) -> int:
        body = {
            "model": cfg.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a careful GRE Mathematics solver. Work from first principles.",
                },
                {"role": "user", "content": _solve_prompt(item)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "blind_solve", "schema": _SOLVE_SCHEMA, "strict": False},
            },
        }
        data = json.dumps(body).encode("utf-8")
        last_exc: Exception | None = None
        for attempt in range(1, DEFAULT_SOLVE_ATTEMPTS + 1):
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg.api_key}"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=cfg.request_timeout) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                text = exc.read().decode("utf-8", "replace")
                if exc.code in (401, 403):
                    raise SolverAuthError(f"HTTP {exc.code}: {text[:200]}") from exc
                if exc.code == 429 or exc.code >= 500:
                    last_exc = SolverTransientError(f"HTTP {exc.code}: {text[:200]}")
                    if attempt < DEFAULT_SOLVE_ATTEMPTS:
                        time.sleep(0.4 * attempt)
                        continue
                    raise last_exc from exc
                raise SolverProtocolError(f"HTTP {exc.code}: {text[:200]}") from exc
            except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
                last_exc = SolverTransientError(f"network error: {exc}")
                if attempt < DEFAULT_SOLVE_ATTEMPTS:
                    time.sleep(0.4 * attempt)
                    continue
                raise last_exc from exc
            content = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content")
            if not isinstance(content, str) or not content.strip():
                raise SolverProtocolError("solver returned no content")
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise SolverProtocolError(f"solver output was not valid JSON: {exc}") from exc
            idx = parsed.get("chosen_index")
            if not isinstance(idx, int) or isinstance(idx, bool) or not NONE_INDEX <= idx < CHOICE_COUNT:
                raise SolverProtocolError(f"solver returned invalid index {idx!r}")
            computed = parsed.get("computed_answer")
            # Return the computed value + the model's index; check_agreement prefers the
            # value (matched by us) and falls back to the index only if it is unusable.
            return {"computed_answer": computed if isinstance(computed, str) else None, "chosen_index": idx}
        # Unreachable in practice (loop either returns or raises), but be explicit.
        raise last_exc or SolverTransientError("blind solve failed")

    return solve


# --- fixtures solver (test double: replaces ONLY the model call) ----------------


def _make_fixture_solver(fixtures: dict[str, Any]) -> Callable[[dict[str, Any]], int]:
    """A deterministic stand-in for the blind solver, for tests / offline e2e.

    Supported shapes (all explicit, none is a silent fallback):
      * ``{"oracle": "trust_label"}`` — a perfect solver: returns the item's own
        ``correct_index`` (so it agrees). Keeps the happy-path e2e green without a key.
      * ``{"oracle": "always_wrong"}`` — returns a different index (so it disagrees),
        to exercise the "verified but solver disagrees -> abstain" path.
      * ``{"by_skill": {"<skill_id>": <index>}, "default": <index>}`` — explicit picks.
    """
    oracle = fixtures.get("oracle")
    by_skill = fixtures.get("by_skill") or {}
    default = fixtures.get("default")
    if not isinstance(by_skill, dict):
        raise SolverConfigError("solve fixtures 'by_skill' must be an object")

    def solve(item: dict[str, Any]) -> int:
        claimed = item.get("correct_index")
        if oracle == "trust_label":
            if not isinstance(claimed, int):
                raise SolverConfigError("trust_label oracle needs an integer correct_index")
            return claimed
        if oracle == "always_wrong":
            if not isinstance(claimed, int):
                raise SolverConfigError("always_wrong oracle needs an integer correct_index")
            return (claimed + 1) % CHOICE_COUNT
        sid = item.get("skill_id")
        if sid in by_skill:
            return int(by_skill[sid])
        if default is not None:
            return int(default)
        raise SolverConfigError(
            f"no fixture solve for skill {sid!r} and no 'oracle'/'default' given"
        )

    return solve


def _load_fixtures(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise SolverConfigError(f"MANIFOLD_SOLVE_FIXTURES points to a missing file: {path}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SolverConfigError(f"MANIFOLD_SOLVE_FIXTURES is not valid JSON ({path}): {exc}") from exc
    if not isinstance(data, dict):
        raise SolverConfigError(f"MANIFOLD_SOLVE_FIXTURES must be a JSON object ({path})")
    return data


# --- config ---------------------------------------------------------------------


class SolveConfig:
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str,
        fixtures_path: str | None,
        samples: int,
        request_timeout: float,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.fixtures_path = fixtures_path
        self.samples = samples
        self.request_timeout = request_timeout

    @classmethod
    def from_env(cls) -> "SolveConfig":
        key = os.environ.get("OPENAI_API_KEY")
        fixtures = os.environ.get("MANIFOLD_SOLVE_FIXTURES")
        samples_raw = os.environ.get("MANIFOLD_SOLVE_SAMPLES")
        try:
            samples = int(samples_raw) if samples_raw else DEFAULT_SAMPLES
        except ValueError as exc:
            raise SolverConfigError(f"MANIFOLD_SOLVE_SAMPLES must be an integer: {samples_raw!r}") from exc
        if samples < 1:
            raise SolverConfigError(f"MANIFOLD_SOLVE_SAMPLES must be >= 1, got {samples}")
        return cls(
            api_key=key.strip() if key and key.strip() else None,
            # A dedicated knob so the solver can differ from the generator's OPENAI_MODEL.
            model=os.environ.get("MANIFOLD_SOLVE_MODEL") or DEFAULT_SOLVE_MODEL,
            base_url=os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL,
            fixtures_path=fixtures.strip() if fixtures and fixtures.strip() else None,
            samples=samples,
            request_timeout=DEFAULT_REQUEST_TIMEOUT,
        )


def select_solver(cfg: SolveConfig) -> tuple[Callable[[dict[str, Any]], int] | None, str | None]:
    """Choose the solve source, or return (None, reason). No silent fallback: fixtures
    (test double) if set, else the real model if a key is present, else unavailable."""
    if cfg.fixtures_path:
        return _make_fixture_solver(_load_fixtures(cfg.fixtures_path)), None
    if cfg.api_key:
        return _make_openai_solver(cfg), None
    return None, "no_key"


# --- the gate -------------------------------------------------------------------


def needs_cross_solve(item: dict[str, Any]) -> bool:
    """True iff this item's check type is tautological w.r.t. the stem and therefore
    REQUIRES a blind cross-solve. Recompute types (matrix/brute/smt/antiderivative)
    derive truth from a spec, so a verify pass already implicates the stem via that
    spec; the stated-value types (numeric/equiv) do not."""
    check_type = (item.get("check") or {}).get("type")
    return check_type in TAUTOLOGICAL_CHECK_TYPES


def check_agreement(
    item: dict[str, Any],
    *,
    config: SolveConfig | None = None,
    solve: Callable[[dict[str, Any]], int] | None = None,
    samples: int | None = None,
) -> dict[str, Any]:
    """Blind-solve ``item`` ``samples`` times and decide whether an independent solver
    agrees with its ``correct_index``.

    Returns a verdict dict ``{agreed, chosen_index, claimed_index, votes, samples,
    model, reason}``. Raises :class:`SolverAuthError` / :class:`SolverTransientError` /
    :class:`SolverProtocolError` / :class:`SolverConfigError` when the solve itself
    could not run — the caller MUST treat that as "unconfirmed" (abstain / skip),
    never as a pass.
    """
    choices = item.get("choices")
    if not isinstance(choices, list) or len(choices) != CHOICE_COUNT:
        raise SolverConfigError("item must have exactly 5 choices to cross-solve")
    stem = item.get("stem")
    if not isinstance(stem, str) or not stem.strip():
        raise SolverConfigError("item must have a non-empty stem to cross-solve")
    claimed = item.get("correct_index")
    if not isinstance(claimed, int) or isinstance(claimed, bool):
        raise SolverConfigError("item must have an integer correct_index to cross-solve")

    cfg = config or SolveConfig.from_env()
    n = samples if samples is not None else cfg.samples
    if n < 1:
        raise SolverConfigError(f"samples must be >= 1, got {n}")

    solver = solve
    model_name = "injected"
    if solver is None:
        solver, reason = select_solver(cfg)
        if solver is None:
            # No key and no fixtures: we cannot independently confirm. Fail loud so the
            # caller abstains rather than serving an unconfirmed item.
            raise SolverAuthError(
                "cannot cross-solve: OPENAI_API_KEY is not set and no MANIFOLD_SOLVE_FIXTURES "
                "were provided (reason: " + (reason or "no_key") + ")"
            )
        model_name = cfg.model

    # Each solver result -> a vote (value-matched to the choices, not the model's own
    # index pick). solver(...) may raise (auth/transient/protocol): propagate loudly.
    # The samples are independent, so run them concurrently to cut cross-solve latency
    # (order does not affect the vote tally); both the OpenAI and fixture solvers are
    # thread-safe (independent calls / pure functions). f.result() re-raises loudly.
    if n == 1:
        votes: list[int] = [_derive_vote(item, solver(item))]
    else:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=n) as pool:
            futures = [pool.submit(solver, item) for _ in range(n)]
            votes = [_derive_vote(item, f.result()) for f in futures]
    counts = Counter(votes)
    modal_index, modal_count = counts.most_common(1)[0]
    enough_agree = modal_count >= min(2, n)
    matches_claim = modal_index == claimed
    agreed = enough_agree and matches_claim

    if not enough_agree:
        reason = f"no {min(2, n)}-way agreement among blind solves (votes {votes})"
    elif modal_index == NONE_INDEX:
        reason = f"blind solver: computed answer matches NONE of the listed choices (votes {votes})"
    elif not matches_claim:
        reason = f"blind consensus index {modal_index} != claimed {claimed} (votes {votes})"
    else:
        reason = f"{modal_count}/{n} blind solves agree with claimed index {claimed}"

    return {
        "agreed": agreed,
        "chosen_index": modal_index if enough_agree else None,
        "claimed_index": claimed,
        "votes": votes,
        "samples": n,
        "model": model_name,
        "reason": reason,
    }


# --- CLI (audit a single item; handy for spot checks) ---------------------------


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        raise SystemExit("usage: independent_solve.py <item.json>")
    with open(argv[0], encoding="utf-8") as handle:
        item = json.load(handle)
    try:
        verdict = check_agreement(item)
    except (SolverAuthError, SolverTransientError, SolverProtocolError, SolverConfigError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    return 0 if verdict["agreed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

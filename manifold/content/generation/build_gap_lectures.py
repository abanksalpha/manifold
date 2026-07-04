# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""build_gap_lectures.py — lectures for the conceptual teach skills that have NO
verified banked problem (Task 1 / Task 3, owner decision "lectures-only").

The 36-ish teach skills in ``teach_bank_gaps.jsonl`` (subspace tests, group
classification, "which must be true", Cauchy-Riemann, ...) are not a single
machine-checkable computation, so the pipeline cannot bank a verified MCQ for
them (they honestly abstain -> content_pending). The owner's decision: give each a
grounded LECTURE (so every New teach skill is taught) but NO auto-unverifiable
problem. This builder authors those lectures.

Grounding, not fabrication: each lecture teaches STANDARD, universally-accepted
mathematics (a competent mathematician can verify every line) with a canonical,
textbook example, and carries a citation to a real, openly-licensed reference for
the topic (Hefferon's Linear Algebra, Judson's Abstract Algebra, OpenStax Calculus,
Trench's ODEs, Grinstead & Snell, Wikipedia). No pirated/copyrighted content is
used or bundled. Every lecture's math is delimited LaTeX, validated by the same
gate the served problems use (``serve_live._validate_display_latex``).

Resumable: authored lectures are appended to ``lectures.gaps.items.jsonl``; a re-run
tops up only the still-missing ones. The result is MERGED into ``lectures.json``
alongside the bank-anchored lectures (never overwriting them).

Requires OPENAI_API_KEY. Run (repo root, key loaded):
    set -a && source .env && set +a
    manifold/content/generation/.venv/bin/python \
        manifold/content/generation/build_gap_lectures.py --concurrency 4
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import serve_live  # noqa: E402  (reuse config, LaTeX gate, error taxonomy)

GAPS_PATH = SCRIPT_DIR / "teach_bank_gaps.jsonl"
SEED_DECK = SCRIPT_DIR.parents[0] / "seed_deck.json"
LECTURES_OUT = SCRIPT_DIR.parents[0] / "lectures" / "lectures.json"

# Real, openly-licensed references per topic, for "Further reading" grounding. These
# are cited by name only (no invented page numbers or quotes); the lecture teaches
# standard math and points here for a fuller treatment. Not bundled, not scraped.
_GAP_SOURCES: dict[str, str] = {
    "vector_spaces": "Hefferon, Linear Algebra (open, CC BY-SA; hefferon.net)",
    "linear_algebra_core": "Hefferon, Linear Algebra (open, CC BY-SA; hefferon.net)",
    "eigen": "Hefferon, Linear Algebra (open, CC BY-SA; hefferon.net)",
    "group_theory": "Judson, Abstract Algebra: Theory and Applications (open, GFDL; abstract.ups.edu)",
    "complex_analysis": "Wikipedia: Cauchy-Riemann equations / Liouville's theorem (CC BY-SA)",
    "differential_equations": "Trench, Elementary Differential Equations (open; digitalcommons.trinity.edu)",
    "multivariable_diff": "OpenStax Calculus Volume 3 (CC BY; openstax.org)",
    "multivariable_int": "OpenStax Calculus Volume 3 (CC BY; openstax.org)",
    "vector_calc": "OpenStax Calculus Volume 3 (CC BY; openstax.org)",
    "combinatorics": "Wikipedia: Stars and bars / Surjection (CC BY-SA)",
    "probability": "Grinstead & Snell, Introduction to Probability (open, GFDL)",
}
_DEFAULT_SOURCE = "Wikipedia (CC BY-SA)"

_LECTURE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {"title": {"type": "string"}, "lecture_latex": {"type": "string"}},
    "required": ["title", "lecture_latex"],
}


def _system_prompt() -> str:
    return "\n".join(
        [
            "You are an expert GRE Mathematics Subject Test tutor writing a SHORT lecture that",
            "teaches ONE conceptual skill to a student about to face problems on it. This skill",
            "is NOT a single plug-and-chug computation (it is a test/classification/'which must be",
            "true' idea), so teach the METHOD with a canonical, textbook-standard worked example.",
            "",
            "Write three brief movements as flowing prose (you may name them inline):",
            "1. Method + when to use it: the criterion or test and the cue that triggers it.",
            "2. Worked example: ONE small, standard, correct example applying the method end to end.",
            "   Use clean numbers and rigorous reasoning; state the conclusion explicitly.",
            "3. Key takeaway: one or two sentences the student carries to the next problem.",
            "",
            "Hard requirements:",
            "- Teach ONLY standard, universally-accepted mathematics: every line must be correct and",
            "  checkable by a competent mathematician. Do NOT invent theorems, values, or edge cases.",
            "- Write ALL mathematics as LaTeX inside delimiters: \\( ... \\) inline and \\[ ... \\]",
            "  displayed. Use standard TeX macros (\\frac{a}{b}, \\sqrt{x}, x^{2}, \\cdot, \\pi, \\sin,",
            "  \\le, \\to, \\begin{bmatrix}...\\end{bmatrix}); keep ordinary words as plain prose OUTSIDE",
            "  the delimiters. Do NOT use $...$ math mode and do NOT paste raw Unicode math glyphs (no",
            "  x as a times sign, no middle dot, no radical sign, no superscript digits, no minus-sign",
            "  glyph, no <=/>= glyphs, no Greek letters as glyphs) — write each as its TeX macro. Every",
            "  \\( closes with \\) and every \\[ with \\], with balanced { } braces.",
            "- Do NOT use Markdown or any markup: no '#'/'##'/'###' headings, no '*' or '**' emphasis,",
            "  no backticks, no bullet-list syntax. Separate the movements with a blank line.",
            "- Keep it tight: a few short paragraphs. The title is a short plain-text noun phrase",
            "  naming the method (no LaTeX).",
            "- Return structured JSON matching the schema: {\"title\": ..., \"lecture_latex\": ...}.",
        ]
    )


def _user_prompt(skill: dict[str, Any], source: str) -> str:
    return "\n".join(
        [
            f"Skill to teach: {skill['skill_name']}",
            f"Topic: {skill['topic_id']}",
            f"A standard openly-licensed reference for this topic (for your grounding): {source}",
            "",
            "Write the lecture teaching this skill with one canonical worked example. Keep every",
            "mathematical claim standard and correct.",
        ]
    )


def _validate_lecture(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise serve_live.GenerationError(f"lecture is not an object: {type(raw).__name__}")
    title = raw.get("title")
    if not isinstance(title, str) or not title.strip():
        raise serve_live.GenerationError("lecture missing 'title'")
    body = raw.get("lecture_latex")
    if not isinstance(body, str) or not body.strip():
        raise serve_live.GenerationError("lecture missing 'lecture_latex'")
    # The title renders as plain text (an <h1>), so a Unicode glyph is fine there;
    # only raw LaTeX delimiters would show as source. Don't run the MathText gate on it.
    t = title.strip()
    if "\\(" in t or "\\[" in t or "$" in t:
        raise serve_live.GenerationError("title must be plain text (no LaTeX delimiters)")
    reason = serve_live._validate_display_latex("lecture_latex", body.strip())
    if reason is not None:
        raise serve_live.GenerationError(f"malformed lecture LaTeX: {reason}")
    return {"title": title.strip(), "lecture_latex": body.strip()}


def _make_generator(cfg: "serve_live.ServeConfig") -> Callable[[dict[str, Any], str], dict[str, str]]:
    url = f"{cfg.base_url.rstrip('/')}/chat/completions"

    def author(skill: dict[str, Any], source: str) -> dict[str, str]:
        body = {
            "model": cfg.model,
            "messages": [
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": _user_prompt(skill, source)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "manifold_gap_lecture", "schema": _LECTURE_SCHEMA, "strict": False},
            },
        }
        data = json.dumps(body).encode("utf-8")
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
                raise serve_live.AuthError(f"HTTP {exc.code}: {text[:200]}") from exc
            if exc.code == 429 or exc.code >= 500:
                raise serve_live.TransientError(f"HTTP {exc.code}: {text[:200]}") from exc
            raise serve_live.GenerationError(f"HTTP {exc.code}: {text[:200]}") from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise serve_live.TransientError(f"network error: {exc}") from exc
        content = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise serve_live.GenerationError("model returned no content")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise serve_live.GenerationError(f"lecture output was not valid JSON: {exc}") from exc
        return _validate_lecture(parsed)

    return author


def load_gap_skills() -> list[dict[str, Any]]:
    names = {s["skill_id"]: (s.get("name") or s["skill_id"]) for s in json.loads(SEED_DECK.read_text())["skills"]}
    out = []
    for line in GAPS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        g = json.loads(line)
        sid = g["skill_id"]
        out.append({"skill_id": sid, "topic_id": g.get("topic_id"), "skill_name": names.get(sid, sid)})
    return out


def load_existing(jsonl_path: Path) -> dict[str, dict[str, Any]]:
    by_skill: dict[str, dict[str, Any]] = {}
    if not jsonl_path.is_file():
        return by_skill
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rec = json.loads(line)
            if rec.get("skill_id") and rec.get("lecture_latex"):
                by_skill[rec["skill_id"]] = rec
    return by_skill


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-tries", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--items-out", default=str(SCRIPT_DIR / "lectures.gaps.items.jsonl"))
    parser.add_argument("--out", default=str(LECTURES_OUT))
    args = parser.parse_args(argv)

    cfg = serve_live.ServeConfig.from_env()
    if not cfg.api_key:
        print("error: OPENAI_API_KEY is not set. Load .env.", file=sys.stderr)
        return 2
    if cfg.fixtures_path:
        print("warning: MANIFOLD_LIVE_FIXTURES is set but IGNORED (lectures need real content).", file=sys.stderr)

    skills = load_gap_skills()
    if args.limit > 0:
        skills = skills[: args.limit]
    if not skills:
        print(f"no gap skills found in {GAPS_PATH}", file=sys.stderr)
        return 0

    items_path = Path(args.items_out)
    existing = load_existing(items_path)
    print(
        f"build_gap_lectures: {len(skills)} conceptual gap skill(s); resume: {len(existing)} authored; "
        f"concurrency={args.concurrency}",
        file=sys.stderr,
    )

    author = _make_generator(cfg)
    write_lock = threading.Lock()
    items_fh = open(items_path, "a", encoding="utf-8")
    lectures: dict[str, dict[str, Any]] = dict(existing)
    counters = {"done": 0, "authored": 0, "failed": 0}

    def work(skill: dict[str, Any]) -> None:
        sid = skill["skill_id"]
        if sid in lectures:
            with write_lock:
                counters["done"] += 1
            return
        source = _GAP_SOURCES.get(skill["topic_id"], _DEFAULT_SOURCE)
        last_err = None
        for attempt in range(1, args.max_tries + 1):
            try:
                out = author(skill, source)
            except serve_live.AuthError as exc:
                last_err = f"auth: {exc}"
                serve_live._log(f"[{sid}] auth error: {exc}")
                break
            except serve_live.TransientError as exc:
                last_err = f"transient: {exc}"
                time.sleep(0.5 * attempt)
                continue
            except serve_live.GenerationError as exc:
                last_err = f"generation: {exc}"
                serve_live._log(f"[{sid}] unusable ({attempt}/{args.max_tries}): {exc}")
                continue
            # Append the real open-source citation as visible "Further reading" prose.
            body = out["lecture_latex"] + f"\n\nFurther reading: {source}"
            rec = {
                "skill_id": sid,
                "topic_id": skill["topic_id"],
                "title": out["title"],
                "lecture_latex": body,
                "anchored_item_id": None,
                "source": source,
            }
            with write_lock:
                lectures[sid] = rec
                items_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                items_fh.flush()
                counters["authored"] += 1
                counters["done"] += 1
                n = counters["done"]
            print(f"  [{n}/{len(skills)}] {sid[:44]:44} -> authored", file=sys.stderr)
            return
        with write_lock:
            counters["failed"] += 1
            counters["done"] += 1
        print(f"  {sid[:44]:44} -> FAILED ({last_err})", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(work, s) for s in skills]
        for fut in as_completed(futures):
            fut.result()
    items_fh.close()

    # Merge gap lectures INTO the existing lectures.json (never overwrite bank-anchored ones).
    out_path = Path(args.out)
    doc = json.loads(out_path.read_text(encoding="utf-8")) if out_path.is_file() else {"lectures": {}}
    merged = dict(doc.get("lectures") or {})
    for sid, rec in lectures.items():
        merged[sid] = {
            "skill_id": sid,
            "topic_id": rec["topic_id"],
            "title": rec["title"],
            "lecture_latex": rec["lecture_latex"],
            "anchored_item_id": rec.get("anchored_item_id"),
            "source": rec.get("source"),
        }
    doc["schema_version"] = doc.get("schema_version", 1)
    doc["generated_at"] = datetime.now(timezone.utc).isoformat()
    doc["lecture_count"] = len(merged)
    doc["lectures"] = dict(sorted(merged.items()))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("=" * 64, file=sys.stderr)
    print(
        f"gap lectures: {counters['authored']} authored, {counters['failed']} failed; "
        f"lectures.json now has {len(merged)} total.",
        file=sys.stderr,
    )
    print(f"  wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

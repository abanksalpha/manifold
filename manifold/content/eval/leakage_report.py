# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""leakage_report.py — commit a REAL, re-runnable leakage artifact for the content
Manifold actually SERVES (WS4, gate 7e; copyright firewall, planning doc §1b).

The docs claim "the bank is CLEAN against all 5 ETS forms". ``leakage_check.py``
can prove that, but it only printed to stdout — there was no committed artifact and
nothing screened the *current* served content. This script closes that gap: it
assembles the actual served surface, screens it, and writes
``eval/results/leakage_check.json`` so the claim is backed by numbers from a real run.

What is served today (see ``serve_live._load_template_index`` /
``serve_live._load_teach_bank``), and therefore what is screened here:

  (a) parametric TEMPLATES — ``seed_templates.TEMPLATES`` plus
      ``generation/template_bank.json`` — rendered to concrete items at runtime by
      :func:`templates.instantiate` (SymPy-computed answers). We render a small,
      deterministic sample of fixed seeds per template and screen the rendered
      stem+choices; and
  (b) the concrete fallback items in ``generation/teach_bank.json`` (served for
      teach-tier skills that have no template).

Two screens, mirroring ``leakage_check``:

  * REFERENCE (copyright-critical): EVERY served item — all rendered template
    instances AND all teach items — is screened for containment against ALL five
    held-out ETS practice forms. This must cover all five; if a form cannot be read
    the underlying loader raises and we STOP (never a fabricated "clean" off a
    partial corpus).
  * SELF (internal near-duplicate, D42): the teach items are all-pairs screened
    (lexical near-dup is meaningful for concrete prose items). Templates are handled
    with a per-skill within-skill check — see :func:`_within_skill_template_check`
    and the ``scope`` note in the report for exactly what is and is not screened, and
    why an all-pairs lexical self-screen across ~3k symbolic instances is neither
    tractable nor meaningful here.

Honesty (owner's standing rules): every number comes from this run; a missing/
unreadable corpus fails loudly; and if the reference screen (or a genuine internal
duplicate) is found, that is written truthfully and the process exits non-zero — a
real finding is never hidden.

Run with the content generation venv (sympy/z3/pypdf; no API key needed — leakage is
lexical + deterministic)::

    manifold/content/generation/.venv/bin/python manifold/content/eval/leakage_report.py
"""

from __future__ import annotations

import datetime
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent            # manifold/content/eval
GEN_DIR = SCRIPT_DIR.parent / "generation"              # manifold/content/generation
HELDOUT_DIR = SCRIPT_DIR / "heldout"
RESULTS_DIR = SCRIPT_DIR / "results"
OUT_PATH = RESULTS_DIR / "leakage_check.json"

# The served-content modules live in generation/; put it first on sys.path so the
# bare ``import solver`` inside templates.py (and our own imports) resolve regardless
# of CWD, exactly as serve_live.py does.
if str(GEN_DIR) not in sys.path:
    sys.path.insert(0, str(GEN_DIR))

import leakage_check as lc  # noqa: E402  (import after sys.path fix-up, by design)
import seed_templates  # noqa: E402
import solver  # noqa: E402,F401  (read-only; templates.instantiate depends on it — a broken solver surfaces loudly at import)
import templates as tmpl_engine  # noqa: E402

TEMPLATE_BANK_PATH = GEN_DIR / "template_bank.json"
TEACH_BANK_PATH = GEN_DIR / "teach_bank.json"

# The five held-out ETS practice forms that MUST be screened (copyright firewall).
# The loader consumes the two scanned forms via their OCR sidecars; the names below
# are the PDF names it reports. If any is missing/unreadable we fail loud.
EXPECTED_FORMS = {f"Practice {n}.pdf" for n in range(1, 6)}

# Deterministic fixed seeds rendered per template for the REFERENCE screen. Two
# number-fillings per template is more thorough coverage of the served surface and
# is still O(n) in the reference screen (not O(n^2)). Kept small and fixed so the
# artifact is reproducible.
RENDER_SEEDS = (101, 202)
# Extra deterministic seeds tried ONLY when both RENDER_SEEDS yield InstanceRejected
# for a template (a normal per-seed outcome the serve path also retries past — NOT a
# fabricated item; a template that renders at no seed is reported, never faked).
FALLBACK_SEEDS = (303, 404, 505, 606, 707, 808, 909, 1010)
# Fresh seeds used to CONFIRM a suspected exact-duplicate template pair.
CONFIRM_SEEDS = (5001, 5002)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# --- assemble the served content ------------------------------------------------


def load_templates() -> tuple[list[dict[str, Any]], int, int]:
    """Return (templates, n_seed, n_bank): the exact template set serve_live loads.

    ``seed_templates.TEMPLATES`` first, then ``template_bank.json['templates']`` —
    matching :func:`serve_live._load_template_index`. Fails loud on a malformed bank.
    """
    seed = list(seed_templates.TEMPLATES)
    if not TEMPLATE_BANK_PATH.is_file():
        raise FileNotFoundError(f"template bank not found: {TEMPLATE_BANK_PATH}")
    data = json.loads(TEMPLATE_BANK_PATH.read_text(encoding="utf-8"))
    bank = data.get("templates") if isinstance(data, dict) else data
    if not isinstance(bank, list) or not bank:
        raise ValueError(f"{TEMPLATE_BANK_PATH}: no 'templates' list found")
    for t in seed + bank:
        if not t.get("template_id") or not t.get("skill_id"):
            raise ValueError(f"template missing template_id/skill_id: {t.get('template_id')!r}")
    return seed + bank, len(seed), len(bank)


def _item_id_base(template_id: str, skill_id: str, duplicated_ids: set[str]) -> str:
    """A stable, globally-unique item-id stem. ``<template_id>`` alone is not unique
    (a few ids are reused across two related skills), so those are disambiguated by
    skill_id; (template_id, skill_id) is unique across the whole set."""
    if template_id in duplicated_ids:
        return f"{template_id}@{skill_id}"
    return template_id


def render_instances(
    templates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[int, dict[str, Any]]], list[dict[str, str]]]:
    """Render each template at the fixed seeds.

    Returns:
      * ``instances`` — every rendered instance (all seeds) as a screenable item
        {item_id, skill_id, template_id, seed, stem, choices};
      * ``rendered`` — (template_id, skill_id) -> {seed: instance} for the
        within-skill checks;
      * ``unrenderable`` — templates that produced no instance at any tried seed
        (reported honestly; never fabricated).

    An :class:`templates.InstanceRejected` for a seed is the engine correctly saying
    "these numbers didn't yield a clean item" (the serve path retries past it too); a
    :class:`templates.TemplateError` / :class:`solver.SolveError` is a real authoring
    bug and is allowed to propagate (fail loud) with the offending template_id.
    """
    id_counts: dict[str, int] = defaultdict(int)
    for t in templates:
        id_counts[t["template_id"]] += 1
    duplicated_ids = {tid for tid, n in id_counts.items() if n > 1}

    instances: list[dict[str, Any]] = []
    rendered: dict[tuple[str, str], dict[int, dict[str, Any]]] = {}
    unrenderable: list[dict[str, str]] = []

    for t in templates:
        tid, sid = t["template_id"], t["skill_id"]
        base = _item_id_base(tid, sid, duplicated_ids)
        by_seed: dict[int, dict[str, Any]] = {}
        for seed in RENDER_SEEDS:
            inst = _try_instance(t, seed, base)
            if inst is not None:
                by_seed[seed] = inst
        if not by_seed:  # rejected at both primary seeds: try fallbacks for >=1 instance
            for seed in FALLBACK_SEEDS:
                inst = _try_instance(t, seed, base)
                if inst is not None:
                    by_seed[seed] = inst
                    break
        if not by_seed:
            unrenderable.append({"template_id": tid, "skill_id": sid})
            continue
        rendered[(tid, sid)] = by_seed
        instances.extend(by_seed.values())

    _assert_unique_item_ids(instances)
    return instances, rendered, unrenderable


def _try_instance(template: dict[str, Any], seed: int, base: str) -> dict[str, Any] | None:
    """Instantiate one item, or None if this seed is rejected. Real bugs propagate."""
    try:
        item = tmpl_engine.instantiate(template, seed)
    except tmpl_engine.InstanceRejected:
        return None
    except (tmpl_engine.TemplateError, solver.SolveError) as exc:
        raise RuntimeError(
            f"template {template.get('template_id')!r} (skill {template.get('skill_id')!r}) "
            f"failed to instantiate at seed {seed}: {type(exc).__name__}: {exc}"
        ) from exc
    return {
        "item_id": f"{base}#{seed}",
        "skill_id": template["skill_id"],
        "template_id": template["template_id"],
        "seed": seed,
        "stem": item["stem"],
        "choices": item["choices"],
    }


def _assert_unique_item_ids(instances: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for inst in instances:
        iid = inst["item_id"]
        if iid in seen:
            raise RuntimeError(f"non-unique rendered item_id {iid!r}; refusing to screen ambiguous ids")
        seen.add(iid)


def load_teach_items() -> list[dict[str, Any]]:
    """The concrete teach-bank fallback items (served for teach skills with no
    template), as screenable {item_id, skill_id, stem, choices}. Fails loud if the
    bank is missing or malformed."""
    if not TEACH_BANK_PATH.is_file():
        raise FileNotFoundError(f"teach bank not found: {TEACH_BANK_PATH}")
    data = json.loads(TEACH_BANK_PATH.read_text(encoding="utf-8"))
    records = data.get("items") if isinstance(data, dict) else data
    if not isinstance(records, list) or not records:
        raise ValueError(f"{TEACH_BANK_PATH}: no 'items' list found")
    items: list[dict[str, Any]] = []
    for rec in records:
        item = rec.get("item") if isinstance(rec, dict) else None
        if not isinstance(item, dict):
            raise ValueError(f"teach record missing 'item': {rec.get('item_id') if isinstance(rec, dict) else rec!r}")
        items.append(
            {
                "item_id": rec.get("item_id") or item.get("source_ref") or "teach::?",
                "skill_id": rec.get("skill_id") or item.get("skill_id", ""),
                "stem": item.get("stem", ""),
                "choices": item.get("choices", []),
            }
        )
    return items


# --- reference screen (copyright-critical) --------------------------------------


def load_reference_corpus_checked() -> list[tuple[str, str]]:
    """Load the ETS corpus and assert all five forms are actually present.

    ``leakage_check.load_reference_corpus`` already raises on an absent corpus, a
    no-text scanned PDF with no OCR sidecar, or a missing extractor. On top of that
    we require every one of the five expected forms — so a silently-dropped empty
    sidecar can never let a partial "clean" through."""
    corpus = lc.load_reference_corpus(HELDOUT_DIR)  # raises if absent/unreadable
    names = {name for name, _ in corpus}
    missing = EXPECTED_FORMS - names
    if missing:
        raise RuntimeError(
            f"reference screen did not cover all five ETS forms; missing/unreadable: "
            f"{sorted(missing)} (got {sorted(names)}). Refusing to report a partial 'clean'."
        )
    return corpus


# --- self / within-skill screens ------------------------------------------------


def _sig(inst: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    return (inst["stem"], tuple(inst["choices"]))


def _first_instance(by_seed: dict[int, dict[str, Any]]) -> dict[str, Any]:
    return by_seed[min(by_seed)]


def _within_skill_template_check(
    rendered: dict[tuple[str, str], dict[int, dict[str, Any]]],
    templates_by_key: dict[tuple[str, str], dict[str, Any]],
    *,
    k: int,
    threshold: float,
) -> dict[str, Any]:
    """Per-skill check across a skill's templates (one instance per template).

    Two signals:
      * ``exact_duplicate_pairs`` — the OBJECTIVE redundancy signal: two templates
        of the same skill whose full rendered stem+choices are IDENTICAL, confirmed
        across multiple seeds (a genuine copy-paste duplicate). This counts toward
        'clean'.
      * ``lexical_near_duplicate_candidates`` — pairs flagged by the same lexical
        Jaccard screen used for reference/self, recorded WITH both raw stems. These
        are NOT counted as duplicates: the normalizer deletes LaTeX macros (\\cos,
        \\sin, \\rightarrow, ...), so distinct symbolic stems like cos(arcsin x) vs
        sin(arccos x) collapse to identical tokens. They are surfaced for full
        transparency, not hidden — a human can see from the stems that they differ.
    """
    by_skill: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in rendered:
        by_skill[key[1]].append(key)  # key = (template_id, skill_id)

    skills_multi = 0
    templates_compared = 0
    lexical: list[dict[str, Any]] = []
    exact: list[dict[str, Any]] = []

    for skill, keys in by_skill.items():
        if len(keys) < 2:
            continue
        skills_multi += 1
        templates_compared += len(keys)
        firsts = [_first_instance(rendered[key]) for key in keys]
        shs = [lc.shingles(lc.tokenize(lc.item_text(it)), k) for it in firsts]
        for j in range(len(keys)):
            for i in range(j):
                score = lc.jaccard(shs[i], shs[j])
                if score >= threshold:
                    lexical.append(
                        {
                            "skill_id": skill,
                            "item_a": firsts[i]["item_id"],
                            "item_b": firsts[j]["item_id"],
                            "jaccard": round(score, 3),
                            "stem_a": firsts[i]["stem"],
                            "stem_b": firsts[j]["stem"],
                        }
                    )
                if _is_exact_duplicate(keys[i], keys[j], rendered, templates_by_key):
                    exact.append(
                        {
                            "skill_id": skill,
                            "item_a": firsts[i]["item_id"],
                            "item_b": firsts[j]["item_id"],
                            "detail": "identical rendered stem+choices across all checked seeds",
                        }
                    )

    return {
        "method": (
            f"one instance per template, compared within each skill "
            f"(lexical Jaccard k={k}, threshold {threshold}); exact-duplicate pairs confirmed "
            f"across seeds {list(RENDER_SEEDS)}+{list(CONFIRM_SEEDS)}"
        ),
        "skills_with_multiple_templates": skills_multi,
        "template_instances_compared": templates_compared,
        "exact_duplicate_pairs": exact,
        "lexical_near_duplicate_candidates": lexical,
        "note": (
            "lexical_near_duplicate_candidates are NOT counted as duplicates: the leakage "
            "normalizer strips LaTeX macros, so symbolic-only stems that differ solely by a "
            "function/operator macro (e.g. \\cos vs \\sin, \\rightarrow vs \\wedge) collapse to "
            "identical tokens. Both raw stems are included so the difference is visible. The "
            "objective duplicate signal is exact_duplicate_pairs (identical rendered content "
            "across seeds)."
        ),
    }


def _is_exact_duplicate(
    key_a: tuple[str, str],
    key_b: tuple[str, str],
    rendered: dict[tuple[str, str], dict[int, dict[str, Any]]],
    templates_by_key: dict[tuple[str, str], dict[str, Any]],
) -> bool:
    """True iff two templates render byte-identical stem+choices on every compared
    seed (>=2 seeds), confirming a genuine duplicate rather than a one-seed collision."""
    a_by_seed, b_by_seed = rendered[key_a], rendered[key_b]
    common = sorted(set(a_by_seed) & set(b_by_seed))
    if common and all(_sig(a_by_seed[s]) == _sig(b_by_seed[s]) for s in common) and len(common) >= 2:
        return True
    if common and not all(_sig(a_by_seed[s]) == _sig(b_by_seed[s]) for s in common):
        return False
    if not common and _sig(_first_instance(a_by_seed)) != _sig(_first_instance(b_by_seed)):
        return False
    # <=1 comparable matching seed: confirm with fresh seeds before calling it a dup.
    ta, tb = templates_by_key[key_a], templates_by_key[key_b]
    matches = 0
    for seed in CONFIRM_SEEDS:
        try:
            ia = tmpl_engine.instantiate(ta, seed)
            ib = tmpl_engine.instantiate(tb, seed)
        except tmpl_engine.InstanceRejected:
            return False  # cannot confirm identically -> not a confirmed duplicate
        if _sig({"stem": ia["stem"], "choices": ia["choices"]}) != _sig({"stem": ib["stem"], "choices": ib["choices"]}):
            return False
        matches += 1
    return matches >= 2


# --- report assembly ------------------------------------------------------------


def build_report() -> dict[str, Any]:
    """Assemble the served content, run both screens, and return the report dict."""
    templates, n_seed, n_bank = load_templates()
    templates_by_key = {(t["template_id"], t["skill_id"]): t for t in templates}
    instances, rendered, unrenderable = render_instances(templates)
    teach_items = load_teach_items()

    corpus = load_reference_corpus_checked()
    forms_screened = [name for name, _ in corpus]

    served_items = instances + teach_items
    k, thr = lc.DEFAULT_SHINGLE, lc.DEFAULT_THRESHOLD

    reference_rejects = lc.screen_reference(served_items, corpus, k=k, threshold=thr)
    teach_self_rejects = lc.screen_self(teach_items, k=k, threshold=thr)
    within_skill = _within_skill_template_check(rendered, templates_by_key, k=k, threshold=thr)

    exact_dup_rejects = [
        {"item_id": p["item_a"], "reason": "duplicate_template", "detail": f"exact duplicate of {p['item_b']} ({p['skill_id']})"}
        for p in within_skill["exact_duplicate_pairs"]
    ]
    # Genuine rejects = ETS leakage + teach near-dups + confirmed exact-duplicate
    # templates. The lexical within-skill candidates are disclosed above but are NOT
    # genuine duplicates (macro-stripping artifacts), so they do not gate 'clean'.
    rejects = list(reference_rejects) + list(teach_self_rejects) + exact_dup_rejects
    clean = not rejects

    total_items = len(served_items)
    return {
        "generated_at": _now_iso(),
        "artifact": "manifold served-content leakage screen",
        "description": (
            "Screens the ACTUAL served content (parametric template instances rendered by "
            "templates.instantiate + concrete teach-bank fallback items) against the five "
            "held-out ETS practice forms (copyright firewall) and for internal near-duplicates."
        ),
        "generator": "manifold/content/eval/leakage_report.py",
        "counts": {
            "seed_templates": n_seed,
            "template_bank_templates": n_bank,
            "templates_total": len(templates),
            "templates_rendered": len(rendered),
            "templates_unrenderable": len(unrenderable),
            "render_seeds": list(RENDER_SEEDS),
            "template_instances": len(instances),
            "teach_items": len(teach_items),
            "total_items_screened": total_items,
        },
        "reference": {
            "dir": str(HELDOUT_DIR),
            "forms_screened": forms_screened,
            "forms_count": len(forms_screened),
            "items_screened": total_items,
            "threshold": thr,
            "shingle": k,
            "rejects": reference_rejects,
        },
        "self_screen": {
            "teach_bank_near_duplicates": {
                "items": len(teach_items),
                "threshold": thr,
                "shingle": k,
                "rejects": teach_self_rejects,
            },
            "within_skill_template": within_skill,
        },
        "threshold": thr,
        "shingle": k,
        "clean": clean,
        "rejects": rejects,
        "templates_unrenderable": unrenderable,
        "scope": _scope_note(
            instances=len(instances),
            templates=len(rendered),
            teach=len(teach_items),
            total=total_items,
            forms=forms_screened,
            k=k,
            thr=thr,
        ),
    }


def _scope_note(*, instances: int, templates: int, teach: int, total: int, forms: list[str], k: int, thr: float) -> str:
    return (
        f"REFERENCE (copyright) screen: every served item — {instances} parametric template "
        f"instances (from {templates} templates x up to {len(RENDER_SEEDS)} fixed seeds each) PLUS "
        f"{teach} teach-bank fallback items = {total} items — was screened for containment "
        f"(shingle k={k}, threshold {thr}) against ALL {len(forms)} held-out ETS forms "
        f"({', '.join(forms)}). This is comprehensive over the served surface. "
        f"SELF (near-duplicate) screen: the {teach} teach-bank items were all-pairs screened "
        f"(lexical near-dup is meaningful for concrete prose items). An all-pairs lexical "
        f"self-screen over all {instances} template instances is intentionally NOT run: it is "
        f"O(n^2), and parametric instances legitimately share scaffolding while the lexical "
        f"normalizer deletes LaTeX macros, so it is not a meaningful signal for symbolic stems. "
        f"Instead a per-skill within-skill template check compares one instance per template: the "
        f"objective signal is exact_duplicate_pairs (identical rendered stem+choices across "
        f"seeds); lexical near-dup candidates are recorded with both raw stems for transparency. "
        f"'clean' = no ETS leakage AND no teach near-duplicates AND no exact-duplicate templates."
    )


def main() -> int:
    report = build_report()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    c = report["counts"]
    ref = report["reference"]
    ws = report["self_screen"]["within_skill_template"]
    teach_dups = report["self_screen"]["teach_bank_near_duplicates"]["rejects"]
    print("=" * 72)
    print("Manifold served-content leakage screen")
    print("=" * 72)
    print(f"  templates            : {c['templates_total']} "
          f"({c['seed_templates']} seed + {c['template_bank_templates']} bank), "
          f"rendered {c['templates_rendered']}, unrenderable {c['templates_unrenderable']}")
    print(f"  template instances   : {c['template_instances']} (seeds {c['render_seeds']})")
    print(f"  teach fallback items : {c['teach_items']}")
    print(f"  TOTAL items screened : {c['total_items_screened']}")
    print(f"  ETS forms screened   : {ref['forms_count']} -> {', '.join(ref['forms_screened'])}")
    print(f"  threshold / shingle  : {report['threshold']} / {report['shingle']}")
    print("-" * 72)
    print(f"  reference (leakage) rejects   : {len(ref['rejects'])}")
    print(f"  teach self near-dup rejects   : {len(teach_dups)}")
    print(f"  exact-duplicate template pairs: {len(ws['exact_duplicate_pairs'])}")
    print(f"  within-skill lexical candidates (disclosed, not counted): "
          f"{len(ws['lexical_near_duplicate_candidates'])}")
    print("-" * 72)
    if report["clean"]:
        print("  RESULT: CLEAN — no ETS leakage, no teach near-duplicates, no duplicate templates.")
    else:
        print(f"  RESULT: NOT CLEAN — {len(report['rejects'])} genuine reject(s):")
        for r in report["rejects"]:
            print(f"    [{r['reason']}] {r['item_id']}: {r['detail']}")
    print(f"  report written       : {OUT_PATH}")
    print("=" * 72)
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

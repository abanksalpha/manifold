# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""Leakage / near-duplicate gate for Manifold's content pipeline (WS1, Gate 5b, 7e).

Two jobs, both protecting the "leaked data = 0" auto-zero and the copyright
firewall (planning doc §1b):

1. **Reference screen** — no banked item may be a copy or near-copy of anything
   in the held-out ETS practice forms (the gold set). Those PDFs are evaluation
   material and must never appear (even paraphrased) in the bank.
2. **Self screen** — the bank's own instances of a skill must genuinely vary
   their surface features (D42), so this also flags internal near-duplicates.

Similarity is **lexical** and deterministic: normalized word n-gram *shingles*
compared by Jaccard (item vs item, symmetric) and by containment (item within a
reference page, asymmetric — the shape of a copied item embedded in a long PDF
page). No semantic-embedding model is bundled; embedding-based dedup is an
optional future augmentation and is **not** silently faked here.

Honesty / fail-loud (cross-cutting rules; firewall §1b):
  - The ETS PDFs are currently NOT on disk. If a reference screen is requested
    but the corpus is absent (only the placeholder ``README`` remains), this
    module raises :class:`LeakageCorpusMissing` — it never reports a fabricated
    "clean" result off an empty corpus.
  - If the reference corpus contains PDFs but no PDF text extractor is installed,
    it raises rather than silently skipping those files.

Interpreter: the generation venv has everything needed (pure stdlib + optional
numpy); no API key. See ``verify.py`` for how the venv was created.

    manifold/content/generation/.venv/bin/python leakage_check.py \
        --bank item_bank.json --reference ../eval/heldout --self
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_HELDOUT_DIR = SCRIPT_DIR.parents[0] / "eval" / "heldout"

# Word n-gram length for shingling. 4 balances sensitivity (catches paraphrase
# with shared runs of words) against noise (isolated shared words don't match).
DEFAULT_SHINGLE = 4
DEFAULT_THRESHOLD = 0.8

# Files in a reference dir that are placeholders/metadata, NOT gold content.
_NON_CORPUS = {"readme.md", "readme.txt", "readme", ".gitkeep", ".ds_store"}
_TEXT_SUFFIXES = {".txt", ".md", ".json"}


class LeakageCorpusMissing(Exception):
    """A reference screen was requested but no usable gold corpus is present."""


class LeakageConfigError(Exception):
    """Malformed inputs (bad bank file, unreadable reference). Fail loudly."""


# --- text normalization + shingling --------------------------------------------


def normalize(text: str) -> str:
    """Lowercase, strip common LaTeX/markup noise, collapse whitespace."""
    text = text.lower()
    text = text.replace("$", " ").replace("\\(", " ").replace("\\)", " ")
    text = text.replace("\\[", " ").replace("\\]", " ")
    text = re.sub(r"\\[a-z]+", " ", text)  # LaTeX commands: \frac, \sqrt, ...
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    """Alphanumeric tokens (keeps numbers and variable names, which carry signal)."""
    return re.findall(r"[a-z0-9]+", normalize(text))


def shingles(tokens: list[str], k: int) -> set[tuple[str, ...]]:
    """Set of word k-grams. Always yields >=1 shingle for non-empty token lists
    (short texts collapse to a single whole-sequence shingle)."""
    if not tokens:
        return set()
    if len(tokens) <= k:
        return {tuple(tokens)}
    return {tuple(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}


def jaccard(a: set[Any], b: set[Any]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def containment(small: set[Any], large: set[Any]) -> float:
    """Fraction of ``small`` covered by ``large`` (asymmetric)."""
    if not small:
        return 0.0
    return len(small & large) / len(small)


# --- item + reference text -----------------------------------------------------


def item_text(item: dict[str, Any]) -> str:
    """The copyright-/leakage-relevant surface of an item: stem + choices.

    The worked solution is Manifold's own prose and is deliberately excluded so
    the reference screen targets the exam-facing content that could be copied."""
    parts = [str(item.get("stem", ""))]
    choices = item.get("choices")
    if isinstance(choices, list):
        parts.extend(str(c) for c in choices)
    return " ".join(parts)


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF, or fail loudly if no extractor is available."""
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError as exc:
            raise LeakageConfigError(
                f"cannot read PDF {path.name}: no PDF text extractor installed "
                "(pip install pypdf into the generation venv, or provide .txt exports "
                "of the reference forms). Refusing to skip it silently."
            ) from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_reference_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return _read_pdf(path)
    if path.suffix.lower() == ".json":
        # A JSON reference is treated as a flat dump of its string values.
        data = json.loads(path.read_text(encoding="utf-8"))
        return _flatten_json_text(data)
    return path.read_text(encoding="utf-8", errors="replace")


def _flatten_json_text(data: Any) -> str:
    out: list[str] = []
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, str):
            out.append(node)
        elif isinstance(node, dict):
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return " ".join(out)


def load_reference_corpus(reference_dir: Path) -> list[tuple[str, str]]:
    """Load (name, text) for every gold/reference file, excluding placeholders.

    Raises :class:`LeakageCorpusMissing` if, after excluding the placeholder
    README/.gitkeep, nothing remains — the ETS forms are simply not on disk yet,
    and a screen against an empty corpus would be a fabricated "clean" result.
    """
    if not reference_dir.is_dir():
        raise LeakageCorpusMissing(
            f"reference corpus directory does not exist: {reference_dir}"
        )
    corpus: list[tuple[str, str]] = []
    skipped_placeholders = 0
    for path in sorted(reference_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.lower() in _NON_CORPUS:
            skipped_placeholders += 1
            continue
        # An OCR sidecar ("<form>.pdf.txt") is consumed via its PDF below, not as a
        # standalone doc, so a scanned form is never double-counted.
        if path.name.lower().endswith(".pdf.txt"):
            continue
        suffix = path.suffix.lower()
        if suffix not in _TEXT_SUFFIXES and suffix != ".pdf":
            continue
        if suffix == ".pdf":
            text = _read_pdf(path)
            if not text.strip():
                # A scanned / image-only PDF (no text layer): screening against it
                # would silently see nothing and report a fabricated "clean". Use an
                # OCR sidecar if present, else fail LOUDLY (leaked data = auto-zero).
                sidecar = path.with_name(path.name + ".txt")
                if sidecar.is_file():
                    text = sidecar.read_text(encoding="utf-8", errors="replace")
                else:
                    raise LeakageConfigError(
                        f"{path.name} yielded no extractable text: it is a scanned / "
                        f"image-only PDF. Provide an OCR sidecar at '{sidecar.name}' "
                        "(or a .txt export) so it can be screened. Refusing to screen "
                        "against it silently, since missed leakage is an auto-zero."
                    )
        else:
            text = _read_reference_file(path)
        if text.strip():
            corpus.append((path.name, text))
    if not corpus:
        raise LeakageCorpusMissing(
            f"no usable reference documents in {reference_dir} "
            f"(skipped {skipped_placeholders} placeholder file(s)). "
            "The held-out ETS practice forms are not on disk; re-provide them to run "
            "the leakage screen. Not reporting a fabricated 'clean' result."
        )
    return corpus


# --- screening -----------------------------------------------------------------


def _item_id(item: dict[str, Any]) -> str:
    existing = item.get("item_id")
    if isinstance(existing, str) and existing:
        return existing
    # Fall back to a source-ref + stem tag so rejects are still identifiable.
    return f"{item.get('source_ref', '?')}::{str(item.get('stem', ''))[:40]}"


def screen_reference(
    banked: list[dict[str, Any]],
    corpus: list[tuple[str, str]],
    *,
    k: int,
    threshold: float,
) -> list[dict[str, Any]]:
    """Reject items whose content is contained in any reference doc above threshold."""
    ref_shingles = [(name, shingles(tokenize(text), k)) for name, text in corpus]
    rejects: list[dict[str, Any]] = []
    for item in banked:
        item_sh = shingles(tokenize(item_text(item)), k)
        best_name, best_score = None, 0.0
        for name, ref_sh in ref_shingles:
            score = containment(item_sh, ref_sh)
            if score > best_score:
                best_name, best_score = name, score
        if best_score >= threshold:
            rejects.append(
                {
                    "item_id": _item_id(item),
                    "reason": "leakage",
                    "detail": f"{best_score:.2f} contained in reference '{best_name}'",
                    "item": item,
                }
            )
    return rejects


def screen_self(
    banked: list[dict[str, Any]],
    *,
    k: int,
    threshold: float,
) -> list[dict[str, Any]]:
    """Flag internal near-duplicates (D42 variability firewall).

    Deterministic: within a near-duplicate pair the later item (by list order) is
    the one rejected, so the first-authored instance is kept."""
    sh = [shingles(tokenize(item_text(item)), k) for item in banked]
    rejects: list[dict[str, Any]] = []
    for j in range(len(banked)):
        for i in range(j):
            score = jaccard(sh[i], sh[j])
            if score >= threshold:
                rejects.append(
                    {
                        "item_id": _item_id(banked[j]),
                        "reason": "near_duplicate",
                        "detail": f"{score:.2f} Jaccard vs item '{_item_id(banked[i])}'",
                        "item": banked[j],
                    }
                )
                break  # one report per duplicated item is enough
    return rejects


def screen_bank(
    banked: list[dict[str, Any]],
    *,
    self_mode: bool,
    reference_dir: Path,
    threshold: float = DEFAULT_THRESHOLD,
    shingle: int = DEFAULT_SHINGLE,
    require_reference: bool = True,
) -> list[dict[str, Any]]:
    """Public entry used by build_bank.py. Returns items to reject.

    Always runs a self near-duplicate screen when ``self_mode``. Runs the
    reference screen against ``reference_dir``; if ``require_reference`` and the
    corpus is missing this raises (fail loud) rather than passing silently.
    """
    rejects: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    def add(new: Iterable[dict[str, Any]]) -> None:
        for reject in new:
            if reject["item_id"] not in seen_ids:
                seen_ids.add(reject["item_id"])
                rejects.append(reject)

    # Reference screen (skipped entirely only in self-only mode).
    if require_reference:
        corpus = load_reference_corpus(reference_dir)  # raises if absent
        add(screen_reference(banked, corpus, k=shingle, threshold=threshold))
    if self_mode:
        add(screen_self(banked, k=shingle, threshold=threshold))
    return rejects


# --- CLI -----------------------------------------------------------------------


def load_bank(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise LeakageConfigError(f"bank file not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        items = [json.loads(line) for line in text.splitlines() if line.strip()]
    else:
        data = json.loads(text)
        items = data if isinstance(data, list) else data.get("items")
    if not isinstance(items, list) or not items:
        raise LeakageConfigError(f"{path}: no items found")
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Leakage / near-duplicate screen for the Manifold item bank."
    )
    parser.add_argument("--bank", required=True, help="item_bank.json (or a JSONL of items)")
    parser.add_argument(
        "--reference",
        default=None,
        help=f"reference corpus dir (gold/ETS forms) [default: {DEFAULT_HELDOUT_DIR}]",
    )
    parser.add_argument(
        "--self",
        dest="self_mode",
        action="store_true",
        help="also screen the bank against itself for internal near-duplicates",
    )
    parser.add_argument(
        "--no-reference",
        action="store_true",
        help="skip the reference screen (self-only). Otherwise a missing corpus fails loudly.",
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--shingle", type=int, default=DEFAULT_SHINGLE)
    args = parser.parse_args(argv)

    try:
        banked = load_bank(Path(args.bank))
    except (LeakageConfigError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    reference_dir = Path(args.reference) if args.reference else DEFAULT_HELDOUT_DIR
    require_reference = not args.no_reference

    try:
        rejects = screen_bank(
            banked,
            self_mode=args.self_mode,
            reference_dir=reference_dir,
            threshold=args.threshold,
            shingle=args.shingle,
            require_reference=require_reference,
        )
    except LeakageCorpusMissing as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 3
    except LeakageConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print("=" * 68)
    print("Manifold leakage / near-duplicate report")
    print("=" * 68)
    print(f"  bank items      : {len(banked)}")
    print(f"  reference screen: {'off (self-only)' if not require_reference else reference_dir}")
    print(f"  self screen     : {'on' if args.self_mode else 'off'}")
    print(f"  threshold       : {args.threshold}")
    print("-" * 68)
    if not rejects:
        print("  CLEAN: no leakage or near-duplicates found.")
    else:
        print(f"  FOUND {len(rejects)} problem item(s):")
        for reject in rejects:
            print(f"    [{reject['reason']}] {reject['item_id']}: {reject['detail']}")
    print("=" * 68)
    return 1 if rejects else 0


if __name__ == "__main__":
    raise SystemExit(main())

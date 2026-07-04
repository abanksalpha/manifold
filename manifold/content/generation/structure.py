# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""structure.py — a lightweight STRUCTURAL signature for a template, used to measure
and report genuine problem-SHAPE variety within a skill. This is a different axis
from templates.validate()'s numeric variety (same shape, different numbers): here we
ask whether two templates test a genuinely different method/relationship/framing, or
are accidentally the same shape with renamed slots.

Two templates collapse to the same signature when they share the same answer-spec
operation AND the same normalized stem skeleton (slots and numbers blanked out, so
wording/structure is what's compared, not the specific numbers or parameter names).
That makes this a cheap, deterministic accidental-duplicate detector — useful for a
human or subagent authoring many templates per skill to sanity-check their own work.

This is ADVISORY tooling only (reporting + duplicate-shape flags). It never gates
banking: correctness and per-template numeric variety stay owned exclusively by
templates.validate() / verify_template.py / build_template_bank.py.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

_SLOT = re.compile(r"\[\[\w+\]\]")
_NUM = re.compile(r"\d+(\.\d+)?")
_WS = re.compile(r"\s+")


def stem_skeleton(stem: str) -> str:
    """Normalize a raw (unsubstituted) template stem to its structural shape: every
    ``[[slot]]`` and every literal number collapsed to ``#``, whitespace collapsed,
    case-folded. Wording differences still differentiate templates on purpose — a
    genuinely different problem framing usually reads differently even at the same
    operation."""
    s = _SLOT.sub("#", stem)
    s = _NUM.sub("#", s)
    s = _WS.sub(" ", s).strip().lower()
    return s


def structure_signature(template: dict[str, Any]) -> str:
    """A short, stable signature for a template's PROBLEM SHAPE: its answer-spec
    operation plus its normalized stem skeleton. Two templates with the same
    signature are testing the same underlying structure."""
    op = (template.get("answer_spec") or {}).get("op", "?")
    skeleton = stem_skeleton(template.get("stem", ""))
    raw = f"{op}::{skeleton}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def distinct_structures(templates_list: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the structural variety within one skill's list of templates."""
    sigs: dict[str, list[str]] = {}
    for t in templates_list:
        sig = structure_signature(t)
        sigs.setdefault(sig, []).append(t.get("template_id", "?"))
    dupes = {sig: ids for sig, ids in sigs.items() if len(ids) > 1}
    return {
        "count": len(templates_list),
        "distinct_structures": len(sigs),
        "duplicate_shapes": dupes,
    }

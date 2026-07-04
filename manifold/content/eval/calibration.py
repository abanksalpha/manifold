# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""calibration.py — the memory-model calibration harness (ASSIGN section 9, step 1).

Manifold's MEMORY score is Anki's FSRS retrievability R (rslib/src/manifold/mastery.rs
reads the FSRS memory state; the scheduler itself is untouched, D3). Step 1 asks:
is R calibrated — when the model says 80%, does the learner recall about 80%?

This is a DATA-AGNOSTIC calibration harness. Give it (predicted_prob, outcome) pairs
from a revlog and it computes the reliability diagram, Brier score, log loss, and
Expected/Max Calibration Error (ECE/MCE) — the standard calibration report section 9
asks for. Plug in the app's real review log (predicted R at review time vs actual
pass/fail) and it prints the calibration of Manifold's memory model on that data.

HONEST LIMIT (section 9): a one-week build has no logged longitudinal student reviews,
so there is no real held-out review set to prove calibration on yet. Two honest things
are provided instead of a fabricated number:
  1. The harness (ready for real revlog data: --revlog pairs.json).
  2. A clearly-labelled SIMULATION: cards forget on an exponential curve p=exp(-t/S);
     the predictor uses FSRS-style p_hat=exp(-t/S_hat) with estimation noise on S_hat.
     Outcomes are drawn from the TRUE p, so the reported numbers are the calibration of
     an FSRS-style predictor under stability-estimation error — a plausibility check of
     the harness and the model form, NOT a measurement on real students.
Externally, FSRS is calibrated on public multi-million-review benchmarks (open-spaced-
repetition/srs-benchmark); we do not re-derive that here, we cite it.

Run: manifold/content/generation/.venv/bin/python manifold/content/eval/calibration.py
     (or --revlog path/to/pairs.json once real reviews exist)
"""

from __future__ import annotations

import argparse
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def reliability(pairs: list[tuple[float, int]], bins: int = 10) -> dict[str, Any]:
    """Reliability diagram + ECE/MCE over `bins` equal-width probability bins."""
    edges = [i / bins for i in range(bins + 1)]
    rows = []
    ece = 0.0
    mce = 0.0
    n = len(pairs)
    for b in range(bins):
        lo, hi = edges[b], edges[b + 1]
        inb = [(p, y) for (p, y) in pairs if (p >= lo and (p < hi or (b == bins - 1 and p <= hi)))]
        if not inb:
            rows.append({"bin": f"[{lo:.1f},{hi:.1f})", "count": 0, "mean_pred": None, "obs_freq": None})
            continue
        mean_pred = sum(p for p, _ in inb) / len(inb)
        obs = sum(y for _, y in inb) / len(inb)
        gap = abs(mean_pred - obs)
        ece += (len(inb) / n) * gap
        mce = max(mce, gap)
        rows.append({
            "bin": f"[{lo:.1f},{hi:.1f})", "count": len(inb),
            "mean_pred": round(mean_pred, 3), "obs_freq": round(obs, 3), "gap": round(gap, 3),
        })
    return {"bins": rows, "ECE": round(ece, 4), "MCE": round(mce, 4)}


def brier(pairs: list[tuple[float, int]]) -> float:
    return round(sum((p - y) ** 2 for p, y in pairs) / len(pairs), 4)


def log_loss(pairs: list[tuple[float, int]]) -> float:
    eps = 1e-12
    s = 0.0
    for p, y in pairs:
        p = min(max(p, eps), 1 - eps)
        s += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return round(s / len(pairs), 4)


def simulate(n: int, sigma: float, seed: int) -> list[tuple[float, int]]:
    """FSRS-style forgetting simulation: true p=exp(-t/S); predictor p_hat=exp(-t/S_hat),
    S_hat = S * lognormal(0, sigma) (stability-estimation error). Outcomes ~ Bernoulli(true p)."""
    rng = random.Random(seed)
    pairs = []
    for _ in range(n):
        S = math.exp(rng.uniform(math.log(1), math.log(365)))  # stability days, log-uniform
        t = rng.uniform(0.0, 2.0 * S)
        true_p = math.exp(-t / S)
        y = 1 if rng.random() < true_p else 0
        S_hat = S * math.exp(rng.gauss(0.0, sigma))
        p_hat = math.exp(-t / S_hat)
        pairs.append((p_hat, y))
    return pairs


def report_for(pairs: list[tuple[float, int]], label: str) -> dict[str, Any]:
    return {
        "label": label,
        "n": len(pairs),
        "brier": brier(pairs),
        "log_loss": log_loss(pairs),
        **reliability(pairs),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Memory-model (FSRS) calibration harness.")
    parser.add_argument("--revlog", default=None, help="JSON list of [predicted_prob, outcome] real pairs")
    parser.add_argument("--n", type=int, default=20000, help="simulated reviews (when no --revlog)")
    parser.add_argument("--sigma", type=float, default=0.35, help="log-normal stability-estimation error")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--out", default=str(SCRIPT_DIR / "results" / "calibration.json"))
    args = parser.parse_args(argv)

    out: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "memory_model": "Anki FSRS retrievability R (rslib/src/manifold/mastery.rs; scheduler untouched, D3)",
        "external_calibration": "FSRS is calibrated on public multi-million-review benchmarks "
        "(open-spaced-repetition/srs-benchmark); cited, not re-derived here.",
    }
    if args.revlog:
        data = json.loads(Path(args.revlog).read_text(encoding="utf-8"))
        pairs = [(float(p), int(y)) for p, y in data]
        out["source"] = f"REAL revlog: {args.revlog} ({len(pairs)} reviews)"
        out["result"] = report_for(pairs, "real_revlog")
    else:
        out["source"] = "SIMULATION (no real longitudinal reviews in a one-week build; see docstring)"
        out["disclaimer"] = (
            "These numbers are a harness plausibility check on an FSRS-style forgetting "
            "simulation, NOT a measurement on real students. Real calibration requires the "
            "app's logged reviews (predicted R vs actual pass/fail): rerun with --revlog."
        )
        noisy = simulate(args.n, args.sigma, args.seed)
        # A perfectly-calibrated control (predictor == truth) to show the harness detects it.
        rng = random.Random(args.seed + 1)
        perfect = []
        for _ in range(args.n):
            p = rng.random()
            perfect.append((p, 1 if rng.random() < p else 0))
        out["result_noisy_predictor"] = report_for(noisy, f"fsrs_style_sigma={args.sigma}")
        out["result_perfect_control"] = report_for(perfect, "perfectly_calibrated_control")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    key = "result" if args.revlog else "result_noisy_predictor"
    r = out[key]
    print(f"calibration ({out['source']}):")
    print(f"  Brier={r['brier']}  log_loss={r['log_loss']}  ECE={r['ECE']}  MCE={r['MCE']}")
    if not args.revlog:
        c = out["result_perfect_control"]
        print(f"  (control, perfectly calibrated: Brier={c['brier']} ECE={c['ECE']})")
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

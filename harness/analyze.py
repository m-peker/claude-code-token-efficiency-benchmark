"""Summarize benchmark results.

For each condition and task: median cost, tokens, peak context, turns, and
success rate over reps. Each condition is compared to the baseline per task,
and the per-task ratios are combined with a geometric mean so no single task
dominates.

Usage: python harness/analyze.py [results/runs.jsonl]
Writes results/summary.json and prints markdown tables.
"""

from __future__ import annotations

import json
import math
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


TASKS = {t["id"]: t for t in json.loads((ROOT / "harness" / "tasks.json").read_text(encoding="utf-8"))}


def regrade_question(r: dict) -> None:
    """Re-apply the current answer rubric to stored answers (rubric fixes apply to all conditions alike)."""
    task = TASKS[r["task"]]
    if task["kind"] != "question":
        return
    text = r.get("answer") or ""
    run_dir = ROOT / "runs" / r.get("sequence_id", r["run_id"])
    full = run_dir / (f"result_{r['step']}_{r['task']}.json" if "sequence_id" in r else "result.json")
    try:
        text = json.loads(full.read_text(encoding="utf-8")).get("result") or text
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    text = text.lower()
    ok = all(any(k.lower() in text for k in g) for g in task["answer_must_mention"])
    r["grade"]["answer_ok"] = ok
    r["grade"]["success"] = ok and r["grade"].get("no_changes", True)


def load(path: Path) -> list[dict]:
    recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    recs = [r for r in recs if r.get("status") == "ok"]
    for r in recs:
        regrade_question(r)
    return recs


# UTC. The Team subscription hit its limit at 21:12 and runs resumed on a Pro subscription;
# the Pro one hit its limit at 22:17 and runs resumed on the Team subscription at ~01:25.
PRO_WINDOW = ("2026-10-09T21:30", "2026-10-10T01:20")


def account(r: dict) -> str:
    return "pro" if PRO_WINDOW[0] < r["ts"] < PRO_WINDOW[1] else "team"


def tokens_in(r: dict) -> int:
    """All input-side tokens processed across every model (main loop + subagents)."""
    return sum((m.get("inputTokens") or 0) + (m.get("cacheReadInputTokens") or 0) + (m.get("cacheCreationInputTokens") or 0)
               for m in r["all_models"].values())


def tokens_out(r: dict) -> int:
    return sum(m.get("outputTokens") or 0 for m in r["all_models"].values())


def metrics(r: dict) -> dict:
    return {"cost": r.get("cost_usd") or 0.0, "tok_in": tokens_in(r), "tok_out": tokens_out(r),
            "peak_ctx": r.get("peak_context") or 0, "turns": r.get("num_turns") or 0,
            "wall_s": r.get("wall_s") or 0, "success": 1.0 if r["grade"]["success"] else 0.0}


def iqr(xs: list[float]) -> tuple[float, float]:
    if len(xs) < 2:
        return xs[0], xs[0]
    q = st.quantiles(xs, n=4, method="inclusive")
    return q[0], q[2]


def gmean(xs: list[float]) -> float:
    xs = [x for x in xs if x > 0]
    return math.exp(sum(map(math.log, xs)) / len(xs)) if xs else float("nan")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results" / "runs.jsonl"
    recs = load(path)
    singles = [r for r in recs if "sequence_id" not in r]
    seqs = [r for r in recs if "sequence_id" in r]

    cell: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in singles:
        cell[(r["condition"], r["task"])].append(metrics(r))

    conds = sorted({c for c, _ in cell}, key=lambda c: (c != "baseline", c))
    tasks = sorted({t for _, t in cell})
    keys = ["cost", "tok_in", "tok_out", "peak_ctx", "turns", "wall_s"]

    per_cell = {}
    for (c, t), ms in cell.items():
        per_cell[f"{c}|{t}"] = {"n": len(ms), "success_rate": st.mean(m["success"] for m in ms),
                                **{k: st.median(m[k] for m in ms) for k in keys},
                                **{f"{k}_iqr": iqr([m[k] for m in ms]) for k in ("cost", "tok_in")}}

    overall = {}
    for c in conds:
        ratios = {k: [] for k in keys}
        for t in tasks:
            a, b = per_cell.get(f"{c}|{t}"), per_cell.get(f"baseline|{t}")
            if a and b:
                for k in keys:
                    if b[k]:
                        ratios[k].append(a[k] / b[k])
        runs = [m for (cc, _), ms in cell.items() if cc == c for m in ms]
        overall[c] = {"n_runs": len(runs), "success_rate": st.mean(m["success"] for m in runs),
                      "median_cost": st.median(m["cost"] for m in runs),
                      **{f"{k}_vs_baseline": gmean(v) for k, v in ratios.items()}}

    # Robustness: runs before the rate limit used a Team subscription, later runs a Pro one, whose
    # system context is ~8.6k tokens smaller. Recompute ratios within each account, then pool.
    strat = defaultdict(list)
    for r in singles:
        strat[(r["condition"], r["task"], account(r))].append(metrics(r)["cost"])
    strat_ratio = {}
    for c in conds:
        rs = []
        for t in tasks:
            for a in ("team", "pro"):
                x, b = strat.get((c, t, a)), strat.get(("baseline", t, a))
                if x and b:
                    rs.append(st.median(x) / st.median(b))
        strat_ratio[c] = gmean(rs)
        if c in overall:
            overall[c]["cost_vs_baseline_stratified"] = strat_ratio[c]

    # 95% bootstrap CI for the pooled cost ratio: resample runs within every cell.
    rng = random.Random(0)
    for c in conds:
        draws = []
        for _ in range(2000):
            rs = []
            for t in tasks:
                x, b = cell.get((c, t)), cell.get(("baseline", t))
                if x and b:
                    mx = st.median(rng.choice(x)["cost"] for _ in x)
                    mb = st.median(rng.choice(b)["cost"] for _ in b)
                    rs.append(mx / mb)
            draws.append(gmean(rs))
        draws.sort()
        overall[c]["cost_ci95"] = (draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws)) - 1])

    seq_summary = {}
    by_seq = defaultdict(list)
    for r in seqs:
        by_seq[r["sequence_id"]].append(r)
    for sid, steps in by_seq.items():
        steps.sort(key=lambda r: r["step"])
        # On resume, reported cost/usage is cumulative for the session (Claude Code >= 2.1.277),
        # so the final step carries the session total.
        seq_summary[sid] = {"steps": len(steps), "success": sum(r["grade"]["success"] for r in steps),
                            "total_cost": steps[-1]["cost_usd"], "total_tok_in": tokens_in(steps[-1]),
                            "peak_ctx_by_step": [r.get("peak_context") for r in steps],
                            "cost_by_step": [r["cost_usd"] for r in steps]}
    fresh_total = {k: sum(per_cell[f"baseline|{t}"][k] for t in tasks if f"baseline|{t}" in per_cell)
                   for k in ("cost", "tok_in")}

    out = {"per_cell": per_cell, "overall": overall, "sequences": seq_summary, "baseline_fresh_total": fresh_total}
    (path.parent / f"summary_{path.stem}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"## Overall ({len(singles)} single runs)\n")
    print("| condition | runs | success | median cost $ | cost × | 95% CI | cost × (stratified) | input tok × | output tok × | peak ctx × | turns × |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for c, o in overall.items():
        print(f"| {c} | {o['n_runs']} | {o['success_rate']:.0%} | {o['median_cost']:.3f} | {o['cost_vs_baseline']:.2f} | "
              f"{o['cost_ci95'][0]:.2f}–{o['cost_ci95'][1]:.2f} | {o['cost_vs_baseline_stratified']:.2f} | "
              f"{o['tok_in_vs_baseline']:.2f} | {o['tok_out_vs_baseline']:.2f} | {o['peak_ctx_vs_baseline']:.2f} | {o['turns_vs_baseline']:.2f} |")
    print("\n## Per task (median)\n")
    print("| condition | task | n | success | cost $ | input tok | output tok | peak ctx | turns |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in conds:
        for t in tasks:
            p = per_cell.get(f"{c}|{t}")
            if p:
                print(f"| {c} | {t} | {p['n']} | {p['success_rate']:.0%} | {p['cost']:.3f} | {p['tok_in']:,.0f} | "
                      f"{p['tok_out']:,.0f} | {p['peak_ctx']:,.0f} | {p['turns']:.0f} |")
    if seq_summary:
        print("\n## Long session vs fresh sessions\n")
        print(f"baseline fresh sessions, sum of task medians: ${fresh_total['cost']:.3f}, {fresh_total['tok_in']:,.0f} input tokens")
        for sid, s in seq_summary.items():
            print(f"{sid}: ${s['total_cost']:.3f}, {s['total_tok_in']:,.0f} input tokens, {s['success']}/{s['steps']} ok, "
                  f"peak ctx by step {s['peak_ctx_by_step']}")


if __name__ == "__main__":
    main()

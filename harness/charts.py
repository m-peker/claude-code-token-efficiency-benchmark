"""Render article figures (English and Turkish) from results/summary_runs.json and runs.jsonl.

Usage: python harness/charts.py
Writes figures/<name>_<lang>.png
"""

from __future__ import annotations

import json
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIG = ROOT / "figures"

# Reference palette (dataviz skill), light mode.
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

MAIN = ["baseline", "specific_prompt", "claudemd_lean", "claudemd_bloated", "mcp_heavy", "mcp_heavy_eager",
        "effort_low", "model_haiku", "model_opus", "best_practice"]
MODEL_MIX = ["model_haiku", "plan_sonnet_exec_haiku", "baseline", "plan_mode", "plan_opus_exec_sonnet",
             "plan_sonnet_exec_opus", "model_opus"]
CODE_TASKS = ["t1_intrange", "t2_help_order", "t3_completion_hash", "t4_keyvalue", "t6_default_map"]

N_RUNS = [0]

LABELS = {
    "en": {
        "baseline": "Baseline (vague prompt, no CLAUDE.md)",
        "specific_prompt": "Specific prompt",
        "claudemd_lean": "Lean CLAUDE.md (20 lines)",
        "claudemd_bloated": "Bloated CLAUDE.md (1,100 lines)",
        "mcp_heavy": "5 MCP servers (tool search on)",
        "mcp_heavy_eager": "5 MCP servers (tool search off)",
        "effort_low": "Effort: low",
        "model_haiku": "Model: Haiku",
        "model_opus": "Model: Opus",
        "best_practice": "Specific prompt + lean CLAUDE.md",
        "plan_mode": "Plan mode (plan, then execute)",
        "mm_model_haiku": "Haiku only", "mm_baseline": "Sonnet only", "mm_model_opus": "Opus only",
        "mm_plan_mode": "Sonnet plans → Sonnet codes", "mm_plan_opus_exec_sonnet": "Opus plans → Sonnet codes",
        "mm_plan_sonnet_exec_haiku": "Sonnet plans → Haiku codes", "mm_plan_sonnet_exec_opus": "Sonnet plans → Opus codes",
        "fig4_title": "Mixing models: who plans, who codes",
        "fig4_x": "Cost multiplier vs. Sonnet only (geometric mean over 5 coding tasks)",
        "compact": "Long session + /compact",
        "fig1_title": "Cost per task relative to baseline",
        "fig1_x": "Cost multiplier (geometric mean over 6 tasks; 1.0 = baseline)",
        "cheaper": "Cheaper than baseline", "costlier": "More expensive than baseline",
        "success": "success",
        "fig2_title": "Context already loaded on the first request",
        "fig2_x": "Tokens in context before Claude reads a single file (median)",
        "fig3_title": "Six tasks: one long session vs. a fresh session per task",
        "fig3_x": "Task number", "fig3_y": "Cumulative cost (USD, list-price estimate)",
        "long": "One long session", "fresh": "Fresh session per task",
        "src": "Source: {n} headless Claude Code runs (Claude Code 2.1.295) on pallets/click, 5 repetitions per cell.",
    },
    "tr": {
        "baseline": "Baseline (muğlak prompt, CLAUDE.md yok)",
        "specific_prompt": "Net prompt",
        "claudemd_lean": "Sade CLAUDE.md (20 satır)",
        "claudemd_bloated": "Şişkin CLAUDE.md (1.100 satır)",
        "mcp_heavy": "5 MCP sunucusu (tool search açık)",
        "mcp_heavy_eager": "5 MCP sunucusu (tool search kapalı)",
        "effort_low": "Effort: low",
        "model_haiku": "Model: Haiku",
        "model_opus": "Model: Opus",
        "best_practice": "Net prompt + sade CLAUDE.md",
        "plan_mode": "Plan mode (önce plan, sonra uygulama)",
        "mm_model_haiku": "Sadece Haiku", "mm_baseline": "Sadece Sonnet", "mm_model_opus": "Sadece Opus",
        "mm_plan_mode": "Sonnet planlar → Sonnet kodlar", "mm_plan_opus_exec_sonnet": "Opus planlar → Sonnet kodlar",
        "mm_plan_sonnet_exec_haiku": "Sonnet planlar → Haiku kodlar", "mm_plan_sonnet_exec_opus": "Sonnet planlar → Opus kodlar",
        "fig4_title": "Model karışımı: kim planlar, kim kodlar",
        "fig4_x": "Maliyet çarpanı, sadece Sonnet'e göre (5 kod görevinin geometrik ortalaması)",
        "compact": "Uzun oturum + /compact",
        "fig1_title": "Görev başına maliyet (baseline'a göre)",
        "fig1_x": "Maliyet çarpanı (6 görevin geometrik ortalaması; 1,0 = baseline)",
        "cheaper": "Baseline'dan ucuz", "costlier": "Baseline'dan pahalı",
        "success": "başarı",
        "fig2_title": "İlk istekte context'e zaten yüklenmiş olan",
        "fig2_x": "Claude tek bir dosya okumadan önce context'teki token (medyan)",
        "fig3_title": "Altı görev: tek uzun oturum vs. her göreve yeni oturum",
        "fig3_x": "Görev sırası", "fig3_y": "Kümülatif maliyet (USD, liste fiyatı tahmini)",
        "long": "Tek uzun oturum", "fresh": "Her göreve yeni oturum",
        "src": "Kaynak: pallets/click üzerinde {n} headless Claude Code çalıştırması (Claude Code 2.1.295), hücre başına 5 tekrar.",
    },
}


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=10, length=0)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def fmt(x: float, lang: str, digits: int = 2) -> str:
    s = f"{x:.{digits}f}"
    return s.replace(".", ",") if lang == "tr" else s


def finish(fig, ax, title: str, src: str, path: Path) -> None:
    fig.text(0.01, 0.97, title, fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.01, 0.01, src.format(n=N_RUNS[0]), fontsize=8.5, color=MUTED, va="bottom")
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def fig_cost(summary: dict, lang: str) -> None:
    L = LABELS[lang]
    rows = sorted(((c, o) for c, o in summary["overall"].items() if c in MAIN), key=lambda x: x[1]["cost_vs_baseline"])
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(rows) + 1.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.36, right=0.86, top=0.91, bottom=0.14)
    style(ax)
    ys = range(len(rows))
    vals = [o["cost_vs_baseline"] for _, o in rows]
    colors = [MUTED if c == "baseline" else (BLUE if v < 1 else ORANGE) for (c, _), v in zip(rows, vals)]
    ax.barh(list(ys), vals, height=0.62, color=colors, edgecolor=SURFACE, linewidth=2)
    ax.axvline(1, color=INK2, linewidth=1, linestyle=(0, (3, 3)))
    for y, (c, o), v in zip(ys, rows, vals):
        ax.text(v + 0.04, y, f"×{fmt(v, lang)}   ·   {o['success_rate']:.0%} {L['success']}",
                va="center", fontsize=9.5, color=INK2,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    ax.set_yticks(list(ys), [L[c] for c, _ in rows], color=INK, fontsize=10.5)
    ax.set_xlabel(L["fig1_x"], color=INK2, fontsize=9.5)
    ax.set_xlim(0, max(vals) * 1.45)
    handles = [plt.Rectangle((0, 0), 1, 1, color=BLUE), plt.Rectangle((0, 0), 1, 1, color=ORANGE)]
    ax.legend(handles, [L["cheaper"], L["costlier"]], loc="lower right", frameon=False, fontsize=9, labelcolor=INK2)
    finish(fig, ax, L["fig1_title"], L["src"], FIG / f"fig1_cost_{lang}.png")


def fig_context(runs: list[dict], lang: str) -> None:
    L = LABELS[lang]
    by = defaultdict(list)
    for r in runs:
        if "sequence_id" not in r and r.get("first_context") and r["condition"] in MAIN:
            by[r["condition"]].append(r["first_context"])
    rows = sorted(((c, st.median(v)) for c, v in by.items()), key=lambda x: x[1])
    base = dict(rows)["baseline"]
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(rows) + 1.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.36, right=0.9, top=0.88, bottom=0.16)
    style(ax)
    ys = range(len(rows))
    colors = [MUTED if c == "baseline" else (ORANGE if v > base * 1.1 else BLUE) for c, v in rows]
    ax.barh(list(ys), [v for _, v in rows], height=0.62, color=colors, edgecolor=SURFACE, linewidth=2)
    for y, (c, v) in zip(ys, rows):
        ax.text(v + base * 0.03, y, f"{v / 1000:.1f}k".replace(".", "," if lang == "tr" else "."), va="center", fontsize=9.5, color=INK2)
    ax.set_yticks(list(ys), [L[c] for c, _ in rows], color=INK, fontsize=10.5)
    ax.set_xlabel(L["fig2_x"], color=INK2, fontsize=9.5)
    ax.set_xlim(0, max(v for _, v in rows) * 1.15)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x / 1000:.0f}k"))
    finish(fig, ax, L["fig2_title"], L["src"], FIG / f"fig2_context_{lang}.png")


def fig_session(summary: dict, runs: list[dict], lang: str) -> None:
    L = LABELS[lang]
    seqs = {k: v for k, v in summary["sequences"].items() if v["steps"] == 6}
    if not seqs:
        return

    def cum(prefix: str) -> list[float]:
        group = [v for k, v in seqs.items() if k.startswith(prefix + "__")]
        return [st.median(v["cost_by_step"][i] for v in group) for i in range(6)] if group else []

    long_cum, compact_cum = cum("long_session"), cum("long_session_compact")
    first = next(k for k in seqs if k.startswith("long_session__"))
    order = [r["task"] for r in sorted((r for r in runs if r.get("sequence_id") == first), key=lambda r: r["step"])]
    fresh, total = [], 0.0
    for t in order:
        total += summary["per_cell"][f"baseline|{t}"]["cost"]
        fresh.append(total)
    xs = list(range(1, len(order) + 1))
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=SURFACE)
    fig.subplots_adjust(left=0.1, right=0.9, top=0.86, bottom=0.18)
    style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.plot(xs, fresh, color=BLUE, linewidth=2, marker="o", markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
    ax.plot(xs, long_cum, color=ORANGE, linewidth=2, marker="o", markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
    names = [L["fresh"], L["long"]]
    ends = [fresh[-1], long_cum[-1]]
    if compact_cum:
        ax.plot(xs, compact_cum, color=AQUA, linewidth=2, marker="o", markersize=7, markeredgecolor=SURFACE, markeredgewidth=2)
        names.append(L["compact"])
        ends.append(compact_cum[-1])
    # The legend names the lines; end labels carry only the totals, nudged apart when close.
    top = max(ends) * 1.15
    placed: list[float] = []
    for v in sorted(ends, reverse=True):
        y = v
        while any(abs(y - q) < top * 0.05 for q in placed):
            y -= top * 0.01
        placed.append(y)
        ax.text(xs[-1] + 0.15, y, f"${fmt(v, lang)}", va="center", fontsize=10, color=INK2)
    ax.set_xticks(xs)
    ax.set_xlabel(L["fig3_x"], color=INK2, fontsize=9.5)
    ax.set_ylabel(L["fig3_y"], color=INK2, fontsize=9.5)
    ax.set_ylim(0, max(fresh[-1], long_cum[-1], *(compact_cum or [0])) * 1.15)
    ax.legend(names, loc="upper left", frameon=False, fontsize=9, labelcolor=INK2)
    finish(fig, ax, L["fig3_title"], L["src"], FIG / f"fig3_session_{lang}.png")


def fig_models(summary: dict, lang: str) -> None:
    L = LABELS[lang]
    pc = summary["per_cell"]
    rows = []
    for c in MODEL_MIX:
        cells = [pc.get(f"{c}|{t}") for t in CODE_TASKS]
        base = [pc.get(f"baseline|{t}") for t in CODE_TASKS]
        if not all(cells):
            continue
        ratio = math.exp(sum(math.log(a["cost"] / b["cost"]) for a, b in zip(cells, base)) / len(cells))
        n = sum(a["n"] for a in cells)
        success = sum(a["success_rate"] * a["n"] for a in cells) / n
        rows.append((c, ratio, success))
    rows.sort(key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(rows) + 1.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.32, right=0.86, top=0.86, bottom=0.18)
    style(ax)
    ys = list(range(len(rows)))
    colors = [MUTED if c == "baseline" else (BLUE if v < 1 else ORANGE) for c, v, _ in rows]
    ax.barh(ys, [v for _, v, _ in rows], height=0.62, color=colors, edgecolor=SURFACE, linewidth=2)
    ax.axvline(1, color=INK2, linewidth=1, linestyle=(0, (3, 3)))
    for y, (c, v, sr) in zip(ys, rows):
        ax.text(v + 0.04, y, f"×{fmt(v, lang)}   ·   {sr:.0%} {L['success']}", va="center", fontsize=9.5, color=INK2,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))
    ax.set_yticks(ys, [L[f"mm_{c}"] for c, _, _ in rows], color=INK, fontsize=10.5)
    ax.set_xlabel(L["fig4_x"], color=INK2, fontsize=9.5)
    ax.set_xlim(0, max(v for _, v, _ in rows) * 1.5)
    finish(fig, ax, L["fig4_title"], L["src"], FIG / f"fig4_models_{lang}.png")


def main() -> None:
    FIG.mkdir(exist_ok=True)
    summary = json.loads((RESULTS / "summary_runs.json").read_text(encoding="utf-8"))
    runs = [json.loads(l) for l in (RESULTS / "runs.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    runs = [r for r in runs if r.get("status") == "ok"]
    N_RUNS[0] = len(runs)
    for lang in ("en", "tr"):
        fig_cost(summary, lang)
        fig_context(runs, lang)
        fig_session(summary, runs, lang)
        fig_models(summary, lang)
    print("figures written to", FIG)


if __name__ == "__main__":
    main()

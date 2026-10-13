"""Run the Claude Code token-efficiency benchmark.

Each run copies the template repo into a fresh workspace, applies one
condition (prompt style, CLAUDE.md variant, MCP servers, model, effort),
runs `claude -p` headlessly, records the JSON result plus per-request context
sizes from the session transcript, and grades the outcome with hidden tests.

Results are appended to results/runs.jsonl; completed run ids are skipped, so
the script can be stopped and restarted at any time.

Usage:
  python harness/runner.py                      # full study: all conditions, 5 reps
  python harness/runner.py --only baseline,specific_prompt --tasks t1_intrange --reps 1

Set CLAUDE_BIN to pin a specific Claude Code binary (the study used 2.1.295).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "harness"
TEMPLATE = ROOT / "template"
GRADING = ROOT / "grading"
RUNS_DIR = ROOT / "runs"
RESULTS = ROOT / "results" / "runs.jsonl"
VENV_SCRIPTS = ROOT / "venv" / ("Scripts" if os.name == "nt" else "bin")
PYTHON = VENV_SCRIPTS / ("python.exe" if os.name == "nt" else "python")
CLAUDE = os.environ.get("CLAUDE_BIN") or shutil.which("claude") or "claude"
TRANSCRIPTS = Path.home() / ".claude" / "projects"
MCP_DIR = HARNESS / "mcp" / "node_modules"

TASKS = {t["id"]: t for t in json.loads((HARNESS / "tasks.json").read_text(encoding="utf-8"))}

BASE = {"prompt": "vague", "claudemd": None, "mcp": False, "model": "sonnet", "effort": None, "env": {},
        "plan": False, "plan_model": None, "compact_between": False}
CONDITIONS = {
    "baseline": {},
    "specific_prompt": {"prompt": "specific"},
    "claudemd_lean": {"claudemd": "lean"},
    "claudemd_bloated": {"claudemd": "bloated"},
    "mcp_heavy": {"mcp": True},
    "mcp_heavy_eager": {"mcp": True, "env": {"ENABLE_TOOL_SEARCH": "false"}},
    "effort_low": {"effort": "low"},
    "model_haiku": {"model": "haiku"},
    "model_opus": {"model": "opus"},
    "best_practice": {"prompt": "specific", "claudemd": "lean"},
    # Plan mode: a read-only planning call, then the plan is executed in the same session.
    "plan_mode": {"plan": True},
    # Model mixing: plan with one model, execute with another (opusplan = Opus plans, Sonnet executes).
    "plan_opus_exec_sonnet": {"plan": True, "plan_model": "opus", "model": "sonnet"},
    "plan_sonnet_exec_haiku": {"plan": True, "plan_model": "sonnet", "model": "haiku"},
    "plan_sonnet_exec_opus": {"plan": True, "plan_model": "sonnet", "model": "opus"},
    # Sequence conditions: all tasks in one resumed session (see run_sequence).
    "long_session": {},
    "long_session_compact": {"compact_between": True},
}
SEQUENCE_CONDITIONS = {"long_session", "long_session_compact"}
# Planning a pure Q&A task is not meaningful.
CODE_ONLY_CONDITIONS = {"plan_mode", "plan_opus_exec_sonnet", "plan_sonnet_exec_haiku", "plan_sonnet_exec_opus"}
EXECUTE_PLAN_PROMPT = "The plan is approved. Implement it now."

CLAUDE_VERSION = "unknown"


def claude_version() -> str:
    try:
        out = subprocess.run([CLAUDE, "--version"], capture_output=True, text=True).stdout
    except OSError:
        sys.exit(f"Claude Code not found at {CLAUDE!r}; install it or set CLAUDE_BIN")
    return out.split()[0] if out else "unknown"


RATE_LIMIT_RE = re.compile(r"usage limit|rate limit|limit reached|429|overloaded|resets", re.I)
_write_lock = threading.Lock()


def rmtree(path: Path) -> None:
    """shutil.rmtree that also removes read-only files (git objects on Windows)."""
    def onerror(func, p, _):
        os.chmod(p, 0o700)
        func(p)
    if path.exists():
        shutil.rmtree(path, onerror=onerror)


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def condition(name: str) -> dict:
    cfg = {**BASE, **CONDITIONS[name]}
    cfg["env"] = {**BASE["env"], **CONDITIONS[name].get("env", {})}
    return cfg


def done_ids() -> set[str]:
    if not RESULTS.exists():
        return set()
    ids = set()
    for line in RESULTS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec.get("status") != "rate_limited":
                ids.add(rec["run_id"])
    return ids


def append_result(rec: dict) -> None:
    with _write_lock:
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        with RESULTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")


def git(ws: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=ws, capture_output=True, text=True, check=True).stdout


def archive_workspace(ws: Path, name: str = "final") -> None:
    """Keep the diff against the starting commit, then delete the workspace copy."""
    diff = subprocess.run(["git", "diff", "HEAD" if name == "final" else "HEAD~1"], cwd=ws, capture_output=True, text=True).stdout
    (ws.parent / f"{name}.diff").write_text(diff, encoding="utf-8")


def make_workspace(run_id: str, cfg: dict) -> Path:
    ws = RUNS_DIR / run_id / "ws"
    if ws.parent.exists():
        rmtree(ws.parent)
    shutil.copytree(TEMPLATE, ws)
    if cfg["claudemd"]:
        shutil.copy(HARNESS / "claudemd" / f"{cfg['claudemd']}.md", ws / "CLAUDE.md")
        git(ws, "add", "CLAUDE.md")
        git(ws, "-c", "user.name=bench", "-c", "user.email=bench@example.com", "commit", "-q", "-m", "Add CLAUDE.md")
    return ws


def mcp_config(ws: Path) -> Path:
    def server(pkg: str, entry: str, *args: str, env: dict | None = None) -> dict:
        return {"command": "node", "args": [str(MCP_DIR / pkg / entry), *args], "env": env or {}}

    cfg = {"mcpServers": {
        "everything": server("@modelcontextprotocol/server-everything", "dist/index.js"),
        "memory": server("@modelcontextprotocol/server-memory", "dist/index.js",
                         env={"MEMORY_FILE_PATH": str(ws.parent / "memory.json")}),
        "filesystem": server("@modelcontextprotocol/server-filesystem", "dist/index.js", str(ws)),
        "sequential-thinking": server("@modelcontextprotocol/server-sequential-thinking", "dist/index.js"),
        "playwright": server("@playwright/mcp", "cli.js", "--headless"),
    }}
    path = ws.parent / "mcp.json"
    path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return path


def claude_env(ws: Path, cfg: dict) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in {"ANTHROPIC_API_KEY", "CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"}}
    env.update({
        "PYTHONPATH": str(ws / "src"),
        "PATH": str(VENV_SCRIPTS) + os.pathsep + env.get("PATH", ""),
        "VIRTUAL_ENV": str(ROOT / "venv"),
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "DISABLE_AUTOUPDATER": "1",
    })
    env.update(cfg["env"])
    return env


def claude_cmd(prompt: str, ws: Path, cfg: dict, session_id: str, resume: bool,
               permission_mode: str = "bypassPermissions", slash: bool = False) -> list[str]:
    cmd = [CLAUDE, "-p", prompt, "--output-format", "json",
           "--model", cfg["model"],
           "--setting-sources", "project",
           "--strict-mcp-config",
           "--permission-mode", permission_mode,
           "--max-turns", "80"]
    if not slash:  # skills off for reproducibility; built-in commands like /compact need them on
        cmd.append("--disable-slash-commands")
    cmd += ["--resume", session_id] if resume else ["--session-id", session_id]
    if cfg["effort"]:
        cmd += ["--effort", cfg["effort"]]
    if cfg["mcp"]:
        cmd += ["--mcp-config", str(mcp_config(ws))]
    return cmd


def transcript_stats(ws: Path, session_id: str) -> dict:
    """Per-request context sizes from the session transcript (main loop only)."""
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(ws))
    candidates = list(TRANSCRIPTS.glob(f"*/{session_id}.jsonl"))
    exact = TRANSCRIPTS / slug / f"{session_id}.jsonl"
    path = exact if exact.exists() else (candidates[0] if candidates else None)
    if not path:
        return {}
    seen, contexts, tools = set(), [], {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = rec.get("message") or {}
        if rec.get("type") != "assistant" or not isinstance(msg, dict):
            continue
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools[block["name"]] = tools.get(block["name"], 0) + 1
        mid, u = msg.get("id"), msg.get("usage")
        if not u or mid in seen:
            continue
        seen.add(mid)
        contexts.append(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
    return {"api_calls": len(contexts), "first_context": contexts[0] if contexts else None,
            "peak_context": max(contexts) if contexts else None, "tool_calls": tools,
            "transcript": str(path)}


def run_tests(ws: Path, *args: str) -> tuple[bool, str]:
    env = {**os.environ, "PYTHONPATH": str(ws / "src")}
    env.pop("ANTHROPIC_API_KEY", None)
    p = subprocess.run([str(PYTHON), "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
                       cwd=ws, capture_output=True, text=True, env=env, timeout=600)
    lines = (p.stdout + p.stderr).strip().splitlines()
    failed = [l for l in lines if l.startswith(("FAILED", "ERROR"))]
    return p.returncode == 0, " | ".join(failed[:5] + lines[-1:])


def grade(ws: Path, task: dict, answer: str) -> dict:
    status = git(ws, "status", "--porcelain")
    diff = git(ws, "diff", "--shortstat")
    out = {"changed_files": len([l for l in status.splitlines() if l.strip()]), "diffstat": diff.strip()}
    if task["kind"] == "question":
        groups = task["answer_must_mention"]  # each group: any one of its terms is enough
        mentioned = [next(k for k in g if k.lower() in answer.lower()) for g in groups if any(k.lower() in answer.lower() for k in g)]
        out.update(answer_ok=len(mentioned) == len(groups), mentioned=mentioned,
                   no_changes=out["changed_files"] == 0)
        out["success"] = out["answer_ok"] and out["no_changes"]
        return out
    hidden = ws / "tests" / task["hidden_test"]
    shutil.copy(GRADING / task["hidden_test"], hidden)
    try:
        out["hidden_ok"], out["hidden_summary"] = run_tests(ws, f"tests/{task['hidden_test']}")
        out["suite_ok"], out["suite_summary"] = run_tests(ws, "--ignore", f"tests/{task['hidden_test']}")
        if not out["suite_ok"]:  # retry once to separate real regressions from flaky tests
            out["suite_first_try"] = out["suite_summary"]
            out["suite_ok"], out["suite_summary"] = run_tests(ws, "--ignore", f"tests/{task['hidden_test']}")
    finally:
        hidden.unlink(missing_ok=True)
    out["success"] = out["hidden_ok"] and out["suite_ok"]
    return out


def invoke(prompt: str, ws: Path, cfg: dict, session_id: str, resume: bool,
           permission_mode: str = "bypassPermissions", slash: bool = False) -> tuple[dict | None, str, float]:
    t0 = time.time()
    try:
        p = subprocess.run(claude_cmd(prompt, ws, cfg, session_id, resume, permission_mode, slash), cwd=ws, env=claude_env(ws, cfg),
                           capture_output=True, text=True, encoding="utf-8", timeout=1800)
        raw = p.stdout.strip()
        err = p.stderr.strip()
    except subprocess.TimeoutExpired as e:
        return None, f"timeout: {e}", time.time() - t0
    try:
        return json.loads(raw.splitlines()[-1]), err, time.time() - t0
    except (json.JSONDecodeError, IndexError):
        return None, (raw + "\n" + err)[-2000:], time.time() - t0


def summarize(result: dict | None) -> dict:
    if not result:
        return {}
    u = result.get("usage") or {}
    mu = result.get("modelUsage") or {}
    return {
        "is_error": result.get("is_error"), "subtype": result.get("subtype"),
        "num_turns": result.get("num_turns"), "duration_ms": result.get("duration_ms"),
        "cost_usd": result.get("total_cost_usd"),
        "main_input": u.get("input_tokens"), "main_output": u.get("output_tokens"),
        "main_cache_write": u.get("cache_creation_input_tokens"), "main_cache_read": u.get("cache_read_input_tokens"),
        "all_models": {m: {k: v.get(k) for k in ("inputTokens", "outputTokens", "cacheReadInputTokens",
                                                   "cacheCreationInputTokens", "costUSD", "thinkingTokens")}
                       for m, v in mu.items()},
        "subagents_spawned": (result.get("subagent_stats") or {}).get("spawned"),
        "permission_denials": len(result.get("permission_denials") or []),
        "answer": (result.get("result") or "")[:4000],
    }


def is_rate_limited(result: dict | None, err: str) -> bool:
    text = (json.dumps(result) if result else "") + err
    if result and not result.get("is_error"):
        return False
    return bool(RATE_LIMIT_RE.search(text))


def run_single(run_id: str, cond: str, task_id: str, rep: int) -> dict:
    cfg, task = condition(cond), TASKS[task_id]
    ws = make_workspace(run_id, cfg)
    session_id = str(uuid.uuid4())
    log(f"start {run_id}")
    plan_info = {}
    if cfg["plan"]:
        plan_cfg = {**cfg, "model": cfg["plan_model"] or cfg["model"]}
        plan, err, plan_wall = invoke(task[cfg["prompt"]], ws, plan_cfg, session_id, resume=False, permission_mode="plan")
        (ws.parent / "plan.json").write_text(json.dumps(plan, indent=2) if plan else err, encoding="utf-8")
        if is_rate_limited(plan, err) or not plan:
            result, wall = plan, plan_wall
        else:
            plan_info = {"plan_cost_usd": plan.get("total_cost_usd"), "plan_turns": plan.get("num_turns"),
                         "plan_changed_files": len(git(ws, "status", "--porcelain").splitlines())}
            result, err, wall = invoke(EXECUTE_PLAN_PROMPT, ws, cfg, session_id, resume=True)
            wall += plan_wall
            if result:  # cost/usage on resume are cumulative; turns are per call
                result["num_turns"] = (result.get("num_turns") or 0) + (plan.get("num_turns") or 0)
    else:
        result, err, wall = invoke(task[cfg["prompt"]], ws, cfg, session_id, resume=False)
    (ws.parent / "result.json").write_text(json.dumps(result, indent=2) if result else err, encoding="utf-8")
    rec = {"run_id": run_id, "condition": cond, "task": task_id, "rep": rep, "session_id": session_id,
           "config": cfg, "wall_s": round(wall, 1), "ts": datetime.now(timezone.utc).isoformat(),
           "claude_version": CLAUDE_VERSION}
    if is_rate_limited(result, err):
        rec["status"] = "rate_limited"
        rec["error"] = err[-500:] or (result or {}).get("result", "")[:500]
        return rec
    rec["status"] = "ok" if result else "crash"
    if not result:
        rec["error"] = err[-1000:]
    rec.update(summarize(result))
    rec.update(plan_info)
    rec.update(transcript_stats(ws, session_id))
    rec["grade"] = grade(ws, task, (result or {}).get("result") or "")
    archive_workspace(ws)
    rmtree(ws)
    log(f"done  {run_id}: success={rec['grade']['success']} cost=${rec.get('cost_usd') or 0:.3f} turns={rec.get('num_turns')}")
    return rec


def run_sequence(run_id: str, cond: str, rep: int, task_ids: list[str]) -> list[dict]:
    """Run all tasks one after another in a single resumed session."""
    cfg = condition(cond)
    ws = make_workspace(run_id, cfg)
    session_id = str(uuid.uuid4())
    recs = []
    for i, task_id in enumerate(task_ids):
        task = TASKS[task_id]
        log(f"start {run_id} step {i + 1}/{len(task_ids)} {task_id}")
        result, err, wall = invoke(task[cfg["prompt"]], ws, cfg, session_id, resume=i > 0)
        (ws.parent / f"result_{i + 1}_{task_id}.json").write_text(json.dumps(result, indent=2) if result else err, encoding="utf-8")
        rec = {"run_id": f"{run_id}__{i + 1}_{task_id}", "sequence_id": run_id, "step": i + 1, "condition": cond,
               "task": task_id, "rep": rep, "session_id": session_id, "config": cfg, "wall_s": round(wall, 1),
               "ts": datetime.now(timezone.utc).isoformat(), "claude_version": CLAUDE_VERSION}
        if is_rate_limited(result, err):
            rec["status"] = "rate_limited"
            rec["error"] = err[-500:]
            return [rec]  # discard the partial sequence; it will be rerun from scratch
        rec["status"] = "ok" if result else "crash"
        rec.update(summarize(result))
        rec.update(transcript_stats(ws, session_id))
        rec["grade"] = grade(ws, task, (result or {}).get("result") or "")
        # Commit the step's work so later steps start from a clean tree and
        # grading of later tasks is unaffected by earlier untracked files.
        git(ws, "add", "-A")
        git(ws, "-c", "user.name=bench", "-c", "user.email=bench@example.com", "commit", "-q", "--allow-empty", "-m", f"step {i + 1}")
        archive_workspace(ws, f"step{i + 1}_{task_id}")
        if cfg["compact_between"] and i < len(task_ids) - 1:
            compact, err, _ = invoke("/compact", ws, cfg, session_id, resume=True, slash=True)
            if compact and "isn't available" in (compact.get("result") or ""):
                raise RuntimeError("/compact did not run")
            if is_rate_limited(compact, err):
                return [{**rec, "status": "rate_limited", "error": err[-500:]}]
            rec["compact_cost_cumulative"] = (compact or {}).get("total_cost_usd")
        recs.append(rec)
        log(f"done  {rec['run_id']}: success={rec['grade']['success']} cost=${rec.get('cost_usd') or 0:.3f}")
    rmtree(ws)
    return recs


def main() -> None:
    global RESULTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--only", default=",".join(CONDITIONS))
    ap.add_argument("--tasks", default=",".join(TASKS))
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--results", default=str(RESULTS))
    ap.add_argument("--rate-limit-wait", type=int, default=1800, help="seconds to pause after a rate limit")
    args = ap.parse_args()
    RESULTS = Path(args.results)
    global CLAUDE_VERSION
    CLAUDE_VERSION = claude_version()

    conds, task_ids = args.only.split(","), args.tasks.split(",")
    rng = random.Random(args.seed)
    jobs = []
    for rep in range(1, args.reps + 1):
        batch = [("single", f"{c}__{t}__r{rep}", c, t, rep) for c in conds if c not in SEQUENCE_CONDITIONS for t in task_ids
                 if not (c in CODE_ONLY_CONDITIONS and TASKS[t]["kind"] == "question")]
        batch += [("seq", f"{c}__r{rep}", c, None, rep) for c in conds if c in SEQUENCE_CONDITIONS]
        rng.shuffle(batch)  # interleave conditions so time-of-day effects spread evenly
        jobs += batch

    pause_until = [0.0]

    def worker(job):
        kind, run_id, cond, task_id, rep = job
        while True:
            done = done_ids()
            if (kind == "single" and run_id in done) or (kind == "seq" and any(d.startswith(run_id + "__") for d in done)):
                return
            if time.time() < pause_until[0]:
                time.sleep(30)
                continue
            try:
                recs = [run_single(run_id, cond, task_id, rep)] if kind == "single" else run_sequence(run_id, cond, rep, task_ids)
            except Exception as e:  # keep the other workers going; the job is retried on the next invocation
                log(f"ERROR {run_id}: {e!r}")
                return
            for rec in recs:
                append_result(rec)
            if recs and recs[-1]["status"] == "rate_limited":
                log(f"rate limited on {run_id}; pausing {args.rate_limit_wait}s")
                pause_until[0] = time.time() + args.rate_limit_wait
                continue
            return

    log(f"{len(jobs)} jobs, {args.workers} workers")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(worker, jobs))
    log("all done")


if __name__ == "__main__":
    sys.exit(main())

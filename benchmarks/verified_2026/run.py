"""Reproducible private benchmark commands, with a persistent 12-attempt ceiling."""
import argparse
import html
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .audit import digest, save
from .tasks import ARMS, COMMON, TASKS, TRANSFER, compose

HERE = Path(__file__).resolve().parent
SURFACE_LABEL = "PROMPT-ONLY SYNTHETIC"
SUPER_PROXY = """Synthetic operationalization of the super-harness instruction chain.
This is a prompt-only comparison, not evidence of installed hook enforcement.
Before solving: maintain the user's entire goal; plan dependent steps; inspect
requirements and trust boundaries; select only necessary capabilities; preserve
full output and readable design; implement the smallest complete solution;
review adversarially against edge cases; refactor without changing behavior;
verify with deterministic tests; distinguish measured facts from assumptions;
finish with completed work and explicit limitations.
Caveman: terse explanation only; never compress code, requirements, errors, negations, or safety checks."""


def capture(command, cwd, env=None, timeout=180):
    start = time.perf_counter()
    try:
        process = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout, check=False)
        out, err, code, timed_out = process.stdout, process.stderr, process.returncode, False
    except subprocess.TimeoutExpired as error:
        out, err, code, timed_out = error.stdout or b"", error.stderr or b"", None, True
    except OSError as error:
        out, err, code, timed_out = b"", str(error).encode(), None, False
    return {"command": [str(x) for x in command], "exit_code": code, "timed_out": timed_out,
            "elapsed_seconds": time.perf_counter() - start,
            "stdout": out.decode("utf-8", "replace"), "stderr": err.decode("utf-8", "replace"),
            "stdout_bytes": len(out), "stderr_bytes": len(err),
            "stdout_sha256": digest(out), "stderr_sha256": digest(err),
            "stdout_hex": out.hex(), "stderr_hex": err.hex()}


def isolated_env(root, inherit_auth=False):
    env = os.environ.copy()
    for key in list(env):
        if (any(word in key.upper() for word in ("TOKEN", "SECRET", "API_KEY", "PROVIDER"))
                and not (inherit_auth and key in ("GH_TOKEN", "GITHUB_TOKEN"))):
            env.pop(key, None)
    for key in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME",
                "XDG_CACHE_HOME", "XDG_DATA_HOME", "TMP", "TEMP", "TMPDIR", "COPILOT_HOME"):
        target = root / key.lower()
        target.mkdir(parents=True, exist_ok=True)
        env[key] = str(target)
    env.update(COPILOT_AUTO_UPDATE="false", USE_TGREP="false", CI="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               PYTHONDONTWRITEBYTECODE="1")
    env.pop("NODE_OPTIONS", None)
    env.pop("BASH_ENV", None)
    return env


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    if (output / "generation-ledger.json").exists() and (output / "manifest.json").exists():
        return json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    for task, prompt in TRANSFER.items():
        path = output / "prompts" / f"transfer-{task}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(COMMON + "\n\n" + prompt, encoding="utf-8")
    sources = {}
    for name, repo in (("ponytail", "DietrichGebert_ponytail"),
                       ("caveman", "JuliusBrussee_caveman")):
        path = output / "upstreams" / repo / "skills" / name / "SKILL.md"
        sources[name] = path.read_text(encoding="utf-8") if path.exists() else ""
    manifest = {"protocol_version": 2, "arms": list(ARMS), "tasks": list(TASKS), "n": 1,
                "scope": "prompt-only synthetic instruction ablation; not full installed harness",
                "super_context": "benchmark-authored operationalization, not private repository text",
                "safety": COMMON, "provider_cache_control": "not exposed; fresh local state only",
                "ceiling": 12, "prompts": [], "missing_sources": [k for k, v in sources.items() if not v]}
    for task in TASKS:
        for arm in ARMS:
            prompt = compose(task, arm, SUPER_PROXY, **sources)
            path = output / "prompts" / task / f"{arm}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(prompt, encoding="utf-8")
            manifest["prompts"].append({"task": task, "arm": arm,
                                        "sha256": digest(prompt.encode()), "bytes": len(prompt.encode())})
    save(output / "manifest.json", manifest)
    return manifest


def extract_answer(raw):
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and isinstance(data.get("solution"), str):
            return data
    except json.JSONDecodeError:
        pass
    texts = []
    for line in raw.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") == "assistant.message":
            content = item.get("data", {}).get("content", "")
            if isinstance(content, str):
                texts.append(content)
        if item.get("type") == "result" and isinstance(item.get("result"), str):
            texts.append(item["result"])
    for text in reversed(texts):
        candidates = [text.strip()]
        fences = text.split("```")
        for index in range(1, len(fences) - 1, 2):
            label, separator, body = fences[index].partition("\n")
            if separator and label.strip() == "json":
                candidates.append(body)
        recovered = []
        for candidate in candidates:
            try:
                value = json.loads(candidate)
                if isinstance(value, dict) and isinstance(value.get("solution"), str):
                    recovered.append(value)
            except json.JSONDecodeError:
                continue
        if recovered:
            if any(value != recovered[0] for value in recovered[1:]):
                raise ValueError("ambiguous complete JSON solutions in final response")
            return recovered[0]
    raise ValueError("no complete JSON solution in provider response")


def coding(output, cli, limit=12):
    """Fail closed until an audited one-generation provider adapter exists."""
    prepare(output)
    blocker = {
        "status": "blocked-before-execution", "model_calls_started": 0,
        "blocker": "Copilot CLI empty available-tools list exposes default tools and may make multiple model calls. A CLI-invocation ceiling is not a generation ceiling.",
        "required_before_reenable": "An audited one-request adapter with zero exposed tools and a persistent provider-request ceiling. No further model calls are authorized for this pilot.",
        "alternative_status": "Not attempted: further provider requests would exceed the requested ceiling.",
        "requested_limit": limit, "configured_cli": str(cli)}
    save(output / "coding-blocker.json", blocker)
    return blocker


def reconcile(output):
    """Normalize only observed documented CLI usage fields, never estimated prices."""
    rows = []
    for path in sorted((output / "coding").glob("*/*/metrics.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        usage_path = path.parent / "usage.json"
        if usage_path.exists():
            usage = json.loads(usage_path.read_text(encoding="utf-8"))
            row.update(usage_metrics(usage))
            row["raw_usage"] = usage
        else:
            row.update(usage_metrics({}))
            row.pop("raw_usage", None)
        raw_path = path.parent / "raw.json"
        if raw_path.exists():
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            events = []
            for line in raw["stdout"].splitlines():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            row["tool_calls"] = sum(e.get("type") == "tool.execution_start" for e in events)
            row["agents"] = sum(e.get("type") == "subagent.started" for e in events)
            row["main_agents"] = 1
            row["model_call_start_events"] = sum(e.get("type") == "model.call_start" for e in events)
            row["control_valid"] = False
            row["validity_reason"] = "Empty CLI tool restriction did not disable tools; invocation count did not bound model calls."
            messages = [event.get("data", {}).get("content") for event in events
                        if event.get("type") == "assistant.message"]
            try:
                final_answer = json.loads(messages[-1]) if messages else None
            except (json.JSONDecodeError, TypeError):
                final_answer = None
            row["response_contract_valid"] = (
                isinstance(final_answer, dict)
                and set(final_answer) == {"solution", "tests", "explanation"}
                and all(isinstance(value, str) for value in final_answer.values()))
            row["response_status"] = "timed_out" if raw.get("timed_out") else (
                "completed" if raw.get("exit_code") == 0 else "failed")
            if raw.get("timed_out"):
                row["blocker"] = "CLI timed out after 240 seconds; incomplete output retained, final usage unavailable"
                row.update(correctness=None, quality=None, loc=None,
                           efficiency_correct_cases_per_second=None)
            elif raw.get("exit_code") == 0 and not (path.parent / "solution.py").exists():
                try:
                    answer = extract_answer(raw["stdout"])
                except ValueError as error:
                    row["blocker"] = str(error)
                else:
                    (path.parent / "solution.py").write_text(answer["solution"], encoding="utf-8")
                    (path.parent / "agent_tests.py.txt").write_text(answer.get("tests", ""), encoding="utf-8")
                    row["loc"] = sum(bool(line.strip()) for line in answer["solution"].splitlines())
                    row["initial_extraction_blocker"] = row.pop("blocker", None)
                    row["recovery"] = "Complete JSON recovered from finalized assistant text; raw response unchanged"
        solution = path.parent / "solution.py"
        if solution.exists() and row.get("response_status") != "timed_out":
            evaluation = capture([sys.executable, str(HERE / "hidden.py"), row["task"], str(solution)],
                                 path.parent, isolated_env(path.parent / "evaluation"), 30)
            save(path.parent / "reevaluation-v3.json", evaluation)
            try:
                score = json.loads(evaluation["stdout"])
                row.setdefault("initial_correctness", row.get("correctness"))
                row["correctness"] = score
                row["quality"] = {"definition": "deterministic contract correctness only; no subjective judge",
                                  "all_correct": score["all_correct"]}
                row["efficiency_correct_cases_per_second"] = score["passed"] / row["seconds"]
                row["scoring_revision"] = "offline v3: complete final-response recovery; strict JSON-only status scored separately"
            except (json.JSONDecodeError, KeyError) as error:
                row["reevaluation_blocker"] = str(error)
        save(path, row)
        rows.append(row)
    save(output / "coding-runs.json", rows)
    save(output / "execution-audit.json", {
        "experiment_valid": False,
        "requested_generation_ceiling": 12,
        "cli_invocations": len(json.loads((output / "generation-ledger.json").read_text()))
        if (output / "generation-ledger.json").exists() else 0,
        "observed_model_call_start_events": sum(r.get("model_call_start_events", 0) for r in rows),
        "finalized_usage_reported_model_requests": sum(
            model.get("requests", {}).get("count", 0)
            for row in rows for model in row.get("raw_usage", {}).get("modelMetrics", {}).values()),
        "observed_tool_calls": sum(r.get("tool_calls", 0) for r in rows),
        "response": "Stopped model execution on discovery; coding command now fails closed.",
        "failure": "The intended 12-generation budget was not enforced. Empty --available-tools= exposed native tools.",
        "separate_valid_evidence": "Local browser, RTK, deterministic scoring guards and archival audit."})
    return rows


def usage_metrics(usage):
    metrics = usage.get("modelMetrics", {})
    result = {"model": usage.get("currentModel"), "provider": "GitHub Copilot CLI",
              "input_tokens": None, "output_tokens": None,
              "uncached_input_tokens": None, "cache_read_tokens": None,
              "cache_write_tokens": None, "reasoning_tokens": None,
              "cost_usd": None, "rate_provenance": None,
              "premium_request_cost": usage.get("totalPremiumRequestCost"),
              "nano_aiu": usage.get("totalNanoAiu"),
              "api_duration_ms": usage.get("totalApiDurationMs"),
              "token_provenance": "Copilot --usage-output-file modelMetrics.*.usage; actual reported counters",
              "cost_note": "Premium requests and nano-AIU are reported units, not USD"}
    mappings = {"input_tokens": "inputTokens", "output_tokens": "outputTokens",
                "cache_read_tokens": "cacheReadTokens", "cache_write_tokens": "cacheWriteTokens",
                "reasoning_tokens": "reasoningTokens"}
    for target, source in mappings.items():
        values = [data.get("usage", {}).get(source) for data in metrics.values()]
        if values and all(type(value) in (int, float) for value in values):
            result[target] = sum(values)
    result["uncached_input_tokens"] = usage.get("tokenDetails", {}).get("input", {}).get("tokenCount")
    result["models_observed"] = list(metrics)
    return result


def command_comparison(output, rtk=None):
    root = output / "commands" / "fixture"
    root.mkdir(parents=True, exist_ok=True)
    environment = output / "commands" / "environment"
    env = isolated_env(environment)
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env["RTK_DB_PATH"] = str(environment / "rtk-history.db")
    env["RTK_TEE"] = "0"
    env["RTK_RECALL"] = "0"
    setup = capture(["git", "-c", "core.hooksPath=" + os.devnull, "init", "--quiet"], root, env)
    save(root / "git-setup.json", setup)
    for i in range(40):
        (root / f"sample_{i:02}.txt").write_text(f"synthetic fixture {i}\n")
    (root / "clean.py").write_text("answer = 42\n")
    (root / "bad.py").write_text("import os\nprint(undefined_name)\n")
    (root / "test_good.py").write_text(
        "import unittest\nclass Tests(unittest.TestCase):\n"
        + "".join(f"    def test_{i}(self): self.assertEqual({i}, {i})\n" for i in range(24)))
    (root / "test_bad.py").write_text(
        "import unittest\nclass Tests(unittest.TestCase):\n"
        "    def test_failure(self): self.assertEqual(1, 2)\n")
    ruff = str(Path(sys.executable).parent / ("ruff.exe" if os.name == "nt" else "ruff"))
    fixtures = [
        ("git-success", ["git", "status", "--short"], ["git", "status", "--short"]),
        ("git-failure", ["git", "rev-parse", "--verify", "refs/heads/missing"],
         ["git", "rev-parse", "--verify", "refs/heads/missing"]),
        ("lint-success", [ruff, "check", "--no-cache", "clean.py"],
         ["ruff", "check", "--no-cache", "clean.py"]),
        ("lint-failure", [ruff, "check", "--no-cache", "bad.py"],
         ["ruff", "check", "--no-cache", "bad.py"]),
        ("test-success", [sys.executable, "-m", "unittest", "-v", "test_good"],
         ["test", sys.executable, "-m", "unittest", "-v", "test_good"]),
        ("test-failure", [sys.executable, "-m", "unittest", "-v", "test_bad"],
         ["test", sys.executable, "-m", "unittest", "-v", "test_bad"]),
    ]
    rows = []
    for name, command, proxy_args in fixtures:
        raw = capture(command, root, env)
        proxy = capture([str(rtk), *proxy_args], root, env) if rtk else None
        row = {"fixture": name, "kind": "fresh-local", "raw": raw, "proxy": proxy,
               "same_fixture": True, "tokenizer": None, "input_tokens": None, "cost_usd": None,
               "exit_preserved": proxy["exit_code"] == raw["exit_code"] if proxy else None,
               "proxy_blocker": None if proxy else "Verified canonical RTK binary unavailable"}
        rows.append(row)
    if rtk:
        save(output / "rtk-runtime.json", {
            "version": capture([str(rtk), "--version"], root, env),
            "binary_sha256": digest(Path(rtk).read_bytes()),
            "canonical_repo": "https://github.com/rtk-ai/rtk",
            "published_artifact_provenance": "binary-audit.json"})
    save(output / "command-runs.json", rows)
    return rows


def svg_chart(path, title, rows, unit):
    if not title.startswith(SURFACE_LABEL):
        title = f"{SURFACE_LABEL} | {title}"
    width, height = 1000, 90 + 42 * len(rows)
    maximum = max([v for _, v in rows if isinstance(v, (int, float))] or [1]) or 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" role="img">',
             f'<title>{html.escape(title)}</title><rect width="100%" height="100%" fill="#fafafa"/>',
             f'<text x="20" y="28" font-family="sans-serif" font-size="14">{html.escape(title)}</text>']
    for index, (label, value) in enumerate(rows):
        y = 65 + index * 42
        numeric = isinstance(value, (int, float))
        bar = 460 * value / maximum if numeric else 0
        text = f"{value:.3f}" if numeric else "null / unavailable"
        parts += [f'<text x="20" y="{y}" font-family="sans-serif" font-size="12">{html.escape(label)}</text>',
                  f'<rect x="420" y="{y-15}" width="{bar:.2f}" height="20" fill="#17675b"/>',
                  f'<text x="885" y="{y}" font-family="sans-serif" font-size="11">{html.escape(text)}</text>']
    path.parent.mkdir(parents=True, exist_ok=True)
    parts.append(
        f'<text x="20" y="{height-10}" font-family="sans-serif" font-size="11">'
        f'{SURFACE_LABEL} | axis: {html.escape(unit)} | n=1; no rankings or significance</text>')
    path.write_text("\n".join(parts + ["</svg>"]), encoding="utf-8")


def reporting_rows(rows):
    """Mask requested display metrics without changing historical evidence."""
    return [{**row, "input_tokens": None, "output_tokens": None, "cost_usd": None}
            for row in rows]


def report(output):
    def load(name, default):
        path = output / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    coding_rows = reporting_rows(load("coding-runs.json", []))
    commands = load("command-runs.json", [])
    browser = load("browser-runs.json", [])
    archive = load("archive-audit.json", {})
    first_audit = load("execution-audit.json", {})
    correction = load("correction-v2/manifest.json", {})
    second_rows = reporting_rows(load("generation-set-2/controlled-runs/coding-runs.json", []))
    expected_cells = {(task, arm) for task in TASKS for arm in ARMS}
    second_valid = (
        len(second_rows) == len(expected_cells)
        and {(row["task"], row["arm"]) for row in second_rows} == expected_cells
        and all(row.get("control_valid") is True for row in second_rows)
    )
    cells = {(r["task"], r["arm"]): r for r in coding_rows}
    display_rows = [cells.get((task, arm), {"task": task, "arm": arm})
                    for task in TASKS for arm in ARMS]
    for metric in ("seconds", "input_tokens", "output_tokens", "cost_usd", "loc", "tool_calls", "agents",
                   "efficiency_correct_cases_per_second"):
        svg_chart(output / "graphs" / f"coding-{metric}.svg",
                  f"ABORTED AND UNCONTROLLED v1: {metric}; not a controlled ranking",
                  [(f'{r["task"]}/{r["arm"]}', r.get(metric)) for r in display_rows],
                  {"seconds": "s", "cost_usd": "USD"}.get(metric, metric))
    svg_chart(output / "graphs" / "coding-correctness.svg",
              "ABORTED AND UNCONTROLLED v1: checks; not a controlled comparison",
              [(f'{r["task"]}/{r["arm"]}',
                r["correctness"]["passed"] / r["correctness"]["total"]
                if r.get("correctness") else None) for r in display_rows], "fraction")
    svg_chart(output / "graphs" / "command-bytes.svg", "Fresh local command stdout+stderr bytes, not billed tokens",
              [(r["fixture"] + "/" + arm, (r[arm]["stdout_bytes"] + r[arm]["stderr_bytes"])
                if r[arm] else None) for r in commands for arm in ("raw", "proxy")], "bytes")
    svg_chart(output / "graphs" / "command-time.svg", "Fresh local command elapsed time; one pair per fixture",
              [(r["fixture"] + "/" + arm, r[arm]["elapsed_seconds"] if r[arm] else None)
               for r in commands for arm in ("raw", "proxy")], "s")
    svg_chart(output / "graphs" / "browser-time.svg", "Fresh local engine timing; representation measured separately",
              [(f'{r["engine"]}/{r.get("phase","blocked")}', r.get("elapsed_seconds")) for r in browser], "s")
    svg_chart(output / "graphs" / "browser-representation.svg",
              "Native representation bytes; not engine timing or billed tokens",
              [(f'{r["engine"]}/{r.get("phase","blocked")}', r.get("representation_bytes"))
               for r in browser], "bytes")
    svg_chart(output / "graphs" / "archive-completeness.svg", "ARCHIVAL 2026-09-11 export completeness; not a new experiment",
              [("Claimed coding runs", archive.get("expected_claimed_rows")),
               ("Exported coding rows", archive.get("coding_rows")),
               ("Complete correct rows", archive.get("correct_complete_rows")),
               ("Missing solution rows", archive.get("missing_solution_rows"))], "rows")
    if second_valid:
        second_cells = {(row["task"], row["arm"]): row for row in second_rows}
        for task in TASKS:
            for metric in ("seconds", "input_tokens", "output_tokens", "loc"):
                svg_chart(
                    output / "graphs" / f"generation-set-2-{task}-{metric}.svg",
                    f"Controlled generation-set-2 / {task} / {metric}; n=1 per cell, no significance",
                    [(arm, second_cells[task, arm].get(metric)) for arm in ARMS], metric,
                )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(), "private": True,
        "scope": SURFACE_LABEL,
        "display_tokens_and_cost": None,
        "coding_experiment_valid": False,
        "targeted_v2_existing_trials": correction.get("selected_existing_trials", 0),
        "targeted_v2_new_model_calls": correction.get("new_model_calls", 0),
        "coding_v1_status": "ABORTED AND UNCONTROLLED",
        "coding_v1_invalid_controls": sum(row.get("control_valid") is False for row in coding_rows),
        "generation_set_2_complete_and_valid": second_valid,
        "generation_set_2_rows": len(second_rows),
        "generation_set_2_json_only_responses": sum(
            row.get("response_contract_valid") is True for row in second_rows),
        "generation_set_2_execution_audit": load(
            "generation-set-2/controlled-runs/execution-audit.json", {}),
        "execution_audit": load("execution-audit.json", {}),
        "coding_attempts": len(load("generation-ledger.json", [])),
        "coding_rows": len(coding_rows), "coding_successes": sum(
            bool(r.get("correctness", {}).get("all_correct")) if r.get("correctness") else False for r in coding_rows),
        "coding_blockers": [{"task": row["task"], "arm": row["arm"], "blocker": row["blocker"]}
                            for row in coding_rows if row.get("blocker")],
        "unattempted_cells": [{"task": task, "arm": arm} for task in TASKS for arm in ARMS
                              if (task, arm) not in cells],
        "full_harness_blocker": "Private installed harness not transmitted; this measures a synthetic prompt-only proxy, not the actual harness.",
        "no_caveman_protocol_note": (
            "Pilot v1 removed the whole Caveman-bearing line, also removing the finish-status clause and retaining a safety-only continuation. Treat this arm as a modified-context arm, not a pure one-variable ablation. Fresh v2 preparation fixes line boundaries; original pilot prompts remain immutable."
            if load("manifest.json", {}).get("protocol_version", 1) == 1 else
            "v2 removes only the complete Caveman instruction line; finish-status clause stays common."),
        "command_pairs": len(commands),
        "command_proxy_pairs": sum(bool(r["proxy"]) for r in commands),
        "command_exit_matches": sum(r["exit_preserved"] is True for r in commands),
        "browser_rows": len(browser),
        "browser_blockers": [r for r in browser if r.get("blocker")],
        "archive": archive,
        "limitations": [
            "At most n=1 per coding cell; no confidence intervals or robust rankings.",
            "Prompt-only synthetic operationalization does not prove installed harness enforcement.",
            "Provider-side cache isolation is unavailable; fresh local directories do not eliminate server caching.",
            "Unknown tokens, model rates, dollar costs, and unexposed telemetry remain null.",
            "Bytes and offline tokenizer counts are never billing or measured LLM token savings.",
            "The generated-code AST gate is not an OS security sandbox.",
            "Deterministic tests measure contract correctness, not general software quality.",
            "Browser startup/cold phases are fresh processes, not a flushed OS disk cache.",
            "Browser representations differ in content; byte reduction alone cannot rank engine speed.",
            "Do not distribute raw private evidence through Pages."]}
    save(output / "summary.json", summary)
    narrative = "# Private benchmark report\n\n" + (
        "**CODING v1 ABORTED AND UNCONTROLLED: "
        f'{first_audit.get("finalized_usage_reported_model_requests", "unavailable")} finalized model requests '
        f'were recorded against an authorized ceiling of {first_audit.get("requested_generation_ceiling", 12)}. '
        f'{summary["coding_v1_invalid_controls"]} of {len(coding_rows)} control_valid flags are false.** '
        "The CLI treated an empty tool list as default tools, so some invocations "
        "made multiple model calls. Model execution was stopped on discovery, "
        "and the coding command now fails closed. Counts are in execution-audit.json. "
        "These coding observations are diagnostic evidence, not controlled ablation "
        "results or a successful budget-limited experiment. The actual installed "
        "harness was not measured. Caveman-browse remains blocked.\n\n"
        "Separate local browser/RTK measurements and archival recovery remain usable "
        "within their stated boundaries. No robust winner is claimed.\n\n")
    narrative += (
        "## Separate generation and scoring revisions\n\n"
        "`reevaluation-v2.json` and `reevaluation-v3.json` files are offline rescoring "
        "of saved v1 answers, not new model generations. Revision v3 recovers complete "
        "fenced JSON from finalized text while retaining a false JSON-only contract flag; "
        "timeout deltas remain incomplete. The separately authorized `generation-set-2/` "
        "contains new invocations and its own audits. Its first preflight rejected "
        "`--deny-tool '*'` before any model start; that evidence remains intact. "
        "`controlled-runs/` uses a non-empty no-match tool allowlist, disabled hooks "
        "in isolated configuration, and explicit built-in/Playwright/Rustwright MCP "
        "disables. The live monitor stops extra starts, tool calls or active MCPs. "
        "Missing telemetry, invalid controls and timeouts stop continuation; no "
        "timed-out cell is retried. The canary is the complex/bare cell, not an "
        "extra sample. The new ceiling is 16 finalized requests including the canary; "
        "the matched matrix requires only 12. The model is `claude-sonnet-5`.\n\n"
    )
    narrative += (
        "**Generation-set-2: all 12 controls valid.** Comparisons below are individual "
        "trials on two different tasks. Two trials per arm is not statistical "
        "significance; each task/arm cell has n=1. Provider-side caches remain uncontrolled.\n\n"
        if second_valid else
        "**Generation-set-2 is not a complete valid comparison.** Do not rank its arms. "
        "Consult its separate audit for completed, invalid or unattempted cells.\n\n"
    )
    narrative += "## Measured counts\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n\n"
    narrative += "## Invalid coding pilot diagnostics (not controlled comparisons)\n\n"
    narrative += "| Task | Arm | Seconds | Input tokens | Output tokens | LOC | Tools | Subagents | Correct checks |\n"
    narrative += "|---|---|---:|---:|---:|---:|---:|---:|---:|\n"
    for row in display_rows:
        def cell(value):
            return "not measured" if value is None else str(round(value, 3) if isinstance(value, float) else value)
        score = row.get("correctness")
        correctness = f'{score["passed"]}/{score["total"]}' if score else "not measured"
        values = [row["task"], row["arm"], cell(row.get("seconds")), cell(row.get("input_tokens")),
                  cell(row.get("output_tokens")), cell(row.get("loc")),
                  cell(row.get("tool_calls")), cell(row.get("agents")), correctness]
        narrative += "| " + " | ".join(values) + " |\n"
    narrative += "\nDollar cost is unknown. Premium requests/nano-AIU are not converted to dollars.\n\n"
    if second_rows:
        narrative += "## Generation-set-2 per-trial observations\n\n"
        narrative += "| Task | Arm | Control valid | Seconds | Input tokens | Output tokens | JSON-only | Correct checks |\n"
        narrative += "|---|---|---|---:|---:|---:|---|---:|\n"
        for row in sorted(second_rows, key=lambda r: (list(TASKS).index(r["task"]), ARMS.index(r["arm"]))):
            correctness = row.get("correctness")
            values = [row["task"], row["arm"], str(row["control_valid"]), cell(row["seconds"]),
                      cell(row.get("input_tokens")), cell(row.get("output_tokens")),
                      str(row.get("response_contract_valid")),
                      f'{correctness["passed"]}/{correctness["total"]}' if correctness else "not measured"]
            narrative += "| " + " | ".join(values) + " |\n"
        narrative += (
            "\nIsolation validity is not output correctness. JSON-only checks use the unmodified "
            "assistant response; code scoring can recover a JSON object enclosed in Markdown fences. "
            "Responses with unrecognized layouts remain unscored rather than being assigned invented "
            "correctness values. Raw responses and scoring blockers remain available.\n\n"
        )
    narrative += "## Fresh command-output comparison\n\n"
    narrative += "| Fixture | Raw bytes | Proxy bytes | Raw exit | Proxy exit |\n|---|---:|---:|---:|---:|\n"
    for row in commands:
        raw, proxy = row["raw"], row["proxy"]
        narrative += f'| {row["fixture"]} | {raw["stdout_bytes"] + raw["stderr_bytes"]} | '
        narrative += f'{proxy["stdout_bytes"] + proxy["stderr_bytes"] if proxy else "not measured"} | '
        narrative += f'{raw["exit_code"]} | {proxy["exit_code"] if proxy else "not measured"} |\n'
    pairs = [row for row in commands if row.get("proxy")]
    if pairs:
        raw_total = sum(row["raw"]["stdout_bytes"] + row["raw"]["stderr_bytes"] for row in pairs)
        proxy_total = sum(row["proxy"]["stdout_bytes"] + row["proxy"]["stderr_bytes"] for row in pairs)
        reductions = [
            100 * (1 - (row["proxy"]["stdout_bytes"] + row["proxy"]["stderr_bytes"]) /
                   (row["raw"]["stdout_bytes"] + row["raw"]["stderr_bytes"]))
            for row in pairs if row["raw"]["stdout_bytes"] + row["raw"]["stderr_bytes"]
        ]
        narrative += (
            f'\nExit codes preserved: {sum(row["exit_preserved"] is True for row in pairs)}/{len(pairs)}. '
            f"Aggregate output: {raw_total:,} raw bytes, {proxy_total:,} proxy bytes. "
        )
        if raw_total and reductions:
            narrative += (
                f"Reduction: {100 * (1 - proxy_total / raw_total):.1f}%; "
                f"individual range {min(reductions):.1f}% to {max(reductions):.1f}%. "
            )
        slower = sum(row["proxy"]["elapsed_seconds"] > row["raw"]["elapsed_seconds"] for row in pairs)
        narrative += f"RTK added elapsed time on {slower}/{len(pairs)} fixtures in this configuration.\n\n"
    narrative += (
        "These are output bytes, not billed tokens, whole-conversation cost savings, "
        "or a general overhead guarantee.\n\n"
        "## Browser representation and timing\n\n"
    )
    cold = {row["engine"]: row for row in browser if row.get("phase") == "cold"}
    if all(engine in cold for engine in ("playwright", "rustwright")):
        pw_bytes, rw_bytes = (cold[engine]["representation_bytes"] for engine in ("playwright", "rustwright"))
        narrative += (
            f"**Native accessibility snapshots:** Playwright {pw_bytes:,} bytes; "
            f"Rustwright {rw_bytes:,} bytes; absolute difference {abs(pw_bytes - rw_bytes):,} bytes. "
            "This is an accessibility-snapshot comparison, not a raw DOM comparison. "
        )
        if abs(pw_bytes - rw_bytes) <= 4:
            narrative += "These measurements do not support dramatically smaller Rustwright snapshots. "
        narrative += "See recorded tokenizer fields; bytes are not token counts.\n\n"
    narrative += (
        "| Engine | Phase | Launch seconds | Task seconds | Representation bytes | Assertions |\n"
        "|---|---|---:|---:|---:|---:|\n"
    )
    for row in browser:
        narrative += "| " + " | ".join([
            row["engine"], row.get("phase", "unavailable"), cell(row.get("launch_seconds")),
            cell(row.get("elapsed_seconds")), cell(row.get("representation_bytes")),
            f'{row["assertions_passed"]}/{row["assertions_total"]}'
            if "assertions_passed" in row else "not run",
        ]) + " |\n"
    narrative += (
        "\nRead launch, cold and warm phases separately, not as a broad speed ranking. "
        "The table contains one trial per engine/phase; Chromium and fixture hashes "
        "are recorded in `browser-runs.json`. Unavailable engines are not replaced "
        "with namesakes or estimates; see `binary-audit.json`.\n\n"
        "Rustwright alpha Chromium-only; Python interface, not MCP. "
        "Cold is process-cold, not OS-cache-cold.\n\n"
    )
    narrative += (
        "## Reproduction and evidence\n\n"
        "Use the checked-in `benchmarks/verified_2026/README.md`. Exact prompts are in "
        "`prompts/`; hidden checks and guard tests ship with the source package. "
        "`coding/*/*/raw.json` preserves CLI output; `usage.json` is provider/CLI "
        "telemetry only when emitted. `command-runs.json` preserves exact bytes as "
        "hex plus readable stdout/stderr, status and elapsed time. "
        "`browser-runs.json` records interface, Chromium identity, correctness and timing. "
        "`archive-audit.json` hashes selectively recovered old files. "
        "`upstream-audit.json` pins inspected public sources and states scan limits.\n\n"
        "## Transfer prompts\n\n"
        "Run `prompts/transfer-complex.txt` and `prompts/transfer-super_complex.txt` "
        "in new sessions on another frontier model. Record that model and actual usage, "
        "not an assumed model price. No judge swarm is used.\n")
    if correction:
        narrative += (
            "\n## Targeted v2 correction without additional generation\n\n"
            "The two no-Caveman cells and the previously timed-out super-complex/super "
            "slot already exist in the separately authorized generation-set-2. "
            "Exactly those three existing trials were selected, their corrected prompt "
            "hashes and one-request controls verified, and their finalized code rescored "
            "offline. No additional requests, arms, repetitions or judges were used. "
            "See `correction-v2/REPORT.md` and its manifest. Original v1 rows, failure "
            "history, prompts and timeout remain intact; historical spend is not "
            "reclassified to fit a 17-total ceiling.\n")
    narrative += (
        "\n## Reporting metric policy\n\n"
        "Tokens and dollar cost are null / unavailable in this report's display. "
        "Historical provider counters remain unchanged in private raw evidence; "
        "they are not relabeled as new measurements or converted into estimated dollars. "
        "The PROMPT-ONLY SYNTHETIC suite label is not a claim of installed full-agent "
        "harness enforcement. Browser and RTK substudies execute actual local tools "
        "on deterministic synthetic fixtures, separately from prompt trials.\n")
    narrative = "\n".join(
        line.split(" ", 1)[0] + " " + SURFACE_LABEL + " | " + line.split(" ", 1)[1]
        if line.startswith("#") and " " in line and SURFACE_LABEL not in line else line
        for line in narrative.splitlines()) + "\n"
    (output / "REPORT.md").write_text(narrative, encoding="utf-8")
    archive_path = output / "private-benchmark-report.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        files = list(output.glob("*.json")) + list(output.glob("*.md"))
        for folder in ("graphs", "prompts", "archive", "correction-v2"):
            files.extend(path for path in (output / folder).rglob("*") if path.is_file())
        for name in ("raw.json", "metrics.json", "evaluation.json", "reevaluation-v2.json", "reevaluation-v3.json",
                     "usage.json", "solution.py", "agent_tests.py.txt"):
            files.extend((output / "coding").glob("*/*/" + name))
        files.extend((output / "browser").glob("*-representation.txt"))
        files.extend((output / "browser").glob("*.html"))
        files.extend((output / "commands" / "fixture").glob("*.py"))
        for path in files:
            bundle.write(path, "evidence/" + path.relative_to(output).as_posix())
        for repo in ("DietrichGebert_ponytail", "JuliusBrussee_caveman"):
            license_path = output / "upstreams" / repo / "LICENSE"
            if license_path.exists():
                bundle.write(license_path, "licenses/" + repo + ".txt")
        for path in HERE.glob("*.py"):
            bundle.write(path, "benchmarks/verified_2026/" + path.name)
        for name in ("README.md", "requirements.txt"):
            if (HERE / name).exists():
                bundle.write(HERE / name, "benchmarks/verified_2026/" + name)
        tests = HERE.parents[1] / "tests" / "test_benchmark_verified.py"
        if tests.exists():
            bundle.write(tests, "tests/" + tests.name)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "coding", "commands", "reconcile", "report"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cli", default=shutil.which("copilot"))
    parser.add_argument("--rtk", type=Path)
    parser.add_argument("--max-attempts", type=int, default=12)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.command == "prepare":
        result = prepare(output)
    elif args.command == "coding":
        result = coding(output, args.cli, args.max_attempts)
    elif args.command == "commands":
        result = command_comparison(output, args.rtk)
    elif args.command == "reconcile":
        result = reconcile(output)
    else:
        result = report(output)
    print(json.dumps({"command": args.command, "output": str(output),
                      "records": len(result)}))


if __name__ == "__main__":
    main()

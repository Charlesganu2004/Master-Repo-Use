"""PROMPT-ONLY SYNTHETIC: select and rescore three existing trials, without generation."""
import argparse
import ast
import json
from pathlib import Path

from .audit import digest, save
from .isolated import audit, response_contract
from .run import HERE, SUPER_PROXY, capture, extract_answer, isolated_env, svg_chart
from .tasks import compose

TARGETS = (
    ("complex", "super_ponytail_nocaveman"),
    ("super_complex", "super_ponytail_nocaveman"),
    ("super_complex", "super"),
)


def recover(raw, task):
    """Recover complete finalized code, never deltas or guessed missing sections."""
    try:
        return extract_answer(raw), "finalized JSON object"
    except ValueError:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        texts = [event.get("data", {}).get("content") for event in events
                 if event.get("type") == "assistant.message"]
        if not texts or not isinstance(texts[-1], str):
            raise ValueError("no finalized assistant text") from None
        fences = texts[-1].split("```")
        solutions, tests = [], []
        expected = "Ledger" if task == "complex" else "Limiter"
        for index in range(1, len(fences) - 1, 2):
            language, separator, body = fences[index].partition("\n")
            if not separator or language.strip() != "python":
                continue
            try:
                tree = ast.parse(body)
            except SyntaxError:
                continue
            if any(isinstance(node, ast.ClassDef) and node.name == expected for node in tree.body):
                solutions.append(body)
            else:
                tests.append(body)
        if len(solutions) != 1:
            raise ValueError("expected exactly one complete fenced solution class") from None
        return {"solution": solutions[0], "tests": "\n\n".join(tests),
                "explanation": texts[-1]}, "finalized Python fence; JSON-only contract remains false"


def build(evidence, output, python):
    """Copy immutable sources and score only the three already executed target cells."""
    if output.exists():
        raise ValueError("Correction version already exists; never overwrite it")
    source = evidence / "generation-set-2" / "controlled-runs"
    entries = []
    for path in source.glob("[0-9][0-9]-*/audit.json"):
        entry = json.loads(path.read_text(encoding="utf-8"))
        if (entry["task"], entry["arm"]) in TARGETS:
            entries.append((path.parent, entry))
    if len(entries) != 3 or {(e["task"], e["arm"]) for _, e in entries} != set(TARGETS):
        raise ValueError("Three existing target cells are required; no new generation is permitted")
    ponytail = (evidence / "upstreams" / "DietrichGebert_ponytail" / "skills" / "ponytail" / "SKILL.md").read_text(encoding="utf-8")
    caveman = (evidence / "upstreams" / "JuliusBrussee_caveman" / "skills" / "caveman" / "SKILL.md").read_text(encoding="utf-8")
    output.mkdir(parents=True)
    baseline = (evidence / "coding-runs.json").read_bytes()
    (output / "frozen-v1-rows.json").write_bytes(baseline)
    rows = []
    for task, arm in TARGETS:
        cell, entry = next((cell, entry) for cell, entry in entries
                           if (entry["task"], entry["arm"]) == (task, arm))
        prompt = (cell / "prompt.txt").read_bytes()
        prompt_text = (cell / "prompt.txt").read_text(encoding="utf-8").encode("utf-8")
        expected = compose(task, arm, SUPER_PROXY, ponytail=ponytail, caveman=caveman).encode()
        if digest(prompt_text) != entry["prompt_sha256"] or prompt_text != expected:
            raise ValueError("Saved prompt differs from its recorded hash or corrected v2 recipe")
        raw = (cell / "stdout.jsonl").read_text(encoding="utf-8")
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        usage = json.loads((cell / "usage.json").read_text(encoding="utf-8"))
        control = audit(events, usage, entry["argv"], exit_code=entry["exit_code"],
                        timed_out=entry["timed_out"])
        if not control["control_valid"]:
            raise ValueError("Existing selected trial fails isolated one-request audit")
        destination = output / task / arm
        destination.mkdir(parents=True)
        sources = []
        for name in ("prompt.txt", "stdout.jsonl", "stderr.txt", "usage.json", "audit.json"):
            data = (cell / name).read_bytes()
            (destination / name).write_bytes(data)
            sources.append({"name": name, "sha256": digest(data)})
        answer, recovery = recover(raw, task)
        solution = destination / "solution.py"
        solution.write_bytes(answer["solution"].encode("utf-8"))
        (destination / "agent_tests.py.txt").write_bytes(answer.get("tests", "").encode("utf-8"))
        evaluation = capture([str(python), str(HERE / "hidden.py"), task, str(solution)],
                             destination, isolated_env(destination / "evaluation"), 30)
        save(destination / "evaluation.json", evaluation)
        row = {
            "version": "v2 targeted correction, existing generation-set-2 trial",
            "scope": "PROMPT-ONLY SYNTHETIC; not installed full-agent harness",
            "task": task, "arm": arm, "source_cell": cell.name,
            "new_model_calls": 0, "source_trial_already_executed": True,
            "source_hashes": sources, "prompt_sha256": digest(prompt_text),
            "prompt_file_sha256": digest(prompt),
            "control": control, "response_contract_valid": response_contract(raw),
            "recovery": recovery, "seconds": entry["seconds"],
            "loc": sum(bool(line.strip()) for line in answer["solution"].splitlines()),
            "input_tokens": None, "output_tokens": None, "cost_usd": None,
            "metric_policy": "null / unavailable in correction view; source usage preserved privately",
            "correctness": json.loads(evaluation["stdout"]),
        }
        rows.append(row)
        save(destination / "metrics.json", row)
    if (evidence / "coding-runs.json").read_bytes() != baseline:
        raise ValueError("V1 rows changed during correction selection")
    manifest = {
        "scope": "PROMPT-ONLY SYNTHETIC", "version": "v2-targeted-existing-trials",
        "selected_existing_trials": 3, "new_model_calls": 0, "new_arms": 0, "judges": 0,
        "reason": "Existing separately authorized second set already contains the two corrected no-Caveman cells and the timeout replacement",
        "v1_rows_sha256": digest(baseline), "v1_preserved": True,
        "historical_budget_note": "Prior history is not relabeled to fit a 17-total ceiling. This correction starts zero requests.",
        "limitations": ["n=1 per cell; no rankings or significance",
                        "Strict JSON-only failures remain failures despite recovered-code correctness",
                        "Provider-side cache isolation unavailable",
                        "Caveman-browse remains unavailable; no binary installed"],
        "rows": rows}
    save(output / "manifest.json", manifest)
    for metric in ("seconds", "loc", "input_tokens", "output_tokens", "cost_usd"):
        svg_chart(output / "graphs" / f"{metric}.svg", f"v2 existing target cells | {metric}",
                  [(row["task"] + "/" + row["arm"], row[metric]) for row in rows], metric)
    lines = ["# PROMPT-ONLY SYNTHETIC v2 targeted correction", "",
             "Three already executed generation-set-2 trials, not three new generations.",
             "Original v1 prompts, rows, incomplete outputs and confound notes remain unchanged.",
             "Tokens and cost: null / unavailable in this view. Raw source telemetry is retained privately.",
             "No installed full-agent harness claim; no n=1 rankings or significance.", "",
             "| Task | Arm | Seconds | Correct checks | JSON-only |",
             "|---|---|---:|---:|---|"]
    for row in rows:
        score = row["correctness"]
        lines.append(f'| {row["task"]} | {row["arm"]} | {row["seconds"]:.3f} | '
                     f'{score["passed"]}/{score["total"]} | {row["response_contract_valid"]} |')
    (output / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    arguments = parser.parse_args()
    result = build(arguments.evidence.resolve(), arguments.output.resolve(), arguments.python.resolve())
    print(json.dumps({"selected_existing_trials": result["selected_existing_trials"],
                      "new_model_calls": result["new_model_calls"]}))

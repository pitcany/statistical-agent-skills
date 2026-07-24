#!/usr/bin/env python3
"""Evaluation harness for the statistical-agent-skills library.

The harness runs evaluation prompts through a model, applies the deterministic
portion of each case's grading contract, and writes a report that a human then
completes. It does NOT claim to score statistical quality automatically — keyword
matching cannot tell a correct leakage argument from a fluent wrong one. Its job is
to (a) catch mechanical regressions cheaply, (b) surface the forbidden patterns that
are genuinely detectable by regex, and (c) organize responses for human review
against the rubric in docs/evaluation-methodology.md.

Modes
-----
--check     Validate case/contract structure only. No model calls. Use in CI.
--run       Send prompts to a model and grade deterministically. Needs --runner.
--report    Render a human-review report from a saved results file.
--compare   Diff two results files to see what changed between skill versions.

Runners
-------
claude-cli  Invokes `claude -p` as a subprocess (default). Set --model to pick one.
stdin       Prints each prompt and reads the response from a file you supply; use for
            harnesses this script cannot drive directly.

Examples
--------
    python3 evals/runners/run_evals.py --check
    python3 evals/runners/run_evals.py --run --runner claude-cli --model sonnet
    python3 evals/runners/run_evals.py --report evals/results/2026-07-23T19-00.json
    python3 evals/runners/run_evals.py --compare old.json new.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
CASES_DIR = REPO / "evals" / "cases"
CONTRACTS_DIR = REPO / "evals" / "expected-behaviors"
RESULTS_DIR = REPO / "evals" / "results"

CONTRACT_REQUIRED_KEYS = {"id", "skill", "polarity", "summary"}
VALID_POLARITY = {"positive", "negative"}
VALID_SEVERITY = {"blocker", "high", "medium", "low", "none"}


# --------------------------------------------------------------------------- parsing


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Minimal YAML-subset frontmatter parser (no PyYAML dependency).

    Supports scalars, inline lists (``[a, b]``) and one level of block lists.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw, body = text[3:end], text[end + 4 :]
    return _parse_block(raw), body


def _coerce(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [v.strip().strip("'\"") for v in inner.split(",")]
    return value.strip("'\"")


def _parse_block(raw: str) -> dict:
    data: dict = {}
    key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and key is not None:
            data.setdefault(key, [])
            if isinstance(data[key], list):
                data[key].append(_coerce(stripped[2:]))
            continue
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            k = k.strip()
            v = v.strip()
            if v in ("", "|", ">"):
                data[k] = [] if v == "" else ""
                key = k
            else:
                data[k] = _coerce(v)
                key = k
    return data


def load_contract(path: Path) -> dict:
    """Load an expected-behaviors YAML file using the same minimal parser."""
    return _parse_block(path.read_text(encoding="utf-8"))


@dataclass
class Case:
    id: str
    skill: str
    polarity: str
    prompt: str
    contract: dict
    tags: list[str] = field(default_factory=list)


def load_cases(only: list[str] | None = None) -> list[Case]:
    cases: list[Case] = []
    for case_path in sorted(CASES_DIR.glob("*.md")):
        fm, body = parse_frontmatter(case_path.read_text(encoding="utf-8"))
        cid = fm.get("id") or case_path.stem
        if only and cid not in only:
            continue
        contract_path = CONTRACTS_DIR / f"{cid}.yaml"
        contract = load_contract(contract_path) if contract_path.is_file() else {}
        prompt = _extract_prompt(body)
        tags = fm.get("tags") or []
        cases.append(
            Case(
                id=cid,
                skill=fm.get("skill", ""),
                polarity=fm.get("polarity", ""),
                prompt=prompt,
                contract=contract,
                tags=tags if isinstance(tags, list) else [tags],
            )
        )
    return cases


def _extract_prompt(body: str) -> str:
    """Return the text under the '## Prompt' heading, or the whole body."""
    m = re.search(r"^##\s+Prompt\s*$", body, re.MULTILINE)
    if not m:
        return body.strip()
    rest = body[m.end() :]
    nxt = re.search(r"^##\s+", rest, re.MULTILINE)
    return (rest[: nxt.start()] if nxt else rest).strip()


# ------------------------------------------------------------------------ structure


def check_structure(cases: list[Case]) -> int:
    """Validate cases and contracts without calling a model. Returns exit code."""
    errors: list[str] = []
    warnings: list[str] = []

    case_ids = {c.id for c in cases}
    for contract_path in sorted(CONTRACTS_DIR.glob("*.yaml")):
        if contract_path.stem not in case_ids:
            errors.append(f"{contract_path.name}: no matching case in evals/cases/")

    for c in cases:
        where = f"{c.id}"
        if not c.prompt or len(c.prompt) < 40:
            errors.append(f"{where}: prompt missing or too short to be realistic")
        if c.polarity not in VALID_POLARITY:
            errors.append(f"{where}: polarity must be one of {sorted(VALID_POLARITY)}")
        if not c.skill:
            errors.append(f"{where}: no target skill declared")
        elif not (REPO / "skills" / c.skill).is_dir():
            errors.append(f"{where}: target skill {c.skill!r} does not exist")

        if not c.contract:
            errors.append(f"{where}: missing evals/expected-behaviors/{c.id}.yaml")
            continue

        missing = CONTRACT_REQUIRED_KEYS - set(c.contract)
        if missing:
            errors.append(f"{where}: contract missing keys {sorted(missing)}")
        if c.contract.get("polarity") != c.polarity:
            errors.append(f"{where}: polarity disagrees between case and contract")

        sev = c.contract.get("required_severity")
        if sev and sev not in VALID_SEVERITY:
            errors.append(f"{where}: required_severity {sev!r} invalid")
        if c.polarity == "negative" and sev not in (None, "none", "low", "informational"):
            warnings.append(
                f"{where}: negative case expects severity {sev!r} — confirm this is "
                "intentional; negative cases usually expect no blocker"
            )

        for pat in c.contract.get("forbidden_patterns") or []:
            try:
                re.compile(pat)
            except re.error as exc:
                errors.append(f"{where}: forbidden_pattern {pat!r} is invalid regex: {exc}")

        if not (c.contract.get("must_identify") or c.contract.get("must_mention_any")):
            warnings.append(f"{where}: contract has no required behaviors")

    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error:   {e}")
    print(
        f"\n{len(cases)} case(s) checked — {len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return 1 if errors else 0


# --------------------------------------------------------------------------- grading


def grade_deterministic(response: str, contract: dict) -> dict:
    """Apply only the mechanically checkable part of the contract.

    Returns a dict with keyword-group hits, forbidden-pattern matches, and a
    deterministic verdict that is explicitly NOT a quality judgement.
    """
    lowered = response.lower()

    groups = contract.get("must_mention_any") or []
    group_results = []
    for group in groups:
        terms = group if isinstance(group, list) else [group]
        hit = next((t for t in terms if str(t).lower() in lowered), None)
        group_results.append({"terms": terms, "hit": hit, "passed": hit is not None})

    violations = []
    for pat in contract.get("forbidden_patterns") or []:
        m = re.search(pat, response, re.IGNORECASE)
        if m:
            violations.append({"pattern": pat, "matched": m.group(0)[:160]})

    groups_passed = all(g["passed"] for g in group_results) if group_results else None
    return {
        "keyword_groups": group_results,
        "groups_passed": groups_passed,
        "forbidden_violations": violations,
        "deterministic_verdict": (
            "FAIL"
            if violations
            else ("PASS" if groups_passed in (True, None) else "PARTIAL")
        ),
        "human_review_required": True,
    }


# --------------------------------------------------------------------------- runners


def run_claude_cli(prompt: str, model: str | None, timeout: int) -> tuple[str, str | None]:
    cmd = ["claude", "-p", prompt]
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        return "", "claude CLI not found on PATH"
    except subprocess.TimeoutExpired:
        return "", f"timed out after {timeout}s"
    if proc.returncode != 0:
        return proc.stdout, f"exit {proc.returncode}: {proc.stderr.strip()[:400]}"
    return proc.stdout, None


def run_cases(
    cases: list[Case], runner: str, model: str | None, timeout: int
) -> dict:
    results = []
    for i, c in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {c.id} ...", flush=True)
        if runner == "claude-cli":
            response, err = run_claude_cli(c.prompt, model, timeout)
        else:
            print(f"--- PROMPT for {c.id} ---\n{c.prompt}\n--- END ---")
            print("Paste response, then EOF (Ctrl-D):")
            response, err = sys.stdin.read(), None
        grading = grade_deterministic(response, c.contract) if response else {}
        results.append(
            {
                "id": c.id,
                "skill": c.skill,
                "polarity": c.polarity,
                "tags": c.tags,
                "prompt": c.prompt,
                "response": response,
                "error": err,
                "grading": grading,
                "contract": c.contract,
                "human": {"verdict": None, "notes": "", "rubric_scores": {}},
            }
        )
        if err:
            print(f"    error: {err}")
        elif grading:
            print(f"    deterministic: {grading['deterministic_verdict']}")

    return {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "runner": runner,
            "model": model or "harness-default",
            "harness_version": "1.0.0",
            "library_version": "1.0.0",
            "case_count": len(cases),
            "note": (
                "Deterministic verdicts check keyword coverage and forbidden patterns "
                "only. They are necessary, not sufficient. Statistical quality requires "
                "human review against docs/evaluation-methodology.md."
            ),
        },
        "results": results,
    }


# ---------------------------------------------------------------------------- report


def render_report(data: dict) -> str:
    meta = data["meta"]
    rows = data["results"]
    out = [
        "# Evaluation report",
        "",
        f"- Run: `{meta['timestamp']}`",
        f"- Runner: `{meta['runner']}`   Model: `{meta['model']}`",
        f"- Harness `{meta.get('harness_version')}`, library `{meta.get('library_version')}`",
        f"- Cases: {meta['case_count']}",
        "",
        f"> {meta['note']}",
        "",
        "## Deterministic summary",
        "",
        "| Case | Skill | Polarity | Deterministic | Forbidden hits | Human verdict |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        g = r.get("grading") or {}
        verdict = g.get("deterministic_verdict", "—")
        nviol = len(g.get("forbidden_violations", []))
        human = (r.get("human") or {}).get("verdict") or "_pending_"
        out.append(
            f"| `{r['id']}` | {r['skill']} | {r['polarity']} | {verdict} | {nviol} | {human} |"
        )

    out += ["", "## Cases requiring attention", ""]
    flagged = [
        r
        for r in rows
        if r.get("error")
        or (r.get("grading") or {}).get("deterministic_verdict") != "PASS"
    ]
    if not flagged:
        out.append("None — every case passed the deterministic checks.")
    for r in flagged:
        g = r.get("grading") or {}
        out.append(f"### `{r['id']}`")
        if r.get("error"):
            out.append(f"- **Harness error:** {r['error']}")
        for v in g.get("forbidden_violations", []):
            out.append(f"- **Forbidden pattern** `{v['pattern']}` matched: `{v['matched']}`")
        for grp in g.get("keyword_groups", []):
            if not grp["passed"]:
                out.append(f"- **Missed concept group:** {grp['terms']}")
        out.append("")

    out += [
        "## Human review",
        "",
        "For each case, score against the rubric in `docs/evaluation-methodology.md` and",
        "record the verdict in the results JSON under `human.verdict`.",
        "",
    ]
    for r in rows:
        contract = r.get("contract") or {}
        out += [
            f"### `{r['id']}` — {contract.get('summary', '')}",
            "",
            f"**Target skill:** {r['skill']}  **Polarity:** {r['polarity']}",
            "",
            "**Must identify:**",
        ]
        for m in contract.get("must_identify") or ["_none specified_"]:
            out.append(f"- [ ] {m}")
        out.append("")
        out.append("**Forbidden behaviors:**")
        for f_ in contract.get("forbidden_behaviors") or ["_none specified_"]:
            out.append(f"- [ ] absent: {f_}")
        out += ["", "<details><summary>Response</summary>", "", "```"]
        out.append((r.get("response") or "").strip()[:6000] or "(no response)")
        out += ["```", "", "</details>", ""]
    return "\n".join(out)


def compare(old: dict, new: dict) -> str:
    o = {r["id"]: r for r in old["results"]}
    n = {r["id"]: r for r in new["results"]}
    lines = [
        "# Evaluation comparison",
        "",
        f"- Old: `{old['meta']['timestamp']}` ({old['meta']['model']})",
        f"- New: `{new['meta']['timestamp']}` ({new['meta']['model']})",
        "",
        "| Case | Old | New | Change |",
        "|---|---|---|---|",
    ]
    regressions = 0
    for cid in sorted(set(o) | set(n)):
        ov = (o.get(cid, {}).get("grading") or {}).get("deterministic_verdict", "—")
        nv = (n.get(cid, {}).get("grading") or {}).get("deterministic_verdict", "—")
        if ov == nv:
            change = "same"
        elif nv == "PASS":
            change = "**improved**"
        elif ov == "PASS":
            change = "**REGRESSION**"
            regressions += 1
        else:
            change = "changed"
        lines.append(f"| `{cid}` | {ov} | {nv} | {change} |")
    lines += ["", f"**Regressions: {regressions}**"]
    return "\n".join(lines)


# ------------------------------------------------------------------------------ main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="validate structure, no model calls")
    mode.add_argument("--run", action="store_true", help="run cases through a model")
    mode.add_argument("--report", type=Path, metavar="RESULTS_JSON")
    mode.add_argument("--compare", nargs=2, type=Path, metavar=("OLD", "NEW"))
    ap.add_argument("--runner", choices=["claude-cli", "stdin"], default="claude-cli")
    ap.add_argument("--model", default=None, help="model id passed to the runner")
    ap.add_argument("--case", action="append", dest="cases", help="run only this case id")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    if args.compare:
        old = json.loads(args.compare[0].read_text())
        new = json.loads(args.compare[1].read_text())
        print(compare(old, new))
        return 0

    if args.report:
        data = json.loads(args.report.read_text())
        text = render_report(data)
        if args.out:
            args.out.write_text(text, encoding="utf-8")
            print(f"wrote {args.out}")
        else:
            print(text)
        return 0

    cases = load_cases(args.cases)
    if not cases:
        print("error: no cases found", file=sys.stderr)
        return 2

    if args.check:
        return check_structure(cases)

    data = run_cases(cases, args.runner, args.model, args.timeout)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = data["meta"]["timestamp"].replace(":", "-")
    out = args.out or RESULTS_DIR / f"{stamp}.json"
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    report_path = out.with_suffix(".md")
    report_path.write_text(render_report(data), encoding="utf-8")
    print(f"\nresults: {out}\nreport:  {report_path}")

    failed = sum(
        1
        for r in data["results"]
        if (r.get("grading") or {}).get("deterministic_verdict") == "FAIL"
    )
    print(f"{failed} case(s) hit a forbidden pattern")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

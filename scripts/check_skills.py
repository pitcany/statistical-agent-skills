#!/usr/bin/env python3
"""Validate every skill in this library against the Agent Skills spec and the
house contract in docs/skill-authoring-guide.md.

Checks performed (all deterministic, no model calls):
  spec      name/description present, name regex + length, description length,
            name matches directory, no top-level `version` field, metadata values
            are strings, allowed-tools (if present) is a space-separated string
  budget    line count and estimated token count
  contract  required section headings present and in order
  style     banned vague-exhortation phrases

Exit status: 0 if all skills pass, 1 otherwise.

Usage:
    python3 scripts/check_skills.py [--skills-dir DIR] [--quiet]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Conservative characters-per-token ratio for dense technical markdown. Lower than the
# usual ~4.0 so the check errs toward flagging a skill as too large rather than missing one.
CHARS_PER_TOKEN = 3.6

MAX_TOKENS = 5000
MAX_LINES = 400
MIN_LINES = 100
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Required headings, in the order the authoring guide mandates. Matching is on a
# lowercased substring of the heading line so wording may vary around the keyword.
REQUIRED_SECTIONS: list[tuple[str, tuple[str, ...]]] = [
    ("purpose", ("purpose",)),
    ("when to use", ("when to use",)),
    ("when not to use", ("when not to use", "when to use / when not")),
    ("procedure", ("procedure",)),
    ("findings catalogue", ("findings catalogue", "findings catalog")),
    ("output contract", ("output contract",)),
    ("anti-patterns", ("anti-pattern",)),
]

BANNED_PHRASES = [
    "be rigorous",
    "be careful",
    "think carefully",
    "consider carefully",
    "use your best judgment",
    "as appropriate",
    "etc. as needed",
]


@dataclass
class Result:
    skill: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_frontmatter(text: str) -> tuple[dict, str] | tuple[None, str]:
    """Split YAML frontmatter from body without requiring PyYAML.

    Returns (mapping, body). Nested one-level mappings are returned as dicts.
    Values keep their raw string form; quoting is reported separately.
    """
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    raw = text[3:end].strip("\n")
    body = text[end + 4 :]

    data: dict = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[0] in " \t"
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if indented and current_key is not None:
            sub = data.setdefault(current_key, {})
            if isinstance(sub, dict):
                sub[key] = value
        else:
            data[key] = value if value else {}
            current_key = key if not value else None
    return data, body


def check_skill(skill_dir: Path) -> Result:
    res = Result(skill=skill_dir.name)
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        res.errors.append("missing SKILL.md")
        return res

    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)

    # --- spec conformance -------------------------------------------------
    if fm is None:
        res.errors.append("missing or malformed YAML frontmatter")
        return res

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        res.errors.append("frontmatter: `name` is required")
    else:
        if len(name) > MAX_NAME_LEN:
            res.errors.append(f"frontmatter: `name` exceeds {MAX_NAME_LEN} chars")
        if not NAME_RE.match(name):
            res.errors.append(
                f"frontmatter: `name` {name!r} must be lowercase alphanumeric with "
                "single hyphens, no leading/trailing/consecutive hyphens"
            )
        if name != skill_dir.name:
            res.errors.append(
                f"frontmatter: `name` {name!r} != directory {skill_dir.name!r}"
            )

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        res.errors.append("frontmatter: `description` is required and must be non-empty")
    elif len(desc) > MAX_DESCRIPTION_LEN:
        res.errors.append(
            f"frontmatter: `description` is {len(desc)} chars, max {MAX_DESCRIPTION_LEN}"
        )
    elif not re.search(r"(^|[.;—-]\s*)use\s", desc, re.IGNORECASE):
        # The spec asks descriptions to say both what the skill does and when to use it.
        # Any trigger clause opening with "Use ..." counts ("Use when", "Use before", ...).
        res.warnings.append(
            "frontmatter: `description` should state WHEN to use the skill "
            "(no 'Use ...' trigger clause found)"
        )

    if "version" in fm:
        res.errors.append(
            "frontmatter: no top-level `version` field exists in the spec; "
            "put it under `metadata`"
        )

    meta = fm.get("metadata")
    if isinstance(meta, dict):
        for k, v in meta.items():
            if k == "version" and not (v.startswith('"') or v.startswith("'")):
                res.warnings.append(
                    f"metadata.version {v!r} is unquoted; quote it so YAML keeps it a string"
                )
    elif meta is not None and not isinstance(meta, dict):
        res.warnings.append("frontmatter: `metadata` should be a mapping")

    if "allowed_tools" in fm:
        res.errors.append(
            "frontmatter: field is `allowed-tools` (hyphen), not `allowed_tools`"
        )
    if "allowed-tools" in fm:
        val = fm["allowed-tools"]
        if isinstance(val, str) and (val.startswith("[") or "," in val):
            res.errors.append(
                "frontmatter: `allowed-tools` must be a space-separated string, not a list"
            )

    # --- budget -----------------------------------------------------------
    lines = text.count("\n") + 1
    tokens = int(len(text) / CHARS_PER_TOKEN)
    if lines > MAX_LINES:
        res.errors.append(f"budget: {lines} lines exceeds hard limit {MAX_LINES}")
    if tokens > MAX_TOKENS:
        res.errors.append(f"budget: ~{tokens} tokens exceeds {MAX_TOKENS}")
    if lines < MIN_LINES:
        res.warnings.append(f"budget: only {lines} lines — likely under-specified")

    # --- contract ---------------------------------------------------------
    headings = [
        line.lstrip("#").strip().lower()
        for line in body.splitlines()
        if line.startswith("#")
    ]
    joined = " || ".join(headings)
    last_index = -1
    for label, needles in REQUIRED_SECTIONS:
        idx = next(
            (
                i
                for i, h in enumerate(headings)
                if any(n in h for n in needles)
            ),
            None,
        )
        if idx is None:
            if label == "when not to use" and "when to use" in joined:
                res.warnings.append(
                    "contract: no explicit 'When NOT to use' heading — "
                    "confirm sibling routing is present"
                )
            else:
                res.errors.append(f"contract: missing required section '{label}'")
        else:
            if idx < last_index:
                res.warnings.append(
                    f"contract: section '{label}' appears out of the mandated order"
                )
            last_index = max(last_index, idx)

    # --- style ------------------------------------------------------------
    lowered = body.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            # Allowed when explicitly quoted as an anti-pattern.
            for ln, line in enumerate(body.splitlines(), 1):
                if phrase in line.lower() and '"' not in line and "never write" not in line.lower():
                    res.warnings.append(
                        f"style: vague exhortation {phrase!r} at line ~{ln}"
                    )
                    break

    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "skills",
    )
    ap.add_argument("--quiet", action="store_true", help="only print failures")
    args = ap.parse_args()

    if not args.skills_dir.is_dir():
        print(f"error: no skills directory at {args.skills_dir}", file=sys.stderr)
        return 2

    dirs = sorted(d for d in args.skills_dir.iterdir() if d.is_dir())
    if not dirs:
        print(f"error: no skills found in {args.skills_dir}", file=sys.stderr)
        return 2

    results = [check_skill(d) for d in dirs]
    failed = [r for r in results if not r.ok]

    for r in results:
        if r.ok and args.quiet and not r.warnings:
            continue
        status = "PASS" if r.ok else "FAIL"
        print(f"[{status}] {r.skill}")
        for e in r.errors:
            print(f"    error:   {e}")
        for w in r.warnings:
            print(f"    warning: {w}")

    total_warn = sum(len(r.warnings) for r in results)
    print(
        f"\n{len(results) - len(failed)}/{len(results)} skills passed"
        f" ({total_warn} warning(s))"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

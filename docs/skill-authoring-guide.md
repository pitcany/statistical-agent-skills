# Skill Authoring Guide

This guide is the **binding contract** for every skill in this library. A skill that
violates it should not be merged. It exists so twelve skills written at different times
behave like one system.

## 1. File layout

```
skills/<skill-name>/
├── SKILL.md          # required, the only file always loaded
└── reference/        # optional, loaded on demand by the model
    └── *.md
```

- Directory name MUST equal the frontmatter `name`.
- `name`: lowercase letters, digits, hyphens only.
- One skill = one reviewing job. If a skill needs two report shapes, it is two skills.

## 2. Frontmatter

```yaml
---
name: leakage-auditor
description: <what it does>. Use when <concrete triggers>.
license: MIT
metadata:
  library: statistical-agent-skills
  version: 1.0.0
  report: standard-review     # or: none
---
```

Required: `name`, `description`. `description` is the **only** text the model sees when
deciding whether to load the skill, so it must contain concrete trigger words a user
would actually type ("AUROC", "backtest", "tCPA", "parallel trends"), not abstractions.
Keep it under ~500 characters.

## 3. Size budget (progressive disclosure)

| File | Budget | Hard limit |
|------|--------|-----------|
| `SKILL.md` | 150–320 lines / ≤10 KB | 400 lines |
| `reference/*.md` | any | — |

`SKILL.md` is loaded into context whenever the skill triggers; long skills tax every
session that touches them. Push worked examples, long tables, and code into `reference/`
and link to them with a one-line description of when to open them.

## 4. Required section order

1. `# Title`
2. **Purpose** — 2–4 sentences. What decision this skill protects.
3. **When to use / When not to use** — the "not" list must name the sibling skill that
   handles the excluded case, so the model routes instead of guessing.
4. **Procedure** — numbered, ordered steps. This is the substance.
5. **Findings catalogue** — the specific defects to look for, each with the *signal* that
   reveals it and the *consequence* if missed.
6. **Output contract** — reference `templates/review-report.md` or inline the subset used.
7. **Anti-patterns** — behaviors that are wrong even if they look thorough.

## 5. House style rules

- **Operational, not exhortative.** Never write "be rigorous", "think carefully",
  "consider the assumptions". Write the check: "list every feature and the timestamp of
  the row that produces it; any feature whose source timestamp is not strictly before the
  decision timestamp is a blocker."
- **Every claim gets a mechanism.** "This is leakage" is not a finding. "`booking_form.
  party_size` is written at booking, the model scores at click; the value is unavailable at
  serving time and its presence in training inflates offline AUROC" is a finding.
- **Name the estimand before the method.** Skills that jump to method selection before
  establishing target/unit/assumptions are defective.
- **Distinguish evidence tiers explicitly.** Use `observed` (seen in the supplied
  artifact), `inferred` (follows from what was supplied), `unverifiable` (needs
  information the user has not given). Never present `inferred` as `observed`.
- **Never fabricate.** No invented citations, theorem names, package APIs, or numeric
  results. If a named result is invoked, either state it precisely or say it needs
  verification. Absence of a citation is always preferable to a plausible fake.
- **Ask, don't assume.** When the deciding fact is missing (label maturity, split
  strategy, randomization unit), the skill must emit an explicit question in
  §14 rather than silently assuming the favorable case.

## 6. Severity rubric

Severities are about **what the finding invalidates**, not about how hard it is to fix.

| Severity | Definition | Test |
|----------|------------|------|
| `blocker` | The reported result or planned deployment is invalid, or would cause dollar/decision harm. Must be fixed before the number is believed or the model ships. | "If we shipped this today, would the conclusion be wrong or would money move on a wrong number?" |
| `high` | A specific, named bias or failure mode is present and plausibly material, but magnitude is unquantified. | "Can I name the mechanism and its direction?" |
| `medium` | Weakens confidence or generality; conclusions likely survive. | "Would a careful reviewer require this before publication but not before a decision?" |
| `low` | Correctness-neutral improvement to robustness, clarity, or efficiency. | — |
| `informational` | Context, alternative approach, or note with no defect attached. | — |

Rules:
- Every `blocker` and `high` MUST state the direction of bias (optimistic / pessimistic /
  unknown-but-bounded) or say explicitly that direction is undetermined.
- Do not inflate severity to seem thorough. A review with everything marked blocker is
  useless. If nothing is a blocker, say so in one sentence.
- Statistical invalidity and software bugs are separate axes. A correct implementation of
  the wrong estimand is a `blocker`; a buggy implementation of the right one is a defect
  report, not a statistical finding — say which you are reporting.

## 7. Output contract

Review skills emit the report in `templates/review-report.md`. Sections that do not apply
are dropped with a one-line reason, not padded. The report is a container for reasoning,
never a substitute: a filled-in template with no mechanism named in any finding is a
failed review.

## 8. Testing a skill

Every skill needs at least one positive and one negative case under `evals/cases/`, with
expected and forbidden behaviors under `evals/expected-behaviors/`. See
`docs/evaluation-methodology.md`. Run `python3 evals/runners/run_evals.py --check` to
validate structure without model calls.

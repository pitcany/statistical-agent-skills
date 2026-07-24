# Validation Report — 2026-07-23

Records what was actually executed and observed. Every claim below corresponds to a command
run during the build; nothing is projected or assumed.

## 1. Structural validation (deterministic, no model)

```
$ python3 scripts/check_skills.py
12/12 skills passed (0 warning(s))
```

Checks applied per skill: spec conformance (`name` regex and length, `name` matches
directory, `description` present and within 1024 chars with a trigger clause, no top-level
`version` field, `metadata` shape, `allowed-tools` spelling and form), budget (line count
and estimated token count against the 5000-token recommendation), contract (required
section headings present and in mandated order), and style (banned vague-exhortation
phrases).

Two defects were found and fixed by this check during the build:

1. Unquoted `metadata.version: 1.0.0` across all 12 skills — quoted so YAML keeps it a
   string, per the spec's "map from string keys to string values".
2. A false positive in the checker itself: the trigger-clause detector only accepted
   "Use when", rejecting the valid "Use before a model launch..." in
   `production-ml-review`. The checker was corrected rather than the skill.

Token budget measured (conservative 3.6 chars/token): largest skill is `bayesian-modeling`
at ~4843 tokens; all 12 are under the 5000-token recommendation and under the 400-line
house limit.

## 2. Installation

```
$ ./scripts/install.sh --dry-run     # inspected, then
$ ./scripts/install.sh
12 skill(s), 8 command(s) linked
```

Verified afterwards:

- `~/.claude/skills/<name>` are symlinks resolving into
  `~/Projects/statistical-agent-skills/skills/<name>` — confirmed with `ls -la`.
- The one pre-existing collision, `~/.claude/commands/stat-review.md` (an ECC command),
  was moved to `~/.claude/_superseded-statskills/20260723-195613/stat-review.md` and
  recorded in `manifest-20260723-195613.tsv`. The file was confirmed present at the backup
  path after installation.
- No other pre-existing file was moved or modified.

## 3. Discovery in Claude Code (end-to-end, not a filesystem check)

A fresh non-interactive session was asked to enumerate which of the twelve skills were
available to it:

```
$ claude -p "List which of these skills are available to you right now, by name only ..."
```

All 12 were returned. This confirms Claude Code parses the frontmatter and registers each
skill from the symlinked directory — symlinks are followed correctly.

The 8 commands were likewise registered and appear in the session's command list.

## 4. Automatic skill selection (end-to-end)

The important test: does the model *select* the right skill from a realistic prompt with no
explicit invocation? A churn-model prompt was sent to a fresh session with no mention of
leakage, skills, or any command:

> "My churn model gets 0.94 AUROC on the holdout, way better than the 0.71 we used to get.
> Features include days_since_last_login, support_tickets_opened, and
> cancellation_reason_code from the accounts table. We score customers monthly. Is this
> good to ship?"

Observed behavior — the response:

- established the **decision timestamp** before evaluating any feature;
- produced the **prediction-time availability table** with the mandated columns, including
  the "when value is written" vs "vs. decision time" ordering;
- identified `cancellation_reason_code` as a `blocker` **with the time-ordering mechanism
  stated** (the code exists only because the label event occurred) and noted the missingness
  pattern alone reproduces the label;
- stated the **direction of bias** (optimistic) and predicted the deployed ceiling near the
  0.71 baseline;
- flagged `days_since_last_login` as `high` via mutable-field temporal leakage — a defect
  not present in the prompt's surface and only reachable by reasoning about snapshot
  semantics;
- used the **evidence tiers** correctly, marking claims `inferred` and `unverifiable`
  rather than asserting them, and converting the unknowns into explicit questions;
- listed entity leakage (`account_id` across splits) and preprocessing-before-split as
  unverified rather than assuming the favorable case;
- **routed to siblings** (`calibration-and-ranking`, `model-evaluation`) with the specific
  question each should answer, and explicitly deferred them as "the second conversation";
- closed with the open questions blocking a verdict.

This exercises the hub-and-spoke routing, the availability table, the severity rubric, the
evidence tiers, and the anti-pattern prohibitions in a single unprompted response. It is
the strongest evidence collected that the library functions as designed.

## 5. Command invocation

The 8 commands are registered and resolve to the repository files through their symlinks.
Their bodies instruct the model to invoke the corresponding skill and request the structured
inputs listed in each command.

## 6. What was NOT validated

Stated plainly so the gaps are not mistaken for coverage:

- **The full evaluation suite has not been run against a model.** The harness's `--check`
  mode validates case structure; a scored `--run` across all cases with human rubric grading
  is the next step and has not been performed.
- **Multi-turn behavior is untested.** Every test above is single-turn. Whether a review
  holds its position under pushback ("are you sure? we've always done it this way") is
  arguably the more important property and is not covered by static cases.
- **Only one automatic-selection scenario was run end-to-end.** Eleven of the twelve skills
  have not been individually verified to trigger from an unprompted realistic query.
- **Negative-case behavior (false-positive resistance) is untested against a model.** The
  sound-design cases exist but have not been scored.
- **Cross-skill contention with the pre-existing ECC statistics skills is unmeasured.** Both
  sets are installed; which one the model selects for an ambiguous query has not been
  characterized.

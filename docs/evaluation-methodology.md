# Evaluation Methodology

## What this evaluation can and cannot establish

The harness in `evals/runners/run_evals.py` performs two mechanically reliable checks:

1. **Forbidden-pattern detection.** Some failures are detectable by regex because they are
   assertions, not reasoning — "AUROC shows the model is well calibrated", "use
   `train_test_split` with shuffle". Any match is an automatic fail.
2. **Concept coverage.** Whether the response mentions at least one term from each required
   group. A miss is strong evidence of a failure. A hit is *weak* evidence of success.

It cannot establish statistical quality. A response can name every required concept and
still be wrong: it can identify "leakage" without the time ordering that makes it leakage,
assert a correct conclusion from an incorrect mechanism, or produce a perfectly formatted
14-section report containing no reasoning. Keyword matching cannot separate these from
correct answers, and pretending otherwise would make the harness actively misleading.

**Therefore: deterministic PASS is a necessary condition for a case to pass, never a
sufficient one.** Every case requires human review against the rubric below. The harness's
job is to make that review cheap and organized, and to catch regressions between versions
without a human in the loop each time.

## Case design

Each case is a pair:

- `evals/cases/<id>.md` — frontmatter (`id`, `skill`, `polarity`, `tags`) plus the verbatim
  prompt under a `## Prompt` heading.
- `evals/expected-behaviors/<id>.yaml` — the grading contract.

### Polarity

| Polarity | Meaning | Failure mode it tests |
|---|---|---|
| `positive` | The flaw is genuinely present | False negatives — the skill misses a real defect |
| `negative` | The design is genuinely sound in the named respect | False positives — the skill manufactures a defect to appear thorough |

A library evaluated only on positive cases rewards paranoia. A reviewer that flags
everything scores perfectly on positive cases and is useless in practice. Negative cases
are what make the score meaningful, and they must be genuinely sound — a "negative" case
with a subtle real flaw is a broken case, not a hard one.

### Contract fields

```yaml
must_identify:        # substantive; human-graded
must_mention_any:     # groups of synonyms; >=1 hit per group required; machine-graded
forbidden_behaviors:  # substantive; human-graded; any occurrence fails the case
forbidden_patterns:   # regex, case-insensitive; machine-graded; any match fails the case
required_severity:    # the top severity a correct review should assign
```

## Human review rubric

Score each dimension 0–2. A case **passes** only with no zeros and a total ≥ 9 of 12.

| # | Dimension | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | **Estimand first** | Method advice given before the target/estimand is stated | Estimand stated but vaguely | Task class, estimand, and unit stated before any method commentary |
| 2 | **Mechanism** | Findings asserted without mechanism ("this is leakage") | Mechanism gestured at | Every finding names the specific mechanism; leakage findings state the time ordering |
| 3 | **Correctness** | A materially wrong statistical claim | Minor imprecision | Statistically sound throughout |
| 4 | **Severity discipline** | Everything blocker, or a real blocker marked low | Severities roughly right | Severities match the rubric; direction of bias stated for blocker/high |
| 5 | **Evidence honesty** | Assumes unstated facts favorably; fabricates a citation or number | Some unmarked inference | `observed` / `inferred` / `unverifiable` distinguished; missing facts become questions |
| 6 | **Actionability** | No concrete change proposed | Vague recommendations | Each required change is specific enough to implement |

Any of the following is an automatic case failure regardless of score:

- A fabricated citation, theorem, dataset, package API, or numeric result.
- A causal claim asserted from an associational design.
- Recommending a random split for time-ordered data.
- Offering a discrimination metric as evidence about calibration.
- On a `negative` case: reporting a blocker that does not exist.

## Running

```bash
# structure only — no model calls, suitable for CI
python3 evals/runners/run_evals.py --check

# full run
python3 evals/runners/run_evals.py --run --runner claude-cli --model sonnet

# single case while iterating on a skill
python3 evals/runners/run_evals.py --run --case booking-form-feature-at-click-time

# regenerate the human-review report from saved results
python3 evals/runners/run_evals.py --report evals/results/<stamp>.json --out review.md

# regression check between skill versions
python3 evals/runners/run_evals.py --compare evals/results/old.json evals/results/new.json
```

Results are written to `evals/results/` (git-ignored) as JSON plus a rendered Markdown
report. The JSON records the model, runner, harness version, and library version, so a
comparison across versions is meaningful.

## Comparing skill versions

The intended loop when changing a skill:

1. Run the affected cases against the current skill; save results.
2. Change the skill; bump `metadata.version`.
3. Re-run the same cases with the **same model**; save to a new file.
4. `--compare` the two. Investigate every `REGRESSION`.

Model differences confound version comparisons — always hold the model fixed. A comparison
across different models measures the model, not the skill.

## Known limitations

- Deterministic grading is coverage-based and cannot assess argument quality.
- The `claude-cli` runner invokes `claude -p`, which is a *fresh* session; it exercises
  automatic skill selection only if the skills are installed at user or project level.
  To test a skill's content in isolation, paste the skill body into the prompt instead.
- Case prompts are static. They do not test multi-turn behavior, where a reviewer must
  hold its position under pushback — arguably the more important property.
- There is no inter-rater reliability process for the human rubric. With one reviewer,
  scores drift over time; re-score a sample of old cases when calibration is in doubt.

# Limitations and Roadmap

## Known limitations

### Evaluation

1. ~~The suite has not been run to completion against a model.~~ **Done 2026-07-24** — full
   16-case scored run against `claude-fable-5`, 16/16 pass on the human rubric (mean
   11.94/12), 0 forbidden-pattern violations. See `docs/eval-run-2026-07-24.md`. The
   remaining evaluation limitations below still hold.
2. ~~False-positive resistance is untested.~~ **Tested 2026-07-24** — both negative cases
   passed; neither sound design was assigned a manufactured blocker (`sound-temporal-split`
   scored 11/12, its one docked point being a mild over-cautious severity tag, not a false
   blocker). Still single-model, single-run.
3. **Only one model has been evaluated.** The run used `claude-fable-5`. A weaker model would
   plausibly score lower, and the suite's power to *discriminate* weak models from strong
   ones is uncharacterized. Run with a lower `--model` and `--compare`.
4. **Deterministic grading cannot assess reasoning quality.** It detects missing concepts
   and forbidden assertions. It cannot distinguish a correct leakage argument from a fluent
   wrong one. The human rubric is not optional — the run confirmed this directly: 4 cases
   scored deterministic PARTIAL (keyword-phrasing misses) yet passed the rubric cleanly.
5. **Single-rater grading.** The rubric was applied by one grader. With one rater, scores
   drift; a second independent pass on a sample is the standard check, not yet done.
6. **Multi-turn robustness untested.** Every case is single-turn; holding position under
   pushback is not covered.
7. **Negative cases are only as good as their author's care.** Demonstrated the hard way
   during validation: a hand-written "sound" test case contained a genuine bi-temporal
   defect the author did not intend, and the model was right to flag it. Any negative case
   must be audited at least as carefully as the reviewer will audit it.

### Coverage

6. **Single-turn only.** Nothing tests whether a review holds its position under pushback
   ("are you sure? we've always done it this way"), which is arguably the property that
   determines whether the library is useful in a real consulting engagement.
7. **Eleven of twelve skills have not been verified to trigger** from an unprompted
   realistic query. Four have (`leakage-auditor`, `adtech-value-optimization`,
   `statistical-proof-review`, and `experiment-design`/`leakage-auditor` jointly on the
   fraud case).
8. **Trigger contention with the ECC statistics skills is unmeasured.** Both collections are
   installed and several descriptions are adjacent. Which one the model selects for an
   ambiguous query has not been characterized. See `docs/architecture.md` §4 for the
   de-duplication options.
9. **No skill executes anything.** These are review procedures, not analysis tooling. They
   will tell you to check rolling-origin interval coverage; they will not compute it. That
   is deliberate, but it means the library cannot catch a defect that only appears when the
   numbers are actually run.
10. **`base` conda environment lacks scikit-learn and statsmodels.** Irrelevant to the
    skills themselves (they import nothing), but relevant if a review's recommended
    diagnostic is to be executed in that environment.

### Scope

11. **No marketing-mix modeling, incrementality, or geo-experiment coverage.** The adtech
    skill covers the value-signal path, not media measurement.
12. **No survival analysis, no experimental design beyond A/B (no factorial, no bandits),
    no missing-data methodology depth (MI vs FIML), no measurement/psychometrics.**
13. **Adtech skill is written against Google/Meta/TikTok conventions** current as of
    2026-07. Platform bidding mechanics change; the statistical content is durable but the
    objective names and integration constraints will drift.

## Recommended next three skills

### 1. `analysis-audit-benchmark` — an eval suite for flaw-auditing, not answering

The gap already identified on this machine: the two existing eval harnesses
(`~/AI/benchmarks/` for model/serving A/B, `~/AI/scripts/rag/eval/` for math-stat RAG) both
test *answering and deriving*. This library's harness tests *review behavior* but only over
16 hand-written cases. The high-ROI next build is a systematically generated benchmark of
seeded analyses — inject one known defect into an otherwise-correct notebook, at a known
severity, and measure detection rate and false-positive rate per defect class. That turns
"the reviews look good" into a number, and it is the only item here that improves confidence
in everything else.

### 2. `sample-size-and-sequential-design`

Currently split across `experiment-design` (MDE, power) and nothing else. Deserves its own
skill because it is *prospective* — invoked before data exists, with a different output
shape (a design specification, not a review report). Should cover: power for ratio and
count metrics, variance estimation from pilot data, cluster designs with ICC estimation,
sequential designs (alpha spending, group sequential, always-valid confidence sequences),
switchback and interleaving designs, and the decision-theoretic framing of how long to run
given the cost of delay. The current library can criticize a design; it cannot produce one.

### 3. `mixed-effects-and-clustered-data`

Repeated measures, nested/crossed random effects, and cluster-robust inference recur in
almost every skill's findings catalogue ("unit mismatch understates variance") without any
skill owning the methodology. Should cover: choosing random effects vs cluster-robust SEs vs
GEE, convergence failures and singular fits, when partial pooling helps and when it hides
heterogeneity, small-cluster corrections (CR2/CR3, Satterthwaite df), crossed designs, and
the relationship to the Bayesian hierarchical treatment already in `bayesian-modeling`. This
is the single most common source of understated uncertainty in applied consulting work and
currently has no home.

### Honorable mentions

- `survey-and-weighting` — sampling frames, raking, design effects, non-response.
- `metric-design` — defining a metric that is sensitive, hard to game, and decision-relevant
  before any experiment is designed around it.
- `notebook-to-production` — the reproducibility path, complementing `production-ml-review`
  from the analysis side rather than the serving side.

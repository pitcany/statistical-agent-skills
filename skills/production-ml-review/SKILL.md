---
name: production-ml-review
description: Review ML systems headed to or in production — training/serving skew, offline/online metric divergence, drift monitoring, delayed labels, shadow and canary deployment, rollback criteria, model/feature/calibrator versioning, retraining triggers, reproducibility. Use before a model launch, when online metrics diverge from offline, or when auditing an ML serving/monitoring/retraining setup.
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Production ML Review

## Purpose

Determine whether a model that performs offline will keep performing after it ships,
and whether anyone will notice when it stops. This skill protects the launch/hold
decision and the operating loop after launch: skew, drift, immature labels, and
unversioned artifacts each convert a valid offline result into an invalid production
one without changing a single line of model code.

## When to use

- A model is about to be deployed, or a deployment plan/design doc is under review.
- Online metrics diverge from offline evaluation.
- Reviewing monitoring, alerting, retraining, or rollback design for a live model.
- Auditing reproducibility of a training pipeline (can this artifact be rebuilt?).

## When NOT to use

- Whether the offline evaluation itself is valid (splits, metrics, baselines) →
  `model-evaluation`. This skill assumes offline results and asks if they transfer.
- Feature availability at prediction time → `leakage-auditor` (train/serving skew
  found here that is *temporal* routes there).
- Data defects in the training snapshot → `data-quality-audit`.
- Probability calibration methodology → `calibration-and-ranking` (this skill covers
  only the *operational* handling of the fitted calibrator).
- Canary/holdback *experimental design* and power → `experiment-design`.
- Forecast-specific serving (horizon handling, retrain cadence for forecasts) →
  `time-series-forecasting`.
- Bid/value optimization loops in adtech → `adtech-value-optimization`.
- Unsure where to start → `statistical-reviewer` (hub).

## Procedure

1. **State the serving contract.** What is scored, at what moment, with what inputs,
   feeding what decision, at what QPS/latency budget. Every skew finding is a
   difference between this contract and the training setup. Tag as `observed` only
   what the supplied code/configs show; design-doc claims are `inferred`.

2. **Diff training vs serving feature computation.** For each feature: same code
   path or reimplemented? Same aggregation window (trailing 30d in training vs
   "since midnight" in serving)? Same null handling (imputed in training, passed
   raw or defaulted at serving)? Same vocabulary/encoder version? Any feature
   computed by two code paths is a standing skew finding until a
   golden-set comparison (identical entities scored through both paths, diffs
   counted) proves equality.

3. **Audit versioning and lineage.** Verify that one identifier pins together:
   model weights, feature-transform code/version, training-data snapshot (vintage),
   hyperparameters, and — if a calibrator exists — the fitted calibrator. A model
   artifact without a pinned feature-transform version is unreproducible: the same
   weights over drifted transforms is a different model with the old model's ID.
   The calibrator is a fitted model; it must be versioned, evaluated, and rolled
   back *with* the model it was fit for — a new model behind an old calibrator
   ships miscalibrated scores under a passing model-eval.

4. **Check data contracts on inputs.** For each upstream dependency: is there a
   declared schema/freshness/volume contract, and what happens on breach — does the
   pipeline fail loudly, or default-fill and score anyway? Default-fill on breach
   is the mechanism behind most silent production incidents: scores keep flowing
   while inputs are garbage.

5. **Classify drift and match the monitor to the type.**
   - *Covariate drift*: P(X) moves, relationship intact. Monitor: per-feature input
     distribution vs training snapshot (PSI/KS or decile shift), plus score
     distribution.
   - *Label/prior drift*: P(Y) moves. Monitor: realized base rate on matured
     labels vs training base rate.
   - *Concept drift*: P(Y|X) moves. Monitor: performance metric on matured labels,
     per segment — input monitors CANNOT detect concept drift; only outcome
     monitors can.
   A monitoring plan with input monitors only must be flagged: it is blind to the
   drift type that most directly degrades decisions.

6. **Define label maturity before reading any online metric.** Maturity window =
   the delay after which the label is considered final (e.g. conversions credited
   up to 30d post-click ⇒ 30d window, or a chosen quantile of the observed delay
   distribution). Rule: evaluating on immature labels biases toward fast
   converters — recent cohorts show only quick outcomes, so any model that
   favors fast-responding entities looks better than it is (optimistic for it,
   pessimistic for slow-converting segments). Every online readout must state the
   cohort's age relative to the maturity window.

7. **Trace backfills into training data.** When history is restated (late events,
   corrected labels, re-run feature jobs), training data for past dates changes
   after the fact. Check: are training snapshots frozen (vintage-stamped) or
   recomputed from live tables? Recomputed-from-live means (a) retraining on data
   the original model never saw at that vintage, and (b) backfilled features can
   embed post-decision information — route that consequence to `leakage-auditor`.

8. **Review the rollout path.**
   - *Shadow*: new model scores live traffic, decisions still made by incumbent.
     Verify shadow scores are logged and compared (score distributions, agreement
     rate, feature-fetch error rate) — a shadow with no readout is a checkbox.
   - *Canary*: new model takes a small traffic slice. Verify the gating readout is
     defined before the canary starts: which metrics, on how much traffic, over how
     long (must cover label maturity for outcome metrics or explicitly gate on
     proxy + input metrics only), and the numeric promote/abort thresholds.
   - *Rollback*: criteria written and agreed BEFORE launch — the metric, the
     threshold, the observation window, who decides, and the mechanical steps
     (previous model + its calibrator + its feature versions restorable). A
     rollback plan defined during the incident is a finding, not a plan.

9. **Audit the monitoring/alerting inventory.** Split explicitly:
   - *Input monitors* (fast, cause-side): feature null/default rates, input volume,
     feature distributions, upstream freshness, score distribution.
   - *Outcome monitors* (slow, effect-side): realized performance on matured
     labels, calibration on matured labels, business KPI per model version.
   Every alarm needs an owner and a runbook action; an alarm nobody acts on is
   informational, not monitoring. Verify alert thresholds were set from historical
   variance, not guessed.

10. **Review retraining triggers and the feedback loop.** Which trigger:
    scheduled, drift-triggered, performance-triggered — and is the trigger's
    metric itself monitored (step 9)? Then check the loop: if the current model's
    decisions determine which labels get observed (only approved loans default,
    only shown ads convert), retraining on that data learns the incumbent's
    selection policy. Ask what breaks the loop — exploration traffic, holdback
    slice, or importance weighting — and flag its absence as a named finding.

11. **Verify reproducibility end to end.** Concrete test: could an engineer rebuild
    the exact production artifact from committed code? Requires: pinned seeds
    (and a note where nondeterminism remains, e.g. GPU ops), vintage-stamped data
    snapshot, pinned environment (lockfile/container digest), and recorded
    hyperparameters. "We could probably reconstruct it" is `unverifiable` — ask
    for the last time a rebuild was actually performed.

12. **Check documentation.** A model card or equivalent stating: intended use and
    known exclusions, training-data window and population, evaluation slices and
    results, fairness/segment caveats, owners, and the rollback contact. Absence
    is a `medium` finding on its own and a `high` one when combined with
    multi-team consumers of the scores.

## Findings catalogue

| Finding | Signal | Consequence if missed |
|---|---|---|
| Training/serving skew (dual code paths) | Feature logic exists in both a training repo and a serving service; no golden-set diff run | Offline metrics do not transfer; online performance silently lower (optimistic offline bias) |
| Aggregation-window mismatch | Training feature uses trailing-N-day window, serving uses since-midnight or cached daily value | Same feature name, different quantity; skew concentrated in time-sensitive segments |
| Null-handling mismatch | Imputer fit in training pipeline, serving path defaults to 0/missing | Scores shift exactly for rows with missing data — the rows where the model is already least reliable |
| Unpinned feature-transform version | Model registry stores weights only; transform code resolved from "latest" | Artifact unreproducible; silent behavior change on every transform deploy |
| Orphaned calibrator | Calibrator fit date ≠ model fit date, or calibrator absent from rollback plan | Miscalibrated probabilities feed thresholds/bids; decision layer wrong while ranking metrics look fine |
| No data contract / soft-fail ingestion | Upstream schema change produced default-filled features and no page | Model scores garbage confidently; detected weeks later via business KPI (direction unknown, often severe) |
| Input-only monitoring | Monitoring doc lists feature/score distributions but no matured-label performance metric | Concept drift invisible until business impact; slowest failure to detect |
| Immature-label readout | Online eval cohort younger than the label maturity window | Optimistic for fast-converter-favoring models; canary promotes the wrong model |
| Backfill into training | Training reads from live restated tables, no vintage stamps | Retrains not comparable across time; possible post-decision information in features |
| Shadow without readout | Shadow deployed, no logged comparison or report | Rollout stage consumed without de-risking anything |
| Canary gate undefined | Canary running, promote/abort thresholds "to be decided based on results" | Post-hoc gate rationalizes promotion; the canary cannot fail |
| Rollback criteria post-hoc | No pre-launch document naming metric, threshold, window, decider | Rollback debated mid-incident; bad model stays live longer; prior artifact set may not be restorable |
| Retraining feedback loop | Labels only observed for entities the current model selected; no exploration/holdback | Model converges to incumbent policy; degradation invisible in its own training data |
| Trigger on unmonitored metric | Retraining "on drift" but no drift monitor deployed | Trigger never fires; scheduled decay by another name |
| Unreproducible build | No seed/vintage/lockfile; last rebuild never attempted | Cannot distinguish code regression from data drift during incidents; rollback target unbuildable |
| Missing model card | No document stating intended use, population, exclusions | Scores reused out of scope by other teams; silent estimand change |

## Output contract

Emit `templates/review-report.md` (standard-review). Domain specifics:
- §4 doubles as the serving contract from step 1.
- §11 (deployment implications) is the report's center of gravity here — never
  omitted; it carries the skew diff (step 2), monitor inventory split
  input/outcome (step 9), and label-maturity statement (step 6).
- Add §11a **Pre-deployment gate** — every item pass / fail / unverifiable:
  1. Golden-set training-vs-serving score diff run; diff rate below stated bound.
  2. One version ID pins weights + transforms + data vintage + hyperparams + calibrator.
  3. Data contracts declared for all upstream inputs; breach behavior is fail-loud.
  4. Label maturity window defined; online eval plan respects it.
  5. Monitoring live for: input distributions, score distribution, matured-label
     performance, calibration — each with owner and runbook.
  6. Canary plan with pre-registered metrics, thresholds, duration, and decider.
  7. Rollback criteria documented pre-launch; previous artifact set restore tested.
  8. Retraining trigger defined and its metric monitored; feedback-loop breaker
     (exploration/holdback) named or its absence justified.
  9. Rebuild-from-commit performed at least once for this artifact.
  10. Model card exists and names intended use and exclusions.
  Any `fail` on items 1–7 is a `blocker` for launch; 8–10 are `high`.
- §12 findings follow the severity rubric; every blocker/high states bias
  direction (skew and immature labels: usually optimistic; contract breaches:
  direction unknown) or that it is undetermined.
- §14 lists the questions the team must answer (maturity window, last rebuild
  date, golden-set results) rather than assuming the favorable answer.

## Anti-patterns

- **Reviewing the model instead of the system.** Re-litigating offline AUROC while
  the calibrator is unversioned and no outcome monitor exists. Offline validity
  belongs to `model-evaluation`; this review owns the loop around the model.
- **Accepting "we monitor it" without the inventory.** Monitoring is a list of
  signals, owners, thresholds, and runbook actions — ask for the list, tag
  anything unlisted `unverifiable`.
- **Blessing input monitors as drift coverage.** Input monitors cannot see
  concept drift; a plan without matured-label outcome monitors has a named blind
  spot, and the review must say so.
- **Reading young cohorts.** Quoting online metrics without stating cohort age vs
  label maturity — the reviewer then commits the same immature-label bias being
  audited.
- **Gate theater.** Marking gate items pass from design-doc intent rather than
  evidence of execution (a rollback *plan* is not a *tested restore*).
- **Severity inflation.** Not every gap blocks launch: a missing model card with a
  single consuming team is `medium`/`high`, not `blocker`. Reserve `blocker` for
  items where shipping today produces wrong decisions or an unrecoverable state.

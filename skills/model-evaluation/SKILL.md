---
name: model-evaluation
description: Review model evaluation methodology — metric choice vs the decision, baselines actually run (majority class, best single feature, seasonal naive, incumbent), test-set discipline, bootstrap CIs and paired tests (McNemar), nested CV, selection-induced metric inflation, slice evaluation, sample size for the claimed precision, threshold selection. Use when a model is claimed "better", when a metric moved between runs, when reviewing an eval harness or a model-comparison table, or before promoting a model.
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Model Evaluation

## Purpose

Determine whether a reported model-quality number supports the decision it is being
used to make — ship, promote, keep, or claim improvement. This skill protects against
believing point metrics that are the product of metric–decision mismatch, unrun
baselines, exhausted test sets, selection inflation, or noise mistaken for signal.

## When to use

- A model comparison table, eval harness, or "model X beats model Y" claim is supplied.
- A metric changed between two runs and someone must decide if the change is real.
- A promotion/ship decision hangs on an offline number.
- An evaluation protocol (splits, folds, seeds, thresholds) is being designed or audited.

## When NOT to use

- Feature availability, split contamination, entity/temporal leakage →
  `leakage-auditor` (run it first; evaluation of a leaky pipeline measures the leak).
- Whether probabilities are calibrated or a ranking metric fits the use →
  `calibration-and-ranking` (this skill decides *whether the number is trustworthy*;
  that one decides *whether it is the right kind of number*).
- Backtesting protocol, rolling-origin evaluation, forecast horizons →
  `time-series-forecasting`.
- Online A/B tests of a deployed model, power, randomization → `experiment-design`.
- Causal claims about why the metric moved → `causal-inference`.
- Post-deployment monitoring, shadow traffic, rollback criteria →
  `production-ml-review`.
- Raw data defects (duplicates, drift, joins) → `data-quality-audit`.
- Unclear which of these applies → `statistical-reviewer`.

## Procedure

1. **State the decision the metric serves.** Write one sentence: "if <metric> is
   <better/worse> than <reference>, we will <action>". If no action can be named, the
   evaluation has no acceptance criterion — record that as the primary finding.
2. **Check metric–decision match.** The metric's loss structure must reflect the
   decision's costs: threshold decisions need metrics at the operating threshold;
   top-k selection needs precision/lift at k; asymmetric error costs need
   cost-weighted metrics or decision curves; accuracy on imbalanced classes matches
   almost no decision (see step 10). Name the mismatch mechanism, not just "wrong
   metric".
3. **Demand run baselines.** Require, as computed rows in the results table, whichever
   apply: (a) majority-class / base-rate predictor; (b) the single best feature alone
   (one shallow model or one threshold rule); (c) last-value or seasonal-naive for
   anything temporal; (d) the incumbent production model on the same eval set.
   A baseline that is *named* but not *run* is a finding: without the row, "model adds
   value" is unverifiable, and the gap to the trivial baseline — not the raw metric —
   is the effect being claimed.
4. **Audit split discipline and count test touches.** Establish: which set tuned
   hyperparameters, which set selected the model, which set produced the headline
   number. Ask directly: "how many distinct configurations have been scored on the
   test set, ever?" Each touch converts test into validation; after tens of touches the
   test metric is optimistically biased by selection just like a validation metric.
   If the count is unknown, the test set's independence is `unverifiable` — say so.
5. **Require nested CV when tuning and estimating share data.** If hyperparameters
   were tuned by CV and the same CV score is reported as the performance estimate,
   the number is the maximum of many noisy draws — biased upward. Fix: outer loop for
   estimation, inner loop for tuning, or a untouched test set outside the tuning loop.
6. **Quantify uncertainty on the metric itself.** A point metric is a sample
   statistic. Require at least one of, matched to the setting:
   - **Bootstrap CI** over eval-set rows (resample rows, recompute metric, 1000+
     replicates; use cluster bootstrap at the entity level when rows share entities).
   - **Seed/fold variance**: metric across ≥5 seeds or folds, reported as mean ± sd —
     mandatory whenever training is stochastic (deep nets, boosted trees with
     subsampling).
   - **McNemar's test** for two classifiers on the same test set: build the 2×2
     discordant-pair table (A right/B wrong vs A wrong/B right); only discordant pairs
     carry information about the difference.
7. **Use paired comparisons on shared eval data.** Two models scored on the same rows
   are correlated; comparing their marginal CIs is throwing away the pairing and
   drastically overstates uncertainty of the *difference*. Compute the per-row (or
   per-fold) metric difference and bootstrap/t-test that difference. Overlapping-CI
   reasoning on paired metrics is a named finding, in both directions: overlapping
   marginal CIs do not imply no difference, and the paired test is the one that decides.
8. **Account for selection over many candidates.** If k models/configurations were
   compared and the best is reported, the winner's metric is inflated by the max of k
   noise draws. Checks: report the runner-up gap relative to the paired-difference CI;
   re-score the single chosen model on a held-out set never used in selection; treat
   "best of 40 configs beats baseline by 0.4 sd" as unresolved, not as a win.
9. **Check sample size against the claimed precision.** For a proportion-like metric
   on n rows, the binomial se is √(p(1−p)/n): at n = 1000, p ≈ 0.8, se ≈ 1.3pp — a
   "+0.5pp improvement" claim is inside one standard error and unresolvable at that n.
   For AUROC, uncertainty is governed by min(n_pos, n_neg), not n. Flag any reported
   decimal place finer than the se supports, and any claimed delta smaller than ~2×
   the paired-difference se.
10. **Evaluate under class imbalance correctly.** At 1% prevalence: accuracy of the
    all-negative predictor is 99% (hence baseline (a) is mandatory); AUROC can be high
    while precision in the actionable range is near zero — require AUPRC or
    precision/recall at the operating point, and note AUPRC's dependence on prevalence
    when comparing across datasets. Never compare metrics across eval sets with
    different prevalence without saying so.
11. **Audit threshold selection.** If a threshold was chosen (max-F1, Youden, cost
    minimum), it is a fitted parameter: it must be selected on validation data and
    the thresholded metrics reported on a separate holdout. A threshold tuned and
    reported on the same set inflates every threshold-dependent metric —
    optimistically, and worst for small eval sets and spiky metric-vs-threshold curves.
12. **Require effect size with the verdict.** Report the absolute and relative delta
    with its CI, next to the decision-relevant scale from step 1 (e.g. "+0.8pp
    precision@100 ≈ +N correct actions/day"). "p < 0.05 vs baseline" without magnitude
    does not support a ship decision; a tightly-estimated negligible delta is a
    "do not ship the added complexity" result, and that is a valid conclusion to report.
13. **Report slice metrics.** Recompute the headline metric on decision-relevant
    slices (segment, geography, time period, cohort vintage, entity size) with per-slice
    n and CIs. Require: no slice with material traffic degrades versus incumbent beyond
    its CI. Aggregate wins composed of large-slice gains and small-slice regressions
    are a routing decision, not a clean win — surface them.

## "The metric moved — is it real?" (procedure)

Run in order; stop at the first step that explains the move.

1. **Same eval set?** Diff row counts, row IDs (hash the ID set), label version, and
   prevalence between the two runs. A changed eval set explains most "movements";
   if changed, re-score both models on the intersection before any other step.
2. **Same metric implementation?** Confirm identical code path/version computed both
   numbers (averaging mode, tie handling, and NaN policy silently change AUROC/F1).
3. **Within noise?** Compute the paired per-row difference on the shared eval set;
   bootstrap its CI (cluster by entity if applicable). If 0 is inside the CI, the move
   is unresolved at this n — report the CI, not the point delta.
4. **Seed variance?** If training is stochastic, retrain each variant on ≥3 seeds. If
   the between-variant gap is inside the within-variant seed spread, the move is noise.
5. **Selection artifact?** Count candidates evaluated before this one "won" (step 8).
   Adjust expectations accordingly or re-score on fresh data.
6. **Slice-localized?** Decompose the delta by slice (step 13). A move concentrated in
   one small slice suggests a data change or slice-specific artifact, not a model
   improvement — inspect that slice's rows before believing it.
7. Only if it survives 1–6: report the move as real, with paired CI, seeds, and the
   slice decomposition attached.

## Findings catalogue

Each entry: **signal** → **consequence**, with direction of bias.

1. **Metric–decision mismatch** — signal: the step-1 sentence cannot be written, or
   the metric ignores the decision's cost structure (accuracy for rare-event
   triage, AUROC for a fixed-budget top-k product). Consequence: optimization and
   selection target the wrong objective; deployed value can fall while the metric
   rises. Direction: unknown until the right metric is computed.
2. **Named-but-unrun baseline** — signal: no baseline row in the results table;
   "obviously beats majority class" asserted. Consequence: claimed lift is
   unverifiable; historically many "strong" models fail to beat seasonal-naive or one
   feature. Direction: optimistic for the claim.
3. **Exhausted test set** — signal: test metrics quoted across many iterations of
   development; no touch count available. Consequence: headline number carries
   selection bias of unknown size; optimistic.
4. **Tuning–estimation contamination (missing nested CV)** — signal: best CV score
   from the tuning search reported as the performance estimate. Consequence: upward
   bias that grows with search-space size and metric noise; optimistic.
5. **No uncertainty on the metric** — signal: point metrics with ≥3 significant
   figures, no CI/sd, single seed. Consequence: noise-level deltas drive ship
   decisions in both directions; direction undetermined by construction.
6. **Unpaired comparison on shared data** — signal: two marginal CIs compared, or
   "CIs overlap so it's a tie" on the same eval rows. Consequence: real improvements
   discarded (pessimistic for detection) or ties miscalled; the paired test is the
   valid one.
7. **Winner's-curse selection** — signal: best of k ≫ 1 candidates reported without
   fresh-data confirmation; winner's margin ≪ candidate-to-candidate spread.
   Consequence: promoted model regresses toward the field in production; optimistic.
8. **Precision beyond sample support** — signal: claimed delta < paired se; deltas
   quoted to 3 decimals on n in the low thousands. Consequence: decisions on digits
   the data cannot resolve; direction random per instance, systematically optimistic
   after selection.
9. **Imbalance-blind metrics** — signal: accuracy headline with prevalence < 5%;
   AUROC alone for a top-k product; AUPRC compared across sets of different
   prevalence. Consequence: trivial predictors look strong; optimistic.
10. **Threshold tuned on the reporting set** — signal: max-F1/Youden threshold and
    the F1 it maximizes quoted from the same split. Consequence: threshold-dependent
    metrics inflated; optimistic, worst at small n.
11. **Significance without effect size** — signal: p-values or "significant" with no
    delta magnitude, CI, or decision-scale translation. Consequence: trivially small
    real effects justify complexity; the ship decision is made on the wrong quantity.
12. **Aggregate-only reporting** — signal: no slice table; headline win with no
    per-segment breakdown. Consequence: material regressions on sub-populations ship
    inside an aggregate win; direction optimistic for affected slices.

## Output contract

Emit `templates/review-report.md`. Specifics: §9 must contain the baseline table
status (which of the four baselines exist as *run* rows) and the test-touch count
(or `unverifiable`); §10 diagnostics come from Procedure steps 6–13 and the
metric-moved procedure, each with the decision it changes; §12 entries name the bias
mechanism and direction per the catalogue. Compact form is appropriate for a single
"is this comparison valid?" question.

## Anti-patterns

- Auditing the evaluation while leaving `leakage-auditor` unrun on a pipeline with
  obvious leakage risk — a perfectly disciplined evaluation of a leaky model is a
  precise measurement of the leak.
- Accepting "beats the baseline" where the baseline is described but absent from the
  results table.
- Treating a 0.003 AUROC gain on a single seed and a single split as a ranking of two
  models.
- Comparing two models on the same rows with unpaired statistics, or calling a tie
  from overlapping marginal CIs.
- Reporting the tuning search's best score as the generalization estimate.
- Declaring the test set clean without asking how many configurations have touched it.
- Choosing the threshold and quoting its metrics from the same split.
- Filling the report with every metric computable instead of the one metric matched
  to the step-1 decision plus its uncertainty.
- Demanding more decimal places of "rigor" (extra metrics, more folds) when the
  binding constraint is eval-set size — say "this n cannot resolve this delta" and
  stop there.

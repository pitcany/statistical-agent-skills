---
name: calibration-and-ranking
description: Review probability calibration and ranking quality — AUROC, AUPRC, top-k lift, reliability curves, Brier score, log loss, calibration slope/intercept, Platt scaling, isotonic regression, beta calibration, subgroup calibration, bucketed/dispatched predictions. Use when predicted probabilities feed thresholds, bids, prices, or budgets; when a calibrator is being chosen; or when someone offers AUROC as evidence that "the probabilities are good".
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Calibration and Ranking

## Purpose

Establish whether a model's scores are fit for the *use* they get: ordering items
(ranking/discrimination), being treated as probabilities (calibration), or driving an
action with asymmetric costs (decision value). These are three different properties;
evidence for one is not evidence for another, and money moves on the confusion.

## When to use

- Predicted probabilities are consumed downstream as numbers (bids, expected values,
  risk scores, budget allocation), not just as an ordering.
- A calibration method (Platt, isotonic, beta) is being chosen or reviewed.
- Reliability curves, Brier scores, or log loss are reported and need interpretation.
- Predictions are bucketed/quantized before dispatch to another system.
- Ranking metrics (AUROC, AUPRC, top-k lift) are the headline and the review must say
  what they do and do not establish.

## When NOT to use

- Whether features leak or the split is valid → `leakage-auditor` (audit that first;
  calibration analysis on a leaky model is analysis of an artifact).
- Baseline choice, test-set discipline, metric uncertainty, model comparison →
  `model-evaluation`.
- Turning calibrated conversion probabilities into ad-platform value signals or
  tCPA/tROAS bidding inputs → `adtech-value-optimization`.
- Forecast intervals and probabilistic forecasts over time → `time-series-forecasting`.
- Posterior calibration of Bayesian models (SBC, coverage of credible intervals) →
  `bayesian-modeling`.
- Monitoring calibration drift of a deployed model → `production-ml-review`.
- Unsure what the question is → `statistical-reviewer`.

## Procedure

1. **Name the downstream consumer of the score.** State exactly what reads the model
   output and what it does with the number: threshold comparison (only ordering near
   the threshold matters), expected-value arithmetic (calibration matters everywhere
   mass sits), top-k selection (only ordering in the head matters), or human display.
   Every later judgement is relative to this.
2. **Identify the dispatched value.** The model's internal continuous score and the
   value actually sent downstream are often different objects (bucketed, clipped,
   remapped, cached). Obtain the transform. All calibration checks in steps 4–8 must
   be run on the **dispatched** value; a reliability curve on the internal score does
   not certify the number the consumer receives.
3. **Classify the evidence supplied.** Sort every reported metric into discrimination
   (AUROC, AUPRC, top-k lift, NDCG), calibration (reliability curve, Brier, log loss,
   slope/intercept), or decision value (net benefit, profit curves). Flag any claim
   that cites a metric from the wrong column.
   **Rule (state it in the report whenever violated): AUROC is invariant to every
   strictly monotone transform of the scores, so it can NEVER evidence calibration.**
   Multiply all scores by 10⁻³ and AUROC is unchanged while every probability is
   absurd. The same holds for AUPRC and all rank-only metrics.
4. **Check discrimination against the use.** AUROC weights all thresholds; if the
   consumer acts only on the top 1%, report top-k lift / precision@k at the operating k
   instead, and report AUPRC rather than AUROC when prevalence is low and the positive
   class is the target of interest (AUROC can be high while the head of the ranking is
   mostly false positives).
5. **Check calibration-in-the-large.** Compare mean predicted probability to observed
   event rate on the evaluation set: `mean(p̂) / mean(y)`. A ratio far from 1 means
   every downstream expected-value computation is scaled wrong by that factor. This is
   the cheapest check and catches resampling artifacts (models trained on
   downsampled/SMOTE'd data without prior correction are miscalibrated-in-the-large by
   construction — mean p̂ ≈ training prevalence, not deployment prevalence).
6. **Fit the calibration slope.** Logistic regression of the outcome on logit(p̂):
   slope < 1 ⇒ predictions too extreme (overfitting signature); slope > 1 ⇒ too
   conservative. Report intercept (calibration-in-the-large on the logit scale) and
   slope together.
7. **Draw the reliability curve — twice.** Once with equal-width bins, once with
   equal-count (quantile) bins, 10–20 bins each, with per-bin counts and binomial CIs.
   If the two binnings disagree qualitatively, the curve is under-supported in the
   sparse regions — say which regions and do not conclude from them. Prefer a
   smoothed (loess) curve as a third view when n permits.
8. **Compute proper scores.** Brier score with its decomposition (reliability −
   resolution + uncertainty): the reliability term isolates miscalibration; resolution
   isolates discrimination; uncertainty is the irreducible `p(1−p)` of the base rate,
   so a raw Brier of 0.09 on a 10% base rate is *worse than predicting the base rate
   for everyone*, not "good because it is small". Log loss punishes confident errors
   without bound — report both, and check for clipped probabilities (p̂ ∈ {0,1})
   before trusting log loss.
9. **If a calibrator is fitted, audit it as a model.** It must be fit on data disjoint
   from both training and final evaluation (a calibrator fit and evaluated on the same
   fold reports near-perfect calibration tautologically). Method choice:
   - **Platt scaling** (2-parameter sigmoid): sample-efficient; correct when the
     miscalibration is a logit-scale shift/stretch; systematically wrong when the
     reliability curve is asymmetric or the score distribution is skewed.
   - **Beta calibration** (3-parameter): strictly generalizes Platt; prefer it when
     scores pile up near 0 or 1 or the curve is asymmetric — it can fit identity,
     Platt cannot always (Platt is forced through a sigmoid family that maps 0.5
     asymmetrically when classes are imbalanced).
   - **Isotonic regression**: nonparametric, monotone, needs the most data (unstable
     below roughly a few thousand calibration points); produces piecewise-constant
     outputs — ties in scores after isotonic are expected and harm downstream systems
     that need strict ordering.
   All three are monotone ⇒ they change calibration and leave AUROC untouched;
   verify AUROC before/after as a smoke test of the implementation.
10. **Check calibration where the data will be, not where it was.** Calibration is a
    property of the joint (p̂, y) distribution and does not survive covariate shift:
    a model calibrated on last quarter's mix is not calibrated on this quarter's.
    Compare the serving-time score distribution to the calibration-set score
    distribution (PSI/KS); if shifted, require recalibration on recent data.
11. **Check calibration by subgroup.** Repeat steps 5–7 within each decision-relevant
    segment (geography, channel, device, price tier, protected classes where
    applicable). Marginal calibration does not imply subgroup calibration: +2pp
    overprediction on segment A and −2pp on segment B average to a perfect marginal
    curve while every segment-level decision is wrong. Report the worst segment,
    with its n.
12. **If predictions are bucketed before dispatch, audit the buckets.** For each
    bucket report: occupancy, within-bucket spread of the internal score, observed
    event rate vs the dispatched representative value, and mass within ±ε of each
    boundary. Bucketing costs information (within-bucket ranking is destroyed), can be
    miscalibrated per-bucket even when the continuous score was calibrated (the
    representative value ≠ within-bucket mean outcome), and creates boundary effects
    (near-identical items dispatched materially different values).
13. **Assess decision value directly when costs are asymmetric.** Compute net benefit
    across the plausible threshold range (decision-curve analysis) against the
    treat-all and treat-none policies. A model can be well calibrated and still add no
    decision value over treat-none in the operating range; conversely a modestly
    miscalibrated model can dominate where it counts. Probability accuracy is the
    means; the decision curve is the verdict.

## Decision table: symptom → likely cause → fix

| Symptom | Likely cause | Fix |
|---|---|---|
| mean(p̂) ≫ mean(y), curve uniformly above diagonal | trained on up/downsampled data, prior not corrected | analytic prior correction of the intercept, or recalibrate on unsampled data |
| Slope < 1, S-shaped reliability curve | overfit base model, predictions too extreme | Platt or beta if curve is sigmoid-shaped; regularize base model |
| Asymmetric curve, Platt leaves residual bias at one end | miscalibration outside the sigmoid family | beta calibration; isotonic if calibration n is large |
| Reliability curve jagged, flips between binnings | too few points per bin | quantile bins, fewer bins, smoothed curve; widen CIs, don't conclude |
| Good AUROC, terrible Brier | pure miscalibration (discrimination intact) | fit a monotone calibrator; base model can stay |
| Good Brier, useless top-k precision | base-rate-dominated Brier hiding weak resolution | read the Brier decomposition; improve the base model — no calibrator adds resolution |
| Calibrated overall, wrong in every segment | offsetting subgroup miscalibration | per-segment recalibration or segment features in the calibrator |
| Calibrated at validation, drifting in production | covariate shift in the score distribution | scheduled recalibration on recent labeled data; monitor slope/intercept |
| Many tied scores downstream, sorting unstable | isotonic's piecewise-constant output | beta/Platt if ordering granularity matters downstream |
| Continuous score calibrated, dispatched values off | bucketing transform, stale bucket representative values | recompute representatives as within-bucket observed rates; narrow hot buckets |

## Findings catalogue

Each entry: **signal** → **consequence**, with direction of bias.

1. **AUROC offered as calibration evidence** — signal: "AUROC 0.85 so the
   probabilities are reliable" or any rank metric answering a calibration question.
   Consequence: unbounded miscalibration ships undetected; direction unknown until
   step 5 is run. Severity `high` when downstream consumes the number.
2. **Calibrator fit on evaluation data** — signal: same split object feeds calibrator
   fit and reliability curve. Consequence: reported calibration is tautologically
   near-perfect; optimistic.
3. **Resampling without prior correction** — signal: class weights / SMOTE /
   downsampling in training, no intercept correction, ratio check ≫ 1. Consequence:
   every EV computation scaled by ~(training prevalence / true prevalence);
   optimistic on the positive class's probabilities.
4. **Single-binning reliability conclusion** — signal: one 10-bin equal-width curve,
   no counts/CIs, conclusions about the tails. Consequence: binning artifact read as
   (mis)calibration; direction unknown.
5. **Marginal-only calibration** — signal: one pooled curve for a model driving
   segment-level decisions. Consequence: offsetting subgroup errors invisible;
   per-segment decisions biased in opposite directions.
6. **Internal score audited, different value dispatched** — signal: calibration
   evaluated upstream of a bucketing/clipping transform. Consequence: the certified
   number is not the number in use; within-bucket miscalibration and boundary
   effects unmeasured; direction unknown.
7. **Isotonic on small calibration sets** — signal: isotonic fit on < ~1000 points,
   step function with long flat runs. Consequence: high-variance calibrator that
   overfits the calibration fold; unstable downstream values.
8. **Brier/log-loss read without a base-rate anchor** — signal: "Brier = 0.08" with
   no comparison to the all-base-rate predictor's `p(1−p)`. Consequence: a model worse
   than the constant predictor reported as good; optimistic.
9. **Stale calibration under shift** — signal: calibrator fitted once, score
   distribution PSI vs calibration set is large. Consequence: systematic drift of
   dispatched values; direction follows the shift, determinable from step 10.
10. **Threshold metrics substituting for the curve** — signal: only accuracy/F1 at
    0.5 reported for a probability product. Consequence: the operating region is
    uncharacterized; ranking and calibration both unknown.

## Output contract

Emit `templates/review-report.md`. Specifics: §9 must place every supplied metric in
the discrimination / calibration / decision-value taxonomy and name what remains
unevidenced; §10 diagnostics are drawn from Procedure steps 5–13, each tied to the
decision it changes; §11 must cover calibrator versioning and recalibration cadence
whenever a fitted calibrator ships. Compact form is acceptable for a single-metric
question ("is this AUROC claim valid?").

## Anti-patterns

- Accepting any rank-only metric (AUROC, AUPRC, NDCG, lift) as evidence about
  probability values. Monotone invariance makes this a category error, not a nuance.
- Reporting a reliability curve without per-bin counts, CIs, or a second binning.
- Fitting isotonic "because it's nonparametric and therefore safer" regardless of
  calibration-set size or the downstream need for strict ordering.
- Certifying calibration of the internal score when a bucketed value is dispatched.
- Treating one pooled reliability curve as clearing a segment-level product.
- Recommending a calibrator to fix weak discrimination — monotone calibration cannot
  add resolution; it only relabels the scores.
- Running calibration analysis before `leakage-auditor` has cleared the pipeline: a
  leaky model can be beautifully calibrated on contaminated data.

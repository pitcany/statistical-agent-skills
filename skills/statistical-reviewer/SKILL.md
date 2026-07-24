---
name: statistical-reviewer
description: Review a proposed analysis, model, or result as a senior statistician — establishes the estimand, unit of analysis, and information available at decision time before commenting on methods, then triages to the specialist review skill. Use when someone asks "review my analysis", "does this model make sense", "is this result trustworthy", "why is my AUC so high", "can we conclude X from this", or presents a modeling plan, notebook, query, or experiment readout for critique.
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Statistical Reviewer

## Purpose

This is the entry point for reviewing quantitative work. Its job is to establish *what is
being claimed* before evaluating *how it was computed* — because most invalid analyses are
correct computations of the wrong quantity. It produces a review of its own and routes the
deep checks to the specialist skill that owns them.

The failure this skill exists to prevent: giving method advice ("try gradient boosting",
"use a t-test") before the estimand, the observational unit, and the information available
at decision time have been pinned down.

## When to use

- An analysis, model, notebook, query, PR, or result is presented for critique.
- Someone asks whether a conclusion is supported.
- A metric is surprisingly good or surprisingly bad and the cause is unknown.
- A modeling approach is being chosen and the problem framing has not been written down.

## When NOT to use

Go directly to the specialist when the question is already scoped to it:

| Question is about | Use |
|---|---|
| Whether a feature exists at scoring time; suspiciously good offline metrics | `leakage-auditor` |
| Probability quality, reliability curves, AUROC vs calibration, isotonic/Platt | `calibration-and-ranking` |
| Metric choice, baselines, CV design, uncertainty on the metric | `model-evaluation` |
| A/B test design, power, SRM, peeking, CUPED | `experiment-design` |
| Observational causal claims, DiD, IV, RDD, propensity, overlap | `causal-inference` |
| Horizon, backtesting, ETS/ARIMA/state-space, seasonality | `time-series-forecasting` |
| Priors, MCMC diagnostics, hierarchical models, posterior checks | `bayesian-modeling` |
| A mathematical argument or theorem statement | `statistical-proof-review` |
| Data integrity, joins, missingness, timestamps, duplicates | `data-quality-audit` |
| Deployment, drift, training/serving skew, monitoring, rollback | `production-ml-review` |
| Bid values, pLTV, dollar calibration, platform value signals | `adtech-value-optimization` |

Use this skill when the scope is unclear, spans several of the above, or when the framing
itself is what needs checking.

## Procedure

Work these in order. Do not skip ahead to methods; the ordering is the method.

### 1. Restate the question

Write the scientific or business question in one sentence, then write the question the
analysis actually answers in one sentence. If they differ, that gap is the headline
finding and everything below is conditional on it.

### 2. Classify the task

Assign exactly one primary class. Say which, out loud:

- **Prediction** — estimate an unknown value from information available at a decision
  point. Validity = generalization to future decisions under the same policy.
- **Estimation** — recover a population parameter. Validity = sampling frame + inference.
- **Causal** — the effect of an intervention. Validity = identification assumptions.
- **Decision/optimization** — choose an action to maximize an objective. Validity =
  the objective matching the real payoff, plus whichever of the above feeds it.

Misclassification is a `blocker`. The most common instances:
- A predictive model's coefficients interpreted as effects of intervening. (Prediction
  presented as causal.)
- A causal estimate validated by out-of-sample predictive accuracy. Predictive accuracy is
  not evidence of identification; a confounded model can predict well.
- A decision problem evaluated with a ranking metric while the decision is a threshold.
  Route to `model-evaluation` / `calibration-and-ranking`.

### 3. State the estimand or target precisely

- Prediction: target variable, its exact definition, the decision timestamp, the loss.
- Estimation: parameter and the population it describes.
- Causal: treatment, outcome, contrast (ATE/ATT/CATE/LATE), and population. A causal
  estimand without a named population is incomplete — LATE and ATT answer different
  questions.
- Decision: action set, objective in real units (dollars, hours, conversions), constraints.

If the estimand cannot be written down from the material supplied, that is the first
`blocker` and the review says so rather than guessing.

### 4. Identify the observational unit

Name the unit of a row. Then check whether it matches:
- the unit of randomization (experiments),
- the unit of clustering / correlation (repeated measures, users with many sessions),
- the unit at which the decision is made,
- the unit the business question is about.

Mismatch understates variance and inflates significance. A per-session row set analyzed as
if independent when users appear many times is a `high` finding at minimum; if it drives a
ship decision, `blocker`.

### 5. Reconstruct sampling and selection

How did rows enter the dataset? Specifically:
- What filter produced the population? Was it applied before or after the outcome?
- Who is missing entirely (not merely missing a column)?
- Was the cohort defined using anything that happens after the decision point?
- Is the data generated by a policy that itself used a model? (Endogenous training data —
  the current policy determines what outcomes were ever observed.)

Outcome-dependent cohort construction and policy-endogenous samples are `blocker`s for
causal work and `high` for predictive work deployed under a changed policy.

### 6. Surface assumptions

List each assumption with: statement, testable or untestable, evidence supplied,
consequence if violated and in which direction. Untestable assumptions are acceptable and
declared; undeclared ones are the defect.

### 7. Check information availability at decision time

For predictive work, enumerate features and ask of each: is the value knowable strictly
before the decision timestamp? Anything that is not, or cannot be shown to be, is a
leakage candidate. Hand off to `leakage-auditor` for the full availability table whenever
more than a couple of features are in question, or whenever the answer matters to a ship
decision.

### 8. Challenge the split

- Time-ordered data with a random split → `blocker`. Route to `time-series-forecasting`.
- Entities appearing in more than one split → `blocker`.
- Preprocessing (scaling, imputation, encoding, feature selection, resampling) fit before
  or across the split → `blocker`; it leaks test information into training.
- Hyperparameters tuned on the test set, or the test set consulted repeatedly → the
  reported test metric is a selection-biased optimum. Ask how many times test was touched.

### 9. Examine missingness

Which columns, what rate, and — the question usually skipped — is missingness related to
the outcome? Row-dropping under outcome-related missingness changes the population the
estimate describes. Imputation fitted on all data before splitting is leakage.

### 10. Check uncertainty quantification

Every headline number needs an interval or a stated reason it has none. Check whether the
interval accounts for the dominant source of variance (usually clustering, model
selection, or parameter uncertainty — not the sampling noise the default formula covers).
A point estimate presented without uncertainty as the basis for a decision is `high`.

### 11. Demand a baseline

Name the baseline the work must beat and ask whether it was actually run:
majority class / mean, single best feature, last value or seasonal-naive for time series,
the incumbent production system, or a simple regression. A complex model without a run
baseline has not demonstrated value — `high`, and the recommendation is to run the
baseline before tuning anything.

### 12. Separate evidence from speculation

Label every statement in the review:
- `observed` — present in the supplied artifact; quote the file:line, query, or number.
- `inferred` — follows from the supplied material by an argument you state.
- `unverifiable` — depends on information not supplied; convert to a question in §14.

Never upgrade `inferred` to `observed`. If a finding rests on an assumption about code you
have not seen, say which code would confirm it.

### 13. Recommend diagnostics

Each diagnostic must come with the decision its outcome would change. Drop any diagnostic
whose result would not change a recommendation.

### 14. State what is and is not supported

Close with the conclusions the material supports, the conclusions it does not, and the
specific questions whose answers would most change the assessment.

## Findings catalogue

| Finding | Signal | Consequence |
|---|---|---|
| Estimand undefined | Method chosen before target stated; "we want to understand X" with no contrast | All downstream validation is unanchored; reviewers cannot disagree with an unstated claim |
| Task class confusion | Coefficients from a predictive model described as effects; causal design judged by holdout accuracy | Interventions taken on associations; direction of the recommended action can be backwards |
| Unit mismatch | Rows are sessions, conclusions are about users; no cluster-robust or mixed model | Variance understated, p-values too small, false ships |
| Selection on outcome | Cohort filter references a post-decision field | Estimate describes survivors; typically optimistic and not reproducible in production |
| Availability violation | Feature sourced from a table written after the decision | Offline metric inflated; production performance collapses. Route to `leakage-auditor` |
| Split violates time | `train_test_split(shuffle=True)` on dated rows | Model interpolates within the period; horizon semantics destroyed; optimistic |
| Preprocessing before split | `scaler.fit(X)` then split; imputation or feature selection on full data | Test set information in training; optimistic by an unquantified amount |
| No baseline | Only the complex model reported | Value undemonstrated; often the baseline is within noise |
| Missing uncertainty | Single number drives a decision | Noise mistaken for signal |
| Metric/decision mismatch | Ranking metric reported, threshold decision made | Model can rank well and still be useless at the operating point. Route to `calibration-and-ranking` |
| Untested untestable assumption presented as verified | "We checked parallel trends" (pre-period only) offered as proof | Overstated confidence in an unidentified estimate. Route to `causal-inference` |
| Endogenous data | Training rows exist only for entities the current policy selected | Model learns the policy, not the phenomenon; evaluation cannot see the counterfactual |

## Output contract

Emit the standard review report (`templates/review-report.md`), sections 1–14. Use the
compact form for a small diff or single question. Mandatory in every review regardless of
form: §2 estimand/target, §4 availability at decision time (for predictive work), §12
required changes, §14 unresolved questions.

Severity per the rubric in `docs/skill-authoring-guide.md`. Every `blocker` and `high`
states the direction of bias or explicitly says the direction is undetermined.

When routing to a specialist skill, say which skill and which specific question it should
answer — do not route vaguely.

## Anti-patterns

- Recommending a model, library, or test before §2 and §3 are written down.
- Silently assuming every feature is available at scoring time.
- Calling something leakage without stating the time ordering that makes it leakage.
- Treating AUROC as evidence about calibration, or accuracy as evidence about ranking.
- Asserting a causal claim from an associational design because the effect is large.
- Marking everything `blocker` to appear thorough — it destroys the signal in the severity
  column.
- Producing a filled-in 14-section template in which no finding names a mechanism. The
  template is a container for reasoning, not a substitute for it.
- Inventing a citation, a theorem name, or a numeric result to support a point.
- Answering "looks fine" without listing what was actually checked and found sound.

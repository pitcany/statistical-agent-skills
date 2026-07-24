---
name: leakage-auditor
description: Audit ML pipelines, feature engineering, and validation splits for data leakage — target leakage, temporal leakage, post-treatment features, aggregate/group-stat leakage, CV and entity leakage, preprocessing-before-split. Use when offline metrics look too good (AUROC > 0.9 on a hard problem), when a model degrades at deployment, when reviewing feature lists or SQL feature jobs, or when anyone asks "is this feature available at prediction time?".
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Leakage Auditor

## Purpose

Determine whether any information used to train or validate a model would be
unavailable, or systematically different, at the moment the deployed model scores.
This skill protects the decision "believe the offline metric and ship" — leakage is
the single most common reason an offline number does not survive contact with
production, and its bias is almost always optimistic.

## When to use

- A feature list, feature-engineering SQL/pandas job, or training pipeline is supplied.
- Offline discrimination is suspiciously high for the problem class.
- A model performed well offline and collapsed after deployment.
- A cross-validation or train/test split design is under review.
- Someone asks whether a specific feature "leaks".

## When NOT to use

- Metric choice, baselines, or test-set discipline in general → `model-evaluation`.
- Probability calibration, reliability curves, ranking metrics → `calibration-and-ranking`.
- Whether a *causal* claim is identified (confounding, not leakage) → `causal-inference`.
- Backtest construction and lookahead in forecasting pipelines → `time-series-forecasting`.
- Join fan-out, duplicates, nulls, schema drift with no model involved → `data-quality-audit`.
- Serving skew, monitoring, retraining cadence after the model is validated → `production-ml-review`.
- Randomization and interference in experiments → `experiment-design`.
- Unsure which failure mode you are looking at → `statistical-reviewer` for triage.

## Procedure

1. **Fix the decision timestamp.** State the exact moment the deployed model scores
   (e.g. "at ad-request time", "at loan application submit"). If the material does not
   state it, emit a §14 question — every subsequent step is relative to this timestamp
   and cannot proceed on an assumed one without flagging the assumption as `inferred`.
2. **Fix the label definition and its maturity.** State when the label becomes known
   relative to the decision timestamp (e.g. conversion observed 0–30 days after click).
   Any feature computed from data written at or after label time is a candidate finding.
3. **Enumerate features.** List every model input from the supplied artifact. If the
   list is long, rank by any available importance measure and audit at least the top 15
   plus every feature whose name contains outcome-adjacent tokens
   (`*_conversion*`, `*_paid*`, `*_final*`, `*_total*`, `*_ltv*`, `*_status*`, `days_to_*`).
4. **Build the prediction-time availability table** (mandatory — see §Availability
   table). One row per audited feature. Any row whose write timestamp is not strictly
   before the decision timestamp is a blocker unless the serving path provably uses an
   as-of snapshot.
5. **Audit the split.** Check, in order: (a) split performed before or after any fitted
   preprocessing (imputation, scaling, target encoding, feature selection); (b) split
   respects time ordering if the serving task is prospective; (c) split groups by entity
   (user, account, device, hospital) when the same entity emits multiple rows;
   (d) hyperparameter tuning used a fold structure separate from the reported test set.
6. **Audit aggregates.** For every group-statistic feature (user historical CTR,
   category mean price, target encoding), verify the aggregation window ends before each
   row's decision timestamp AND was computed on training rows only. Read the actual
   `GROUP BY` / window-function code; do not accept the feature name as evidence.
7. **Audit cohort construction.** Check whether the training population was filtered on
   anything downstream of the decision (e.g. "users who completed onboarding",
   "delivered orders only"). Conditioning the cohort on a post-decision event is
   outcome-dependent selection even when no single feature leaks.
8. **Run empirical corroboration** (see §Empirical detection) on whatever artifacts
   allow it. These signals corroborate; they never substitute for step 4's time-ordering
   argument.
9. **Write findings.** Apply the validity rule below, assign severities, state
   direction of bias for every blocker/high (leakage is optimistic unless argued
   otherwise), and emit the report.

### Availability table (mandatory)

Columns, exactly:

| feature | source table/field | timestamp value is written | decision timestamp | available at serve? | evidence tier | verdict |

Worked example (loan-default model scoring at application submit):

| feature | source table/field | timestamp value is written | decision timestamp | available at serve? | evidence tier | verdict |
|---|---|---|---|---|---|---|
| `applicant_income` | `applications.income` | at application submit | application submit | yes | observed | clean |
| `days_to_first_payment` | `payments.first_pmt_dt - loans.orig_dt` | first payment, 30–60 d after origination | application submit | **no** | observed | **blocker** — written after the label window opens |
| `bureau_score` | `bureau_pull.score` | bureau pull, minutes before submit | application submit | yes | observed | clean |
| `avg_default_rate_zip` | full-table `GROUP BY zip` over all loans incl. test rows | job runs after all outcomes mature | application submit | no (uses future outcomes) | inferred | high — aggregate leakage; recompute as-of, train-only |
| `account_status` | `accounts.status` (mutable, no history table) | overwritten on every status change | application submit | unknown — current value may reflect post-decision state | unverifiable | high — needs point-in-time snapshot evidence; §14 question |

Rules for the table:
- `evidence tier` is `observed` only when the write path was read in the supplied code
  or schema; `inferred` when it follows from naming/semantics; `unverifiable` when the
  user must answer.
- A mutable field with no history table defaults to verdict `high` (unverifiable
  point-in-time correctness), never to `clean`.

### Empirical detection (corroborating signals, not proof)

Run whichever apply; report results as `observed`:

- **Implausible discrimination.** AUROC ≥ 0.95 (or near-zero error) on a task where
  the literature or the incumbent sits far lower. Signal, not proof — some tasks are easy.
- **Single-feature ablation.** Drop the suspect feature and refit. A discrimination
  collapse (e.g. AUROC 0.97 → 0.71) is strong corroboration.
- **Importance concentration.** Permutation importance or gain concentrated ≥ 50% in
  one feature, especially an outcome-adjacent name, flags that feature for a table row.
- **Suspect-feature-alone model.** A model using only the suspect feature nearly
  matching the full model localizes the leak.
- **Train/serve distribution divergence.** Compare the feature's training distribution
  against logged serving values (PSI, KS). A feature populated in training but largely
  null/default at serving indicates it is written post-decision.
- **Too-good early-stopping.** Validation loss below training loss from epoch 1
  suggests the validation fold shares leaked information.

**Proof standard:** leakage is established only by the time-ordering argument — a
statement of the form "value X is written at time T_w, the decision occurs at T_d, and
T_w ≥ T_d (or T_w is not provably < T_d)". Empirical signals without this statement
support at most a `medium` "investigate" finding.

**Validity rule:** a leakage finding that does not contain an explicit time-ordering
statement (write time vs decision time) is an invalid finding and must not be emitted.
Rewrite it with the time ordering or downgrade it to a §14 question.

## Findings catalogue

Each entry: **signal** that reveals it → **consequence** if missed. Direction of bias
is optimistic (offline metric overstates deployed performance) for all entries unless
noted.

1. **Target leakage** — a feature is a proxy for or derivative of the label.
   Signal: outcome-adjacent name; near-perfect single-feature discrimination; write
   time at/after label time. Consequence: model learns the label, not the phenomenon;
   deployed performance collapses to the leak-free ceiling.
2. **Temporal leakage** — feature computed over a window extending past the decision
   timestamp. Signal: window functions without an as-of bound; `MAX(event_ts)` per
   entity ≥ decision timestamp. Consequence: model peeks at the future; backtest
   metrics unreproducible in production.
3. **Post-treatment variables** — feature measured after an intervention the model's
   score will itself trigger. Signal: feature is causally downstream of the action
   (e.g. `discount_applied` in a model that decides discounts). Consequence: feedback
   loop; offline metric optimistic and the deployed policy distorts its own inputs.
4. **Conversion-time features at scoring time** — fields populated only when the
   positive outcome occurs (e.g. `purchase_value`, `days_to_convert`). Signal: feature
   is null/default for almost all negatives in training; null at serving for everyone.
   Consequence: missingness pattern encodes the label; serving scores degenerate.
5. **Label leakage** — the label (or a re-expression of it) enters preprocessing:
   target encoding fit on all rows, feature selection scored against the label before
   splitting, label-based outlier removal. Signal: any label-consuming transform
   executed outside the training fold. Consequence: every downstream metric optimistic;
   magnitude grows with cardinality of the encoded variable.
6. **Aggregate leakage** — group statistics (means, rates, counts) computed over the
   full dataset including test rows or future rows. Signal: `GROUP BY` over an
   unpartitioned table; aggregation job scheduled after outcome maturity. Consequence:
   each test row's features contain its own outcome's contribution; inflates
   discrimination in proportion to group sparsity (worst for small groups).
7. **Cross-validation leakage** — fold assignment ignores time or entity structure;
   tuning and reporting share folds. Signal: `KFold(shuffle=True)` on temporal or
   multi-row-per-entity data; the same split object used for both selection and the
   headline metric. Consequence: reported CV score is a biased-upward estimate of
   generalization; model selection picks the best overfit.
8. **Entity leakage** — the same user/account/device appears in both train and test.
   Signal: `nunique(entity_id)` < `n_rows` combined with a row-level random split.
   Consequence: model memorizes entities; metric measures re-identification, not
   generalization to new entities.
9. **Repeated-user leakage** — near-duplicate rows from repeated sessions/visits of
   one user straddle the split. Signal: high feature-vector duplication rate across
   the split boundary. Consequence: test set is partially a copy of train; same
   optimistic direction as entity leakage, harder to see because IDs may differ.
10. **Future-derived features** — feature built from a table version, model output, or
    lookup refreshed after the training period (e.g. embeddings trained on the full
    corpus, current-day exchange rates applied to historical rows). Signal: artifact
    creation date after the newest training label. Consequence: silent lookahead;
    backtest unreproducible.
11. **Preprocessing before splitting** — imputation, scaling, PCA, SMOTE, or feature
    selection fit on all rows then split. Signal: `fit`/`fit_transform` called before
    the split in code order; resampling applied to the full dataset. Consequence: test
    statistics contaminate training transforms; optimistic, largest for
    high-variance transforms (selection, SMOTE) and small n.
12. **Outcome-dependent cohort construction** — training population filtered on a
    post-decision event. Signal: `WHERE` clauses referencing delivery, completion,
    approval, survival. Consequence: training distribution differs from the scoring
    population; direction of bias depends on the filter — state it per case, default
    unknown-but-bounded, and pair with a distribution comparison against the serving
    population.

## Output contract

Emit `templates/review-report.md`. Mandatory specifics for this skill:

- §4 contains the full availability table (add as §7a if long).
- §7 lists every finding with its time-ordering statement; "no leakage identified"
  must enumerate what was audited (features, split, aggregates, cohort).
- §8 records the four split checks from Procedure step 5 with pass/fail each.
- §12 blockers each name: the feature or transform, write time vs decision time,
  direction of bias, and the fix (as-of join, snapshot table, refit inside fold,
  regroup split, drop feature).
- Use the compact form only for single-feature questions.

## Anti-patterns

- Declaring leakage from a feature *name* alone. The name selects a table row for
  audit; the write path decides the verdict.
- Emitting "AUROC is 0.98, therefore leakage" as a finding. High AUROC triggers the
  audit; only time ordering concludes it.
- Marking every temporal ambiguity a blocker. A mutable field without snapshot
  evidence is `high` + a §14 question, not a blocker, until the write path is known.
- Auditing only the feature list and skipping the split, aggregates, and cohort filter
  — three of the twelve catalogue entries live outside the feature list.
- Accepting "we split by time" without checking that fitted preprocessing and
  group-statistic jobs also respect that boundary.
- Presenting an `inferred` write time as `observed` because the schema "obviously"
  works that way.
- Recommending "collect more data" as a fix. Leakage is a construction defect; the fix
  is always in the pipeline, never in the sample size.

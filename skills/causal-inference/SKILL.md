---
name: causal-inference
description: Identification review for observational and quasi-experimental causal claims. Covers estimands, DAGs and adjustment sets, confounding, positivity/overlap, colliders, post-treatment bias, DiD and parallel trends, staggered TWFE, synthetic control, IV and LATE, RDD and McCrary tests, propensity matching/weighting, AIPW, E-value/Rosenbaum/Oster sensitivity. Use when a non-randomized analysis claims "effect", "impact", "lift", "drove", or "caused".
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Causal Inference Review (Observational & Quasi-Experimental)

## Purpose

Protects decisions made on causal claims that were not produced by randomization: policy
changes, budget shifts, and "X drove Y" narratives built from observational or
quasi-experimental data. The reviewer's job is to force the estimand and identification
assumptions into the open, probe each assumption with a concrete diagnostic, and — when
identification fails — downgrade the claim to the associational language it actually
supports rather than reject the analysis wholesale.

## When to use

- Any analysis of non-randomized data whose conclusion uses causal verbs: caused, drove,
  increased, reduced, impact, lift, effect of.
- Reviews of DiD, event studies, synthetic control, IV, RDD, matching, weighting, or
  regression-adjustment analyses.
- Deciding which covariates belong in an adjustment set, or whether a "controlled for"
  list constitutes identification.
- Post-treatment adjustment questions escalated from `experiment-design`.

## When NOT to use

- Randomization was performed and its integrity is the question (SRM, power, peeking,
  unit mismatch) → `experiment-design`. Come back here only for its observational
  fallbacks (broken randomization, per-protocol rescue attempts).
- Pure prediction with no causal claim → `model-evaluation`; if the claim is that a
  predictive model's features "explain" the outcome causally, stay here.
- Feature timing / target contamination in a model pipeline → `leakage-auditor`.
- Score calibration or ranking quality → `calibration-and-ranking`.
- Counterfactual forecasting mechanics (backtest design, horizon handling) →
  `time-series-forecasting`; DiD and synthetic control identification stay here.
- Priors, posterior computation, or Bayesian model criticism → `bayesian-modeling`.
- Formal derivations and proofs of estimator properties → `statistical-proof-review`.
- Source-data integrity (joins, dedup, missingness mechanics) → `data-quality-audit`.
- Serving/monitoring of an uplift or targeting model → `production-ml-review`.
- Ad-platform incrementality and value-bidding specifics → `adtech-value-optimization`.
- Unclear routing → `statistical-reviewer`.

## Procedure

1. **Write the estimand before any method talk.** One sentence containing: contrast
   (ATE / ATT / CATE / LATE), treatment definition with timing, outcome with window,
   and population. Example: "ATT of adopting feature X in month m on 90-day revenue,
   among organic adopters in 2025." If the supplied material cannot support this
   sentence, stop and put the gaps in §14 — a method applied to an unstated estimand
   cannot be reviewed, only re-derived.

2. **Consistency / well-defined intervention.** Write the intervention as an operation:
   what exactly is set, for whom, by what mechanism. Signal of failure: treatments like
   "being engaged" or "having high LTV" that no action can set, or a treatment with
   materially different versions pooled together (self-serve vs sales-assisted
   onboarding as one "onboarded" flag). Consequence: the estimate answers no
   implementable question; any decision mapped onto it inherits an unknown-direction gap.

3. **Draw the DAG and derive the adjustment set.** List causes of treatment, causes of
   outcome, and their overlap (confounders). Choose the adjustment set by the backdoor
   criterion: block every path from treatment to outcome that starts with an arrow into
   treatment; exclude mediators (on the causal path), colliders (common effects), and
   every post-treatment variable. Check the supplied covariate list against this set in
   both directions: missing confounders, and included variables that are mediators or
   colliders. "We controlled for everything we had" is a signal, not a defense — kitchen-
   sink adjustment routinely includes post-treatment variables.

4. **Selection into the sample.** State how rows entered the data. Conditioning on a
   post-treatment event (analyzing only converters, survivors, completers, non-churned)
   is collider conditioning at the sampling stage: treatment and unobserved causes of
   the selection event become dependent inside the sample. Signal: any filter clause
   whose variable is measured after treatment. Consequence: bias of unknown sign that
   no covariate adjustment repairs.

5. **Positivity / overlap.** Fit a propensity score on the adjustment set and plot its
   distribution by treatment arm. Diagnostics: regions where one arm has (near-)zero
   density; PS values outside [0.01, 0.99]; extreme weights dominating a weighted
   estimate (report max weight and effective sample size). Non-overlap means the data
   contain no counterfactual for those units; the model fills the gap by extrapolation.
   Remedies, each with its cost stated: trim to the overlap region (this **changes the
   estimand** — name the new population) or redefine the estimand up front (e.g. ATT
   where controls overlap treated). Never let trimming pass silently as a technicality.

6. **Run the design-specific checks** from the table below for whichever design is used.

7. **Propensity methods: balance is the diagnostic, not model fit.** After matching or
   weighting, compute standardized mean differences on every adjustment-set covariate;
   flag |SMD| > 0.1. The PS model's AUC/likelihood is irrelevant to bias — a
   high-AUC propensity model is a warning of poor overlap, not an achievement. Reporting
   PS model fit in place of balance tables is itself a finding.

8. **Doubly robust / AIPW.** AIPW is consistent if either the outcome model or the
   propensity model is correctly specified — not if both are wrong, and it does not
   manufacture overlap where none exists. Check that both nuisance models are fit
   honestly (cross-fitting if flexible learners are used) and that the overlap
   diagnostics from step 5 were still run.

9. **Sensitivity analysis — say precisely what each answers.**
   - **E-value**: for a risk-ratio-scale estimate, the minimum strength of association
     (RR) an unmeasured confounder would need with *both* treatment and outcome to fully
     explain away the estimate (and, separately, the CI bound). Answers "how strong must
     the missing confounder be", not "does one exist".
   - **Rosenbaum bounds**: in matched designs, the odds multiplier Γ on differential
     treatment assignment within matched sets at which the test's conclusion flips.
     Answers "how much hidden assignment bias the significance result tolerates".
   - **Oster's δ**: using coefficient and R² movement from adding observed controls, the
     ratio of selection-on-unobservables to selection-on-observables needed to drive the
     effect to zero (given a chosen R_max). Answers "how much worse than the observed
     controls would the unobserved ones have to be"; it is not a test that they aren't.
   Report the sensitivity value next to the estimate; an analysis whose conclusion dies
   at trivial confounding (e.g. E-value ≈ 1.1) is fragile even if p is small.

10. **Language gate — when causal claims are unjustified.** Causal wording is
    unsupported when any of these holds: no identification argument stated; adjustment
    set known to omit a named confounder; overlap failure left untrimmed; design-specific
    key assumption has contrary evidence (failed pre-trends, McCrary rejection, first-
    stage F near noise). Required replacement language: "is associated with", "differed
    by X between groups after adjustment for ⟨set⟩", "predicts", or an explicit bound
    ("effect between a and b under ⟨sensitivity assumption⟩"). Downgrading the language
    is a valid review outcome; specify the exact sentence to use.

11. **Emit the report**, tagging each finding `observed` / `inferred` / `unverifiable`,
    and listing in §14 the missing facts that would most change the verdict (DAG inputs,
    treatment timing, selection rules, donor pool construction).

## Design → assumption → probe → failure table

| Design | Key assumption | How to probe it | Failure implies (direction) |
|---|---|---|---|
| Regression / matching / weighting | Conditional ignorability given the adjustment set (untestable) | Negative-control outcomes and exposures; E-value / Oster δ; check set against DAG | Bias sign = sign(confounder→T) × sign(confounder→Y); e.g. healthy-user confounding is optimistic for "treatment helps" |
| Difference-in-differences | Parallel trends of *untreated potential outcomes in the post period* — untestable; pre-trends are supporting evidence only, never proof | Event-study plot of pre-period coefficients; placebo periods/outcomes; inspect for anticipation | Bias = the differential trend itself; direction = sign of counterfactual divergence (e.g. treated group already improving → optimistic) |
| TWFE with staggered adoption | Homogeneous, non-dynamic effects across cohorts (already-treated units serve as controls) | Goodman-Bacon decomposition; inspect negative weights; re-estimate with a staggered-robust estimator (e.g. Callaway–Sant'Anna, Sun–Abraham) and compare | Heterogeneous/dynamic effects give negatively weighted comparisons; estimate can attenuate or flip sign — direction unknown until decomposed |
| Synthetic control | Pre-period fit reflects the counterfactual process; donor pool untreated and unaffected by spillover | Pre-period RMSPE; in-space placebos (permute treatment across donors, rank post/pre RMSPE ratio); leave-one-out donors; backdate the treatment | Poor pre-fit or fragile donors → post-period gap is noise or spillover; direction unknown |
| Instrumental variables | Relevance; exclusion (instrument affects outcome only through treatment — untestable); monotonicity (no defiers) | First-stage F (weak below conventional thresholds; report effective F, not just F>10 folklore); argue exclusion substantively; check reduced form in never-taker-rich strata | Weak instrument biases 2SLS toward OLS (usually toward the confounded estimate); exclusion violation adds sign(instrument→Y direct) bias; and even when valid, LATE is a complier-only estimand — generalizing it to ATE is a separate, unearned claim |
| Regression discontinuity | Continuity of conditional expected potential outcomes at the cutoff | McCrary density test for running-variable manipulation; covariate continuity at cutoff; bandwidth and polynomial sensitivity; donut-RD near the cutoff | Manipulation biases toward whichever group sorts across the cutoff (direction = who benefits from sorting); estimand is local to the cutoff either way |

## Findings catalogue

| Finding | Signal | Consequence if missed | Bias direction | Typical severity |
|---|---|---|---|---|
| Causal claim with no identification argument | "Controlled for available covariates" is the entire justification | Decision made on an associational number wearing causal language | Unknown | blocker |
| Post-treatment / mediator adjustment | Covariate measured after treatment in the model (engagement, usage, downstream funnel) | Blocks part of the effect and opens collider paths | Often attenuating, but sign unreliable — treat as unknown | blocker |
| Collider conditioning via sample selection | Filter on converters / survivors / completers; "among users who stayed…" | Treatment correlated with unobservables inside the sample | Unknown | blocker |
| Overlap failure ignored | PS mass near 0/1; one arm empty in covariate regions; max IPW weight dominates | Estimate is model extrapolation presented as data | Unknown; variance also understated | blocker |
| Weak instrument | First-stage F near conventional weak thresholds; CI ignores weak-ID | 2SLS pulled toward confounded OLS; nominal CIs undercover | Toward OLS (usually optimistic for the causal story) | blocker |
| Staggered TWFE with heterogeneous effects | Staggered rollout + single TWFE coefficient; no decomposition run | Negative weights can attenuate or flip the estimate | Unknown until decomposed | high |
| Pre-trends treated as proving parallel trends | "Pre-trends flat, so parallel trends holds" | Untestable post-period assumption asserted as verified; anticipation and shocks unexamined | Unknown | high |
| RDD manipulation | McCrary density discontinuity at cutoff; covariate jumps at cutoff | Sorting mimics a treatment effect | Toward the sorting group's advantage | high |
| Balance not demonstrated | No SMD table; PS model AUC reported instead | Residual confounding on imbalanced covariates | Direction of the imbalanced confounders | high |
| LATE generalized to ATE | IV estimate quoted as "the effect" for the full population | Policy scaled to non-compliers on complier-only evidence | Unknown (compliers atypical) | high |
| Estimand silently changed by trimming | Trimmed sample, conclusions still phrased for original population | Number is right for a population nobody named | Unknown | high |
| Table-2 fallacy | Coefficients on adjustment covariates interpreted as their causal effects | Each covariate needs its own adjustment set; readings are confounded | Unknown per covariate | medium |
| Fragile sensitivity | E-value or Γ barely above 1 / δ ≪ 1, not reported | Conclusion dies at mild hidden bias; decision-maker never told | Optimistic in presentation | medium |
| Anticipation effects in DiD | Outcome moves in periods just before treatment | Effect start misdated; post-estimate contaminated | Usually attenuates the measured jump | medium |

## Output contract

Emit `templates/review-report.md`. Domain notes:
- §2 must state the contrast (ATE/ATT/CATE/LATE) and population; a LATE must name the
  complier population.
- §5 lists each identification assumption with testable/untestable status and the probe
  actually run — the design table above supplies the rows.
- Add **§5a Identification card**: design, key assumption, probe result, sensitivity
  value (E-value / Γ / δ) beside the point estimate.
- §4 (decision-time availability) and §8 (validation design) usually collapse; keep §8
  when nuisance models are ML (cross-fitting yes/no).
- If the language gate (step 10) fires, §12 must contain the exact replacement sentence.

## Anti-patterns

- Accepting a covariate list as identification. The question is never "what was
  controlled for" but "what does the DAG say must be, and must not be, controlled for".
- Adding controls until the estimate stabilizes, then reporting only the final model.
  Stability across kitchen-sink specs is not robustness if the specs share the same
  omitted confounder or the same post-treatment control.
- Declaring parallel trends "verified" from flat pre-trends. Pre-trends support; only
  the untestable post-period counterfactual identifies.
- Reporting propensity model AUC, pseudo-R², or feature importances as evidence of
  adjustment quality instead of post-adjustment balance and overlap.
- Treating doubly robust estimators as immunity: AIPW with two misspecified nuisance
  models and no overlap is a confounded estimate with smaller reported SEs.
- Running several sensitivity analyses and citing only the reassuring one.
- Rejecting every observational claim reflexively. The deliverable is a graded verdict:
  identified under stated assumptions, bounded under sensitivity, or associational —
  with the exact language the author should use.

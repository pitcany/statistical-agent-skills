---
name: experiment-design
description: Design and analysis review for randomized experiments (A/B tests). Covers randomization unit vs analysis unit, SRM, power and MDE, cluster designs and ICC, CUPED, interference/SUTVA, peeking and sequential monitoring, multiple testing, attrition, noncompliance, ITT vs CACE, novelty effects, guardrails. Use when planning a test, computing sample size, or reading out results — triggers include "A/B test", "sample ratio mismatch", "MDE", "CUPED", "peeking", "underpowered", "switchback".
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Experiment Design & Analysis Review

## Purpose

Protects two decisions: (a) whether a planned experiment can answer its question at all,
and (b) whether a completed experiment's read-out justifies the ship/no-ship call being
made on it. The dominant failure modes are variance understated by unit mismatch,
type-I inflation from peeking and metric fishing, and read-outs performed on assignment
mechanisms that were already broken (SRM).

## When to use

- Reviewing an experiment plan: randomization scheme, sample size, metric set, stop rule.
- Reviewing a read-out: "B won by 2.3%, p = 0.03, ship it."
- Debugging a suspicious result: effect flipped sign mid-test, arms have unequal counts,
  a metric moved that "shouldn't have".
- Choosing between user-level, cluster, and switchback randomization.

## When NOT to use

- No randomization happened (pre/post comparison, matched markets, "we launched and
  revenue went up") → `causal-inference`. That skill also owns the deep treatment of
  post-treatment adjustment, DiD, synthetic control, IV, and RDD.
- The experiment's metric is produced by a model and the question is whether the model's
  offline evaluation is sound → `model-evaluation`; feature/label timing → `leakage-auditor`.
- Probability calibration or ranking quality of scores used inside the experiment
  → `calibration-and-ranking`.
- Bayesian decision rules, priors, or posterior stopping criteria for a test
  → `bayesian-modeling`.
- The assignment logs or metric pipelines themselves are suspected corrupt (dupes, late
  events, join fanout) → `data-quality-audit` first; SRM here only diagnoses, it does not
  repair pipelines.
- Forecast-based counterfactuals or time-series holdouts → `time-series-forecasting`.
- Shipping the winning variant into a serving system → `production-ml-review`.
- Ad-platform lift/value bidding experiments (conversion lift, tCPA/tROAS)
  → `adtech-value-optimization`.
- Unsure which skill applies → `statistical-reviewer` for triage.

## Procedure

1. **State the estimand before touching any number.** Write: treatment contrast,
   population (all assigned? all exposed?), analysis population (ITT / per-protocol /
   CACE), primary metric with its exact definition and window, and the decision the
   result feeds. If the plan says "improve engagement" without one pre-designated primary
   metric, record that as a finding — everything downstream is exploratory.

2. **Unit audit.** Record three units: randomization, analysis, decision. If the analysis
   unit is finer than the randomization unit (randomize users, analyze pageviews;
   randomize geos, analyze users), naive standard errors treat correlated rows as
   independent and are understated. Require one of: aggregate to one row per randomized
   unit, cluster-robust SEs at the randomization unit, or a mixed model — anything else
   is a blocker.

3. **Interference / SUTVA check.** Enumerate channels through which one unit's treatment
   can touch another unit's outcome: two-sided marketplaces (shared supply), shared
   budgets or inventory, social/network features, shared infrastructure (caches, ranking
   pools). If any channel exists, unit-level randomization does not estimate the launch
   effect; require cluster randomization at the interference boundary (geo, market,
   social cluster) or switchback (time-sliced) designs, and note that switchbacks need
   washout/burn-in periods against carryover.

4. **Power and MDE.** For a two-arm test on a mean with per-arm size n and outcome
   variance σ², the minimum detectable effect at two-sided level α and power 1−β is
   `MDE = (z_{1−α/2} + z_{1−β}) · sqrt(σ²/n_T + σ²/n_C)` (equal arms:
   `(z_{1−α/2} + z_{1−β}) · sqrt(2σ²/n)`). Compute it from a pre-period variance
   estimate, then compare MDE to the smallest effect worth shipping — obtain that number
   from the owner; do not invent it. If MDE exceeds it, the experiment cannot answer the
   question: a null is uninformative and a significant result is magnitude-exaggerated
   (winner's curse). For cluster designs, inflate required sample by the design effect
   `DEFF = 1 + (m̄ − 1) · ICC` where m̄ is mean cluster size and ICC the intra-cluster
   correlation; with ICC 0.01 and clusters of 200, DEFF ≈ 3 — a tripled sample. Ignoring
   DEFF understates variance (optimistic).

5. **Variance reduction (CUPED and covariate adjustment).** CUPED uses
   `Y_adj = Y − θ(X − X̄)` with `θ = cov(Y, X)/var(X)`; variance shrinks by roughly the
   squared correlation between X and Y. Hard rule: X must be measured strictly before
   first possible exposure. Verify the covariate's computation window against the
   experiment start date. Any covariate whose window overlaps the experiment is itself an
   outcome; adjusting for it is post-treatment adjustment (step 12) and a blocker.

6. **Pre-analysis checklist** — every item answered in writing before first unblinded look:
   - [ ] One primary metric, exact definition, exposure window.
   - [ ] Guardrail metrics named, each with a threshold that halts the launch.
   - [ ] Randomization unit, analysis unit, planned SE treatment for any mismatch.
   - [ ] Planned allocation ratio and the SRM test that gates the read-out.
   - [ ] n per arm, variance source, resulting MDE, and the smallest effect worth
     shipping it is compared to.
   - [ ] Stop rule: fixed horizon, or named sequential method (alpha-spending boundary
     such as O'Brien–Fleming, or always-valid inference such as mSPRT / confidence
     sequences). "We check daily and stop when significant" is not a stop rule.
   - [ ] Multiple-testing plan across metrics × variants (correction method, or explicit
     "exploratory" labels).
   - [ ] Pre-registered subgroups, if any.
   - [ ] Exposure/trigger definition and expected compliance rate.

7. **Read-out gate — fixed order, no skipping:**
   1. **SRM check.** Chi-squared goodness-of-fit of observed assignment counts against
      the planned ratio (e.g. observed 50,912 / 49,088 vs 50/50). Gate at p < 0.001. SRM
      failure means the assignment or logging mechanism selected units differentially;
      every downstream metric compares non-exchangeable groups, so SRM invalidates the
      entire read-out — including guardrails — until the cause is found. Do not proceed
      to step 2 on "but the effect is huge".
   2. **Guardrails.** Any breached guardrail blocks the ship decision regardless of the
      primary result.
   3. **Primary metric**, with the pre-registered test and stop rule.
   4. **Secondary and exploratory metrics**, corrected or labeled per the plan.

8. **Multiple testing.** Count the actual test family: metrics × variants × segments ×
   looks. With 20 independent tests at α = 0.05 the chance of at least one false positive
   is 1 − 0.95²⁰ ≈ 64%. Require Bonferroni or Benjamini–Hochberg for confirmatory
   secondaries; results outside the plan are exploratory and cannot ship on their own.

9. **Sequential monitoring.** If results were viewed before the planned horizon, fixed-n
   p-values are invalid: each look is another draw at α. Accept only pre-specified
   alpha-spending boundaries or always-valid methods; otherwise reclassify the reported
   p-value as descriptive and the "significant" call as unsupported (optimistic).

10. **Time dynamics.** Plot the treatment effect by days-since-first-exposure and by
    exposure cohort. A decaying effect signals novelty (long-run effect overstated); an
    increasing one signals primacy/learning (understated). For switchback or crossover
    designs, check for carryover: outcome in period t correlated with treatment in
    t−1 requires washout periods or carryover terms.

11. **Attrition, noncompliance, ITT vs CACE.** Compare dropout / missing-outcome rates
    between arms (two-proportion test); differential attrition means completers are no
    longer randomized groups. Primary analysis is ITT on all assigned units. If exposure
    is partial (compliance < 100%), ITT is diluted toward zero — report the compliance
    rate alongside it. Treatment-on-treated / CACE may be estimated with randomization
    as an instrument for exposure, but it is a complier-only estimand and must be
    labeled as such; naive per-protocol (compare exposed-treatment vs all-control) breaks
    randomization and is a blocker.

12. **Post-treatment adjustment rule.** Adjusting, filtering, or segmenting on any
    variable measured after exposure (sessions, engagement, purchase funnel stage)
    conditions on an outcome and destroys the randomization guarantee — the adjusted
    comparison is observational. State the rule here; route the full collider/mediator
    analysis to `causal-inference`.

13. **Heterogeneous treatment effects.** Subgroup claims are confirmatory only if the
    subgroup was pre-registered (step 6). Post-hoc subgroup wins found by scanning are
    exploratory: the search multiplies tests (step 8) and selected effects are inflated.
    Recommend a follow-up experiment powered for the subgroup, not a targeted launch.

14. **Emit the report** per the Output contract, tagging every claim `observed`,
    `inferred`, or `unverifiable`, and putting missing deciding facts (planned ratio,
    exposure definition, smallest shippable effect) as direct questions in §14.

## Findings catalogue

| Finding | Signal | Consequence if missed | Bias direction | Typical severity |
|---|---|---|---|---|
| Unit mismatch | Analysis row count ≫ randomized-unit count; SEs computed on events/user-days when users/geos were randomized | Correlated rows treated as independent; SEs understated; false positives ship | Optimistic (overstated significance) | blocker |
| SRM | Chi-squared GOF p < 0.001 on assignment counts vs planned ratio | Differential inclusion contaminates every metric incl. guardrails | Unknown but invalidating | blocker |
| Peeking without valid stop rule | Daily dashboard + "stopped when it hit significance"; no boundary named | Type-I inflation across looks; "winner" is noise | Optimistic | blocker |
| CUPED covariate overlaps exposure | Covariate window end date ≥ experiment start date | Covariate is an outcome; adjustment biases the effect | Unknown | blocker |
| Naive per-protocol comparison | Exposed-treatment users vs all controls | Compares self-selected engagers to everyone; randomization gone | Usually optimistic | blocker |
| Post-treatment segmentation | Read-out sliced by in-experiment behavior ("among users who opened the feature") | Conditioning on outcome; observational comparison presented as experimental | Unknown | blocker |
| Underpowered vs shippable effect | Computed MDE > smallest effect worth shipping | Null misread as "no effect"; significant results exaggerated (Type-M) | Optimistic on significant results | high |
| Ignored interference | Marketplace/social/shared-budget product with user-level randomization | Control arm contaminated; e.g. cannibalization inflates treatment−control gap above launch effect | Channel-dependent; state per channel | high |
| Cluster design without DEFF | Geo/store randomization, user-level power calc, ICC never estimated | Variance understated by factor DEFF | Optimistic | high |
| Uncorrected metric family | Many metrics × variants, no correction, narrative built on whichever moved | Family-wise false positive drives the decision | Optimistic | high |
| Differential attrition | Missing-outcome rate differs between arms | Completers non-exchangeable | Unknown | high |
| Post-hoc subgroup as confirmatory | Subgroup absent from plan; found by scanning | Selection inflation; targeted launch on noise | Optimistic | high |
| Novelty effect | Effect decays across exposure days/cohorts | Long-run impact overstated at read-out horizon | Optimistic | medium |
| ITT dilution misread | Compliance ≪ 100%, ITT reported as the feature's per-user effect | Feature judged ineffective when uptake was the problem | Pessimistic | medium |
| No guardrails defined | Plan lists only success metrics | Harm ships silently alongside a primary win | Optimistic for the ship decision | medium |
| Carryover in switchback | Outcome in period t predicts prior-period treatment; no washout | Effect smeared across arms, usually attenuated | Typically pessimistic | medium |

## Output contract

Emit `templates/review-report.md`. Domain additions and expected collapses:
- §2 must name ITT / per-protocol / CACE explicitly, not just the metric.
- §3 carries the three-unit audit (randomization / analysis / decision).
- Add **§7a Read-out gate status**: SRM test statistic and p-value → guardrail states →
  primary → secondary, in that order, each marked pass / fail / not-run.
- §4 (decision-time availability) usually collapses to the CUPED pre-exposure check;
  §8 (validation design) collapses to the stop rule and look schedule.
- Compact form is acceptable for plan reviews with no data yet; it must still state the
  estimand, the MDE vs smallest-shippable-effect comparison, and §14 questions.

## Anti-patterns

- Proceeding past a failed SRM check because the effect "is too big to be an artifact".
  SRM is exactly how artifacts that big are produced.
- Reporting post-hoc power computed from the observed effect. It is a deterministic
  transform of the p-value and adds no information; the pre-registered MDE is the answer.
- Treating p > 0.05 as evidence of no effect without stating the MDE the test had.
- Adding or swapping covariates after unblinding until the primary crosses significance.
- Presenting per-protocol or exposed-only results first and ITT as a footnote.
- Declaring a winner from the best of k variants without accounting for selection over k.
- Marking every finding a blocker; if the read-out gate passes and units match, say so.

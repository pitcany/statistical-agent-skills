---
id: sound-cluster-randomized-test
skill: experiment-design
polarity: negative
tags: [experiment, cluster-randomized, CRVE, SRM, pre-registration, false-positive-resistance]
---

# Cluster-randomized menu test with clustered SEs and a passed SRM check

## Prompt

Cluster-randomized test readout for a menu redesign. I would like a design review before we
scale it to all 1,100 stores.

**Design**

- Unit of randomization: store. 120 corporate-owned stores randomized 60/60 by a seeded hash
  of `store_id`, stratified by region and by pre-period average-check quartile.
- Pre-registration (doc dated and circulated two weeks before launch): primary metric =
  average check per transaction; guardrails = food-cost margin % and complaints per 1,000
  transactions, Holm-corrected across the two guardrails; one readout, at week 4.
- Power: computed on 8 weeks of pre-period store-week data. ICC 0.11, 120 clusters, 4-week
  run → MDE 1.7% at 80% power, α = 0.05 two-sided.
- Analysis: transaction-level regression of check amount on treatment plus region and
  pre-period-quartile strata dummies; standard errors clustered at `store_id` (CR2, 120
  clusters).
- SRM: 60/60 stores as assigned; transaction counts 1.41M treatment vs 1.39M control,
  χ² p = 0.31.
- Interference: stores are at least 10 miles apart with no shared catchment; the menu change
  is in-store only, with no advertising or app surface.
- Attrition: 2 treatment stores and 1 control store closed for renovation partway through.
  All three are retained in the ITT analysis with the weeks they were open, which was
  pre-declared in the analysis plan.

**Result:** +1.8% average check (95% CI +0.6% to +3.0%). Both guardrails sit inside their
pre-declared non-inferiority margins.

Anything wrong with this before we scale it?

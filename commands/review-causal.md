---
description: Review an observational or quasi-experimental causal claim — estimand, identification assumptions, DAG, overlap, DiD/IV/RDD/propensity/doubly-robust diagnostics, and sensitivity analysis.
---

# Causal review

Target: $ARGUMENTS

## What to do

1. Invoke the `causal-inference` skill.
2. Write the estimand **before** examining the method: treatment, outcome, contrast
   (ATE / ATT / CATE / LATE), and the population it describes. A causal estimand without a
   named population is incomplete — refuse to proceed to method critique until it is stated
   or explicitly marked as missing.
3. State each identification assumption, whether it is testable, and what evidence was
   supplied. Parallel trends in the post-period and unconfoundedness are untestable; treat
   pre-trend plots and balance tables as supporting evidence, never as proof.
4. Check overlap/positivity concretely before discussing estimator choice.
5. Say explicitly whether a causal claim is justified. If it is not, supply the associational
   language that *is* supported.

## Output

Standard review report. §5 must contain the identification card: estimand, assumptions,
testability, evidence, consequence of failure with direction.

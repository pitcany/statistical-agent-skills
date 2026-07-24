---
name: statistical-proof-review
description: Verify mathematical and statistical proofs, derivations, and theorem invocations step by step. Use when reviewing a proof, lemma, derivation, asymptotic argument, convergence claim (a.s., in probability, in distribution, in Lp), CLT/LLN/Slutsky/dominated-convergence invocation, or when asked "is this proof correct" or "does this argument hold".
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: proof-review
---

# Statistical Proof Review

## Purpose

Determine whether a supplied mathematical or statistical argument actually proves what
it claims, at the level of individual implication steps. This skill protects the
decision "can this result be relied on downstream" — a plausible-looking derivation
with one unverified hypothesis is not a proof, and results built on it inherit the gap.

## When to use

- A proof, lemma, derivation, or "it can be shown that" argument is supplied for review.
- A named theorem (CLT, LLN, dominated convergence, Fubini, Slutsky, delta method,
  continuous mapping) is invoked and correctness of the invocation is in question.
- A convergence or consistency claim is made (estimator consistency, asymptotic
  normality, uniform convergence, exchange of limits).

## When NOT to use

- Whether an *empirical* analysis supports its conclusion → `statistical-reviewer`
  (hub) or the specific sibling it routes to.
- Whether model features leak future information → `leakage-auditor`.
- Design of an experiment or power analysis → `experiment-design`.
- Causal identification arguments (backdoor, IV validity) → `causal-inference`;
  route here only for the *mathematical* steps inside such an argument.
- Priors, posterior derivations reviewed for modeling adequacy rather than algebraic
  correctness → `bayesian-modeling`.
- Metric or calibration reasoning about a fitted model → `calibration-and-ranking`
  or `model-evaluation`.

## Procedure

1. **Normalize the theorem statement.** Rewrite the claim in the form
   "Under hypotheses H1…Hk, conclusion C holds." Make every quantifier explicit and
   check the ∀/∃ ordering: "for all ε there exists N" is not "there exists N for all ε".
   Check uniformity of constants: does the constant/N depend on the parameter, the
   sample point, or the function class? A constant silently promoted from
   pointwise to uniform is a gap. If the statement cannot be normalized because a term
   is undefined, stop and report that as the first finding.

2. **Extract stated assumptions.** List every hypothesis the author states, verbatim,
   each tagged `observed`.

3. **Extract hidden regularity conditions.** For each analytic operation in the proof,
   write down the condition it silently requires, tagged `inferred`:
   integrability / finite moments (which order?), finite variance, measurability of
   every function integrated or conditioned on, continuity, differentiability
   (of what order, on what set), compactness (of parameter space or unit ball),
   independence, identical distribution, positive definiteness / invertibility of any
   matrix inverted, interchange of limit and integral/expectation, interchange of
   differentiation and integration, Fubini applicability (σ-finiteness + integrability
   of |f|; Tonelli needs only nonnegativity), existence of densities, non-degeneracy
   (variance > 0), and support conditions for any division or logarithm.

4. **Verify each implication step by step.** Build the ledger (see Output contract).
   For each step, classify: derived (mechanism shown), asserted (claimed without
   derivation — mark as `gap` unless it is a standard result correctly invoked per
   step 5), or false (a concrete counterexample or algebraic error exists). "Clearly",
   "obviously", "it is easy to see", and "similarly" are assertion markers — each one
   gets its own ledger row.

5. **Audit every named-theorem invocation.** For each invoked theorem, enumerate its
   hypotheses and check each one against the context. Reference statements that must
   be applied exactly:
   - Lindeberg–Lévy CLT: iid with finite variance. Non-iid settings need
     Lindeberg/Lyapunov conditions or an explicit dependence structure (e.g. martingale
     CLT) — the author must say which and verify it.
   - Kolmogorov SLLN: iid with E|X1| < ∞ gives a.s. convergence to the mean.
     Weak LLN (Khinchin): iid with finite mean gives convergence in probability.
     Finite variance is NOT required for either iid law, but independence-without-
     identical-distribution versions need extra conditions (e.g. Kolmogorov's variance
     summability criterion for the SLLN).
   - Dominated convergence: pointwise a.e. convergence AND a single integrable
     dominating function g with |f_n| ≤ g a.e. for all n. A different bound for each n
     does not qualify. Monotone convergence needs monotonicity and nonnegativity;
     Fatou gives only an inequality and only for nonnegative integrands.
   - Slutsky: if X_n ⇒ X in distribution and Y_n → c in probability for a *constant* c,
     then X_n + Y_n ⇒ X + c, Y_n X_n ⇒ cX, and X_n / Y_n ⇒ X/c if c ≠ 0. It does NOT
     apply when Y_n converges to a non-degenerate random limit.
   - Continuous mapping: g must be continuous on a set the limit hits with
     probability 1, not everywhere-continuous by assumption.
   If any hypothesis is unverified in context, the step is `gap` even if the
   conclusion is probably true.

6. **Check modes of convergence.** Identify the mode of every convergence claim
   (a.s., in probability, in distribution, in Lp) and verify only true implications
   are used:
   - a.s. ⇒ in probability ⇒ in distribution.
   - Lp (p ≥ 1) ⇒ in probability; Lq ⇒ Lp for 1 ≤ p ≤ q on a probability space.
   - In distribution to a *constant* ⇒ in probability to that constant.
   - In probability ⇒ a.s. along a subsequence (only a subsequence).
   - NOT true: in probability ⇒ a.s.; in distribution ⇒ in probability (non-constant
     limit); a.s. ⇒ Lp (needs uniform integrability or domination); in probability
     ⇒ L1 (needs uniform integrability).
   Any step using a non-implication above is `false`, not merely a gap.

7. **Check finite- vs infinite-dimensional reasoning.** Flag any use of: compactness
   of the closed unit ball (true in finite dimensions, false in infinite-dimensional
   normed spaces), equivalence of norms, exchange of sup and limit
   (sup_n lim ≠ lim sup_n in general), and pointwise convergence used where uniform
   convergence is needed (e.g. to pass limits through integrals or to preserve
   continuity). Each such use must state the finite-dimensional or uniformity
   hypothesis that licenses it.

8. **Run counterexample search as an active procedure.** For each hypothesis Hi,
   delete it and attempt to break the conclusion. Standard probes: n = 1; zero
   variance / degenerate distribution; empty set or null event; boundary of the
   parameter space; ties / atoms in a distribution assumed continuous; singular or
   near-singular covariance; infinite or unbounded support where boundedness was
   used; heavy tails (Cauchy kills mean-based arguments; t with 2 df kills
   variance-based ones); perfectly dependent copies where independence was dropped.
   Record every counterexample found, and for hypotheses that survive probing,
   record which probes were tried.

9. **Classify the artifact.** State whether the supplied text is (a) intuition,
   (b) a proof sketch (correct skeleton, gaps flagged or flaggable), or (c) a
   complete proof. Judging a sketch by sketch standards is fine only if the author
   labels it a sketch; a sketch presented as a proof is itself a finding.

10. **Absolute rule — never fabricate.** Do not invent a theorem, citation, page
    number, or named result to close a gap. If a needed result cannot be stated
    precisely from verified knowledge, mark the step `unverifiable` and state exactly
    what must be looked up and which hypotheses must be confirmed.

## Findings catalogue

| Finding | Signal | Consequence if missed |
|---|---|---|
| Quantifier inversion | "there exists N such that for all ε" where the proof needs the reverse; N or δ used before its dependence is fixed | Claim silently strengthens from pointwise to uniform; downstream uniform bounds are unproven |
| Non-uniform constant treated as uniform | Constant C(θ) or N(x) later used as C or N with the argument dropped | Uniform convergence / uniform bound claims fail on the boundary or as θ varies |
| Unverified theorem hypothesis | Named theorem invoked with no line checking each hypothesis (e.g. CLT with variance never shown finite) | Conclusion may fail exactly in the intended application (heavy tails, dependence) |
| Illegal limit–integral interchange | lim ∫ swapped with no domination/monotonicity cited | Result can be off by the mass escaping to infinity; classic escaping-mass counterexamples apply |
| Fubini without integrability | Double integral order swapped with no check of ∫∫|f| < ∞ or nonnegativity | Iterated integrals can differ; identity used later is false |
| Mode-of-convergence upgrade | "converges in probability, hence a.s." or "in distribution, hence in probability" (non-constant limit) | The strengthened claim is false; anything requiring the stronger mode is unproven |
| Moment claim from convergence | E[X_n] → E[X] concluded from X_n → X a.s. or in probability without uniform integrability | Expectations need not converge; bias/consistency claims for estimators break |
| Slutsky misuse | Both sequences converge in distribution to non-degenerate limits, product/sum treated by Slutsky | Joint behavior is undetermined without joint convergence; limit law is unjustified |
| Division/inversion without non-degeneracy | Dividing by a variance, determinant, or probability never shown positive | Argument collapses on degenerate cases; asymptotic variance formulas invalid |
| Hidden independence | Covariance cross-terms dropped, variances added, or expectations factored with no independence hypothesis | Variance and limit distribution wrong under dependence; direction of error unknown |
| Compactness in infinite dimensions | Bolzano–Weierstrass-style subsequence extraction in a function space with no compactness argument (e.g. no tightness, no Arzelà–Ascoli hypotheses checked) | Claimed limit point need not exist; existence proofs fail |
| Asserted step | "clearly", "it follows that", "similarly" bridging a nontrivial derivation | The one wrong step in most false proofs hides here |
| Edge case exclusion | Proof implicitly assumes n ≥ 2, non-empty support, distinct values, or interior parameter | Statement as written is false; boundary applications produce wrong answers |
| Fabricated or misremembered citation | Named result whose statement cannot be reproduced precisely | Reader trusts a nonexistent guarantee; the gap propagates as fact |

## Output contract

This skill does NOT emit the standard review report; its output shape is the
per-step verification ledger below (report: proof-review).

```
## Statement (normalized)
Under: H1 ..., H2 ..., [hidden: R1 ..., R2 ...]   Conclude: C
Artifact class: intuition | proof sketch | complete proof

## Verification ledger
| step | claim | status | reason |
|------|-------|--------|--------|
| 1 | <claim as written> | verified | <mechanism / hypotheses checked> |
| 2 | <claim> | gap | <what is asserted but not derived; what would close it> |
| 3 | <claim> | false | <counterexample or algebraic error> |
| 4 | <claim> | unverifiable | <exact result to look up and hypotheses to confirm> |

## Counterexamples found
<hypothesis perturbed → construction → which conclusion fails>, or "none found;
probes tried: <list>"

## Verdict
One of: proof is complete | proof has a repairable gap (list gaps, repairs if known)
| proof is false (point to the false step and counterexample) | not assessable
(list the unverifiable steps and the exact information needed).

## Severity and confidence
Severity per severity rubric (blocker = conclusion unsupported or false; high =
named gap with plausible but unproven repair; medium = rigor debt, conclusion
survives; low/informational = presentation). Tag every ledger reason as
observed / inferred / unverifiable.
```

## Anti-patterns

- **Verdict-first reviewing.** Declaring the proof "essentially correct" and then
  sampling a few steps. The ledger covers every step or the review is incomplete.
- **Closing gaps by authority.** "This is standard" or citing a textbook result you
  cannot state precisely. State it or mark `unverifiable`.
- **Fabricating a rescue.** Inventing a lemma or reference that would fix the gap.
  Never; this is the one absolute rule.
- **Grading intuition as proof.** Rejecting a labeled sketch for missing epsilon
  management, or accepting an unlabeled sketch as a proof.
- **Counterexample theater.** Listing exotic pathologies unrelated to any hypothesis
  actually used. Every probe must target a specific Hi.
- **Mode blindness.** Writing "converges" without a mode in your own findings —
  the review must be held to the same standard as the proof.
- **Severity inflation.** Marking presentation gaps as blockers. A blocker means the
  conclusion is unsupported as stated, nothing less.

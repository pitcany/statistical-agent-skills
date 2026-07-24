---
name: bayesian-modeling
description: Review Bayesian analyses — priors and prior predictive checks, MCMC diagnostics (R-hat, ESS, divergences, funnels), hierarchical models and partial pooling, centered vs non-centered parameterization, LOO/WAIC and Pareto-k, posterior predictive checks, SBC, posterior-to-decision translation. Use when reviewing Stan/PyMC/brms/NumPyro models, MCMC output, prior choices, or posterior-based decisions.
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Bayesian Modeling Review

## Purpose

Protects decisions made from posteriors against three failure classes: posteriors that
were never actually sampled (broken MCMC reported as converged), models whose priors or
structure encode impossible worlds (never checked against simulation), and correct
posteriors translated into the wrong action (mean reported where the loss is asymmetric).
The verdict is whether the posterior is computationally trustworthy, statistically
identified, and correctly turned into the decision it feeds.

## When to use

- A Stan / PyMC / brms / NumPyro / JAGS model's output is being interpreted or shipped.
- Priors are being chosen or defended; a hierarchical/multilevel structure is proposed.
- MCMC diagnostics show warnings (divergences, R-hat, low ESS, max treedepth) or were
  never reported.
- Models are compared via LOO / WAIC / Bayes factors.
- A posterior summary is about to become an action, price, or threshold.

## When NOT to use

- Unclear which review applies, or a mixed artifact → **statistical-reviewer** (hub) triages.
- The model is Bayesian but the question is temporal backtest design, horizons, or
  forecast-interval coverage over time → **time-series-forecasting** (this skill still
  owns its MCMC and prior diagnostics).
- Whether features leak future information into training → **leakage-auditor**.
- Frequentist-style probability calibration of a classifier's scores, ranking metrics → **calibration-and-ranking**.
- Offline metric and baseline choice for model selection generally → **model-evaluation**.
- Designing the data collection / randomization → **experiment-design**.
- Whether the posterior for a coefficient is a causal effect → **causal-inference**;
  a posterior is not identification.
- Verifying a derivation, conjugacy claim, or proof → **statistical-proof-review**.
- Raw-data integrity (duplicates, impossible values) before modeling → **data-quality-audit**.
- Serving latency, retraining, monitoring of a deployed Bayesian model → **production-ml-review**.
- Bid/value optimization mechanics → **adtech-value-optimization**.

## Procedure

1. **State the estimand and the decision first.** Record what quantity the posterior is
   for (parameter, prediction, contrast), the population it describes, and the action the
   posterior feeds with its loss function. A review that starts at the sampler has skipped
   the step where most Bayesian analyses fail: computing the right posterior for the
   wrong question.

2. **Run (or demand) a prior predictive check.** Concrete step, not advice: draw
   parameters from the prior, simulate datasets through the likelihood, and compare the
   simulated data's range to physical/business plausibility (negative counts? adult
   heights of 40 m? conversion rates above 1 before the link?). Signal of failure:
   simulated outcomes routinely outside the possible range, or a "weakly informative"
   prior that puts most mass on absurd scales (e.g. Normal(0, 100) on a log-odds ⇒ prior
   probability mass piled at 0 and 1). Consequence: the prior silently dominates or
   distorts small-data inferences in a direction set by where its mass sits.

3. **Verify the computation before interpreting anything.** In order:
   - **Chains and inits:** at least 4 chains from dispersed initializations. One chain
     cannot reveal multimodality or non-mixing.
   - **R-hat:** flag any parameter with rank-normalized R-hat > 1.01. R-hat near 1 with
     few chains or short runs is necessary, not sufficient.
   - **ESS:** check bulk ESS (governs posterior means/medians) and tail ESS separately —
     tail ESS governs interval endpoints and tail probabilities, which is usually what
     the decision consumes; a model can have healthy bulk ESS and unusable 95% intervals.
     Treat ESS < ~400 total (roughly 100/chain across 4 chains) as unreliable for
     reported quantities.
   - **Divergences:** any divergence is a red flag, not noise. Geometrically it means the
     Hamiltonian integrator broke in a region of high curvature — the sampler is being
     repelled from part of the posterior, so estimates are biased away from that region
     (typically the small-variance neck of a funnel: group-level variances biased upward,
     shrinkage understated). Raising `adapt_delta` shrinks step size and sometimes hides
     the symptom; when divergences concentrate in a funnel, the fix is reparameterization
     (step 5), not tuning.
   - **Traces:** inspect trace plots for the worst-R-hat parameters; look for chains
     exploring different regions (multimodality/non-identifiability) vs slow drift
     (poor mixing).

4. **Probe identifiability.** Signals: a parameter whose posterior is visually ≈ its
   prior (overlay them — the data taught the model nothing about it); ridges or banana
   shapes in pairwise posterior plots (only a combination of parameters is identified);
   funnels between group-level scales and group effects. Consequence if missed: reported
   posterior precision for that parameter is inherited from the prior and presented as
   evidence; conclusions about it are prior-driven with the prior's direction. Additive
   or multiplicative aliasing (intercept vs group means, scale vs loading) requires a
   constraint or a reparameterized model, not more iterations.

5. **Check hierarchical structure and its parameterization.** Partial pooling is the
   correct default when units (stores, patients, campaigns) are exchangeable draws from a
   population: it buys shrinkage of noisy unit estimates toward the population mean,
   sane estimates for small groups, and an explicit between-group variance instead of the
   false dichotomy of complete pooling vs no pooling. Then apply the concrete
   parameterization rule: with few observations per group (data weakly informative about
   group effects), the *centered* form (theta ~ Normal(mu, tau)) produces a funnel —
   posterior curvature between tau and theta that HMC cannot traverse — so use
   *non-centered* (theta = mu + tau * z, z ~ Normal(0,1)). With many observations per
   group the funnel disappears and centered often mixes better. Divergences clustered at
   small tau are the deciding signal for non-centering.

6. **Run posterior predictive checks with failure-targeted statistics.** Simulate
   replicated data from the posterior and compare to observed — but choose test
   statistics that would actually expose this model's likely failure mode: proportion of
   zeros for count models, max/min and tail quantiles for outlier-sensitive models,
   group-wise means for hierarchical models, autocorrelation of residuals for sequential
   data. A PPC on the overall mean of a model fitted to that mean is guaranteed to pass
   and verifies nothing. Consequence of a skipped/weak PPC: a misspecified likelihood
   ships with confident intervals (e.g. Poisson under overdispersion → intervals too
   narrow, overconfident).

7. **Test prior sensitivity — required, not optional, when priors are informative or the
   data are weak** (few observations, separated logistic outcomes, variance components
   with few groups). Refit under at least one materially different defensible prior and
   report how the decision-relevant posterior quantity moves. If the conclusion flips,
   the report must say the data do not decide the question — the prior does — and state
   which direction each prior pushes.

8. **Audit model comparison.** LOO/WAIC estimate *predictive* performance; they cannot
   arbitrate causal structure or parameter "truth" — a confounded model can win on LOO.
   Check Pareto-k diagnostics for LOO: k > 0.7 for some observations means the importance
   sampling is unreliable there and those points' contribution needs refitting
   (moment matching or exact leave-one-out). Bayes factors are sensitive to the prior on
   the compared parameters — including regions of the prior the data never contradicts —
   so a Bayes factor reported without the priors it depends on is uninterpretable; flag
   any BF computed under default/improper priors as invalid.

9. **Translate posterior to action through the loss.** The correct action is the one
   minimizing expected loss under the posterior — the posterior mean is that action only
   under squared-error loss. Under asymmetric loss (stockout costs 10× overstock;
   under-dosing worse than over-dosing) the optimal action is a quantile or a decision
   from explicit expected-loss computation, not the mean. Signal of the defect: a report
   that presents posterior mean ± sd and lets the reader pick the action. Consequence:
   systematically biased decisions in the direction the loss asymmetry penalizes least
   often but most expensively.

10. **Check interval calibration claims.** If the workflow claims "the 90% credible
    interval contains the truth 90% of the time", require evidence: simulation-based
    calibration (simulate parameters from the prior, data from them, refit, check that
    rank statistics of the true parameter within posterior draws are uniform) validates
    the *computation* under the model. Bayesian intervals are not automatically
    frequentist-calibrated — under a misspecified model or informative prior, repeated-
    sampling coverage can be far from nominal in either direction; if the consumer needs
    frequentist coverage, it must be measured (simulation at plausible truths), not
    asserted.

11. **Emit the report** (Output contract), tagging findings `observed` / `inferred` /
    `unverifiable`, with direction of bias on every blocker/high.

### Diagnostic triage table (check in this order)

| Symptom | Likely cause | Fix |
|---|---|---|
| R-hat > 1.01 on many parameters, chains in different regions | Multimodality or non-identifiability | Find the aliasing (pairs plots); add constraints/priors that identify; do not just run longer |
| R-hat > 1.01, chains drifting slowly in same region | Poor mixing / strong posterior correlations | Reparameterize (QR for regression, non-centered for hierarchies); longer warmup second |
| Divergences clustered at small group-level scale (tau) | Funnel from centered hierarchical parameterization | Non-centered parameterization; `adapt_delta` up only for a residual handful |
| Divergences scattered, no pattern | Heavy tails or stiff curvature in likelihood | Reparameterize/rescale predictors; tighten absurd prior tails; then `adapt_delta` |
| Bulk ESS fine, tail ESS low | Sticky tail exploration | More iterations if mild; heavy-tailed reparameterization (e.g. Student-t as scale-mixture) if not |
| Max treedepth warnings, no divergences | High posterior correlation → long integration paths | Reparameterize to decorrelate (center predictors, QR); raising treedepth just pays more per iteration |
| Posterior ≈ prior for a parameter | Parameter not informed by data (non-identified or data irrelevant) | Report as prior-driven; fix design/model rather than tightening the prior to fake precision |
| PPC fails on zeros or tails | Likelihood misspecification (overdispersion, zero inflation, outliers) | Change family (negative binomial, zero-inflated, Student-t), refit, re-run PPC |
| Pareto-k > 0.7 for some points | Influential observations; LOO importance weights unstable | Moment-matched or exact refits for those points; investigate the points themselves |
| Conclusion moves under a defensible alternative prior | Data weakly informative for the decision quantity | Report prior-dependence explicitly; collect data or elicit priors formally |

## Findings catalogue

Each finding: **signal** → **consequence** → direction of bias.

- **Posterior interpreted despite failed convergence** [`blocker`]. Signal: R-hat > 1.01,
  divergences, or tail ESS below ~400 on decision-relevant quantities — or diagnostics
  absent from the report. Consequence: reported posterior is an artifact of the sampler,
  not the model. Direction: undetermined (that is the problem).
- **Single chain or shared inits** [`high`]. Signal: `chains=1` or identical seeds.
  Consequence: multimodality and non-mixing invisible; R-hat uninformative. Direction:
  optimistic about convergence.
- **No prior predictive check with non-default priors** [`high` when data are weak].
  Signal: priors stated, no simulated-data check. Consequence: prior mass on impossible
  values steers small-data posteriors. Direction: set by where the prior mass sits — must
  be stated per parameter.
- **Funnel divergences "fixed" by adapt_delta alone** [`high`]. Signal: adapt_delta ≥
  0.99, centered hierarchy, divergences reduced but nonzero. Consequence: small-tau
  region still unexplored; group-level variance biased upward, shrinkage understated.
  Direction: anti-conservative about between-group differences.
- **Prior-driven parameter presented as data-driven** [`high`]. Signal: posterior ≈ prior
  overlay; narrative cites its credible interval as evidence. Consequence: the prior's
  author, not the data, made the claim. Direction: the prior's direction.
- **LOO/WAIC used to claim causal or structural truth** [`high`]. Signal: "model A is
  correct because lower WAIC". Consequence: predictive fit laundered into a structural
  claim; confounded models can win. Direction: undetermined.
- **Ignored Pareto-k warnings** [`medium`]. Signal: k > 0.7 flagged, comparison reported
  anyway. Consequence: LOO difference and its SE unreliable. Direction: undetermined.
- **Bayes factor with default/improper or unreported priors** [`high`]. Signal: BF cited,
  priors on tested parameters unstated. Consequence: the number is a function of an
  arbitrary prior width. Direction: wider prior on the alternative → BF pushed toward the
  null (Lindley-type behavior).
- **Posterior mean used under asymmetric loss** [`high` when loss asymmetry is stated or
  obvious]. Signal: mean/MAP reported as "the" answer where costs differ by direction.
  Consequence: expected-loss-suboptimal actions, systematically toward the cheap error.
  Direction: toward the under-penalized side.
- **Credible interval sold as frequentist coverage** [`medium`, `high` if a guarantee is
  claimed downstream]. Signal: "95% CI so it covers 95% of the time" without SBC or
  coverage simulation. Consequence: consumers size risk on an unverified property.
  Direction: undetermined without simulation.
- **PPC statistic chosen to pass** [`medium`]. Signal: only the fitted mean checked.
  Consequence: misspecification in tails/zeros/dependence survives review. Direction:
  optimistic about model adequacy.
- **Complete pooling or no pooling where units are exchangeable** [`medium`]. Signal:
  per-unit independent fits with tiny groups, or one global fit despite visible
  heterogeneity. Consequence: small groups' estimates are noise (no pooling) or real
  heterogeneity erased (complete pooling). Direction: no pooling → extreme groups
  exaggerated; complete pooling → differences understated.

## Output contract

Emit `templates/review-report.md`. Domain additions: in §10 (Diagnostics), include a
**computation table** — per decision-relevant quantity: R-hat, bulk ESS, tail ESS,
divergence count, and the parameterization used; in §5 (Assumptions), list each prior
with its justification and whether sensitivity was tested. Severity per the library
rubric (`blocker`/`high`/`medium`/`low`/`informational`); every blocker/high states
mechanism and direction of bias; every claim tagged `observed`/`inferred`/`unverifiable`.
If sampler diagnostics, priors, or the loss function were not supplied, ask for them in
§14 — do not assume convergence, default priors, or squared-error loss. Use the compact
form for single-model spot checks.

## Anti-patterns

- Running more iterations to "fix" R-hat when chains sit in different modes — burns
  compute, converges to nothing; the model is unidentified.
- Tightening a prior until divergences disappear and calling it domain knowledge — that
  is using the prior as a sampler patch, and it moves the posterior in the tightened
  direction.
- Reporting the posterior of a non-identified parameter with extra decimal places —
  precision inherited from the prior is not evidence.
- Comparing LOO across models fitted to different datasets or transformed outcomes —
  the numbers are not on a common scale.
- Declaring "the data overwhelmed the prior" without the overlay or sensitivity refit
  that would show it.
- Dropping divergent transitions from the posterior sample as if they were outliers —
  they mark unexplored regions; deleting them hides the bias.
- Treating a passed SBC as evidence the model is true — SBC validates computation under
  the model's own assumptions, not the model against the world.
- Padding the report's diagnostics section with every available plot while the single
  decision-relevant quantity (tail ESS of the 95% bound the decision uses) goes unchecked.

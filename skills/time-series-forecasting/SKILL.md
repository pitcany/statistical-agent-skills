---
name: time-series-forecasting
description: Review time-series forecasts and backtests — rolling-origin evaluation, random-split leakage, ARIMA/ETS/state-space model choice, seasonality and holidays, count data and overdispersion, prediction-interval coverage, long-horizon extrapolation, seasonal-naive baselines. Use when reviewing a forecast, backtest, demand plan, ARIMA/ETS/Prophet-style model, or any train/test split on temporal data.
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Time-Series Forecasting Review

## Purpose

Protects decisions fed by forecasts (inventory, staffing, budget, capacity) from three
recurring failures: evaluation schemes that let the model see the future, model classes
mismatched to the data-generating pattern, and uncertainty statements that are too narrow
to be actionable. The output is a verdict on whether the reported forecast accuracy and
intervals would survive contact with genuinely unseen future data.

## When to use

- A train/test split, cross-validation scheme, or backtest exists on time-indexed data.
- A forecasting model (ARIMA, ETS, state-space, Prophet-style, gradient boosting on lags,
  neural) is being selected, fitted, or compared.
- Prediction intervals, safety stock, or scenario ranges are being reported.
- Someone reports forecast MAPE/RMSE/MASE and a decision depends on it.

## When NOT to use

- Uncertain which review applies, or the artifact mixes several concerns → **statistical-reviewer** (hub) triages.
- Feature-availability leakage in a general (non-forecast) supervised pipeline → **leakage-auditor**.
- Probability calibration, ranking quality, AUROC-style questions on cross-sectional data → **calibration-and-ranking**.
- Offline metric choice and baseline comparison for a non-temporal model → **model-evaluation**.
- Designing an experiment to *measure* the effect of acting on a forecast → **experiment-design**.
- "Did X cause the spike?" / intervention effects on a series → **causal-inference**.
- Priors, MCMC diagnostics, hierarchical shrinkage in a Bayesian structural model → **bayesian-modeling** (this skill still owns the backtest design).
- Missing timestamps, duplicated rows, silent unit changes in the raw series → **data-quality-audit** first.
- Serving, retraining cadence, drift monitoring for a deployed forecaster → **production-ml-review**.
- Proof or derivation checking → **statistical-proof-review**. Bid/value optimization → **adtech-value-optimization**.

## Procedure

1. **Fix the horizon and the decision before touching the model.** Record: forecast
   origin(s), horizon h (steps and calendar units), granularity, and the decision the
   forecast feeds (e.g. "order quantity placed 2 weeks ahead, weekly buckets"). A model
   selected before these are written down is unranked evidence: reject comparisons whose
   evaluation horizon differs from the decision horizon (1-step-ahead accuracy does not
   certify 13-step-ahead orders).

2. **Audit the split.** A random or shuffled train/test split on temporal data is a
   `blocker`, always: it places training points on both sides of each test point, so the
   model interpolates between neighbouring timestamps instead of extrapolating, and it
   destroys horizon semantics (every test point is effectively 0-steps-ahead). Direction:
   optimistic, often dramatically. Required design: rolling-origin (walk-forward)
   evaluation — fit through origin t, forecast t+1..t+h, advance the origin, repeat.
   Record whether the window is *expanding* (uses all history; right when the process is
   stable) or *sliding* (fixed length; right when old regimes should be forgotten), and
   that the choice was stated, not defaulted.

3. **Check feature availability at the forecast origin.** For every covariate, verify it
   is either (a) known at origin for the whole horizon (calendar, contracted prices,
   planned promotions), or (b) itself forecast — in which case its forecast error
   propagates and the backtest must use *forecast* covariate values, not realized ones.
   Backtesting with realized future covariates is leakage: signal = covariate column has
   the same timestamp as the target being predicted; consequence = optimistic accuracy
   that vanishes at deployment. Also check data vintages: if the series is revised
   (economic data, late-arriving transactions), the backtest must use the values as they
   existed at each origin, not the final revised series.

4. **Match model class to pattern.** Use the decision table below. Confirm stationarity
   handling for ARIMA (order of differencing justified by inspection/tests, not by
   whatever an auto-search picked), and note that automatic order selection over many
   candidate (p,d,q)(P,D,Q) models inflates apparent in-sample fit — the selected model's
   accuracy must be validated on rolling-origin folds *outside* the selection loop.

5. **Check trend and seasonality treatment.** Multiple seasonalities (daily + weekly +
   annual) need a model that represents them (Fourier terms, multiple seasonal
   components), not a single seasonal period. Holidays and calendar effects
   (moving-date holidays, trading days) must be explicit regressors or the residuals will
   show them. Scan for structural breaks: plot the series and rolling mean/variance; a
   level or trend shift (policy change, product launch, pandemic-era regime) fitted by a
   single global model biases both point forecasts and intervals — require changepoint
   handling, a post-break training window, or an intervention regressor.

6. **Check the outcome's distributional family.** Counts (orders, arrivals, failures)
   modeled as Gaussian produce negative and non-integer forecasts and wrong intervals at
   low volumes. For count models, test for overdispersion (variance > mean, e.g.
   dispersion statistic well above 1): under overdispersion a Poisson model understates
   interval width because it forces variance = mean. Check zero inflation: excess zeros
   relative to the fitted count distribution require a zero-inflated or hurdle model, or
   intervals and low-quantile forecasts are wrong.

7. **Audit uncertainty statements.** Confirm the report distinguishes a *prediction
   interval* (covers a future observation) from a *confidence interval* (covers a mean or
   parameter) — decisions about single future periods need the former. Flag that most
   software intervals condition on estimated parameters as if known: they ignore
   parameter uncertainty and are therefore too narrow, worst at long horizons and short
   histories. Then require an empirical check: on the rolling-origin folds, compute the
   fraction of realized values inside the nominal 80% interval, per horizon step. Values
   materially below 0.80 (e.g. 0.60) mean intervals are unusable for stock/capacity
   decisions; above (e.g. 0.95) means they are wastefully wide.

8. **Stress long-horizon behavior.** Local-linear-trend models — and any model with a
   stochastic or deterministic trend — produce forecast variance that grows with horizon
   and point paths that extrapolate the recent slope indefinitely; at long h this yields
   implausible values (negative demand, demand exceeding market size). Require a damped
   trend where long horizons matter, and explicit reality bounds (non-negativity,
   capacity/market ceilings) applied to paths and intervals. For scenario forecasting,
   check scenarios are defined as covariate paths fed through the model (what-if on
   inputs), not hand-drawn output curves, and that scenario intervals still carry the
   model's own uncertainty.

9. **Audit the backtest protocol itself.** Confirm: (a) whether the model was *retrained
   at each origin* or *frozen* — the backtest must mirror the production retraining
   cadence, and the report must say which was done; (b) preprocessing (scaling,
   imputation, Box-Cox lambda) fitted only on data before each origin; (c) the
   **seasonal-naive** forecast (value from one seasonal period ago) was run as a baseline
   on the identical folds — this is mandatory; a model that does not beat seasonal-naive
   on MASE or per-fold error has no demonstrated value regardless of its absolute MAPE.

10. **Emit the report** (Output contract), tagging every finding `observed` /
    `inferred` / `unverifiable` and every blocker/high with direction of bias.

### Decision table: pattern → model class → what it cannot do

| Data pattern / requirement | Suitable model class | What it CANNOT do |
|---|---|---|
| Noisy level, no trend/season | Local level (random walk + noise state-space); ETS(A,N,N) | No trend or seasonal structure; long-h forecast is flat at last level |
| Level + evolving trend | Local linear trend state-space; ETS(A,A,N) / damped ETS(A,Ad,N) | Undamped: variance and point path grow without bound in h; extrapolates recent slope past plausibility |
| Trend + single seasonality | ETS (A/M error, A/Ad trend, A/M season); SARIMA | ETS: no external regressors in the classical form; SARIMA: one seasonal period only |
| Multiple seasonalities, holidays | Harmonic (Fourier) regression + ARMA errors; structural/state-space with multiple seasonal components | Fixed Fourier terms assume stable seasonal shape; abrupt seasonal-pattern changes need time-varying components |
| Stationary (after differencing) autocorrelation, regressors needed | ARIMA / ARIMAX | Assumes stable dynamics; auto-selected orders overfit the search set; no natural handling of multiplicative seasonality without transformation |
| Low counts, intermittent demand | Poisson / negative-binomial state-space; Croston-type for intermittency | Gaussian intervals invalid; Poisson invalid under overdispersion; Croston gives demand-rate, not a full predictive distribution |
| Known future drivers (price, promo) | ARIMAX, regression + ARMA errors, structural models with regressors | Requires driver values over the horizon; unknown drivers must be forecast, injecting their own error |
| Structural breaks / regime shifts | Changepoint-aware fitting, intervention regressors, sliding window | Global smooth models average across regimes; breaks near the forecast origin remain hard for every class |

**ETS vs local-linear-trend (both handle trend — the real differences):** the linear
state-space (Kalman) formulation of local-linear-trend gives exact likelihood-based
uncertainty propagation, native handling of missing observations, and (in structural
form) irregular spacing, plus interpretable level/slope states and a natural place to
inject regressors or priors (Bayesian structural variants). ETS is a compact taxonomy
(Error/Trend/Season, additive or multiplicative) with built-in damped trend and direct
multiplicative-seasonality support, but classical ETS has no exogenous regressors and
needs complete, regularly spaced data. Additive ETS models have equivalent state-space
forms; multiplicative ones do not reduce to the linear-Gaussian case. Choose on these
operational needs, not on point-forecast accuracy alone.

## Findings catalogue

Each finding: **signal** (what reveals it) → **consequence** (if missed) → direction of bias.

- **Random/shuffled split on temporal data** [`blocker`]. Signal: `train_test_split`
  without ordering, shuffled indices, or CV folds not contiguous in time. Consequence:
  model interpolates between temporal neighbours; reported accuracy unattainable in
  production. Direction: optimistic.
- **Realized future covariates in the backtest** [`blocker`]. Signal: covariate values
  at t+k used when forecasting from origin t without a stated forecast for them.
  Consequence: accuracy conditional on information that will not exist. Direction: optimistic.
- **No seasonal-naive baseline** [`high`]. Signal: metrics reported with no naive/
  seasonal-naive row on the same folds. Consequence: a model worse than a free heuristic
  can ship. Direction: optimistic for the model's claimed value.
- **Selection-set overfitting in auto-ARIMA** [`high`]. Signal: model chosen by
  information criterion over a large grid, evaluated on the same span used to select.
  Consequence: apparent fit inflated by search; out-of-sample decay. Direction: optimistic.
- **Poisson intervals under overdispersion** [`high`]. Signal: count series with sample
  variance a multiple of the mean; Poisson or Gaussian intervals reported. Consequence:
  intervals too narrow, stockouts/under-capacity at the tails. Direction: optimistic
  (overconfident).
- **Intervals ignore parameter uncertainty** [`medium`, `high` if history is short].
  Signal: intervals straight from a fitted-parameters formula, no bootstrap/Bayesian
  widening, no coverage check. Consequence: nominal 80% covers less. Direction: optimistic.
- **Undamped trend at long horizon** [`high` when h is large]. Signal: linear point path
  and fan chart widening without bound; forecasts crossing zero or capacity. Consequence:
  implausible plans at the horizon that matters. Direction: undetermined for points,
  optimistic for confidence in them.
- **Backtest cadence ≠ production cadence** [`medium`]. Signal: refit-every-fold backtest
  for a model deployed frozen, or vice versa. Consequence: measured accuracy describes a
  different system than the one shipped. Direction: usually optimistic (refit backtest,
  frozen deployment).
- **Final-vintage data in backtest of a revised series** [`high`]. Signal: single
  "current" table with no as-of dimension for a series known to revise. Consequence:
  model trained/evaluated on information unavailable at origin. Direction: optimistic.
- **Holiday/calendar effects left in residuals** [`medium`]. Signal: residual spikes at
  recurring calendar dates. Consequence: predictable error treated as noise; intervals
  inflated mid-series and points wrong at holidays. Direction: unknown-but-bounded.
- **Structural break fitted by one global model** [`high` if break is recent]. Signal:
  level/trend shift visible in the plot; single model over the whole span. Consequence:
  forecasts pulled toward the defunct regime. Direction: determined by break sign.
- **80% interval covering ≠ 80% empirically** [`high`]. Signal: no per-horizon coverage
  computation on the folds, or computed coverage far from nominal. Consequence: every
  downstream buffer (safety stock, SLA) is mis-sized. Direction: as measured.

## Output contract

Emit `templates/review-report.md`. Domain additions: in §8 (Validation design), state
window type (expanding/sliding), retrain-vs-frozen, and the origin schedule; in §9,
include the seasonal-naive comparison and per-horizon-step errors; add **§9a Interval
coverage table** — nominal vs empirical coverage per horizon step. Severity per the
library rubric (`blocker`/`high`/`medium`/`low`/`informational`); every blocker/high
names mechanism and direction of bias; every claim tagged `observed`/`inferred`/
`unverifiable`. Missing deciding facts (retraining cadence, revision behavior, covariate
availability) become explicit questions in §14, never assumptions. Use the compact form
for single-question reviews.

## Anti-patterns

- Reporting average error over all horizon steps when the decision uses one specific
  step — averaging hides the decay curve the decision depends on.
- Treating a low MAPE as success without the seasonal-naive row; MAPE also explodes near
  zero values and rewards under-forecasting — pair it with MASE or scale-aware error.
- "Validated with cross-validation" where the folds shuffle time — thorough-looking, still
  a blocker.
- Widening intervals by an ad-hoc multiplier to pass a coverage check instead of fixing
  the distributional family or adding parameter uncertainty — the multiplier will not
  transfer to the next regime.
- Declaring a series "stationary after differencing" from a single test's p-value while
  the rolling variance visibly drifts — tests screen, plots decide.
- Adding a forecast covariate because it improves the backtest that used its *realized*
  values — the improvement is the leak.
- Hand-editing scenario curves after the model run and presenting them with the model's
  intervals attached.

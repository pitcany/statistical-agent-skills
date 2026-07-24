---
description: Review a forecasting or time-series model — horizon, rolling-origin evaluation, seasonality, structural breaks, interval coverage, and long-horizon extrapolation risk.
---

# Forecast review

Target: $ARGUMENTS

## What to do

1. Invoke the `time-series-forecasting` skill.
2. Establish the **horizon and the decision it feeds** before discussing model families.
   Model choice is downstream of horizon.
3. Check the evaluation design: rolling-origin (walk-forward) with the forecast origin
   respected. A random split on time-ordered data is a blocker — say why, in terms of the
   horizon semantics it destroys, not just "it's temporal data".
4. Verify feature availability at the forecast origin. A covariate that must itself be
   forecast injects its own error into the interval.
5. Check interval calibration empirically (coverage of the nominal interval across
   rolling-origin folds), and whether parameter uncertainty is included at all.
6. For horizons beyond the data's support, state the extrapolation risk in terms of the
   model's trend component, and recommend damping and reality bounds.
7. Require the seasonal-naive (or last-value) baseline to have actually been run.

## Output

Standard review report, with the horizon, origin, and baseline comparison stated up front.

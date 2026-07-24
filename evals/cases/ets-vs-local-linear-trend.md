---
id: ets-vs-local-linear-trend
skill: time-series-forecasting
polarity: positive
tags: [model-choice, horizon, uncertainty, structural-break, seasonality]
---

# ETS or local linear trend for a 13-week inventory horizon

## Prompt

DTC skincare brand. I forecast weekly net revenue to size the inventory buy. 182 weeks of
history (3.5 years). The horizon I need is 13 weeks, because that is our manufacturing plus
freight lead time — the buy I place now lands in week 13 and has to cover weeks 13–26.

What I know about the series:

- Strong annual seasonality; peak is weeks 46–51 (Black Friday through mid-December), where
  weekly revenue runs 2.5–3x the annual median.
- A level shift at week 96: we changed 3PL, and the new shipping cutoff permanently moved
  roughly 6% of revenue between adjacent weeks. Nothing else changed.
- We flag promo weeks (about 9 per year); promo weeks run 1.6–2.4x baseline. The promo
  calendar for the next quarter is already fixed and known.
- The last 40 weeks trend upward at roughly 1.1% per week.

I am choosing between `ETS(A,Ad,A)` in statsmodels and a local linear trend state-space
model with a stochastic slope. A colleague says the state-space model is "more principled",
so we should use that. AIC on the full sample slightly favours the local linear trend.

Which should I use?

---
id: selection-bias-acquired-leads-only
skill: adtech-value-optimization
polarity: positive
tags: [adtech, selection-bias, endogenous-data, off-policy, feedback-loop, suppression]
---

# Lead-quality model trained only on traffic the incumbent bidder already bought

## Prompt

Mortgage brokerage. We have 14 months of leads (240k) from our Google and Meta campaigns,
all bought under a tCPA strategy that has been running essentially unchanged the whole
time. For each lead we know whether it reached "funded loan" (5.1% overall).

Lead-quality model: gradient boosting on click/keyword/geo/device/time-of-day features plus
the lead form fields. Out-of-time holdout AUROC 0.78; top decile funds at 19%, bottom decile
at 0.6%.

Proposed rollout, starting in two weeks:

1. Suppress — send no conversion at all — for the bottom two deciles.
2. Send a conversion value proportional to `p(funded)` for everything else.
3. Use the model to expand into keyword themes and audience segments we have never bought
   before, bidding on predicted quality.

We do not log bid decisions or any randomisation — the campaigns just run and the platform
does what it does. There is no holdout traffic; every dollar is optimised.

AUROC is stable month over month and across both platforms, so I am fairly confident it
generalises. Green light?

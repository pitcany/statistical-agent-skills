---
id: delayed-conversion-outcomes
skill: adtech-value-optimization
polarity: positive
tags: [adtech, censoring, delayed-feedback, maturity, attribution-window, feedback-loop]
---

# Nightly retraining on 30 days of clicks with a 90-day conversion tail

## Prompt

Residential solar, paid search lead gen. Current pipeline:

- Nightly job pulls the last 30 days of clicks from the ads export.
- Label = `signed_contract` (1/0). Anything without a signed contract at pull time is
  labelled 0.
- XGBoost binary classifier; we upload `p(sign) * avg_contract_margin` to Google Ads as an
  offline conversion value keyed on GCLID.
- The account's click-through conversion window is 30 days.

Conversion-lag curve from the CRM, measured on clicks that are now older than 180 days:

```
day 14 :  18% of eventual signings have happened
day 30 :  37%
day 60 :  71%
day 90 :  90%
day 120:  97%
median days-to-sign: 34
```

Two things I have noticed in the 10 weeks since we turned this on:

1. The conversion rate in each night's training set keeps drifting down week over week
   (started at 4.8%, now 3.1%).
2. The average uploaded value has fallen from $71 to $44 — while the actual close rate we
   see in the CRM, measured on matured cohorts, is flat.

Is the pipeline doing something wrong, or is this just noise?

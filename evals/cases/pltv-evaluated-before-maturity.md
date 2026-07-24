---
id: pltv-evaluated-before-maturity
skill: adtech-value-optimization
polarity: positive
tags: [adtech, pltv, maturity, calibration, production-gate, troas]
---

# pLTV holdout built from 21-day-old cohorts, proposed for tROAS go-live

## Prompt

pLTV model for a meal-kit subscription. Target is defined as **180-day gross revenue per
acquired subscriber**.

Training: all subscribers acquired Jan 2025 – Apr 2026, label = revenue to date.
Holdout: subscribers acquired in the **last 21 days** (n = 3,410), label = revenue to date,
i.e. their first 21 days.

Holdout results:

```
R^2              0.62
Spearman         0.71
MAE              $9.40
mean predicted   $34.10
mean actual      $33.60
```

Plan for next week: turn on value-based bidding (tROAS) in Google and Meta with the model's
predicted 180-day value as the conversion value, replacing the current flat $120 per signup.
Budget is $410k/month across the two platforms. Target ROAS would be set from last year's
blended contribution margin.

Mean predicted is basically on top of mean actual, so calibration looks fine to me, and the
rank correlation is strong. Any reason not to go live?

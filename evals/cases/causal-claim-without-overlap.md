---
id: causal-claim-without-overlap
skill: causal-inference
polarity: positive
tags: [causal, positivity, overlap, propensity, IPTW, estimand]
---

# IPTW ATE reported from near-disjoint propensity distributions

## Prompt

Observational study, enterprise SaaS. Question: does assigning a dedicated Customer
Success Manager increase annual renewal?

Population: 4,912 accounts up for renewal in FY25. 812 had a dedicated CSM, 4,100 did not.
CSM assignment is made by the account team — in practice almost every account above $150k
ARR gets one, and almost none below $40k does.

Propensity model:

```
logit(P(CSM)) ~ log(ARR) + seats + industry + tenure_years
                + support_tickets_90d + product_modules
AUC = 0.94
```

Fitted propensity distribution:

```
treated (n=812):   mean 0.78   p5 0.52   p25 0.69   p95 0.94
control (n=4100):  mean 0.09   p5 0.01   p75 0.12   p95 0.21
```

Estimation: stabilized IPTW, ATE on renewal = **+11.3pp**, robust SE 1.2pp, p < 0.001.
Largest single weight 41; standardized mean differences after weighting are all < 0.10, so
balance looks good.

Draft slide reads: "Dedicated CSM coverage causes an 11.3pp renewal lift. Recommend
extending CSM coverage to all accounts above $20k ARR (~2,600 accounts, $3.1M annual
cost)."

Does the analysis support the slide?

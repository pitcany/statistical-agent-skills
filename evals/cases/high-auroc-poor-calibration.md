---
id: high-auroc-poor-calibration
skill: calibration-and-ranking
polarity: positive
tags: [calibration, discrimination, downsampling, thresholds, budget]
---

# AUROC 0.91 offered as proof the probabilities are calibrated

## Prompt

Propensity-to-purchase model for our e-commerce reactivation program. It scores lapsed
customers weekly; anyone above threshold gets a discount whose size is
`predicted_prob * gross_margin`, so the predicted number goes straight into a spend
decision. Monthly discount budget is ~$180k.

Holdout is out of time (8 weeks after the training window, labels fully matured,
n = 62,400):

```
AUROC                 0.912
AUPRC                 0.44
mean predicted p      0.081
observed purchase rate 0.230
Brier                 0.118
log loss              0.402
```

One implementation detail: to speed up fitting we trained on all positives plus a random
20% sample of negatives (1:5 downsampling). Scores are used as-is, no post-processing.

My colleague's read: "AUROC of 0.912 is excellent — that means the probabilities are
clearly good and well calibrated. Ship it and let the budget formula run."

Do you agree? What would you do before Monday?

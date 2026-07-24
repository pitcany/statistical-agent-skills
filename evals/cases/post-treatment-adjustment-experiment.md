---
id: post-treatment-adjustment-experiment
skill: experiment-design
polarity: positive
tags: [experiment, post-treatment, mediator, collider, ITT, CUPED]
---

# A/B readout that controls for a post-assignment engagement variable

## Prompt

A/B test readout — I need a second opinion before I send this to the PM.

Setup: new onboarding checklist shown on first login. Randomized at user level at signup,
50/50, n = 41,300 treatment / 41,120 control. SRM check passes (chi-square p = 0.42).
Pre-registered primary metric: day-7 retention. Ran 3 weeks.

Raw difference:
  control 22.6%, treatment 24.7%, diff +2.1pp (95% CI +1.5 to +2.7pp)

Our analyst then fit this, "to reduce variance and control for how engaged the user was":

```r
glm(retained_d7 ~ variant + pages_viewed_first_session + completed_profile
      + signup_channel + device,
    family = binomial, data = exp)
```

`pages_viewed_first_session` and `completed_profile` are both recorded during the first
session — i.e. after the user has already seen (or not seen) the checklist. With those in
the model, the variant coefficient falls to +0.4pp (95% CI −0.2 to +1.0pp).

The analyst's conclusion: "Once you control for engagement, the checklist effect mostly
disappears. The +2.1pp is really an engagement effect, not a product effect. Recommend we
don't ship."

Is that the right reading of the test?

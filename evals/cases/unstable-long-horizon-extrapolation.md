---
id: unstable-long-horizon-extrapolation
skill: time-series-forecasting
polarity: positive
tags: [extrapolation, horizon, uncertainty, r-squared, capacity-planning]
---

# Linear trend on 18 months extrapolated three years out

## Prompt

Physio clinic network, 11 sites. I have 18 monthly observations of new-patient bookings
(Jan 2025 – Jun 2026), rising from 1,180 to 2,090.

```r
d   <- read.csv("bookings_monthly.csv")   # month_index 1..18
fit <- lm(bookings ~ month_index, data = d)

summary(fit)$r.squared
# [1] 0.9714

coef(fit)
# (Intercept) month_index
#     1146.3        52.4

predict(fit, newdata = data.frame(month_index = 54), interval = "prediction")
#        fit      lwr      upr
# 1   3976.9   3702.1   4251.7
```

The board wants a 3-year capacity plan, so I predicted out to month 54 (mid-2029): about
3,977 new patients per month.

For reference: our 11 sites have a combined physical throughput of roughly 3,000 new
patients/month at full staffing, and hitting 3,977 would need something like 40 additional
clinicians plus two new sites. Also worth saying — most of the growth in the sample came
after we launched a corporate-partnerships channel in month 5, which is now fully rolled
out to the partners we had lined up.

R-squared is 0.97 and the prediction interval is only ±275, so this feels defensible. Is
it safe to build the capacity plan on this number?

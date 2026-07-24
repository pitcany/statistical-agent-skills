---
id: bucketing-calibrated-predictions
skill: adtech-value-optimization
polarity: positive
tags: [adtech, bucketing, calibration, skew, value-bidding, dispatched-value]
---

# Bucket midpoints dispatched instead of calibrated continuous value

## Prompt

Follow-up on our pLTV work. The continuous model is calibrated properly this time: isotonic
regression fitted on cohorts past the 180-day maturity window, calibration-in-the-large on
a held-out matured cohort is 0.98 (predicted $186 vs actual $190), decile calibration slope
1.03, and per-channel calibration is within ±6%.

Realized 180-day value on matured cohorts:

```
mean $186   median $92   p75 $214   p90 $431   p99 $1,450   max $11,200
```

Sales wants five named tiers for their reporting, so the upload job buckets:

```python
edges = np.quantile(pltv_cal, [0, .2, .4, .6, .8, 1.0])
buckets = pd.cut(pltv_cal, bins=edges,
                 labels=["T5", "T4", "T3", "T2", "T1"], include_lowest=True)

# representative value sent to Google Ads offline conversions
mid = {
    "T5": (edges[0] + edges[1]) / 2,
    "T4": (edges[1] + edges[2]) / 2,
    "T3": (edges[2] + edges[3]) / 2,
    "T2": (edges[3] + edges[4]) / 2,
    "T1": (edges[4] + min(edges[5], np.quantile(pltv_cal, .99))) / 2,
}

upload["conversion_value"] = buckets.map(mid)
```

We cap T1 at the 99th percentile so a single outlier can't blow up the bid. Campaigns run
tROAS off these values.

Is the midpoint fine as the representative value, or does it actually matter?

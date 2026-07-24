---
id: booking-form-feature-at-click-time
skill: leakage-auditor
polarity: positive
tags: [leakage, temporal, serving-skew, adtech, value-bidding]
---

# Booking-form fields used to score at click time

## Prompt

We run paid search for a hotel group. A model scores each ad click and predicts the
expected booking value; that predicted value gets uploaded to Google Ads as an offline
conversion value. Training data is the last 9 months of clicks joined to bookings.

Feature job (BigQuery), abbreviated:

```sql
CREATE OR REPLACE TABLE features.click_training AS
SELECT
  c.click_id,
  c.click_ts,
  c.campaign_id,
  c.device,
  c.geo_region,
  c.keyword_match_type,
  b.party_size,
  b.room_nights,
  b.quoted_rate,
  b.rate_plan,
  DATE_DIFF(b.checkin_date, DATE(c.click_ts), DAY) AS lead_time_days,
  u.prior_bookings_12m,
  IFNULL(b.booking_value, 0) AS label_value
FROM ads.clicks c
LEFT JOIN crm.bookings b
  ON b.click_id = c.click_id
LEFT JOIN crm.user_history u
  ON u.user_id = c.user_id AND u.as_of_date = DATE(c.click_ts)
WHERE DATE(c.click_ts) BETWEEN '2025-09-01' AND '2026-05-31';
```

`crm.bookings` rows are written when the guest completes the booking form, which is
between 4 minutes and 60 days after the click. LightGBM regression on
`log1p(label_value)`. Holdout is the last 6 weeks, out of time. Holdout Spearman 0.68;
on the binary "did it book" version of the target we get AUROC 0.93. Top features by
gain: `quoted_rate`, `room_nights`, `lead_time_days`, `prior_bookings_12m`, `party_size`.

We want to switch the campaign to value-based bidding on Monday. Anything wrong here?

---
id: sound-temporal-split
skill: leakage-auditor
polarity: negative
tags: [leakage, temporal, embargo, entity-grouping, false-positive-resistance]
---

# Out-of-time split with embargo and entity grouping

## Prompt

B2B telecom churn model. I would like a leakage review of the validation design before we
present it internally.

**Decision timestamp.** The model scores every active account at 00:00 on the 1st of each
month; the account team works the resulting list during that month.

**Label.** The account submits a cancellation within 60 days of the scoring date. Labels
are observed from the cancellations table, never imputed. Analysis date is 2026-03-01, so
every label used below has fully matured.

**Features.** Read exclusively from `account_snapshot_monthly` — an append-only table with
one row per `(account_id, as_of_date)`, written by a job that runs at 23:00 on the last day
of each month. Every aggregate in that job (90-day MRC, ticket counts, last NPS, usage
deltas, contract months remaining) is computed with an explicit `WHERE event_ts <
as_of_date` bound. No dimension tables are joined at training time; every column comes from
the snapshot row.

**Split.**

```
train   :  as_of_date in [2023-01-01, 2025-06-01]
embargo :  as_of_date in Jul, Aug, Sep 2025  -- dropped entirely
test    :  as_of_date in [2025-10-01, 2025-12-01]
```

The embargo is 3 months, longer than the 60-day label horizon, so no training row's label
window overlaps any test row's feature window.

**Tuning.** `GroupKFold(n_splits=5)` on `account_id`, inside the training period only.
Imputation, scaling and target encoding all live in a `sklearn` `Pipeline` that is fit
inside each fold. The test period was scored exactly once, after tuning was finished.

**Result.** Test AUROC 0.74, PR-AUC 0.21 against a 4.8% base rate.

Do we have a leakage problem?

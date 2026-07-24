---
description: Audit a model, feature set, or pipeline for data leakage — builds the prediction-time availability table and states the time ordering behind every finding.
---

# Leakage audit

Target: $ARGUMENTS

## What to do

1. Invoke the `leakage-auditor` skill.
2. Establish the **decision timestamp** first: the moment the model scores in production.
   Every subsequent judgement is relative to it. If it cannot be established from the
   material, ask — an availability table without a decision timestamp is meaningless.
3. Enumerate features and build the **prediction-time availability table**. One row per
   feature, including the source table/field and the timestamp at which the value is
   written.
4. Audit the split, preprocessing order, aggregate features, entity grouping, and cohort
   construction.
5. Report empirical corroboration (suspiciously high metrics, single-feature ablation,
   concentrated importance) as *supporting* signals only — the proof is the time ordering.

## Rules

- A leakage finding without an explicit time-ordering statement is invalid. State which
  value is written when, relative to the decision timestamp.
- "No leakage found" must enumerate what was audited.
- Distinguish `observed` (seen in the supplied code/schema) from `inferred` from
  `unverifiable`.

## Output

Standard review report with the full availability table as §7a, plus §12 required changes.

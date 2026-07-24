---
description: Pre-deployment and in-production ML review — training/serving skew, drift, delayed labels, versioning of model/features/calibrator, shadow and canary rollout, rollback criteria, monitoring, retraining triggers.
---

# Production ML review

Target: $ARGUMENTS

## What to do

1. Invoke the `production-ml-review` skill.
2. Run the pre-deployment gate checklist and report each item as pass / fail /
   unverifiable. Do not summarize the gate as "mostly ready" — report the items.
3. Trace the feature computation path in training and in serving separately, then compare.
   Training/serving skew is found by comparing the two code paths, not by inspecting one.
4. Check that every fitted artifact is versioned — including the calibrator, which is a
   fitted model and must roll back with the scoring model.
5. Establish label maturity and whether online evaluation respects it.
6. Require rollback criteria to be defined before launch, in measurable terms.

## Required inputs

Ask if not supplied: how features are computed at serve time, label maturity window,
current monitoring, retraining trigger, and what "roll back" concretely means here.

## Output

Standard review report plus the gate checklist. §11 (deployment implications) is mandatory.

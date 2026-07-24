---
description: Review an A/B test or randomized experiment — design or readout. Covers randomization unit, SRM, power/MDE, peeking, CUPED, interference, attrition, and post-treatment adjustment.
---

# Experiment review

Target: $ARGUMENTS

## What to do

1. Invoke the `experiment-design` skill.
2. State whether this is a **design** review (pre-launch) or a **readout** review
   (post-launch). The procedure differs and mixing them hides defects.
3. For a readout, follow the gate ordering strictly: sample-ratio mismatch → guardrails →
   primary metric → secondary metrics. A failed SRM check invalidates everything below it;
   do not report a primary-metric result past a failed SRM without saying so.
4. For a design, require the MDE be compared against the smallest effect worth shipping,
   not against whatever the available sample can detect.
5. Flag any adjustment for a variable measured after assignment — it breaks randomization.
   Route the deep treatment to `causal-inference`.

## Required inputs

Ask if not supplied: unit of randomization, unit of analysis, planned duration and whether
it was fixed in advance, number of metrics and variants examined, pre-registration status.

## Output

Standard review report, with the read-out gate results stated explicitly before any effect
estimate is discussed.

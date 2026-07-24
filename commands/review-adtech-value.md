---
description: Review a pLTV, lead-scoring, or conversion-value model whose output becomes a dollar value sent to an ad platform — dollar calibration, bucketing, maturity, endogenous data, and the mandatory production gate.
---

# AdTech value review

Target: $ARGUMENTS

## What to do

1. Invoke the `adtech-value-optimization` skill.
2. Draw the full value path first: features → model → raw score → calibrator → internal
   value → transform → dispatched value → platform objective. Name the units at each hop.
3. Build the click-time vs conversion-time table. Any conversion-time feature used at
   click-time scoring is a blocker.
4. Separate ranking evidence from dollar-calibration evidence. Value-based bidding consumes
   the magnitude; ranking metrics say nothing about it.
5. Check outcome maturity against the attribution window — they are different clocks.
6. Report the **mandatory production gate** as a four-item checklist with pass / fail /
   unverifiable, and name the fallback that stays active while any item is unmet:
   calibrator fitted on the real dollar target; evaluated out-of-time on matured labels
   with per-segment calibration; versioned as an artifact; explicitly approved by the
   spend owner.
7. State the direction of the spend error (overbid / underbid / undetermined) for every
   blocker and high finding.

## Rules

- Do not approve a dollar path on ranking metrics alone.
- Do not treat an offline replay as evidence about business outcomes; require a live
  randomized comparison and route its design to `experiment-design`.
- Payload mechanics (hashing, dedup, event schemas) belong to the `adtech-signal-engineering`
  skill, not this review.

## Output

Standard review report plus §4a (click-time vs conversion-time table) and §11a (gate
checklist).

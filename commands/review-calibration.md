---
description: Review probability quality — separates discrimination from calibration, checks reliability curves, calibration-in-the-large and slope, subgroup calibration, and calibration method choice.
---

# Calibration and ranking review

Target: $ARGUMENTS

## What to do

1. Invoke the `calibration-and-ranking` skill.
2. State which claim is actually being made — "we can rank" or "the probabilities are
   right" — and which evidence was supplied for it. These are orthogonal axes.
3. AUROC is invariant to any monotone transform of the scores and therefore can never be
   evidence about calibration. If AUROC has been offered as calibration evidence, that is
   the headline finding.
4. Compute or request: calibration-in-the-large, calibration slope, reliability curve with
   a stated binning choice, Brier score decomposition, log loss.
5. Check calibration **by subgroup**. Marginal calibration does not imply subgroup
   calibration.
6. If the prediction is transformed before use (bucketed, capped, floored), evaluate the
   dispatched value, not only the internal one.
7. Recommend a calibration method with a reason: Platt for small data and roughly sigmoidal
   distortion; isotonic for larger data and arbitrary monotone distortion (note its step
   function and overfitting risk); beta calibration when the distortion is not sigmoidal.

## Output

Standard review report with discrimination and calibration reported in separate subsections
of §9. Merging them defeats the review.

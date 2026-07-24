# Standard Review Report

Every review skill in this library emits this structure. Skills may **omit** a section
with a one-line reason ("no deployment path described"), and may add domain sections
(e.g. §7a Prediction-Time Availability Table for `leakage-auditor`). Skills may not
silently drop §2, §4, §12, or §14.

---

## 1. Objective

The scientific or business question, restated in the reviewer's own words. If the
supplied material states a different question than the analysis answers, say so here —
that mismatch is usually the most important finding in the report.

## 2. Estimand or target

State exactly one of:
- **Prediction** — target variable, decision timestamp, loss.
- **Estimation** — population parameter, population it describes.
- **Causal** — treatment, outcome, contrast (e.g. ATE / ATT / CATE / LATE), population.
- **Decision/optimization** — the action set, objective, and constraints.

Name the *task class* explicitly. Analyses that blur prediction and causal inference are
the single most common source of invalid conclusions in this domain.

## 3. Unit of analysis

The observational unit, and whether it matches the unit of randomization, the unit of
clustering, and the unit at which the decision is made. State the sampling frame and how
rows entered it (selection mechanism).

## 4. Available information at decision time

What is knowable at the moment the model scores or the decision is made. For predictive
work, this is a table; anything not provably available before the decision timestamp is
a leakage candidate. See `leakage-auditor` for the full availability table format.

## 5. Assumptions

Each assumption with: statement, whether it is **testable** or **untestable**, the
evidence supplied for it, and the consequence if it fails. Untestable assumptions are not
defects — undeclared ones are.

## 6. Main risks

Ranked list of what could make the conclusion wrong, largest first, independent of
whether a defect has been observed yet.

## 7. Leakage findings

Leakage findings with mechanism and time ordering. "No leakage identified in the supplied
material" is a valid entry; "no leakage" without saying what was inspected is not.

## 8. Validation design

Split strategy, and whether it respects time ordering, entity grouping, and the
train/serve gap. State whether preprocessing was fit inside or outside the split.

## 9. Metrics

Metrics reported vs metrics that answer §1. Separate **discrimination**, **calibration**,
and **decision value** — a metric of one is not evidence of another. Name the baseline the
model must beat, and whether that baseline was actually run.

## 10. Diagnostics

Concrete diagnostics to run, each with the specific decision it would change. A diagnostic
whose outcome changes nothing should not be recommended.

## 11. Deployment implications

Training/serving skew, monitoring, label maturity, rollback criteria, versioning of any
fitted artifact (including calibrators). Omit only when nothing ships.

## 12. Required changes (blockers and high)

Numbered, each with: severity, the defect, the mechanism, the direction of bias, and the
specific change that resolves it. This is the section a reader acts on.

## 13. Optional improvements (medium / low)

Same format, explicitly marked as not gating.

## 14. Confidence and unresolved questions

- What the review is confident about and why.
- What could not be determined from the supplied material.
- The specific questions whose answers would most change the assessment, phrased so the
  author can answer them directly.

---

## Compact form

For short reviews (a single query, a small diff), collapse to:

```
Target: <task class + estimand>            Unit: <unit>
Blockers:   <n>   High: <n>   Medium: <n>
1. [blocker] <defect> — <mechanism> — <direction of bias> — <fix>
2. [high]    ...
Verified clean: <what was checked and found sound>
Unresolved: <question 1>, <question 2>
```

Use the compact form when the full report would be mostly "not applicable". Never use it
to avoid stating the estimand or the unresolved questions.

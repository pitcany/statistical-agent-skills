---
name: adtech-value-optimization
description: Review lead-generation, conversion-optimization, and predicted-LTV modeling where a model-derived number is sent to an ad platform as a bid, conversion value, or suppression signal. Covers click-time vs conversion-time information, dollar calibration, value bucketing, tCPA vs tROAS/value optimization, delayed and censored outcomes, endogenous training data from the current acquisition policy, and platform feedback loops. Use when reviewing pLTV or lead-scoring models, offline conversion uploads, value-based bidding, or any change to the dollar value dispatched to Google/Meta/TikTok.
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# AdTech Value Optimization

## Purpose

When a model's output becomes a dollar value sent to an ad platform, statistical errors
stop being reporting errors and start moving spend. This skill reviews that path
end-to-end: what the model predicts, whether the number is calibrated in dollars, what
actually gets dispatched, and whether the platform's optimizer will do something sane with
it.

The distinctive risk here is that the ad platform will *act on* the number regardless of
whether it is right, and the resulting spend reshapes the training data. Errors are
self-reinforcing rather than self-correcting.

## When to use

- A pLTV, lead-quality, lead-scoring, or conversion-value model is being built or reviewed.
- A change is proposed to the value sent via offline conversion upload, Enhanced
  Conversions, CAPI, or a value-based bidding feed.
- Someone proposes switching between tCPA and tROAS / value optimization.
- Value bucketing, suppression, or a fallback constant is being discussed.
- Offline model metrics look good and the question is whether to turn the dollar path on.

## When NOT to use

- Payload mechanics — hashing, normalization, dedup keys, event schemas, API contracts:
  that is engineering, not this skill. (The user's `adtech-signal-engineering` skill covers
  the sending layer; this skill covers whether the *number* is right.)
- Pure calibration technique with no platform in the loop → `calibration-and-ranking`.
- Whether a lift test identified an effect → `causal-inference` or `experiment-design`.
- Feature availability mechanics in general → `leakage-auditor`.
- Deployment, drift, and monitoring in general → `production-ml-review`.

## Procedure

### 1. Draw the value path

Write the chain explicitly, one arrow per hop, before any critique:

```
raw features (available at ____) → model → raw score → calibrator (fitted on ____)
→ internal value → transform (bucket/cap/floor) → dispatched value → platform objective
```

For each hop, record what the value means in units and who consumes it. Most defects in
this domain are visible as a units change or an unlabeled transform between two hops.

### 2. Split the timeline into click time and conversion time

Build a two-column table:

| Information | Known at click/impression | Known at conversion/booking | Known at value maturity |
|---|---|---|---|

Every feature the model uses must be in the **first** column if the model scores at click
time. A feature collected on a booking or checkout form (party size, plan tier, quoted
price, sales-call notes, CRM stage) is conversion-time information. Using it to score at
click time is a `blocker`: at serving time the value does not exist, so production either
imputes a default (silently making the model a different model) or the pipeline fails.

Route to `leakage-auditor` for the full prediction-time availability table whenever more
than a handful of features are involved.

### 3. Separate acquisition from value realization

State which of these the model predicts, and do not let them merge:
- **P(lead)** — will this click become a lead?
- **P(qualified | lead)** — will the lead be real / reachable / in-market?
- **P(sale | qualified)** and **value | sale** — downstream money.
- **pLTV** — expected realized value per acquisition, which is a product/decomposition of
  the above.

A model trained on "became a lead" and dispatched as a *value* tells the platform that all
leads are worth the same. That is a `high` finding whenever lead value is dispersed: the
platform will optimize toward cheap, low-value leads and the CPL will look excellent while
revenue does not move.

### 4. Distinguish ranking quality from dollar calibration

These are different claims and require different evidence:

- **Ranking** (AUROC, top-decile lift, Spearman) supports: "we can order leads by value."
- **Dollar calibration** supports: "a lead we call \$180 is worth \$180 on average."

Value-based bidding consumes the *magnitude*. tROAS targets, budget allocation across
campaigns, and the platform's own bid computation are all functions of the level, not the
order. A model with excellent AUROC and a systematic 3× overstatement will cause the
platform to overbid uniformly — and, because the error is uniform, offline ranking
diagnostics will not show it.

Required evidence for dollar calibration, on a holdout with matured labels:
- calibration-in-the-large: mean predicted value vs mean realized value, with an interval;
- calibration slope over predicted-value deciles (regression of realized on predicted);
- reliability curve by decile of predicted value;
- the same, computed *by segment* (channel, campaign, geo, device, new vs returning).
  Marginal calibration does not imply segment calibration, and the platform allocates
  across exactly those segments.

Route the technique choice (isotonic vs Platt vs beta, shift handling) to
`calibration-and-ranking`.

### 5. Check raw vs calibrated vs dispatched

Three distinct numbers, frequently conflated:
- **raw prediction** — model output, arbitrary scale;
- **calibrated prediction** — mapped to expected dollars by a fitted calibrator;
- **dispatched value** — what leaves the system after bucketing, capping, flooring,
  currency conversion, and any margin multiplier.

Verify each transform between them is intentional and documented. Common defects: a cap
applied for "safety" that silently truncates the top decile the whole model exists to
find; a currency mismatch; a margin multiplier applied twice; a floor that makes
worthless leads look mediocre rather than worthless.

### 6. Evaluate bucketing on its own terms

Bucketing continuous values (e.g. into 5 tiers) is sometimes required by an integration
and sometimes chosen. Either way, state the cost:
- within-bucket variance is discarded — the platform cannot distinguish the top of a
  bucket from the bottom;
- boundary effects: two nearly identical leads land in different tiers;
- the bucket *representative* value matters. Using the bucket midpoint when value is
  right-skewed understates the top bucket badly; use the within-bucket **mean of realized
  value**, computed on matured data, not the midpoint;
- an unbounded top bucket must have its representative estimated, not guessed.

If bucketing is not required by the integration, dispatching the continuous calibrated
value is the default and bucketing needs a justification.

### 7. Match the platform objective to the signal quality

| Objective | What it needs | Fails when |
|---|---|---|
| tCPA / max conversions | A consistent conversion definition; value irrelevant | Lead values are dispersed — optimizes toward cheap junk |
| Value optimization / tROAS | Calibrated dollar magnitudes, adequate conversion volume per campaign | Values are ranked but not calibrated; volume too thin to learn; value variance dominated by noise |
| Suppression / negative signalling | Reliable identification of worthless leads | Suppression is confused with "low value" — see below |

**Suppression vs positive value signalling** are not interchangeable. Withholding a
conversion (or sending zero) teaches the optimizer that the click produced *nothing*, and
removes it from the learning set. Sending a small positive value teaches relative worth
and keeps it in. Choose deliberately and state which is intended; using suppression as a
proxy for "low value" throws away the ordering information the model was built to provide.

### 8. Reconcile attribution window against outcome maturity

Two different clocks, routinely conflated:
- **attribution window** — how long the platform will credit a conversion to a click;
- **outcome maturity window** — how long until the true value is realized and observed.

If value matures in 90 days and the attribution window is 30, the value uploaded at day 30
is necessarily a *prediction*, not an observation — which is the whole reason a model
exists. Say so explicitly, and evaluate the model against **matured** labels, never
against the partial value visible inside the upload window.

### 9. Handle delayed and censored outcomes correctly

Recent cohorts are censored, not zero. The standard failure: training or evaluating on the
last N days where late converters have not converted yet, which biases the model toward
fast converters and understates value.

Required checks:
- Is there a maturity cutoff, and is training restricted to cohorts past it?
- Are censored rows treated as censored (survival / delayed-feedback model, or excluded)
  rather than labeled zero?
- Is the maturity window itself estimated from data (cumulative conversion curve by days
  since click), or assumed?

Evaluating a pLTV model on immature labels is a `blocker` for a go-live decision.

### 10. Interrogate selection bias and endogenous data

Training data exists only for traffic the **current** acquisition policy bought. Outcomes
are unobserved for everything it did not buy. Consequences:
- the model is fitted on a biased slice and extrapolates off-support when the policy
  changes — which is precisely what happens when you deploy it;
- offline "improvement" can reflect better fit to the incumbent policy's footprint rather
  than better decisions;
- once dispatched values change bidding, the platform buys different traffic, which
  becomes the next training set. This feedback loop can converge to a self-confirming
  segment.

Mitigations to check for: exploration budget or randomized holdout traffic, propensity /
policy logging, geo or account-level holdouts, and monitoring of the training population's
drift after launch.

### 11. Insist on live randomized validation

Offline replay of historical auctions cannot observe what the platform *would have done*
under different values — the auction, competitors, and pacing all respond. Offline replay
is evidence about the model; it is not evidence about the business outcome.

The only sound validation of a value change is a live randomized comparison (geo split,
campaign split, or account-level split) with a pre-declared primary metric, a pre-declared
duration covering at least one full maturity window, and guardrails (spend, CPL, volume).
Route the design to `experiment-design`.

### 12. Verify the fallback path

Every dollar path needs a documented fallback: the incumbent value, a constant, or a
segment average. Check that it exists, that it is used when the model or calibrator is
unavailable, and that switching to it is a runtime decision rather than a redeploy. A
model-derived value with no fallback is an availability risk with direct spend impact.

## Mandatory production gate

**A model-derived dollar path must not become active until all of the following hold.**
Until every item passes, the documented fallback or incumbent value path stays in force.
This gate is a `blocker` by construction — a review that finds any item unmet reports it
as a blocker regardless of how good the offline metrics are.

1. A **calibration artifact** has been fitted on the **actual lead-value target** — the
   realized dollar outcome, not a proxy such as lead count, form fill, or a hand-assigned
   tier.
2. It has been **evaluated on an appropriate holdout**: out-of-time, with **matured**
   labels, reporting calibration-in-the-large, calibration slope, and per-segment
   calibration for the segments the platform allocates across.
3. It is **versioned** as an artifact in its own right — the calibrator is a fitted model,
   pinned alongside the scoring model and the feature-transform version, and rolled back
   with them.
4. It has been **explicitly approved** by the owner of the spend, with the evaluation
   evidence attached and the expected direction of spend change stated in advance.

Report the gate status as a checklist with per-item pass / fail / unverifiable, and name
the fallback that remains active while any item is unmet.

## Findings catalogue

| Finding | Signal | Consequence / direction |
|---|---|---|
| Conversion-time feature at click-time scoring | Feature sourced from booking/checkout/CRM tables; not in the click-time column | `blocker`. Offline metrics inflated; at serve the value is absent or defaulted — the deployed model differs from the evaluated one |
| Lead-count model dispatched as value | Target is binary "became a lead", output sent to a value objective | `high`. Platform optimizes to cheap leads; CPL improves while revenue does not |
| Ranking evidence offered for a dollar claim | AUROC / lift reported, no calibration-in-the-large | `blocker` for value bidding. Level error invisible to the reported diagnostics; systematic over- or under-bidding |
| Uncalibrated raw score dispatched | No calibrator in the path, or calibrator fitted on a proxy target | `blocker`. Magnitudes meaningless to the platform optimizer |
| Bucket midpoint used as representative | Midpoint on right-skewed value | `high`, understates top bucket, starves the highest-value segment of bids |
| Cap silently truncating top decile | A `min(value, X)` with no stated rationale | `high`, optimistic-for-safety but removes the model's main value |
| Evaluation on immature labels | Holdout cohorts inside the maturity window | `blocker` for go-live. Biased toward fast converters; understates value |
| Censored rows labeled zero | Recent non-converters coded 0 in training | `high`, systematically pessimistic on recent cohorts and drifts as the pipeline runs |
| Attribution window mistaken for maturity | Upload-window value used as ground truth | `high`, conflates a partial observation with the target |
| Endogenous training data unacknowledged | No exploration, no policy logging, no holdout | `high`. Off-support extrapolation exactly when the policy changes; feedback loop |
| Offline replay presented as validation | "Backtest shows +X% ROAS" with no live split | `blocker` for a spend decision. Replay cannot observe auction response |
| Suppression used as low-value proxy | Zero/withheld conversions for low tiers, no stated intent | `medium`–`high`. Discards ordering information and shrinks the learning set |
| No fallback | Model output is the only path | `high`, availability risk with direct spend impact |
| Gate unmet but path live | Any of the four gate items failing | `blocker` |

## Output contract

Emit the standard review report (`templates/review-report.md`), with two additions:

- **§4a Click-time vs conversion-time table** — the two-column timeline from step 2.
- **§11a Production gate checklist** — the four gate items with pass / fail /
  unverifiable, and the fallback that remains active.

§9 (Metrics) must report ranking and dollar-calibration evidence in separate subsections;
merging them defeats the point of the review.

Severity per the rubric in `docs/skill-authoring-guide.md`. State the direction of the
spend error (overbid / underbid / undetermined) for every `blocker` and `high`.

## Anti-patterns

- Approving a dollar path on ranking metrics alone.
- Treating high offline AUROC as readiness to bid.
- Accepting "the values are directionally right" as calibration.
- Reading the attribution window as the maturity window.
- Evaluating pLTV on cohorts that have not matured, then citing the number as a result.
- Proposing tROAS when conversion volume per campaign is too thin for the platform to
  learn, without saying so.
- Recommending suppression and positive value signalling interchangeably.
- Presenting an offline replay as evidence about business outcomes.
- Letting the production gate be waived because the model "clearly works".

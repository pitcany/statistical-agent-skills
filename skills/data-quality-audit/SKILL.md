---
name: data-quality-audit
description: Audit a dataset or pipeline for quality defects — duplicate keys, join fan-out, nulls and sentinel values (0, -1, 1970-01-01), timezone/timestamp mixups, late-arriving data, unit mismatches, label noise, drift, survivorship. Use when profiling a new table, debugging row-count inflation, validating an extract before modeling, or when "the numbers look off".
license: MIT
metadata:
  library: statistical-agent-skills
  version: "1.0.0"
  report: standard-review
---

# Data Quality Audit

## Purpose

Establish whether a dataset means what its users think it means before any model or
analysis consumes it. This skill protects the decision "is this data fit to train on,
evaluate on, or report from" — most downstream statistical defects (inflated metrics,
phantom lift, unstable models) are data defects that were cheaper to catch here.

## When to use

- First contact with a table, extract, or pipeline output destined for modeling
  or reporting.
- Row counts, sums, or rates changed unexpectedly between pipeline stages.
- A metric moved and "data issue" is a candidate explanation.
- Pre-training snapshot validation, or comparing a training snapshot to the serving
  population.

## When NOT to use

- Whether a *feature* is available at prediction time (temporal leakage) →
  `leakage-auditor`. This skill flags timestamp-semantics defects that *enable*
  leakage, then routes there.
- Whether the model's metrics and validation design are sound → `model-evaluation`.
- Probability calibration or ranking quality → `calibration-and-ranking`.
- Serving-time skew, monitoring, retraining → `production-ml-review` (this skill
  audits the data at rest; that one audits the deployed loop).
- Seasonality/stationarity of a series being *forecast* → `time-series-forecasting`.
- Unsure which review applies → `statistical-reviewer` (hub).

## Procedure

1. **Name the estimand first.** State what population the data is supposed to
   represent, at what grain, over what time window, before profiling anything.
   Every later check compares the data against this statement.

2. **Run the profile.** Compute, per table, before any interpretation:
   - total row count;
   - candidate primary key: `count(*)` vs `count(distinct key)` — any difference is
     a duplicate finding;
   - null rate per column;
   - min / max / p1 / p25 / p50 / p75 / p99 per numeric column;
   - distinct count per categorical column;
   - min and max per date/timestamp column;
   - row count by day over the full window.
   Tag every subsequent claim `observed` only if it comes from these outputs;
   claims from documentation are `inferred`; anything else is `unverifiable`.

3. **Verify schema and type contracts.** Compare declared types against observed
   values: numerics stored as strings, booleans as 0/1/NULL tristate, IDs that
   lost leading zeros, floats used for money. Check that the schema the consumer
   codes against matches the schema that actually arrives.

4. **Audit every join.** For each join in the lineage: record row count and key
   cardinality of both inputs and of the output. Output rows > left input rows on a
   supposedly many-to-one join is fan-out — find the duplicated key on the right
   side. Also check the opposite failure: inner joins silently dropping rows
   (referential integrity — count left keys with no match on the right).

5. **Probe missingness.** For each high-null column: is missingness flat across
   time, segments, and the label (closest to MCAR), or does the null rate covary
   with them (MAR/MNAR)? Concrete probe: null rate by day, by source system, and by
   outcome class. Record that a missingness *indicator* correlated with the label
   can itself be leakage (e.g. field only populated after conversion) — route that
   to `leakage-auditor`.

6. **Hunt sentinel values.** Check frequency spikes at 0, -1, 9999, empty string,
   "unknown", "N/A", and 1970-01-01 / 2038-01-19 / 1900-01-01 in timestamps. A
   sentinel that is a legal value for the column (0 revenue, -1 offset) is the
   dangerous case — compare its frequency against the plausible real rate.

7. **Check units, currency, and scale.** For each numeric measure: single unit
   throughout, or mixed (cents vs dollars, seconds vs ms, local currency vs USD)?
   Signal: bimodal distribution with modes ~100x or ~1000x apart, or a step change
   in the daily mean at a deploy date.

8. **Resolve timestamp semantics.** For every timestamp column determine which of
   event time, ingestion time, or processing time it records, and its timezone
   (stored UTC? local without offset?). Mixing these silently breaks temporal
   validity: a model split "by date" on ingestion time can train on events that
   happened after its test window. Signal: hour-of-day histogram with impossible
   troughs/spikes, or event_time > load_time rows.

9. **Check arrival dynamics.** Late-arriving and backfilled records: recompute a
   past day's aggregate today vs its value when first computed — any difference
   measures restatement. At-least-once delivery: check for duplicate event IDs and
   verify the dedup key actually identifies an event (same key, different payload =
   wrong key).

10. **Separate outliers from errors.** For extreme values: does the value have a
    physical/business interpretation (whale customer) or not (negative age,
    session length > 24h)? Errors get a correction rule; outliers get a modeling
    decision — do not delete either silently.

11. **Compare snapshot to serving population.** For each key feature compute the
    distribution in the training snapshot vs the current/serving population
    (population stability index or simple decile shift). Also check categorical
    cardinality growth over time — a categorical whose distinct count grows without
    bound will break one-hot encodings and inflate memory.

12. **Audit labels.** How was the label produced (human annotation, proxy event,
    rule)? Check: inter-annotator agreement if available, label definition changes
    over time (signal: step change in base rate at a known date), and whether a
    proxy label (click for satisfaction, chargeback for fraud) diverges from the
    target concept for identifiable segments.

13. **Look for silent selection.** Survivorship: does the extract include entities
    that later churned/delisted/were deleted, or only current survivors? Upstream
    filters: diff the extract's row count and segment mix against the source
    table's; ask the pipeline owner for every WHERE clause between source and
    extract — undocumented filters are a standing finding until enumerated.

14. **Check coverage per slice.** For every slice the analysis will report on,
    count rows and events. A slice with too few events for its intended read is
    reported now, not discovered after the analysis ships.

## Findings catalogue

Symptom → likely root cause → check to run:

| Symptom | Likely root cause | Check to run |
|---|---|---|
| Row count grows through a many-to-one join | Duplicate keys on the dimension side (fan-out) | `count(*)` and `count(distinct key)` on the right table; row counts before/after the join |
| Sums/averages inflated vs source-of-truth report | Join fan-out double-counting the measure | Recompute the sum on the pre-join table; compare |
| Null rate jumps on a specific date | Upstream schema change or new source onboarded | Null rate by day per column; align spike with deploy log |
| Spike at exactly 0 or -1 in a numeric | Sentinel default written on failure path | Frequency of the exact value vs neighbors; correlate with an error/status column |
| Cluster of timestamps at 1970-01-01 or midnight | Epoch-0 default, or date truncated to day | Count exact-epoch rows; hour-of-day histogram |
| Daily counts show a 7-day sawtooth that flips at a date | Timezone change or local-vs-UTC mix | Hour-of-day histogram split by source; compare offsets |
| Yesterday's KPI changes when recomputed today | Late-arriving events / backfill restating history | Recompute a frozen past window daily; measure delta by lag |
| Duplicate conversions / events | At-least-once delivery without dedup, or dedup key too coarse | Duplicate rate by event ID; same-ID-different-payload rate |
| Metric differs ~100x between segments | Unit or currency mix (cents/dollars, ms/s) | Distribution per source system; look for two modes at fixed ratio |
| Model degrades only on recent data | Drift between training snapshot and serving population | Per-feature snapshot-vs-current distribution comparison (e.g. PSI) |
| Encoder/feature dimension blows up over time | Categorical cardinality explosion (free-text IDs in a categorical) | Distinct count by month for each categorical |
| Base rate steps at a known date | Label definition change or annotation guideline change | Label rate by day; ask for labeling changelog |
| Historical cohort performs implausibly well | Survivorship — dead entities removed from extract | Compare cohort size at formation vs in extract; check for deletion flags |
| Extract smaller than source with no documented reason | Undocumented upstream row filter | Row count and segment mix: source vs extract; enumerate WHERE clauses |
| A reported slice has huge variance run-to-run | Insufficient events per slice | Event count per reported slice vs minimum needed for the intended read |

Consequence column, applied globally: each of these, if missed, feeds a model or a
report a population that differs from the stated estimand — inflated offline metrics
(fan-out, survivorship, leakage-adjacent timestamps: optimistic bias), broken
comparisons (units, timezones: direction unknown), or silent invalidation of the
train/test contract (late data, label changes: usually optimistic).

## Output contract

Emit `templates/review-report.md` (standard-review). Domain specifics:
- §4 (available at decision time): reduce to the timestamp-semantics table from
  step 8 — column | semantic (event/ingest/process) | timezone | evidence tier.
- Add §7a **Profile results**: the step-2 aggregates actually computed, verbatim.
  A review that skipped the profile must say so and mark every distributional
  claim `unverifiable`.
- Add §7b **Join ledger**: join | left rows | right rows | output rows |
  key-cardinality check | verdict.
- §12 severity per the rubric: a defect that changes the population or the measure
  consumed downstream (fan-out on a revenue join, survivorship in the training
  cohort) is `blocker`; a named mechanism with unquantified magnitude (MNAR
  missingness in a key feature) is `high`; robustness items are `medium`/`low`.
  Every blocker/high states bias direction or that it is undetermined.
- §14 must list the questions only the pipeline owner can answer (upstream filters,
  dedup key definition, label changelog) rather than assuming the favorable case.

## Anti-patterns

- **Profiling after concluding.** Writing findings and running the step-2 profile
  only to decorate them. The profile runs first; findings cite it.
- **"Data looks fine" without a checklist.** Clean is a claim about specific checks
  passed; name them, or the assurance is worthless.
- **Silent row surgery.** Recommending "drop nulls/outliers/dupes" without stating
  what population the survivors represent — the fix can be a worse defect than
  the finding.
- **Treating documentation as observation.** Schema docs and pipeline comments are
  `inferred` at best; only computed aggregates are `observed`.
- **One-number drift checks.** Reporting a global PSI while a single segment
  shifted violently; drift checks run per feature and per key slice.
- **Auditing the extract, blessing the pipeline.** A clean snapshot says nothing
  about arrival dynamics (steps 9, 11); say explicitly which of the two was audited.

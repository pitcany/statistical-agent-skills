# Architecture

This document explains how the library is structured and why. The binding rules for
individual skill content live in `docs/skill-authoring-guide.md`; this document covers the
system-level decisions.

## 1. Hub and spoke

The library is one hub plus eleven specialists.

- **`statistical-reviewer`** is the hub. It owns the framing steps that every review
  needs — restate the question, classify the task (prediction / estimation / causal /
  decision), pin the estimand, the unit of analysis, and the information available at
  decision time — and then routes to the specialist that owns depth in the relevant
  failure mode. It also produces a complete review of its own when the scope spans
  several specialists or when the framing itself is the defect.
- The **specialists** (`leakage-auditor`, `calibration-and-ranking`, `model-evaluation`,
  `experiment-design`, `causal-inference`, `time-series-forecasting`,
  `bayesian-modeling`, `statistical-proof-review`, `data-quality-audit`,
  `production-ml-review`, `adtech-value-optimization`) each own one reviewing job and go
  deep on it: the leakage auditor owns the prediction-time availability table, the
  experiment skill owns SRM/power/peeking, and so on.

### Why routing lives in each skill's "When NOT to use" section

There is no central router file. Instead, every skill's mandatory "When NOT to use"
section names the sibling skill that handles each excluded case (see
`skills/leakage-auditor/SKILL.md` for the pattern: seven exclusions, each with an arrow
to a named sibling).

Reasons:

1. **Routing information is only in context when it can act.** A central routing table
   would either live in a thirteenth skill (loaded only if *it* triggers) or be
   duplicated into all twelve. Putting the exits inside each skill means that whichever
   skill activates — even the wrong one — carries the map to the right one.
2. **The model picks skills from descriptions, then course-corrects from bodies.**
   Description-level triggering is approximate. A misfire is cheap if the loaded body's
   first job is to say "not mine, use X"; it is expensive if the wrong skill soldiers on.
3. **It keeps boundaries honest.** Writing the exclusion list forces each skill to state
   where its job ends. Overlapping ownership shows up immediately as two skills claiming
   the same case, which is caught at authoring time.

The hub's own "When NOT to use" is the closest thing to a global routing table (a
one-line-per-specialist map), and it earns its place because the hub is the designated
target for unscoped requests.

## 2. Coherence: the shared output contract and severity rubric

Twelve skills written as twelve independent essays would drift into twelve report shapes,
twelve notions of "critical", and no way to compare reviews. Two shared artifacts prevent
that:

- **`templates/review-report.md`** — every review skill emits the same 14-section
  structure (objective, estimand, unit, decision-time information, assumptions, risks,
  leakage, validation, metrics, diagnostics, deployment, required changes, optional
  improvements, confidence/unresolved questions). Sections that do not apply are dropped
  with a one-line reason. Skills may add domain sections (the leakage auditor adds §7a,
  the availability table) but may never silently drop §2, §4, §12, or §14. A compact form
  exists for small targets.
- **The severity rubric** (`docs/skill-authoring-guide.md` §6) — `blocker` / `high` /
  `medium` / `low` / `informational`, defined by *what the finding invalidates*, not by
  fix effort. Every `blocker` and `high` must state the direction of bias. The rubric is
  defined once and referenced by all skills, so a `blocker` from the causal skill and a
  `blocker` from the forecasting skill mean the same thing to the reader.

Both are enforced mechanically where possible: `scripts/check_skills.py` verifies that
each SKILL.md contains the required sections in the mandated order, and the eval rubric
(`docs/evaluation-methodology.md`) scores severity discipline as one of its six graded
dimensions.

## 3. Why twelve skills — not one, not thirty

The Agent Skills progressive-disclosure model has three levels with very different costs:

| Level | When loaded | Cost |
|---|---|---|
| Metadata (`name` + `description`) | Always, for every installed skill | ~100 tokens per skill, every session |
| SKILL.md body | On activation only | budgeted at ≤5000 tokens here |
| References / scripts / assets | On demand | zero until opened |

The two costs pull in opposite directions:

- **One big skill** minimizes the always-on cost (~100 tokens) but destroys the
  activation economics: every review, however narrow, would load one enormous body — and
  a body that covered leakage *and* MCMC diagnostics *and* RDD *and* bid feedback loops
  at this library's depth would blow far past the 5000-token / 500-line budget, forcing
  either shallowness or a violation of the spec's recommendation. It would also have one
  description trying to advertise a dozen unrelated trigger vocabularies, degrading
  activation precision in both directions.
- **Thirty small skills** (one per finding family: "SRM checker", "peeking detector",
  "parallel-trends checker" …) minimizes per-activation load but triples the permanent
  tax — 30 × ~100 tokens in *every* session, statistical or not — and shreds review
  coherence: a real experiment readout needs SRM, power, peeking, and multiple-testing
  checks *in one report*, which would require reliably co-activating four skills and
  merging their outputs.

Twelve is the granularity at which one skill equals one *reviewing job* — one report a
user actually asks for ("audit this for leakage", "review this experiment") — while the
permanent cost stays around 1200 tokens for the whole library. The authoring guide encodes
this as a rule: one skill = one reviewing job; if a skill needs two report shapes, it is
two skills.

## 4. Overlap with the pre-existing ECC statistics skills

This machine already has roughly 80 user-level skills from the ECC collection, including
a cluster of statistics advisors that are semantically adjacent to this library. None of
the twelve new skill *names* collide with them; exactly one *command* name collides
(`stat-review.md` — the installer moves the ECC file aside and records it in a manifest
for exact rollback; see `docs/installation.md`).

Name collisions are not the real issue, though. The real issue is *trigger* overlap: two
installed skills with adjacent descriptions can both match the same query, and the model
picks one. That is how the mechanism works; with both collections installed you should
expect that a prompt like "check this A/B test" sometimes lands on
`experiment-design-optimizer` (ECC) and sometimes on `experiment-design` (this library).

### Mapping

| This library | Adjacent ECC skill(s) | Overlap character |
|---|---|---|
| `statistical-reviewer` | `reviewer2-emulator`, `stat-assumptions-auditor` | ECC: skeptical-reviewer persona / assumptions audit. New: full estimand-first triage with the 14-section report and routing |
| `leakage-auditor` | `stat-code-smell-detector` | ECC: line-level code-smell scan (leakage among several smells). New: decision-timestamp-anchored audit with a mandatory availability table |
| `calibration-and-ranking` | `loss-function-reality-check` | ECC: metric-vs-objective alignment. New: calibration methodology in depth (reliability, slope/intercept, calibrator choice, subgroups) |
| `model-evaluation` | `loss-function-reality-check`, `estimator-target-mismatch-detector` | ECC: two targeted mismatch detectors. New: whole evaluation design — baselines, CIs, paired tests, selection-induced inflation |
| `experiment-design` | `experiment-design-optimizer`, `post-experiment-truth-extractor` | ECC splits design vs readout into two advisors. New: one skill covering both, under the report contract |
| `causal-inference` | `causal-identification-validator` | Closest pair in the two collections. ECC: identification yes/no. New: full identification review with estimand, diagnostics per design, and sensitivity analysis |
| `time-series-forecasting` | `stat-assumptions-auditor` (stationarity only) | Weak overlap; no dedicated ECC forecasting reviewer |
| `bayesian-modeling` | — | No ECC counterpart |
| `statistical-proof-review` | — | No ECC counterpart |
| `data-quality-audit` | `stat-code-smell-detector` (join inflation) | ECC covers joins as a code smell; new skill audits the dataset itself (nulls, sentinels, timezones, label noise, drift) |
| `production-ml-review` | `reproducibility-hardener` | ECC: reproducibility hardening as an action. New: pre-deployment review (skew, monitoring, rollback, versioning) |
| `adtech-value-optimization` | `adtech-signal-engineering` | Complementary, not duplicative. ECC: *builds* signal pipelines (CAPI payloads, hashing, dedup). New: *reviews* the statistical validity of the value being sent |

Also adjacent with no counterpart here: `executive-translation-layer` (ECC) turns results
into leadership language — out of scope for this library and unaffected.

### Difference in role

The two collections are different kinds of object:

- The **ECC skills** are shorter topic advisors: focused checks or improvement passes on
  one dimension (assumptions, code smells, identification, power), typically invoked
  mid-task, with free-form output.
- **This library's skills** are structured reviews: estimand-first procedure, a findings
  catalogue with mechanisms, the shared report contract, the severity rubric with
  direction-of-bias requirements, and explicit `observed`/`inferred`/`unverifiable`
  evidence tiers.

They compose rather than compete: the `stat-review` command explicitly notes that
`stat-code-smell-detector` and `stat-assumptions-auditor` can be used *in addition* when
reviewing code, not instead of the estimand-first procedure.

### De-duplication options (recommendation)

1. **Keep both (default, recommended).** The descriptions are differentiated enough that
   routine triggering is acceptable, and the ECC advisors remain useful as lightweight
   in-flight checks where a full report would be overkill. Cost: ~1100 tokens of
   always-on descriptions for the 11 adjacent ECC skills, plus occasional
   non-deterministic skill selection between adjacent pairs. When a specific review is
   wanted, invoke it explicitly (slash command or by name) rather than relying on
   auto-selection.
2. **Disable specific ECC skills via `skillOverrides`.** Your `~/.claude/settings.json`
   already uses this mechanism; the observed value `"user-invocable-only"` keeps a skill
   available on explicit invocation while removing it from automatic selection. This is
   the right tool if adjacent-pair misrouting becomes annoying in practice — the obvious
   first candidates are `causal-identification-validator` and
   `experiment-design-optimizer`, the two tightest overlaps. Non-destructive and
   reversible by deleting the entry.
3. **Uninstall the ECC statistics cluster.** Only worth it if you decide the advisor
   style is fully superseded. Removes the ambiguity and the token cost, but also removes
   the lightweight mode, and ECC updates may reintroduce the skills.

Honest caveat: as long as both collections are installed, skill selection between
adjacent pairs is a model choice, not a rule. If a review *must* come from this library,
use its slash command.

## 5. Design decisions log

| Decision | Alternative rejected | Rationale |
|---|---|---|
| Hub-and-spoke with routing in each skill's "When NOT to use" | Central router skill; routing tables duplicated everywhere | Routing info is in context exactly when a skill (right or wrong) has loaded; misfires self-correct; boundaries stay explicit (§1) |
| 12 skills, one per reviewing job | 1 monolith; ~30 micro-skills | Progressive-disclosure token economics plus report coherence (§3) |
| Shared report template + severity rubric defined once | Per-skill formats | Cross-skill comparability; mechanical checkability (§2) |
| Version in `metadata`, quoted string | Top-level `version` field | The Agent Skills spec has no top-level `version`; `check_skills.py` rejects it |
| No `allowed-tools` in any skill | Restricting tools per skill | Field is experimental with harness-dependent support; these skills need ordinary read/search tools anyway |
| Skills are pure instructions — no bundled scripts, no hooks, no network access | Executable helpers per skill | Keeps the security review trivial and the attack surface near zero (`docs/security.md`); the deterministic tooling lives in `scripts/` and `evals/`, invoked by the developer, not by skills |
| Symlink install with manifest and supersede directory | Copy install | Repo stays the single source of truth; `git pull` updates every installed skill; nothing is overwritten and everything is restorable (`docs/installation.md`) |
| Deterministic eval harness that explicitly refuses to score quality | LLM-as-judge autograding | Keyword matching cannot distinguish a correct leakage argument from a fluent wrong one; the harness catches regressions and forbidden patterns, humans grade quality (`docs/evaluation-methodology.md`) |
| Nothing vendored from third-party repos | Adapting existing skill repos | Every candidate was evaluated and rejected for cause — security findings, licensing (CC BY-NC-SA), staleness, or scope mismatch (`docs/source-attribution.md`) |
| Coexist with ECC statistics skills by default | Auto-disabling ECC skills at install | Disabling another collection's skills is a user policy decision, not an installer's; the installer touches only true name collisions and records what it moved (§4) |

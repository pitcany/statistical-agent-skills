# statistical-agent-skills

A library of twelve Agent Skills and eight slash commands for Claude Code that perform
structured statistical reviews: of analyses, models, experiments, forecasts, proofs, and
production ML systems. Every review skill follows the same estimand-first procedure,
emits the same report structure (`templates/review-report.md`), and grades findings on
the same severity rubric, so a review of a causal study and a review of a bidding model
read as output of one system.

All skill text is original work; no third-party material was vendored
(see `docs/source-attribution.md`). Licensed MIT.

## Skills

| Skill | What it reviews | When it triggers |
|---|---|---|
| `statistical-reviewer` | Any quantitative work — establishes estimand, unit, and decision-time information, then routes to a specialist | "review my analysis", "is this result trustworthy", "why is my AUC so high", unscoped critique requests |
| `leakage-auditor` | Feature sets, pipelines, and splits for data leakage; builds a prediction-time availability table | Suspiciously good offline metrics, deployment collapse, "is this feature available at prediction time?" |
| `calibration-and-ranking` | Probability quality vs discrimination; reliability curves, isotonic/Platt, ranking metrics | AUROC vs calibration confusion, thresholding on raw scores |
| `model-evaluation` | Metric choice, baselines, CV design, uncertainty on the metric | "which metric should I use", missing baseline, test-set discipline |
| `experiment-design` | A/B test design and readouts — power, randomization unit, SRM, peeking, CUPED | Planning or interpreting an experiment |
| `causal-inference` | Observational causal claims — DiD, IV, RDD, propensity, overlap, identification | "did X cause Y" without randomization |
| `time-series-forecasting` | Forecast pipelines — horizon, backtesting, lookahead, seasonality, baselines | Backtest construction, ETS/ARIMA/state-space model review |
| `bayesian-modeling` | Priors, MCMC diagnostics, hierarchical structure, posterior checks | Divergences, prior choice, posterior interpretation |
| `statistical-proof-review` | Mathematical arguments and theorem statements | Checking a derivation or proof step by step |
| `data-quality-audit` | Data integrity before modeling — joins, duplicates, missingness, timestamps | Fan-out suspicion, row-count drift, schema questions |
| `production-ml-review` | Deployment readiness — training/serving skew, drift, monitoring, rollback | Pre-ship review of a model going to production |
| `adtech-value-optimization` | Value signals sent to ad platforms — pLTV, dollar calibration, bucketing, bid feedback loops | tCPA/tROAS value models, conversion-value pipelines |

`statistical-reviewer` is the hub: it triages and routes; the other eleven own depth in
their area. Each skill's "When NOT to use" section names the sibling that handles the
excluded case. Design rationale: `docs/architecture.md`.

## Commands

| Command | Invokes |
|---|---|
| `/stat-review [target]` | `statistical-reviewer` — full review of a path, PR, or the working diff |
| `/audit-leakage [target]` | `leakage-auditor` — availability table plus split audit |
| `/review-experiment [target]` | `experiment-design` |
| `/review-causal [target]` | `causal-inference` |
| `/review-forecast [target]` | `time-series-forecasting` |
| `/review-calibration [target]` | `calibration-and-ranking` |
| `/review-production-ml [target]` | `production-ml-review` |
| `/review-adtech-value [target]` | `adtech-value-optimization` |

## Install

The git repository is the source of truth. The installer symlinks skills into
`~/.claude/skills/` and commands into `~/.claude/commands/`; it never overwrites a real
file (pre-existing entries are moved aside and recorded in a manifest for exact rollback).

```bash
# preview — prints every action, changes nothing
./scripts/install.sh --dry-run

# install to ~/.claude (user level)
./scripts/install.sh

# project-level instead
./scripts/install.sh --target .claude

# skills only, no slash commands
./scripts/install.sh --skills-only
```

Note for this machine: a pre-existing `stat-review.md` command (from the ECC collection)
collides with this library's command of the same name. The installer moves it to
`~/.claude/_superseded-statskills/<timestamp>/` and records it in the manifest;
`scripts/uninstall.sh --manifest <path>` restores it exactly. Details and full rollback
procedure: `docs/installation.md`.

### Verify

```bash
# symlinks resolve into this repo
ls -l ~/.claude/skills | grep statistical-agent-skills

# every skill passes the structural checks
python3 scripts/check_skills.py
```

In a Claude Code session, the skills appear in the available-skills listing and the
commands under `/`. `claude --debug 2>&1 | grep -i skill` shows discovery at startup.

## Usage examples

1. Full review of an analysis notebook:

   ```
   /stat-review notebooks/churn_model_v3.ipynb
   ```

   Returns the standard 14-section review report: estimand and unit first, then
   assumptions, leakage findings, validation design, metrics, and a numbered list of
   required changes with severity and direction of bias.

2. Leakage audit of a feature job:

   ```
   /audit-leakage sql/features/conversion_features.sql
   ```

   Returns the report with a prediction-time availability table (one row per feature,
   with the timestamp each value is written relative to the decision timestamp) and
   blockers for anything not provably available at scoring time.

3. Natural-language trigger, no command:

   ```
   Our tROAS campaign's conversion values come from a pLTV model — can you sanity-check
   the value pipeline before we raise budgets?
   ```

   Activates `adtech-value-optimization` from its description alone and returns a review
   of the full value path (model → calibrator → bucketing → platform payload), including
   dollar-calibration and feedback-loop findings.

## Repository layout

```
statistical-agent-skills/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE                      # MIT
├── skills/                      # 12 skill directories, one SKILL.md each
│   ├── statistical-reviewer/    # hub / triage
│   ├── leakage-auditor/
│   └── ...
├── commands/                    # 8 slash commands (*.md)
├── templates/
│   └── review-report.md         # shared output contract, sections 1–14
├── docs/
│   ├── architecture.md          # hub-and-spoke design, ECC overlap analysis
│   ├── installation.md          # install / verify / disable / rollback
│   ├── security.md              # security posture and environment findings
│   ├── skill-authoring-guide.md # binding contract for every skill
│   ├── evaluation-methodology.md
│   └── source-attribution.md    # third-party evaluation matrix (nothing vendored)
├── scripts/
│   ├── install.sh               # symlink installer with manifest
│   ├── uninstall.sh             # symlink removal + manifest restore
│   └── check_skills.py          # spec/budget/contract/style validator
└── evals/
    ├── runners/run_evals.py     # eval harness (--check / --run / --report / --compare)
    ├── cases/                   # case prompts (one positive + one negative per skill)
    └── expected-behaviors/      # grading contracts
```

## Documentation

- [Architecture](docs/architecture.md) — why 12 skills, the shared output contract, and
  how this library relates to the ~80 pre-existing ECC skills on this machine.
- [Installation](docs/installation.md) — install, verify, disable a single skill, full rollback.
- [Security](docs/security.md) — posture of this library and findings about other skill
  collections installed in this environment.
- [Skill authoring guide](docs/skill-authoring-guide.md) — the binding contract for skill content.
- [Evaluation methodology](docs/evaluation-methodology.md) — what the harness can and cannot establish.
- [Source attribution](docs/source-attribution.md) — every third-party repository evaluated, and why none was adopted.
- [Contributing](CONTRIBUTING.md) — adding a skill, required eval cases, pre-commit checks.

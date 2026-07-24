# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Skill
versions are tracked per skill in each `SKILL.md` under `metadata.version`.

## [1.0.0] - 2026-07-23

Initial release.

### Added

- Twelve review skills under `skills/`, each a single `SKILL.md` conforming to the Agent
  Skills specification and the house authoring contract:
  - `statistical-reviewer` — hub: estimand-first triage and routing to specialists
  - `leakage-auditor` — prediction-time availability table, split and preprocessing audit
  - `calibration-and-ranking` — discrimination vs calibration, calibrator choice
  - `model-evaluation` — metric choice, baselines, uncertainty, test-set discipline
  - `experiment-design` — randomization, power, SRM, peeking, CUPED, interference
  - `causal-inference` — identification review for observational and quasi-experimental claims
  - `time-series-forecasting` — rolling-origin evaluation, lookahead, interval coverage
  - `bayesian-modeling` — priors, MCMC diagnostics, hierarchical models, posterior checks
  - `statistical-proof-review` — step-by-step verification of proofs and derivations
  - `data-quality-audit` — joins, duplicates, missingness, timestamps, label noise
  - `production-ml-review` — training/serving skew, drift, monitoring, rollback, versioning
  - `adtech-value-optimization` — dollar-valued model outputs sent to ad platforms
- Eight slash commands under `commands/`: `stat-review`, `audit-leakage`,
  `review-experiment`, `review-causal`, `review-forecast`, `review-calibration`,
  `review-production-ml`, `review-adtech-value`.
- Shared output contract `templates/review-report.md` (14-section standard review report
  plus compact form), used by all review skills.
- Symlink installer and uninstaller (`scripts/install.sh`, `scripts/uninstall.sh`) with
  dry-run mode, project-level `--target`, a supersede directory, and a restore manifest
  so pre-existing files (including the colliding ECC `stat-review.md` command) are moved
  aside and exactly restorable.
- Deterministic skill validator `scripts/check_skills.py` (spec conformance, size budget,
  required sections, style rules; no model calls).
- Evaluation harness `evals/runners/run_evals.py` with `--check`, `--run`, `--report`,
  and `--compare` modes; deterministic grading is explicitly limited to forbidden-pattern
  and concept-coverage checks, with human review required for quality.
- Sixteen evaluation cases under `evals/cases/` with grading contracts under
  `evals/expected-behaviors/` — fourteen positive cases covering the library's target
  failure modes, and two genuinely sound negative cases for false-positive resistance.
- Documentation: `docs/skill-authoring-guide.md` (binding authoring contract),
  `docs/evaluation-methodology.md`, `docs/architecture.md`, `docs/installation.md`,
  `docs/security.md`, `docs/source-attribution.md`, `docs/environment-audit.md`,
  `docs/validation-report.md`, `docs/limitations-and-roadmap.md`, `README.md`,
  `CONTRIBUTING.md`.
- MIT license.

### Fixed during initial development

- `run_evals.py` recorded an empty runner response with no grading and no error, so a run
  in which every model call failed would have reported a clean sweep. Empty responses now
  raise an explicit error and the exit status is nonzero when any case errors.
- `check_skills.py` rejected valid trigger clauses that did not open with the exact words
  "Use when" (for example "Use before a model launch"), producing a false warning against
  `production-ml-review`.
- The `fabricated-theorem-citation` grading contract scored a correct response `PARTIAL`
  because two concept groups matched fixed phrases rather than the operative verb and
  argument shape. Both were widened; see `docs/validation-report.md` §8.

### Notes

- All skill text is original work. No third-party code or skill content was vendored,
  copied, or installed; every candidate repository evaluated during research was
  rejected for cause, as recorded in `docs/source-attribution.md`. The library therefore
  carries no third-party license obligations beyond its own MIT license.
- Skills bundle no executable scripts, define no hooks, and make no network or
  credential access; the security posture is documented in `docs/security.md`.

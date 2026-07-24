# Source Evaluation and Attribution

Research conducted 2026-07-23. Every repository below was checked for existence, license,
last push, contents, and security signals before any adoption decision. **No third-party
repository was cloned, installed, or vendored into this library.** All skill text in
`skills/` is original work written for this repository.

## Evaluation matrix

| Repository | Exists | Stars | License | Last push | Statistical relevance | Security signals | Verdict |
|---|---|---|---|---|---|---|---|
| `anthropics/skills` | yes | ~164k | Mixed — repo has no top-level LICENSE; many skills Apache-2.0; `docx`/`pdf`/`pptx`/`xlsx` are source-available/proprietary | 2026-07-22 | **None.** Document and design skills only | Bundled Python scripts; no hooks; no network exfiltration patterns. Low | **Pattern source only.** Used `template/` + frontmatter conventions as the format reference. Nothing vendored |
| `agentskills.io/specification` | yes | n/a | spec | current | n/a (normative) | n/a | **Adopted as the normative spec.** `anthropics/skills/spec/` is now a stub pointing here |
| `K-Dense-AI/claude-scientific-skills` | yes | ~32k | MIT at repo level, but **per-skill licenses vary incl. CC BY-NC-SA 4.0** (non-commercial) | 2026-07-23 | Moderate — `statistical-analysis`, `statistical-power`, `experimental-design`, `pymc`, `statsmodels`, `scikit-learn`, `shap`. 149 skills, overwhelmingly bioinformatics | **High.** Repo's own auto-generated `SECURITY.md` (2026-07-20) reports 913 findings across 149 skills: 67 CRITICAL, 54 HIGH, only 103/149 rated safe. Categories include env-var exfiltration, cross-file exfiltration chains, prompt injection, unpinned dependency installs | **Rejected for vendoring.** Quality bar reference only. Already installed on this machine as a plugin — see the security review; the NC-licensed skills are also not reusable in commercial consulting work |
| `obra/superpowers` | yes | ~260k | MIT | 2026-07-24 | **Zero domain statistics.** High *authoring* relevance (`skills/writing-skills`) | Ships an always-on **SessionStart hook** that injects a skill file verbatim into every session wrapped in `<EXTREMELY_IMPORTANT>`. Readable bash, no network or credential access, but permanent context cost and always-on behavior modification | **Rejected for installation.** Authoring patterns noted; the session-start injection is not accepted for this environment |
| `anthropics/claude-cookbooks` | yes | ~50k | MIT | 2026-07-23 | Weak — notebooks, not skills. Financial modeling + LLM-eval methodology | Notebook execution, API keys via `.env`. Low | **Reference only** for eval patterns. Not a statistical source |
| `brycewang-stanford/StatsPAI` | yes | 282 | MIT | 2026-07-23 | **High** — causal inference + applied econometrics library, agent-native API. One thin bundled skill | Rust component, standard library risk | **Not adopted.** It is a Python library, not a skill set; worth evaluating separately as a *tool* the skills could reference |
| `Aperivue/medsci-skills` | yes | 214 | MIT | 2026-07-23 | **High** — `analyze-stats`, `calc-sample-size`, `design-study`, `model-evaluation`, `model-validation`, `check-reporting` | Ships installer/bin scripts (supply-chain caution); otherwise the best-engineered small repo found (CI, evals, SECURITY.md, third-party notices) | **Not adopted, recommended for future review.** Medical framing; methods transfer. Closest external quality peer |
| `brycewang-stanford/Awesome-Journal-Skills` | yes | 854 | MIT | 2026-07-24 | Moderate — 400+ journal-specific reporting/identification standards | Volume makes per-pack review infeasible | **Rejected.** Reporting conventions, not analysis methodology; unreviewable at that size |
| `sshtomar/claude-code-skills-social-science` | yes | 8 | MIT | 2026-03-15 (stale) | High structural match — DiD, RCT design/power/randomization, regression diagnostics | Low | **Rejected** — stale, and superseded by this library's `causal-inference` + `experiment-design` |
| `LeihuaYe/claude-experimentation` | yes | 0 | MIT | 2026-06-14 | On-target — SRM, CUPED, BH correction, ship verdict | Low | **Rejected** for adoption; concepts independently covered in `experiment-design` |
| `param087/agent-ml-skills` | yes | 7 | MIT | 2026-06-06 | Moderate — sklearn pipelines, model evaluation, reproducible ML | **Installs via `npx`/`install.mjs`** — supply-chain caution | **Rejected.** Install model not acceptable without inspection; content independently covered |
| `jeremylongshore/plugins-nixtla` | yes | 8 | NOASSERTION | 2026-07-10 | Forecasting-specific (StatsForecast/MLForecast/NeuralForecast) | Unclear license | **Rejected** — license unresolved; library-binding rather than methodology |
| `dylantmoore/stata-skill` | yes | 272 | NOASSERTION | 2026-04-10 | DiD/IV/RDD in Stata | Unclear license | **Rejected** — Stata not in this environment's stack |
| `xiaomihu1992/econometrics-skill` | yes | 32 | MIT | 2026-04-17 | 17 causal estimators with selection templates | Low | **Rejected** for adoption; overlaps `causal-inference` |

## Notable finding

Searches for adtech, marketing-mix-modeling, incrementality, geo-experiment, or
conversion-signal agent skills returned **zero** public repositories. The
`adtech-value-optimization` skill in this library has no public prior art to adapt from and
is entirely original.

## Adoption summary

- **Installed from third parties:** none.
- **Vendored (copied) from third parties:** none.
- **Adapted patterns only:** the Agent Skills frontmatter/layout conventions from the
  official specification and `anthropics/skills/template`.
- **Explicitly rejected:** every repository in the matrix above, for the stated reason.

Because nothing was copied, this library carries no third-party license obligations beyond
its own MIT license. If material is vendored later, record it here with its upstream
commit SHA, license, and the local modifications made — and add the upstream license text
to a `THIRD_PARTY_NOTICES.md`.

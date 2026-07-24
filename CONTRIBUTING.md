# Contributing

This library values coherence over coverage. Twelve skills behave like one system because
every one of them follows the same contract. A contribution that adds capability but
breaks the contract is a net loss and will not be merged.

## Adding a skill

`docs/skill-authoring-guide.md` is the binding contract — read it first, in full. The
short version of what it requires:

1. **One skill = one reviewing job.** If your skill needs two report shapes, it is two
   skills. If its job is already covered by an existing skill's findings catalogue,
   extend that skill instead.
2. **Layout.** Create `skills/<name>/SKILL.md`. The directory name must equal the
   frontmatter `name` (lowercase alphanumeric and hyphens, max 64 chars, no
   leading/trailing/consecutive hyphens). Optional `references/` files stay one level
   deep.
3. **Frontmatter.** `name` and `description` (max 1024 chars) are required;
   `license: MIT` and the `metadata` block (`library`, quoted `version`, `report`) follow
   the house convention. No top-level `version` field — the spec does not define one and
   `check_skills.py` rejects it. Do not use `allowed-tools`; this library does not.
4. **Description quality.** The description is the only text the model sees when deciding
   whether to load the skill. It must state both what the skill does and when to use it,
   with concrete trigger words a user would actually type — not abstractions.
5. **Size budget.** 150–320 lines and at most 5000 estimated tokens; 400 lines is the
   hard limit. Push worked examples and long tables into `references/`.
6. **Section order.** Title, Purpose, When to use / When NOT to use, Procedure, Findings
   catalogue, Output contract, Anti-patterns. The "When NOT to use" list must name the
   sibling skill that owns each excluded case — this is how routing works
   (see `docs/architecture.md`).
7. **Update the routing.** Add your skill to `statistical-reviewer`'s routing table, and
   add exclusion arrows to any sibling whose boundary your skill now defines.
8. **House style.** Operational, not exhortative; every claim gets a mechanism; estimand
   before method; `observed`/`inferred`/`unverifiable` evidence tiers; never fabricate;
   ask instead of assuming. Severities follow the rubric in the authoring guide §6.

If the skill warrants a slash command, add `commands/<verb>-<noun>.md` following the
existing pattern: a `description` frontmatter line, `Target: $ARGUMENTS`, a short "What
to do" that invokes the skill by name, and the output contract.

## Required eval cases

Every skill needs at least **one positive and one negative case**:

- `evals/cases/<id>.md` — frontmatter (`id`, `skill`, `polarity`, `tags`) plus the
  verbatim prompt under a `## Prompt` heading.
- `evals/expected-behaviors/<id>.yaml` — the grading contract (`id`, `skill`, `polarity`,
  `summary`, plus `must_identify`, `must_mention_any`, `forbidden_behaviors`,
  `forbidden_patterns`, `required_severity` as applicable).

The positive case contains a genuine flaw the skill must catch (tests false negatives).
The negative case is genuinely sound in the named respect and the skill must *not*
manufacture a defect (tests false positives). A negative case with a subtle real flaw is
a broken case, not a hard one. See `docs/evaluation-methodology.md` for the full case
design rules and the human review rubric.

## Before committing

Run both deterministic checks; both must pass:

```bash
python3 scripts/check_skills.py
python3 evals/runners/run_evals.py --check
```

`check_skills.py` validates spec conformance, size budget, required sections, and style
for every skill. `run_evals.py --check` validates case/contract structure without any
model calls. Neither check claims to assess statistical quality — that is what the human
rubric is for.

When you *change* an existing skill, additionally run the affected cases before and after
and compare, holding the model fixed:

```bash
python3 evals/runners/run_evals.py --run --case <id>          # before, save results
# ... edit the skill, bump metadata.version ...
python3 evals/runners/run_evals.py --run --case <id>          # after
python3 evals/runners/run_evals.py --compare evals/results/<old>.json evals/results/<new>.json
```

Investigate every `REGRESSION`. Do not claim eval results you did not run.

## Commit messages

```
<type>: <description>
```

- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
- Imperative mood: "Add forecast baseline check", not "Added" or "Adds".
- One logical change per commit. A new skill and its eval cases belong in one commit;
  an unrelated fix to another skill does not.

## Review checklist for a new skill

- [ ] `python3 scripts/check_skills.py` passes with no errors for the new skill.
- [ ] `python3 evals/runners/run_evals.py --check` passes.
- [ ] Directory name equals frontmatter `name`; no top-level `version`.
- [ ] Description states what *and* when, with concrete trigger vocabulary, ≤1024 chars.
- [ ] SKILL.md within budget (≤400 lines hard, ≤5000 estimated tokens).
- [ ] Required sections present, in order; "When NOT to use" names sibling skills for
      every exclusion.
- [ ] `statistical-reviewer` routing table updated; affected siblings' exclusion lists
      updated. No two skills claim the same case.
- [ ] Findings catalogue entries each name a signal and a consequence; no exhortations.
- [ ] Output contract references `templates/review-report.md` (or states `report: none`
      in metadata with a reason).
- [ ] At least one positive and one negative eval case, with contracts.
- [ ] The negative case is genuinely sound — reviewed by a second reader if possible.
- [ ] No fabricated citations, theorem names, package APIs, or numbers anywhere in the
      skill text.
- [ ] No bundled scripts, hooks, network access, or credential access (security posture
      in `docs/security.md`); anything executable belongs in `scripts/` or `evals/`.
- [ ] Description does not overlap an existing skill's triggers without an explicit
      boundary in both skills' "When NOT to use" sections.

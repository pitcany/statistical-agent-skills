---
description: Full statistical review of an analysis, model, notebook, query, or diff — establishes estimand, unit, and decision-time information before critiquing method, then routes to the specialist skill.
---

# Statistical review

Target: $ARGUMENTS

## What to do

1. **Resolve the target.**
   - If `$ARGUMENTS` names a path, review that path.
   - If it names a PR or commit, review that diff.
   - If empty, review uncommitted changes (`git diff` + `git diff --staged`); if the
     working tree is clean or this is not a repository, ask what to review rather than
     guessing.
2. Invoke the `statistical-reviewer` skill. Work its procedure in order — do not skip to
   method commentary before the estimand and unit are written down.
3. Route to specialists as `statistical-reviewer` directs. Name the specific question each
   specialist should answer.
4. If the material is code, also state plainly which findings are statistical invalidity
   and which are software defects. They are separate axes.

## Required inputs

If any of these cannot be determined from the target, ask for them before concluding —
do not assume the favorable case:

- What decision does this feed, and when is it made?
- What is the observational unit of a row?
- For predictive work: what timestamp does the model score at?
- Which labels are matured, and over what window?

## Output

The standard review report (`templates/review-report.md`), sections 1–14. Compact form is
acceptable for a small diff. §2 (estimand), §12 (required changes) and §14 (unresolved
questions) are mandatory in every form.

## Related

The user's environment also has ECC skills `stat-code-smell-detector` and
`stat-assumptions-auditor`, which are line-level and complementary. Use them in addition
when reviewing code, not instead of the estimand-first procedure above.

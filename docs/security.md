# Security

## Threat model: skills are instructions executed with your authority

An Agent Skill is not passive documentation. When it activates, its text is injected into
the model's context and steers what the agent does next — with whatever tool permissions,
file access, and credentials the session has. A malicious or careless skill can direct
the agent to run shell commands, read `~/.ssh` or `.env` files, exfiltrate environment
variables, install unpinned dependencies, or quietly weaken your own review standards.
Hooks are stronger still: they execute on harness events without any activation decision
at all.

Treat every third-party skill as untrusted code, because functionally that is what it is.
The distribution model (a Markdown file in a git repo) makes this easy to forget.

## Review checklist before adopting any third-party skill

Applied to every candidate during this library's research phase
(`docs/source-attribution.md` records the verdicts):

- [ ] Read the full instruction text. Does it ask the agent to do anything beyond its
      stated purpose?
- [ ] Bundled scripts: read every one. What do they execute, and with what inputs?
- [ ] Hooks: does the package register SessionStart/PreToolUse/PostToolUse hooks? Hooks
      run without activation and deserve the highest scrutiny.
- [ ] Shell commands: does the skill instruct the agent to run commands, especially
      `curl | bash`, package installs, or anything with `sudo`?
- [ ] Network access: does anything fetch remote content at use time (an injection and
      supply-chain vector even when the fetched content is benign today)?
- [ ] Credential access: any reference to environment variables, key files, `~/.aws`,
      `~/.ssh`, tokens, or "send/upload/post" of local data?
- [ ] Destructive operations: deletes, overwrites, force-pushes, permission changes.
- [ ] Prompt-injection vectors: instructions that tell the agent to ignore other
      instructions, escalate its own permissions, or treat fetched/quoted content as
      directives.
- [ ] License: compatible with your use? Non-commercial licenses (CC BY-NC-SA) are not
      usable in paid consulting work.
- [ ] Conflicts with local policy: does the skill contradict your CLAUDE.md rules
      (e.g. your prohibition on reading `.env` files and `~/.secrets`)?

If you cannot complete the checklist — the package is too large to review, as with
400-pack collections — that is itself a rejection reason, not an excuse to skip review.

## This library's posture

Deliberately minimal attack surface:

- **Skills are pure instructions.** No skill bundles or invokes scripts; each is a single
  `SKILL.md`. The executable tooling in this repository (`scripts/check_skills.py`,
  `scripts/install.sh`, `scripts/uninstall.sh`, `evals/runners/run_evals.py`) is run by
  the developer from the shell, never triggered by a skill, and is dependency-free
  (Python standard library and bash/coreutils only).
- **No hooks.** Nothing runs at session start or on tool events.
- **No network access.** No skill instructs the agent to fetch anything remote.
- **No credential access.** No skill references environment variables, key files, or
  secrets; the review procedures operate on material the user supplies.
- **No destructive operations.** Review skills read and report. The installer never
  overwrites a file (move-aside plus manifest; see `docs/installation.md`).
- **MIT licensed, nothing vendored.** All text is original; there are no third-party
  license obligations and no upstream to be compromised (`docs/source-attribution.md`).

The honest residual risk: these skills shape the agent's *judgment*. A subtly wrong
review procedure produces subtly wrong reviews with the library's confident tone. The
mitigations are the eval harness, the human review rubric, and the authoring rules
against fabrication — not sandboxing, which does not apply to instruction-only content.

## Findings in this environment

### K-Dense-AI/claude-scientific-skills — installed, review recommended

This plugin **is installed on this machine at user scope**. Its own auto-generated
`SECURITY.md` (dated 2026-07-20) reports **913 findings across 149 skills, including 67
CRITICAL and 54 HIGH, with only 103 of 149 skills rated safe**. The reported categories
include environment-variable exfiltration, cross-file exfiltration chains, prompt
injection, and unpinned dependency installs. Those categories are exactly the ones the
checklist above exists to catch, and they are reported by the project itself, not by a
hostile third party.

Additionally, while the repository is MIT at top level, **per-skill licenses vary and
include CC BY-NC-SA 4.0 (non-commercial)**. Output produced with those skills is
encumbered for commercial consulting work — a practical problem for Pitcan Analytics
engagements independent of the security findings.

Recommendation: review the plugin's `SECURITY.md` against the skills you actually use,
and remove the plugin (or at minimum the CRITICAL-flagged and NC-licensed skills) unless
a specific skill earns its place after individual review. This library's statistical
skills do not depend on it in any way.

### obra/superpowers — rejected pattern: always-on SessionStart hook

Evaluated and not installed. The package ships a SessionStart hook that injects a skill
file verbatim into **every** session, wrapped in `<EXTREMELY_IMPORTANT>` tags. The bash
is readable and makes no network or credential access, but the pattern is rejected here
on principle: it modifies agent behavior in all sessions without an activation decision,
costs permanent context, and normalizes exactly the mechanism a malicious package would
use. This library uses no hooks; nothing in it runs without either a description-match
activation or an explicit user invocation.

## General guidance

- Do not grant broad standing permissions to make skills "work better". A review skill
  needs read and search access; it does not need network access, `sudo`, or write access
  outside the workspace. Keep allowlists narrow and per-tool.
- Never run with permission prompts disabled while third-party skills are installed. The
  prompt is the last checkpoint between an injected instruction and its effect.
- Prefer instruction-only skills over script-bundling ones; when scripts are unavoidable,
  pin dependencies and read the pinned versions.
- Re-review on update. A `git pull` of a third-party skill repo is a code change to
  something that executes with your authority; upstream compromise of a popular skill
  repo is a realistic supply-chain path.
- Watch for skill-name and command-name collisions at install time — a look-alike name is
  a cheap way to hijack an established trigger. This library's installer surfaces every
  collision explicitly and records what it displaced.

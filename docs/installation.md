# Installation

Verified against Claude Code 2.1.218 on Linux, user configuration at `~/.claude`.

## How the install works

`scripts/install.sh` does not copy anything. It creates symlinks:

- each `skills/<name>/` directory → `<target>/skills/<name>`
- each `commands/<name>.md` file → `<target>/commands/<name>.md`

The git repository stays the single source of truth. Consequences:

- `git pull` in this repository updates every installed skill and command instantly —
  there is no re-install step and no drift between repo and installed copies.
- Editing an installed skill edits the repo file (they are the same file), so changes are
  visible to `git diff` and never silently diverge.
- There are no unmanaged copies to hunt down later; uninstalling is symlink removal.

Safety properties (from the script itself):

- It never overwrites a real file or directory. A pre-existing entry at a destination is
  moved to `<target>/_superseded-statskills/<timestamp>/` and recorded in a manifest
  (`<target>/_superseded-statskills/manifest-<timestamp>.tsv`) so `uninstall.sh` can
  restore it exactly.
- Symlinks that already point into this repository are refreshed idempotently; re-running
  the installer is safe.
- Every action is printed; `--dry-run` performs none of them.

## Prerequisites

- Claude Code with a user configuration directory at `~/.claude` (or a project `.claude/`
  directory for project-level installs). The target directory must already exist — the
  installer exits with an error if it does not.
- bash and coreutils (standard on Linux).
- Python 3 for the validation and eval scripts (no third-party packages required; both
  scripts are dependency-free by design).

## Recommended: back up first

Before the first install, snapshot the parts of `~/.claude` the installer can touch:

```bash
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p ~/.claude/backups/pre-statskills-$STAMP
tar czf ~/.claude/backups/pre-statskills-$STAMP/claude-config-snapshot.tgz \
    -C ~ .claude/skills .claude/commands .claude/settings.json
```

The backup tarball pattern used on this machine is
`~/.claude/backups/pre-statskills-<timestamp>/claude-config-snapshot.tgz`. This is a
belt-and-suspenders measure — the installer's own manifest already covers everything it
moves — but it also covers you against your *own* subsequent edits.

## Install

Always dry-run first. It prints exactly what would change and modifies nothing:

```bash
cd ~/Projects/statistical-agent-skills
./scripts/install.sh --dry-run
```

Read the output. Expected: 12 skill links, 8 command links, and — on this machine — one
warning that `stat-review.md` already exists and will be preserved (see the collision
section below). Then apply:

```bash
./scripts/install.sh
```

The installer prints the manifest path and the exact rollback command at the end. Keep
that manifest path; it is the key to restoring superseded files.

### Flags

| Flag | Effect |
|---|---|
| `--dry-run` | Print every action; change nothing |
| `--target <dir>` | Install into `<dir>` instead of `~/.claude` |
| `--skills-only` | Link skills only; skip slash commands |
| `-h`, `--help` | Print usage |

### User-level vs project-level

- **User level** (default, `~/.claude`): skills and commands are available in every
  project. This is the normal mode for a personal review library.
- **Project level** (`--target .claude` from inside a project): available only in that
  project, and — if the `.claude` directory is committed — note that symlinks pointing
  into `~/Projects/statistical-agent-skills` will not resolve on other machines. For a
  shared project, copy rather than symlink, or have each contributor run the installer.

```bash
./scripts/install.sh --target /path/to/project/.claude --dry-run
./scripts/install.sh --target /path/to/project/.claude
```

## The `stat-review.md` collision

This machine's ECC collection already provides `~/.claude/commands/stat-review.md`. That
is the only name collision between this library and the ~80 pre-existing skills and
commands (no *skill* names collide).

What the installer does: because the existing file is a real file (not a symlink), it is
moved to `~/.claude/_superseded-statskills/<timestamp>/stat-review.md`, a `path` line is
written to the manifest, and the library's `stat-review.md` is linked in its place. The
installer prints a warning naming the file when this happens.

To restore the ECC version later, either:

```bash
# full restore via the uninstaller (removes this library's links too)
./scripts/uninstall.sh --manifest ~/.claude/_superseded-statskills/manifest-<timestamp>.tsv
```

or, to restore only that one file while keeping the rest of the library installed:

```bash
rm ~/.claude/commands/stat-review.md   # removes the symlink only
mv ~/.claude/_superseded-statskills/<timestamp>/stat-review.md ~/.claude/commands/
```

## Verify discovery

```bash
# 1. Symlinks exist and resolve into this repository
ls -l ~/.claude/skills | grep -c statistical-agent-skills    # expect 12
ls -l ~/.claude/commands | grep -c statistical-agent-skills  # expect 8

# 2. Structural validity of what is linked
python3 scripts/check_skills.py

# 3. Claude Code sees them
claude --debug 2>&1 | grep -i skill
```

In a session: the twelve skills appear in the available-skills listing (check that
`statistical-reviewer` and `leakage-auditor` are present), and typing `/` shows the eight
commands. A quick functional check: `/stat-review` with no arguments in a clean directory
should ask what to review rather than guessing.

## Disabling a single skill

If one skill misbehaves or triggers too eagerly, you do not need to uninstall the
library.

**Option A — non-destructive (recommended): `skillOverrides` in `~/.claude/settings.json`.**
Your settings already use this mechanism for other skills. Adding an entry with the
observed value `"user-invocable-only"` keeps the skill available when explicitly invoked
but removes it from automatic selection:

```json
{
  "skillOverrides": {
    "bayesian-modeling": "user-invocable-only"
  }
}
```

Reversible by deleting the entry. No files change on disk.

**Option B — remove the symlink.** The skill disappears entirely until you re-run the
installer (which recreates it idempotently):

```bash
rm ~/.claude/skills/bayesian-modeling
```

This removes only the symlink; the skill's content in the repository is untouched.

## Uninstall and full rollback

`scripts/uninstall.sh` removes only symlinks that resolve into this repository — anything
else in `~/.claude/skills` or `~/.claude/commands` is left alone.

```bash
# preview
./scripts/uninstall.sh --dry-run

# remove the library's symlinks from ~/.claude
./scripts/uninstall.sh

# remove symlinks AND restore everything the installer moved aside
./scripts/uninstall.sh --manifest ~/.claude/_superseded-statskills/manifest-<timestamp>.tsv

# project-level target
./scripts/uninstall.sh --target /path/to/project/.claude
```

Restore behavior details: entries are restored in reverse manifest order; a backup that
has gone missing is reported and skipped; if something new now occupies an original path,
the uninstaller refuses to overwrite it and tells you where the backup remains.

Full rollback procedure, in order:

1. `./scripts/uninstall.sh --dry-run` — confirm what will be removed.
2. `./scripts/uninstall.sh --manifest <manifest>` — remove links, restore superseded
   files (including the ECC `stat-review.md`).
3. Verify: `ls -l ~/.claude/skills ~/.claude/commands | grep statistical-agent-skills`
   should return nothing, and `~/.claude/commands/stat-review.md` should again be the ECC
   file (a regular file, not a symlink).
4. Remove any `skillOverrides` entries you added for this library's skills.
5. If anything else looks wrong, the pre-install snapshot at
   `~/.claude/backups/pre-statskills-<timestamp>/claude-config-snapshot.tgz` restores the
   entire prior state:

   ```bash
   tar xzf ~/.claude/backups/pre-statskills-<timestamp>/claude-config-snapshot.tgz -C ~
   ```

The repository itself is never touched by install or uninstall.

## Updating the library

Because installs are symlinks, updating is just:

```bash
cd ~/Projects/statistical-agent-skills
git pull
python3 scripts/check_skills.py   # confirm the updated skills still pass
```

Running sessions pick up changed skill bodies the next time the skill activates; new or
renamed skills require re-running `./scripts/install.sh` (idempotent — existing correct
links are reported as `= already linked`) so the new directories get linked. If a skill
was *removed* upstream, its now-dangling symlink is cleaned up by
`./scripts/uninstall.sh` followed by a fresh `./scripts/install.sh`, or by deleting the
dangling link manually.

#!/usr/bin/env bash
# Install statistical-agent-skills into a Claude Code configuration directory by
# symlinking, so this git repository stays the single source of truth.
#
#   ./scripts/install.sh                 # install to ~/.claude (user level)
#   ./scripts/install.sh --dry-run       # show what would change, touch nothing
#   ./scripts/install.sh --target .claude  # install to a project-level directory
#   ./scripts/install.sh --skills-only   # skip slash commands
#
# Safety properties:
#   * Never overwrites a real file or directory. Pre-existing entries are moved to
#     a timestamped directory under <target>/_superseded-statskills/ and recorded in
#     a manifest so uninstall.sh can restore them exactly.
#   * Symlinks that already point into this repository are refreshed idempotently.
#   * Every action is printed. --dry-run performs none of them.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${HOME}/.claude"
DRY_RUN=0
SKILLS_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)     DRY_RUN=1; shift ;;
    --skills-only) SKILLS_ONLY=1; shift ;;
    --target)      TARGET="$(cd "$2" 2>/dev/null && pwd || echo "$2")"; shift 2 ;;
    -h|--help)     sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

STAMP="$(date +%Y%m%d-%H%M%S)"
SUPERSEDED="${TARGET}/_superseded-statskills/${STAMP}"
MANIFEST="${TARGET}/_superseded-statskills/manifest-${STAMP}.tsv"

say()  { printf '%s\n' "$*"; }
act()  { if [[ $DRY_RUN -eq 1 ]]; then say "  [dry-run] $*"; else say "  $*"; fi; }
run()  { if [[ $DRY_RUN -eq 0 ]]; then "$@"; fi; }

say "statistical-agent-skills installer"
say "  repo:   ${REPO}"
say "  target: ${TARGET}"
[[ $DRY_RUN -eq 1 ]] && say "  MODE:   dry run — nothing will be modified"
say ""

if [[ ! -d "$TARGET" ]]; then
  echo "error: target directory ${TARGET} does not exist" >&2
  exit 1
fi

record() {  # record <kind> <original-path> <backup-path-or-dash>
  if [[ $DRY_RUN -eq 0 ]]; then
    mkdir -p "$(dirname "$MANIFEST")"
    printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$MANIFEST"
  fi
}

link_one() {  # link_one <source> <dest>
  local src="$1" dest="$2" name
  name="$(basename "$dest")"

  if [[ -L "$dest" ]]; then
    local current
    current="$(readlink -f "$dest" || true)"
    if [[ "$current" == "$(readlink -f "$src")" ]]; then
      say "  = ${name} (already linked)"
      return
    fi
    act "unlink foreign symlink ${name} -> ${current}"
    run rm "$dest"
    record symlink "$dest" "$current"
  elif [[ -e "$dest" ]]; then
    act "move existing ${name} aside -> ${SUPERSEDED}/${name}"
    run mkdir -p "$SUPERSEDED"
    run mv "$dest" "${SUPERSEDED}/${name}"
    record path "$dest" "${SUPERSEDED}/${name}"
  fi

  act "link ${name}"
  run ln -s "$src" "$dest"
  record link "$dest" -
}

# ---------------------------------------------------------------- skills
say "Skills -> ${TARGET}/skills/"
run mkdir -p "${TARGET}/skills"
count=0
for skill_dir in "${REPO}"/skills/*/; do
  [[ -f "${skill_dir}SKILL.md" ]] || continue
  name="$(basename "$skill_dir")"
  link_one "${skill_dir%/}" "${TARGET}/skills/${name}"
  count=$((count + 1))
done
say "  ${count} skill(s)"
say ""

# -------------------------------------------------------------- commands
if [[ $SKILLS_ONLY -eq 0 ]]; then
  say "Commands -> ${TARGET}/commands/"
  run mkdir -p "${TARGET}/commands"
  ccount=0
  for cmd in "${REPO}"/commands/*.md; do
    [[ -f "$cmd" ]] || continue
    name="$(basename "$cmd")"
    if [[ -e "${TARGET}/commands/${name}" && ! -L "${TARGET}/commands/${name}" ]]; then
      say "  ! ${name} already exists and is not a symlink — it will be preserved in"
      say "    ${SUPERSEDED}/ and restorable via scripts/uninstall.sh"
    fi
    link_one "$cmd" "${TARGET}/commands/${name}"
    ccount=$((ccount + 1))
  done
  say "  ${ccount} command(s)"
  say ""
fi

if [[ $DRY_RUN -eq 1 ]]; then
  say "Dry run complete. Re-run without --dry-run to apply."
  exit 0
fi

say "Manifest: ${MANIFEST}"
say "Rollback: ${REPO}/scripts/uninstall.sh --manifest ${MANIFEST}"
say ""
say "Verify discovery with:  claude --debug 2>&1 | grep -i skill"
say "or list installed skills in a session with the /help menu."

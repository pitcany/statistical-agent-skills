#!/usr/bin/env bash
# Remove statistical-agent-skills symlinks and restore anything the installer moved aside.
#
#   ./scripts/uninstall.sh                                # remove links from ~/.claude
#   ./scripts/uninstall.sh --manifest <path>              # also restore superseded files
#   ./scripts/uninstall.sh --dry-run
#   ./scripts/uninstall.sh --target .claude
#
# Only symlinks that point into this repository are removed. Anything else is left alone.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${HOME}/.claude"
MANIFEST=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN=1; shift ;;
    --manifest) MANIFEST="$2"; shift 2 ;;
    --target)   TARGET="$(cd "$2" 2>/dev/null && pwd || echo "$2")"; shift 2 ;;
    -h|--help)  sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

say() { printf '%s\n' "$*"; }
act() { if [[ $DRY_RUN -eq 1 ]]; then say "  [dry-run] $*"; else say "  $*"; fi; }
run() { if [[ $DRY_RUN -eq 0 ]]; then "$@"; fi; }

say "statistical-agent-skills uninstaller"
say "  repo:   ${REPO}"
say "  target: ${TARGET}"
[[ $DRY_RUN -eq 1 ]] && say "  MODE:   dry run"
say ""

removed=0
for dir in "${TARGET}/skills" "${TARGET}/commands"; do
  [[ -d "$dir" ]] || continue
  say "Scanning ${dir}"
  for entry in "$dir"/*; do
    [[ -L "$entry" ]] || continue
    dest="$(readlink -f "$entry" || true)"
    case "$dest" in
      "${REPO}"/*)
        act "remove $(basename "$entry")"
        run rm "$entry"
        removed=$((removed + 1))
        ;;
    esac
  done
done
say ""
say "${removed} symlink(s) removed"

if [[ -n "$MANIFEST" ]]; then
  if [[ ! -f "$MANIFEST" ]]; then
    echo "error: manifest not found: ${MANIFEST}" >&2
    exit 1
  fi
  say ""
  say "Restoring superseded entries from ${MANIFEST}"
  restored=0
  # Restore in reverse order so nested moves unwind correctly.
  while IFS=$'\t' read -r kind original backup; do
    [[ "$kind" == "path" ]] || continue
    [[ -e "$backup" ]] || { say "  ! backup missing, skipping: ${backup}"; continue; }
    if [[ -e "$original" || -L "$original" ]]; then
      say "  ! ${original} exists again — not overwriting; backup remains at ${backup}"
      continue
    fi
    act "restore $(basename "$original")"
    run mv "$backup" "$original"
    restored=$((restored + 1))
  done < <(tac "$MANIFEST")
  say "${restored} entry(ies) restored"
fi

say ""
say "Done. The repository at ${REPO} is untouched."

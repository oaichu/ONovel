#!/usr/bin/env bash
# sync-onovel.sh — re-copy /CODE novel tooling into onovel-repo and push if changed.
# Same exclusion rules as the initial ONovel backup. Never prints secret values.
set -euo pipefail

SRC_ROOT="${CODE_ROOT:-/CODE}"
REPO_DIR="${ONOVEL_REPO:-/workspace/CODE/onovel-repo}"
BRANCH="${ONOVEL_BRANCH:-main}"

die() { echo "sync-onovel: $*" >&2; exit 1; }

[[ -d "$SRC_ROOT/inkos" ]] || die "missing $SRC_ROOT/inkos"
[[ -d "$REPO_DIR/.git" ]] || die "missing git repo at $REPO_DIR (create it first)"

# Stage into a temp tree, then rsync-like replace of tracked trees (via tar).
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/inkos" "$STAGE/novel-skills" "$STAGE/lessons-library"

tar -C "$SRC_ROOT/inkos" -cf - \
  --exclude='runs' \
  --exclude='genre-kit/vendor' \
  --exclude='__pycache__' \
  --exclude='*.bak*' \
  --exclude='.env' \
  --exclude='*.env' \
  --exclude='*.log' \
  --exclude='scratch_*' \
  --exclude='.onovel' \
  --exclude='*.db' \
  --exclude='.pytest_cache' \
  . | tar -C "$STAGE/inkos" -xf -

if [[ -d "$SRC_ROOT/novel-skills" ]]; then
  tar -C "$SRC_ROOT/novel-skills" -cf - \
    --exclude='__pycache__' --exclude='*.bak*' --exclude='.env' --exclude='*.env' \
    . | tar -C "$STAGE/novel-skills" -xf -
fi

if [[ -d "$SRC_ROOT/lessons-library" ]]; then
  tar -C "$SRC_ROOT/lessons-library" -cf - \
    --exclude='__pycache__' --exclude='*.bak*' --exclude='.env' --exclude='*.env' \
    . | tar -C "$STAGE/lessons-library" -xf -
fi

[[ -f "$SRC_ROOT/RECOVERY.md" ]] && cp "$SRC_ROOT/RECOVERY.md" "$STAGE/RECOVERY.md"

# Preserve README.md / .gitignore already in repo; replace content trees.
rm -rf "$REPO_DIR/inkos" "$REPO_DIR/novel-skills" "$REPO_DIR/lessons-library"
cp -a "$STAGE/inkos" "$REPO_DIR/inkos"
cp -a "$STAGE/novel-skills" "$REPO_DIR/novel-skills"
cp -a "$STAGE/lessons-library" "$REPO_DIR/lessons-library"
[[ -f "$STAGE/RECOVERY.md" ]] && cp "$STAGE/RECOVERY.md" "$REPO_DIR/RECOVERY.md"

# Ensure this sync script itself is present in the staged inkos/tools
mkdir -p "$REPO_DIR/inkos/tools"
cp -a "$SRC_ROOT/inkos/tools/sync-onovel.sh" "$REPO_DIR/inkos/tools/sync-onovel.sh"
chmod +x "$REPO_DIR/inkos/tools/sync-onovel.sh" "$SRC_ROOT/inkos/tools/sync-onovel.sh"

# CI workflow lives in inkos/ci (single source)
# (pushing .github/workflows needs a token with `workflow` scope, which the box gh token lacks as of 2026-10-19: opt in with ONOVEL_SYNC_WORKFLOW=1
#  after `gh auth refresh -s workflow`; without it the push of the whole sync is rejected)
if [[ "${ONOVEL_SYNC_WORKFLOW:-0}" == 1 ]]; then mkdir -p "$REPO_DIR/.github/workflows"; cp "$SRC_ROOT/inkos/ci/github-ci.yml" "$REPO_DIR/.github/workflows/ci.yml"; fi

# Tests must pass before anything is committed (mocked LLM, no network)
# Audit A01: no tests -> no commit (missing pytest is a hard failure, not a warning).
PY_T="${ONOVEL_PYTHON:-}"; [[ -z "$PY_T" && -x /home/box/.venvs/onovel-test/bin/python ]] && PY_T=/home/box/.venvs/onovel-test/bin/python; PY_T="${PY_T:-python3}"
"$PY_T" -c 'import pytest' 2>/dev/null || die "pytest not available for $PY_T (set ONOVEL_PYTHON to a python with pytest); not committing"
( cd "$REPO_DIR" && ONOVEL_HOME="$REPO_DIR/inkos" ONOVEL_LESSONS=/nonexistent-lessons "$PY_T" -m pytest -q -p no:cacheprovider inkos/tests ) || die "tests failed; not committing"
( ONOVEL_HOME="$REPO_DIR/inkos" bash "$REPO_DIR/inkos/tests/smoke.sh" ) || die "smoke test failed; not committing"

# Secret scan (fail if literal named keys / sk-or- / Bearer tokens look embedded)
SCAN_TMP="$(mktemp)"
rg -n -i '(api[_-]?key|token|secret|sk-or-|Bearer )' "$REPO_DIR" \
  -g '!.git/**' -g '!*.png' -g '!*.jpg' -g '!*.gif' -g '!*.woff*' -g '!*.ttf' \
  > "$SCAN_TMP" || true

if rg -n -e '(BAI_API_KEY|GEMINI_API_KEY|CLOUDFLARE_API_TOKEN|INKOS_LLM_API_KEY|HF_TOKEN|OPENROUTER_API_KEY)\s*=\s*["'\''][^$'"'"'][^"'\'']{8,}["'\'']' \
     -e 'sk-or-[A-Za-z0-9]{16,}' \
     -e 'Bearer [A-Za-z0-9._\-]{20,}' \
     "$REPO_DIR" -g '!.git/**' -g '!**/verify_agent_kit.py' >/dev/null 2>&1; then  # verify_agent_kit.py: known fake test fixture (also allowlisted for gitleaks below)
  echo "sync-onovel: ABORT — possible hardcoded secret detected (values not printed)." >&2
  echo "sync-onovel: re-check with: rg -n -i '(api[_-]?key|token|secret|sk-or-|Bearer )' $REPO_DIR" >&2
  exit 2
fi

GL="$(command -v gitleaks || true)"; [[ -z "$GL" && -x "$HOME/.local/bin/gitleaks" ]] && GL="$HOME/.local/bin/gitleaks"
if [[ -n "$GL" ]]; then
  # known fake fixtures (verify_agent_kit.py) are allowlisted in inkos/ci/gitleaks.toml; values are always redacted
  if ! "$GL" detect --source "$REPO_DIR" --no-git --no-banner --redact --config "$REPO_DIR/inkos/ci/gitleaks.toml" >"$SCAN_TMP.gl" 2>&1; then
    echo "sync-onovel: ABORT — gitleaks found potential secrets (run gitleaks with --redact locally; values not printed)." >&2
    exit 2
  fi
else echo "sync-onovel: WARN gitleaks not installed; CI secrets job will scan"; fi

cd "$REPO_DIR"
git add -A
if git diff --cached --quiet; then
  echo "sync-onovel: no changes"
  exit 0
fi

MSG="sync: refresh from /CODE $(date +%Y-%m-%dT%H:%M:%S%z)"
git commit -m "$MSG"
git push origin "$BRANCH"
echo "sync-onovel: pushed $(git rev-parse --short HEAD) to $BRANCH"

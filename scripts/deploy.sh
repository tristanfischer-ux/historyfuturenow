#!/usr/bin/env bash
set -euo pipefail

# ─── HFN Deploy Script ──────────────────────────────────────────────────────
# Builds the site, commits to git, pushes, and deploys to Vercel production.
#
# Usage:
#   ./scripts/deploy.sh                    # Build + deploy
#   ./scripts/deploy.sh --skip-build       # Deploy without rebuilding
#   ./scripts/deploy.sh "commit message"   # Custom commit message
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/hfn-build-system"
OUTPUT_DIR="$ROOT_DIR/hfn-site-output"
LOG_FILE="$HOME/.memory/daily/$(date +%Y-%m-%d).md"

SKIP_BUILD=false
COMMIT_MSG=""

for arg in "$@"; do
    case "$arg" in
        --skip-build) SKIP_BUILD=true ;;
        *) COMMIT_MSG="$arg" ;;
    esac
done

echo "═══════════════════════════════════════════════════"
echo "  HFN Deploy"
echo "═══════════════════════════════════════════════════"

# ─── Step 1: Build ───────────────────────────────────────────────────────────
if [ "$SKIP_BUILD" = false ]; then
    echo ""
    echo "▸ Building site..."
    cd "$BUILD_DIR"
    python3 build.py
    echo "  ✓ Build complete"
else
    echo ""
    echo "▸ Skipping build (--skip-build)"
fi

# ─── Step 2: Git commit + push ──────────────────────────────────────────────
cd "$ROOT_DIR"

if [ -z "$(git status --porcelain)" ]; then
    echo ""
    echo "▸ No changes to commit"
else
    echo ""
    echo "▸ Committing changes..."
    git add .

    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="deploy: $(date +%Y-%m-%d\ %H:%M)"
    fi

    git commit -m "$COMMIT_MSG"
    echo "  ✓ Committed: $COMMIT_MSG"
fi

BRANCH=$(git branch --show-current)
COMMIT_HASH=$(git rev-parse --short HEAD)
COMMIT_MSG_ACTUAL=$(git log -1 --format='%s')
FILES_CHANGED=$(git diff --stat HEAD~1 HEAD 2>/dev/null | tail -1 || echo "unknown")

echo ""
echo "▸ Pushing to origin/$BRANCH..."
git push origin "$BRANCH"
echo "  ✓ Pushed"

# ─── Step 3: Deploy to Vercel ────────────────────────────────────────────────
echo ""
echo "▸ Deploying to Vercel production..."
cd "$OUTPUT_DIR"
vercel --prod --yes 2>&1 | tail -5
echo "  ✓ Vercel deploy complete"

# ─── Step 4: Verify ─────────────────────────────────────────────────────────
echo ""
echo "▸ Verifying site..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://www.historyfuturenow.com/" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo "  ✓ Site is live (HTTP $HTTP_STATUS)"
else
    echo "  ⚠ Site returned HTTP $HTTP_STATUS — check manually"
fi

# ─── Step 5: Log deployment ─────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG_FILE")"

if [ ! -f "$LOG_FILE" ]; then
    cat > "$LOG_FILE" << HEADER
# Daily Log: $(date +%Y-%m-%d)

## Entries

HEADER
fi

cat >> "$LOG_FILE" << ENTRY

### $(date +%H:%M) - #HistoryFutureNow [AUTO-DEPLOY]
**Tags:** #HistoryFutureNow #deploy
**Branch:** $BRANCH
**Commit:** $COMMIT_HASH — $COMMIT_MSG_ACTUAL
**Files:** $FILES_CHANGED
**Status:** complete

ENTRY

# ─── Step 6: Regenerate section intros in background ─────────────────────────
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "▸ Regenerating section intros in background..."
    (
        cd "$BUILD_DIR"
        if python3 generate_section_intros.py 2>&1 | tail -5; then
            python3 build.py 2>&1 | tail -3
            cd "$ROOT_DIR"
            if [ -n "$(git status --porcelain)" ]; then
                git add . && git commit -m "chore: update section editorial intros" && git push origin "$BRANCH"
                cd "$OUTPUT_DIR" && vercel --prod --yes 2>&1 | tail -3
                echo "  ✓ Section intros updated and deployed"
            else
                echo "  ✓ Section intros unchanged"
            fi
        else
            echo "  ⚠ Section intro generation failed (non-critical)"
        fi
    ) &
    echo "  (running in background, PID: $!)"
else
    echo ""
    echo "▸ Skipping section intro regeneration (ANTHROPIC_API_KEY not set)"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Deploy complete"
echo "  Branch: $BRANCH"
echo "  Commit: $COMMIT_HASH"
echo "  Site:   https://www.historyfuturenow.com"
echo "═══════════════════════════════════════════════════"

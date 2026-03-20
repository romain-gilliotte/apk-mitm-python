#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMMIT=$(cat "$PROJECT_ROOT/UPSTREAM_COMMIT")
TARGET_DIR="$PROJECT_ROOT/upstream"

if [ -d "$TARGET_DIR" ]; then
  echo "upstream/ already exists, checking commit..."
  CURRENT=$(git -C "$TARGET_DIR" rev-parse HEAD 2>/dev/null || echo "unknown")
  if [ "$CURRENT" = "$COMMIT" ]; then
    echo "Already at commit $COMMIT"
    exit 0
  fi
  echo "Removing stale upstream/ (was $CURRENT, want $COMMIT)"
  rm -rf "$TARGET_DIR"
fi

echo "Cloning apk-mitm at $COMMIT..."
git clone --no-checkout https://github.com/niklashigi/apk-mitm.git "$TARGET_DIR"
git -C "$TARGET_DIR" checkout "$COMMIT"
echo "Done. upstream/ is at $COMMIT"

#!/usr/bin/env bash
set -euo pipefail
PATCH="${1:-/dev/stdin}"
git apply --whitespace=fix "$PATCH"
echo "✅ Patch applied. Next: git add -A && git commit -m \"apply patch\""

#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/.."

docs=(
  AGENTS.md CHANGELOG.md CLAUDE.md CONTRIBUTING.md DISCLAIMER.md PRIVACY.md README.md RELEASE.md SECURITY.md
  pwa/README.md tests/FIXTURE_REVIEW.md
)
while IFS= read -r file; do docs+=("$file"); done < <(find prompts -type f -name '*.md' | sort)

scratch_dir="$(mktemp -d -t vehicle-maint-prose.XXXXXX)"
trap 'rm -rf -- "$scratch_dir"' EXIT
node pwa/scripts/extract-copy.mjs > "$scratch_dir/ui-copy.md" || exit 2

status=0
banned='delve|leverage|seamless|robust|testament|pivotal|tapestry|showcase|underscores?\b'
if grep -nE '—|\\u2014' "${docs[@]}" pwa/src/App.tsx "$scratch_dir/ui-copy.md"; then
  echo "prose guard: replace em dashes with direct punctuation"
  status=1
fi
if grep -niE "$banned" "${docs[@]}" pwa/src/App.tsx "$scratch_dir/ui-copy.md"; then
  echo "prose guard: replace generic AI-associated vocabulary with specific language"
  status=1
fi

if [ -x .venv/bin/slopscore-lint ]; then
  slopscore=.venv/bin/slopscore-lint
elif command -v slopscore-lint >/dev/null 2>&1; then
  slopscore=slopscore-lint
else
  echo "slopscore-lint is missing; run 'uv sync --extra dev --locked'"
  exit 2
fi

"$slopscore" scan "${docs[@]}" "$scratch_dir/ui-copy.md" \
  --profile technical --strictness conservative --fail-on high || status=1
"$slopscore" scan src --recursive \
  --profile technical --strictness conservative --fail-on high || status=1

slopless=pwa/node_modules/.bin/slopless
if [ ! -x "$slopless" ]; then
  echo "slopless is missing; run 'npm ci' in pwa/"
  exit 2
fi
"$slopless" "${docs[@]}" "$scratch_dir/ui-copy.md" > "$scratch_dir/slopless.json" 2>/dev/null || true
node scripts/filter-slopless.mjs < "$scratch_dir/slopless.json" || status=1

if [ "$status" -eq 0 ]; then
  echo "prose lint: PASS"
else
  echo "prose lint: FAIL; review evidence manually and do not auto-rewrite"
fi
exit "$status"

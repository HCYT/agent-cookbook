#!/bin/bash

set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
TEST_HOME=$(mktemp -d)
TEST_BIN=$(mktemp -d)
trap 'rm -rf "$TEST_HOME" "$TEST_BIN"' EXIT

mkdir -p "$TEST_HOME/.claude"
printf '{}\n' > "$TEST_HOME/.claude/settings.json"

cat > "$TEST_BIN/gemini" <<'EOF'
#!/bin/bash
echo "stub gemini"
EOF
chmod +x "$TEST_BIN/gemini"

HOME="$TEST_HOME" PATH="$TEST_BIN:$PATH" bash "$REPO_ROOT/scripts/install.sh"
HOME="$TEST_HOME" PATH="$TEST_BIN:$PATH" bash "$REPO_ROOT/scripts/install.sh"

HOOK_DIR="$TEST_HOME/.claude/hooks/agent-cookbook/claude-cache-safe-images"
SETTINGS_PATH="$TEST_HOME/.claude/settings.json"

test -x "$HOOK_DIR/intercept-image-read.sh"
test -x "$HOOK_DIR/image-describe.mjs"

jq -e --arg cmd "bash $HOOK_DIR/intercept-image-read.sh" '
  any(
    (.hooks.PreToolUse // [])[];
    .matcher == "Read"
    and any((.hooks // [])[]; .command == $cmd)
  )
' "$SETTINGS_PATH" >/dev/null

COUNT=$(jq -r --arg cmd "bash $HOOK_DIR/intercept-image-read.sh" '
  [
    (.hooks.PreToolUse // [])[]
    | select(.matcher == "Read")
    | (.hooks // [])[].command
    | select(. == $cmd)
  ] | length
' "$SETTINGS_PATH")

[ "$COUNT" = "1" ]

HOME="$TEST_HOME" PATH="$TEST_BIN:$PATH" bash "$REPO_ROOT/scripts/doctor.sh" >/dev/null

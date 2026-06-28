#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
RECIPE_DIR="$REPO_ROOT/hooks/claude-cache-safe-images"

SETTINGS_DIR="$HOME/.claude"
HOOK_DIR="$SETTINGS_DIR/hooks/agent-cookbook/claude-cache-safe-images"
SETTINGS_PATH="$SETTINGS_DIR/settings.json"
HOOK_COMMAND="bash $HOOK_DIR/intercept-image-read.sh"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing dependency: $1" >&2
    exit 1
  fi
}

require_cmd jq
require_cmd node
require_cmd "${VISION_CLI_BIN:-agy}"

mkdir -p "$HOOK_DIR"
mkdir -p "$SETTINGS_DIR"

cp "$RECIPE_DIR/hooks/intercept-image-read.sh" "$HOOK_DIR/intercept-image-read.sh"
cp "$RECIPE_DIR/hooks/image-describe.mjs" "$HOOK_DIR/image-describe.mjs"
chmod +x "$HOOK_DIR/intercept-image-read.sh" "$HOOK_DIR/image-describe.mjs"

if [ ! -f "$SETTINGS_PATH" ]; then
  printf '{}\n' > "$SETTINGS_PATH"
fi

TMP_SETTINGS=$(mktemp "${TMPDIR:-/tmp}/agent-cookbook-settings-XXXXXX.json")

jq --arg cmd "$HOOK_COMMAND" '
  .hooks = (.hooks // {})
  | .hooks.PreToolUse = (.hooks.PreToolUse // [])
  | if any(.hooks.PreToolUse[]?; .matcher == "Read") then
      .hooks.PreToolUse |= map(
        if .matcher == "Read" then
          .hooks = (.hooks // [])
          | if any(.hooks[]?; .command == $cmd) then
              .
            else
              .hooks += [{
                type: "command",
                command: $cmd,
                timeout: 60
              }]
            end
        else
          .
        end
      )
    else
      .hooks.PreToolUse += [{
        matcher: "Read",
        hooks: [{
          type: "command",
          command: $cmd,
          timeout: 60
        }]
      }]
    end
' "$SETTINGS_PATH" > "$TMP_SETTINGS"

mv "$TMP_SETTINGS" "$SETTINGS_PATH"

echo "installed recipe: claude-cache-safe-images"
echo "hook dir: $HOOK_DIR"
echo "settings updated: $SETTINGS_PATH"
echo "next: bash \"$REPO_ROOT/hooks/claude-cache-safe-images/scripts/doctor.sh\""

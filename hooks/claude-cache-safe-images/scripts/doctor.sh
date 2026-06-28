#!/bin/bash

set -euo pipefail

SETTINGS_PATH="$HOME/.claude/settings.json"
HOOK_DIR="$HOME/.claude/hooks/agent-cookbook/claude-cache-safe-images"
HOOK_COMMAND="bash $HOOK_DIR/intercept-image-read.sh"

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "ok   command: $1"
  else
    echo "fail command: $1"
    return 1
  fi
}

STATUS=0

check_cmd jq || STATUS=1
check_cmd node || STATUS=1
check_cmd "${VISION_CLI_BIN:-agy}" || STATUS=1

if [ -x "$HOOK_DIR/intercept-image-read.sh" ]; then
  echo "ok   file: $HOOK_DIR/intercept-image-read.sh"
else
  echo "fail file: $HOOK_DIR/intercept-image-read.sh"
  STATUS=1
fi

if [ -x "$HOOK_DIR/image-describe.mjs" ]; then
  echo "ok   file: $HOOK_DIR/image-describe.mjs"
else
  echo "fail file: $HOOK_DIR/image-describe.mjs"
  STATUS=1
fi

if [ -f "$SETTINGS_PATH" ]; then
  if jq -e --arg cmd "$HOOK_COMMAND" '
    any(
      (.hooks.PreToolUse // [])[];
      .matcher == "Read"
      and any((.hooks // [])[]; .command == $cmd)
    )
  ' "$SETTINGS_PATH" >/dev/null 2>&1; then
    echo "ok   settings: Read hook registered"
  else
    echo "fail settings: Read hook missing"
    STATUS=1
  fi
else
  echo "fail settings: $SETTINGS_PATH missing"
  STATUS=1
fi

if command -v tesseract >/dev/null 2>&1; then
  echo "ok   optional: tesseract"
else
  echo "warn optional: tesseract not found, OCR fallback disabled"
fi

if command -v sips >/dev/null 2>&1; then
  echo "ok   optional: sips"
else
  echo "warn optional: sips not found, resize shortcut disabled"
fi

exit "$STATUS"

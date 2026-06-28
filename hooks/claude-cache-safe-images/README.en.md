# Reduce Claude token consumption by converting images to text

[繁體中文說明](./README.md)

If your Claude workflow mixes text turns with image turns, image bytes (especially base64) dramatically inflate the token count on every turn, and multi-turn conversations resend the full history each time. A simple fix is to keep the main session text-only and turn images into short text descriptions before they enter the prompt.

This recipe gives you two ways to do that:

1. **Claude Read hook**
   Intercept local image reads and redirect them to a generated text file.
2. **Discord integration example**
   Describe Discord attachments first, then append the resulting text to your normal prompt instead of sending image blocks directly.

## Why this works

Images in a prompt create two concrete costs:

1. **Token bloat** — a single screenshot base64-encoded can consume thousands of tokens, and multi-turn conversations resend the full history on every turn ([Anthropic Vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)), so image bytes accumulate and requests grow heavier over time.
2. **Request size** — large image payloads increase transfer time and processing overhead per turn.

Converting an image into a short text description (typically a few hundred tokens) before it enters the main session dramatically reduces per-turn token consumption and request size.

## Included files

- `hooks/intercept-image-read.sh`
- `hooks/image-describe.mjs`
- `examples/claude-settings.json`
- `examples/discord-adapter.ts`

## Dependencies

Required:

- `jq`
- `node`
- Any vision-capable CLI or agent (defaults to `agy`). Anything that accepts `-p` prompts and `@path` image syntax works — `agy`, `codex`, `claude`, `devin`, `gemini`, or your own API wrapper. Switch via the `VISION_CLI_BIN` env var

Optional:

- `tesseract` for OCR fallback
- `sips` on macOS for pre-resize

## Approach

The pattern is intentionally simple:

1. Detect whether the target is an image.
2. Resize it if the local environment supports cheap resizing.
3. Run the vision CLI to get a compact semantic description.
4. Run OCR if available.
5. Write both outputs into a plain text file.
6. Feed that text file to Claude instead of the original image.

This keeps the main session free of raw image blocks and dramatically reduces token consumption.

## Install the Claude Read hook

### Fast path

If you already have `agy` (or another vision CLI), `node`, and `jq`:

```bash
cd hooks/claude-cache-safe-images
bash scripts/install.sh
bash scripts/doctor.sh
```

### Manual path

Copy the two hook files somewhere stable on your machine, then register the shell script as a `PreToolUse(Read)` hook in your Claude settings.

Example registration:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "bash /ABSOLUTE/PATH/TO/intercept-image-read.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

See [`examples/claude-settings.json`](./examples/claude-settings.json) for the same shape.

## What the installer does

- copies the hook files into `~/.claude/hooks/agent-cookbook/claude-cache-safe-images`
- makes both scripts executable
- creates `~/.claude/settings.json` if it does not exist
- registers the `PreToolUse(Read)` hook idempotently

The installer does not overwrite unrelated Claude settings.

## Supported environment variables

`VISION_CLI_BIN`
: Defaults to `agy`. Can be any vision CLI that supports `-p` prompts and `@path` image syntax.

`VISION_CLI_MODEL`
: Optional. If unset, the CLI's default model is used.

`OCR_BIN`
: Defaults to `tesseract`. Set to `none` to disable OCR.

`MAX_WIDTH`
: Defaults to `1400`

## Discord integration example

If your agent receives images over Discord, the same idea still applies:

- fetch the attachment
- save it to a temp file
- describe it first
- append the text result into the normal prompt

The example in [`examples/discord-adapter.ts`](./examples/discord-adapter.ts) keeps the shape minimal and does not depend on any project-specific session system.

## Direct use with subagents or `codex exec`

You do not need the Claude hook if you only want the image-to-text step itself.

### Direct CLI use

```bash
node hooks/claude-cache-safe-images/hooks/image-describe.mjs ./screenshot.png
```

### Feed the result into `codex exec`

```bash
IMG_TEXT="$(node hooks/claude-cache-safe-images/hooks/image-describe.mjs ./screenshot.png)"
codex exec "Treat the following as the screenshot content:\n\n$IMG_TEXT\n\nNow debug the issue."
```

### Feed the result into a subagent

Use the same pattern: describe the image first, then pass the text to the subagent prompt.

## Privacy notes

This public version intentionally avoids:

- hardcoded user paths
- private OAuth files
- private client IDs or secrets
- project-specific bot names
- repo-specific imports

If your original setup uses an internal OCR tool or calls a private API directly, keep those parts in your private environment and only share the integration interface and overall approach.

## Limitations

- **Not suitable when fine detail matters** — this approach compresses images into a short text summary of a few hundred tokens. If your task requires the agent to read precise image details (pixel-level UI comparisons, complex chart data, fine print), send the original image directly instead of using this recipe.
- OCR quality depends on your local OCR tool. `OCR_BIN` defaults to `tesseract` and the invocation is bound to the tesseract CLI interface (`$OCR_BIN <image> stdout`). To use a different OCR tool, you will need a compatible wrapper.
- Image paths are passed to the vision CLI via the `@path` syntax. Paths with special characters may need attention.
- The resize step is macOS-centric because `sips` is fast and usually pre-installed.
- Generated description files (`claude-image-desc-*.txt`) are intentionally left in the temp directory so the Claude hook can still read them after returning. Over time these may accumulate. You can clean them periodically: `find "${TMPDIR:-/tmp}" -name 'claude-image-desc-*' -mmin +60 -delete`
- The Discord integration example trusts the attachment `contentType` directly, but in practice Discord may return incorrect MIME types (e.g. labeling a JPEG as `image/png`). For more reliable detection, consider checking magic bytes instead.

# Fix Claude cache breakage caused by image inputs

[繁體中文說明](./README.md)

If your Claude workflow mixes text turns with image turns, cache reuse can become unstable in practice. A simple fix is to keep the main session text-only and turn images into short text descriptions before they enter the prompt.

This recipe gives you two ways to do that:

1. **Claude Read hook**
   Intercept local image reads and redirect them to a generated text file.
2. **Discord integration example**
   Describe Discord attachments first, then append the resulting text to your normal prompt instead of sending image blocks directly.

## Why this works

### Evidence 1: images can invalidate the cache

> Anthropic Prompt caching docs
>
> “Changes to `tool_choice` or the presence/absence of images anywhere in the prompt will invalidate the cache, requiring a new cache entry to be created.”
>
> Source:
> https://platform.claude.com/docs/en/build-with-claude/prompt-caching

This is the direct rule: if image presence changes anywhere in the prompt, the cache is invalidated.

### Evidence 2: multi-turn requests resend full history

> “each request resends the full conversation history”
>
> Anthropic Vision docs
>
> Source:
> https://platform.claude.com/docs/en/build-with-claude/vision

If those images stay in the history as base64 payloads, their bytes keep traveling on every turn.

### Put together, the practical meaning is straightforward

- images directly affect whether the cache stays valid;
- if image bytes keep traveling through multi-turn history, requests get heavier over time.

That is why this recipe converts images into compact text before they enter the main session.

## Included files

- `hooks/intercept-image-read.sh`
- `hooks/image-describe.mjs`
- `examples/claude-settings.json`
- `examples/discord-adapter.ts`

## Dependencies

Required:

- `jq`
- `node`
- `gemini` CLI already installed and authenticated

Optional:

- `tesseract` for OCR fallback
- `sips` on macOS for pre-resize

## Approach

The pattern is intentionally simple:

1. Detect whether the target is an image.
2. Resize it if the local environment supports cheap resizing.
3. Run Gemini vision to get a compact semantic description.
4. Run OCR if available.
5. Write both outputs into a plain text file.
6. Feed that text file to Claude instead of the original image.

This keeps the main session free of raw image blocks and usually preserves better cache behavior.

## Install the Claude Read hook

### Fast path

If you already have `gemini`, `node`, and `jq`:

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

`GEMINI_BIN`
: Defaults to `gemini`

`GEMINI_MODEL`
: Optional. If unset, the Gemini CLI default model is used.

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

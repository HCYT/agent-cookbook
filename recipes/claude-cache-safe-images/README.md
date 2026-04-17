# 有效解決 Claude cache 被破壞的問題

If your Claude workflow mixes text turns with image turns, cache reuse can become unstable in practice. A simple fix is to keep the main session text-only and turn images into short text descriptions before they enter the prompt.

This recipe gives you two ways to do that:

1. **Claude Read hook**
   Intercept local image reads and redirect them to a generated text file.
2. **Discord adapter example**
   Describe Discord attachments first, then append the resulting text to your normal prompt.

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

## Supported environment variables

`GEMINI_BIN`
: Defaults to `gemini`

`GEMINI_MODEL`
: Optional. If unset, the Gemini CLI default model is used.

`OCR_BIN`
: Defaults to `tesseract`. Set to `none` to disable OCR.

`MAX_WIDTH`
: Defaults to `1400`

## Discord adapter example

If your agent receives images over Discord, the same idea still applies:

- fetch the attachment
- save it to a temp file
- describe it first
- append the text result into the normal prompt

The example in [`examples/discord-adapter.ts`](./examples/discord-adapter.ts) shows the minimal shape without any project-specific session system.

## Privacy notes

This public version intentionally avoids:

- hard-coded user paths
- private OAuth files
- private client IDs or secrets
- project-specific bot names
- repo-specific imports

If your original implementation uses internal OCR tools or direct HTTP APIs, keep those private and expose only the integration contract here.

## Limitations

- OCR quality depends on your local OCR engine.
- Gemini CLI behavior can vary by installed version and configured default model.
- The example resize path is macOS-first because `sips` is cheap and already present there.
- The generated temp description files are intentionally left in your temp directory so Claude can read them after the hook returns.

# Generate Images via ChatGPT Responses API Using Codex OAuth

[繁體中文說明](./README.md)

If you have a ChatGPT Plus or Pro subscription, you can use the Codex CLI's OAuth to call ChatGPT's Responses API for image generation. No separate API credit needed — image generation runs against your existing subscription quota.

This recipe walks you through building an image generation script from scratch: authentication, single-image generation, and batch workflows.

## Why this approach

| | Standard OpenAI Images API | Codex OAuth + Responses API |
| --- | --- | --- |
| Auth | API key | OAuth (Codex CLI handles it) |
| Billing | Per-image | Uses ChatGPT subscription quota |
| Reference images | Supported | Supported |
| Prompt caching | No | Yes (`prompt_cache_key`) |
| Streaming | No | Yes (progressive image data) |

For subscribers, the Codex OAuth path is effectively free.

## Prerequisites

1. **ChatGPT Plus or Pro subscription**
2. **Codex CLI**:
   ```bash
   npm install -g @openai/codex
   ```
3. **Log in to get an OAuth token**:
   ```bash
   codex login
   ```
   The token is saved to `~/.codex/auth.json`.

## Auth structure

After `codex login`, `~/.codex/auth.json` looks like this:

```json
{
  "tokens": {
    "access_token": "eyJhbGci...",
    "account_id": "acct_xxxx..."
  }
}
```

Your script only needs these two values:

```python
import json, pathlib
auth = json.loads(pathlib.Path("~/.codex/auth.json").expanduser().read_text())
token = auth["tokens"]["access_token"]
account_id = auth["tokens"]["account_id"]
```

```typescript
import { readFileSync } from "node:fs";
const auth = JSON.parse(readFileSync(`${process.env.HOME}/.codex/auth.json`, "utf-8"));
const token = auth.tokens.access_token;
const accountId = auth.tokens.account_id;
```

> **Tokens expire.** If you get a 401 mid-run, just re-run `codex login`.

## API endpoint and headers

```
POST https://chatgpt.com/backend-api/codex/responses
```

Required headers:

| Header | Value | Purpose |
| --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | OAuth token |
| `Content-Type` | `application/json` | |
| `chatgpt-account-id` | `{account_id}` | Account ID |
| `OpenAI-Beta` | `responses=experimental` | Enable Responses API |
| `originator` | `codex_sdk_ts` | Source identifier |
| `User-Agent` | `codex_sdk_ts/0.130.0` | |
| `session_id` | Random UUID | Fresh per request |
| `x-client-request-id` | Same as session_id | |

## Request body

Minimal working body:

```json
{
  "model": "gpt-5.5",
  "store": false,
  "stream": true,
  "instructions": "Generate images immediately without text response.",
  "input": [
    {
      "role": "user",
      "content": [
        { "type": "input_text", "text": "your prompt here" }
      ]
    }
  ],
  "reasoning": { "effort": "low", "summary": "auto" },
  "tools": [{ "type": "image_generation", "output_format": "png" }]
}
```

### Adding reference images

To have the model reference an existing image, include its base64 before the text prompt:

```json
{
  "input": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_image",
          "image_url": "data:image/png;base64,{base64 of image}"
        },
        { "type": "input_text", "text": "Draw this character sitting in a cafe" }
      ]
    }
  ]
}
```

Multiple reference images are supported — just add more `input_image` entries.

### Prompt caching

When generating images in batch, set `prompt_cache_key` so the API caches the shared prefix (instructions, system message, etc.). Subsequent calls with the same key and prefix hit the cache:

```json
{
  "prompt_cache_key": "my-batch-v1",
  ...
}
```

## Streaming response

The API returns Server-Sent Events (SSE). Parse line by line:

```
data: {"type": "response.image_generation_call.partial_image", "partial_image": "base64..."}
data: {"type": "response.output_item.done", "item": {"type": "image_generation_call", "result": "full base64"}}
data: {"type": "response.completed", "response": {"usage": {...}}}
data: [DONE]
```

Key events:

| type | Meaning |
| --- | --- |
| `response.image_generation_call.partial_image` | Generation in progress (incomplete base64, useful for progress display) |
| `response.output_item.done` + `item.type === "image_generation_call"` | Generation complete. `item.result` is the full base64 |
| `response.output_item.done` + `item.type === "message"` | Text response (look for "cannot", "policy" — means the request was blocked) |
| `response.completed` | Request finished, includes usage info |

## Quickstart

### Single image — TypeScript

```bash
npx tsx examples/basic-gen.ts "anime girl at a cozy cafe, morning sunlight"
```

With a reference image:

```bash
npx tsx examples/basic-gen.ts "draw her at the beach" ./my-character.png sunset-beach
```

### Single image — Python

```bash
python examples/basic-gen.py "anime girl at a cozy cafe, morning sunlight"
```

With a reference image:

```bash
python examples/basic-gen.py "draw her at the beach" ./my-character.png sunset-beach
```

### Batch generation

Edit the `PROMPTS` dict in `examples/batch-gen.py`, then:

```bash
python examples/batch-gen.py
```

Features:
- Skips existing files (resumable)
- Writes JSON log per generation
- 3-second delay between requests
- Shows summary stats at the end

## Advanced tips

### Negative prompts

Append a negative prompt section to avoid unwanted elements:

```
Your positive description here

## Negative prompt:
bad anatomy, extra fingers, deformed hands, western face, plastic skin
```

### Controlling model behavior

`reasoning.effort` controls how much the model thinks:

- `"low"` — sufficient for image generation, fastest
- `"medium"` — default
- `"high"` — when complex reasoning is needed

### Token expiration

Tokens typically expire after a few hours. For batch scripts, handle 401 gracefully:

```python
if resp.status == 401:
    print("Token expired — please re-run `codex login`")
    sys.exit(1)
```

## Included examples

| File | Language | Purpose |
| --- | --- | --- |
| [`examples/basic-gen.ts`](./examples/basic-gen.ts) | TypeScript | Minimal single-image generation |
| [`examples/basic-gen.py`](./examples/basic-gen.py) | Python | Minimal single-image generation |
| [`examples/batch-gen.py`](./examples/batch-gen.py) | Python | Batch generation with logging and resume |

## Privacy notes

These examples intentionally avoid:

- Hardcoded user paths
- Private OAuth tokens
- Project-specific prompts or character settings
- Internal bot names

If your project uses character reference sheets, specific negative prompt templates, or other internal resources, wrap these examples in your own project-specific layer.

## Limitations

- Tokens expire. Long batch runs need 401 handling.
- Image generation is subject to ChatGPT content policy. Blocked requests return text instead of images.
- `prompt_cache_key` caching is server-controlled and not guaranteed to hit.
- Streaming `partial_image` events contain incomplete base64 — only save from the `output_item.done` event.
- Base64 reference images make request bodies large. A single PNG is roughly 1–5 MB in base64. Watch request size when using multiple references.

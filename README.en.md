# Agent Cookbook

[繁體中文 README](./README.md)

Practical recipes for making coding agents cheaper, safer, and easier to operate.

This repository starts with one small chapter and leaves room for many more:

## Repository sections

- [`hooks/`](./hooks/) for executable hooks, interceptors, and operational scripts
- [`prompt-engineering/`](./prompt-engineering/) for prompt templates and prompt assembly patterns
- [`context-engineering/`](./context-engineering/) for memory, summarization, compression, and context-loading patterns

## Current entries

| Section | Recipe | What it solves |
| --- | --- | --- |
| Hooks | [`claude-cache-safe-images`](./hooks/claude-cache-safe-images/README.en.md) | Effective ways to stop image inputs from wrecking Claude cache reuse |

## Why this repo exists

Many useful agent improvements are too small for a full framework but too valuable to stay buried inside one private codebase. This cookbook packages those improvements as reusable scripts, examples, and short integration guides.

## What you will find here

- Copy-pasteable hooks
- Minimal integration examples
- Opinionated setup notes
- Public-safe versions of patterns that originally lived inside larger systems

## Current focus

The first recipe lives under `hooks/`:

**Fix Claude cache breakage caused by image inputs**

It covers two practical patterns:

1. A Claude `Read` hook that intercepts image reads and converts them into text descriptions before they enter the main session.
2. A Discord adapter example that describes attachments first, then appends text into the prompt instead of pushing raw image blocks.

## Quickstart

If you already have `gemini`, `node`, and `jq`, the current recipe is close to plug-and-play:

```bash
git clone <repo-url>
cd agent-cookbook
bash scripts/install.sh
bash scripts/doctor.sh
```

That installs the Claude `Read` hook into `~/.claude/hooks/agent-cookbook/claude-cache-safe-images` and updates `~/.claude/settings.json` for you.

## License

MIT

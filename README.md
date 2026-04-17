# Agent Cookbook

Practical recipes for making coding agents cheaper, safer, and easier to operate.

This repository starts with one small chapter and leaves room for many more:

| Recipe | What it solves |
| --- | --- |
| [`claude-cache-safe-images`](./recipes/claude-cache-safe-images/README.md) | Effective ways to stop image inputs from wrecking Claude cache reuse |

## Why this repo exists

Many useful agent improvements are too small for a full framework but too valuable to stay buried inside one private codebase. This cookbook packages those improvements as reusable scripts, examples, and short integration guides.

## What you will find here

- Copy-pasteable hooks
- Minimal integration examples
- Opinionated setup notes
- Public-safe versions of patterns that originally lived inside larger systems

## Current focus

The first recipe is titled:

**有效解決 Claude cache 被破壞的問題**

It covers two practical patterns:

1. A Claude `Read` hook that intercepts image reads and converts them into text descriptions before they enter the main session.
2. A Discord adapter example that describes attachments first, then appends text into the prompt instead of pushing raw image blocks.

## License

MIT

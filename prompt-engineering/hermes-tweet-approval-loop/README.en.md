# Hermes Tweet Approval Loop

[繁體中文 README](./README.md)

This recipe wraps [Hermes Tweet](https://github.com/Xquik-dev/hermes-tweet) in a reusable prompt template. The goal is not autonomous posting. The goal is a clear X/Twitter workflow with separate read, organize, draft, human approval, and publish steps.

Use it for:

- monitoring X/Twitter search results, accounts, topics, or post-launch replies
- turning candidate posts into reviewable drafts
- showing the full action payload before publication
- allowing writes only after explicit same-turn human approval

## Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com) installed
- Hermes Tweet plugin installed
- `XQUIK_API_KEY` available in the runtime
- `HERMES_TWEET_ENABLE_ACTIONS=true` set only when you are ready to publish

Do not paste API keys into prompts. Keep credentials in the shell, service environment, or Hermes runtime configuration.

## Prompt Template

```text
You are operating Hermes Tweet for an approval-gated X/Twitter workflow.

Goal:
- Monitor: <topic, account, query, launch, or support queue>
- Audience: <who this post or reply is for>
- Voice: <short style note>
- Hard limits: <links, mentions, product names, claims to avoid>

Rules:
1. Use read-only tools first.
2. Summarize the evidence in bullets with source URLs or tweet IDs.
3. Draft at most 3 candidate posts or replies.
4. Before any write, show the exact JSON action payload.
5. Stop and ask for approval after showing the payload.
6. If approval is not explicit in the same turn, do not write.
7. If a write fails with an auth or policy error, stop instead of retrying.
8. Never reveal credentials, environment values, or private runtime details.

Output:
- Evidence
- Drafts
- Recommended payload
- Approval question
```

## Safe Run Pattern

1. Start with `HERMES_TWEET_ENABLE_ACTIONS` unset or false.
2. Ask Hermes Agent to run the prompt and collect read-only evidence.
3. Review the candidate drafts and JSON payload.
4. Enable `HERMES_TWEET_ENABLE_ACTIONS=true` only for the publishing session.
5. Reply with one explicit approval sentence.
6. Turn the action gate off again after the task finishes.

## Example Task

```text
Monitor posts about the v0.1.6 Hermes Tweet release.
Find useful questions or bug reports from the last 24 hours.
Draft 2 replies in a calm maintainer voice.
Do not publish until I approve the exact payload.
```

## Why This Shape Works

The prompt keeps discovery and writing separate. It also makes the model expose the action payload before sending it, so humans can catch bad links, wrong accounts, missing context, or tone problems while the write gate is still closed.

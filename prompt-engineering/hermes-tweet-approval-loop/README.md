# Hermes Tweet approval loop

[English README](./README.en.md)

這篇 recipe 把 [Hermes Tweet](https://github.com/Xquik-dev/hermes-tweet) 包成一個可重用的 prompt 模板。重點不是讓 agent 自動發文，而是把 X/Twitter 任務拆成「讀取、整理、草稿、人工核准、發布」幾個清楚步驟。

適合用在：

- 監看 X/Twitter 搜尋結果、帳號、話題或發布後回覆
- 把候選貼文整理成可審核草稿
- 發布前先列出完整動作 payload
- 只有人在同一輪明確核准後才允許寫入動作

## 前置條件

- 已安裝 [Hermes Agent](https://hermes-agent.nousresearch.com)
- 已安裝 Hermes Tweet plugin
- runtime 裡有 `XQUIK_API_KEY`
- 只有要真的發布時才設定 `HERMES_TWEET_ENABLE_ACTIONS=true`

不要把 API key 貼進 prompt。把憑證放在 shell、服務環境變數或 Hermes runtime 設定裡。

## Prompt 模板

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

## Safe run pattern

1. Start with `HERMES_TWEET_ENABLE_ACTIONS` unset or false.
2. Ask Hermes Agent to run the prompt and collect read-only evidence.
3. Review the candidate drafts and JSON payload.
4. Enable `HERMES_TWEET_ENABLE_ACTIONS=true` only for the publishing session.
5. Reply with one explicit approval sentence.
6. Turn the action gate off again after the task finishes.

## Example task

```text
Monitor posts about the v0.1.6 Hermes Tweet release.
Find useful questions or bug reports from the last 24 hours.
Draft 2 replies in a calm maintainer voice.
Do not publish until I approve the exact payload.
```

## Why this shape works

The prompt keeps discovery and writing separate. It also makes the model expose the action payload before sending it, so humans can catch bad links, wrong accounts, missing context, or tone problems while the write gate is still closed.

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

## 安全執行模式

1. 一開始先不設定 `HERMES_TWEET_ENABLE_ACTIONS`，或將其設為 false。
2. 讓 Hermes Agent 執行 prompt 並收集唯讀證據。
3. 審查候選草稿和 JSON payload。
4. 只在準備發布的 session 啟用 `HERMES_TWEET_ENABLE_ACTIONS=true`。
5. 回覆一句明確的核准語句。
6. 任務完成後，再次關閉寫入權限。

## 範例任務

```text
Monitor posts about the v0.1.6 Hermes Tweet release.
Find useful questions or bug reports from the last 24 hours.
Draft 2 replies in a calm maintainer voice.
Do not publish until I approve the exact payload.
```

## 為什麼這種模式有效

這個 prompt 會把探索與寫入分開。它也要求模型在送出前先展示 action payload，讓人在寫入權限仍關閉時，就能發現錯誤連結、錯誤帳號、缺少上下文或語氣不合適的問題。

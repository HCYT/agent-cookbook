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
你正在操作 Hermes Tweet，處理需要核准的 X/Twitter 工作流。

目標：
- 監看：<話題、帳號、查詢、發布活動或支援佇列>
- 受眾：<這篇貼文或回覆要給誰看>
- 語氣：<簡短風格說明>
- 硬性限制：<避免使用的連結、提及、產品名稱或聲明>

規則：
1. 先使用唯讀工具。
2. 用條列整理證據，附上來源 URL 或 tweet ID。
3. 最多草擬 3 則候選貼文或回覆。
4. 任何寫入前，先展示完整 JSON action payload。
5. 展示 payload 後停止，並詢問是否核准。
6. 如果同一輪沒有明確核准，不要寫入。
7. 如果寫入因認證或政策錯誤失敗，停止，不要重試。
8. 永遠不要揭露憑證、環境變數值或私有 runtime 細節。

輸出：
- 證據
- 草稿
- 建議 payload
- 核准問題
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
監看最近 24 小時內關於 Hermes Tweet v0.1.6 發布的貼文。
找出有價值的問題或 bug 回報。
用冷靜的維護者語氣草擬 2 則回覆。
在我核准完整 payload 前，不要發布。
```

## 為什麼這種模式有效

這個 prompt 會把探索與寫入分開。它也要求模型在送出前先展示 action payload，讓人在寫入權限仍關閉時，就能發現錯誤連結、錯誤帳號、缺少上下文或語氣不合適的問題。

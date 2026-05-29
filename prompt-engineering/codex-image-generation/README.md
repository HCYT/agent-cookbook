# 用 Codex OAuth 呼叫 ChatGPT 生圖 API

[English README](./README.en.md)

如果你有 ChatGPT Plus / Pro 訂閱，其實可以用 Codex CLI 的 OAuth 機制，直接呼叫 ChatGPT 的 Responses API 來生圖。不用另外買 API credit，也不用管 API key — 訂閱裡的圖就是你的額度。

這篇教你怎麼從零開始寫一個生圖腳本，從認證、單張生成、到批次跑圖都有。

## 為什麼用這招

| | 標準 OpenAI Images API | Codex OAuth + Responses API |
| --- | --- | --- |
| 認證方式 | API key | OAuth（Codex CLI 幫你處理） |
| 計費 | 每張另計 | 走 ChatGPT 訂閱額度 |
| 參考圖 | 支援 | 支援 |
| Prompt 快取 | 無 | 有（`prompt_cache_key`） |
| 串流回傳 | 無 | 有（邊生邊拿進度） |

對已經有訂閱的人來說，Codex OAuth 這條路基本上是免費的。

## 前置準備

1. **ChatGPT Plus 或 Pro 訂閱**
2. **Codex CLI** — 安裝方式：
   ```bash
   npm install -g @anthropic-ai/codex  # 不是這個
   npm install -g @openai/codex         # 是這個
   ```
3. **登入取得 OAuth token**：
   ```bash
   codex login
   ```
   登入後 token 會自動存到 `~/.codex/auth.json`。

## 認證結構

`codex login` 跑完之後，`~/.codex/auth.json` 長這樣：

```json
{
  "tokens": {
    "access_token": "eyJhbGci...",
    "account_id": "acct_xxxx..."
  }
}
```

你的腳本只需要讀這兩個值：

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

> **Token 會過期。** 如果跑到一半拿到 401，重新 `codex login` 就好。

## API 端點與 Headers

```
POST https://chatgpt.com/backend-api/codex/responses
```

必要 Headers：

| Header | 值 | 說明 |
| --- | --- | --- |
| `Authorization` | `Bearer {access_token}` | OAuth token |
| `Content-Type` | `application/json` | |
| `chatgpt-account-id` | `{account_id}` | 帳號 ID |
| `OpenAI-Beta` | `responses=experimental` | 啟用 Responses API |
| `originator` | `codex_sdk_ts` | 標記來源 |
| `User-Agent` | `codex_sdk_ts/0.130.0` | |
| `session_id` | 隨機 UUID | 每次呼叫換一個 |
| `x-client-request-id` | 同 session_id | |

## Request Body

最小可用的 body：

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
        { "type": "input_text", "text": "你的 prompt" }
      ]
    }
  ],
  "reasoning": { "effort": "low", "summary": "auto" },
  "tools": [{ "type": "image_generation", "output_format": "png" }]
}
```

### 加參考圖

如果要讓模型參考一張圖來畫，把圖的 base64 放在 prompt 前面：

```json
{
  "input": [
    {
      "role": "user",
      "content": [
        {
          "type": "input_image",
          "image_url": "data:image/png;base64,{圖片的 base64}"
        },
        { "type": "input_text", "text": "根據這張角色設定，畫出她在咖啡廳的樣子" }
      ]
    }
  ]
}
```

可以放多張參考圖，依序加 `input_image` 就好。

### Prompt 快取

批次跑圖的時候，加上 `prompt_cache_key` 可以讓 API 端快取共用的 prefix（instructions、system message 等），後面的圖只需要重新算變動的部分：

```json
{
  "prompt_cache_key": "my-batch-v1",
  ...
}
```

同一個 `prompt_cache_key` + 相同的 instructions / ref 圖 → 後續呼叫會命中快取，回應更快。

## 串流回應解析

API 回傳 Server-Sent Events（SSE），你需要逐行解析：

```
data: {"type": "response.image_generation_call.partial_image", "partial_image": "base64..."}
data: {"type": "response.output_item.done", "item": {"type": "image_generation_call", "result": "完整 base64"}}
data: {"type": "response.completed", "response": {"usage": {...}}}
data: [DONE]
```

要注意的事件：

| type | 意義 |
| --- | --- |
| `response.image_generation_call.partial_image` | 生圖進度（不完整的 base64，可以用來顯示進度條） |
| `response.output_item.done` + `item.type === "image_generation_call"` | 生圖完成，`item.result` 是完整的 base64 |
| `response.output_item.done` + `item.type === "message"` | 文字回應（如果出現 "cannot"、"policy" 等字就是被擋了） |
| `response.completed` | 整個請求結束，帶 usage 資訊 |

## 快速開始

### 單張生成 — TypeScript

```bash
npx tsx examples/basic-gen.ts "anime girl at a cozy cafe, morning sunlight"
```

帶參考圖：

```bash
npx tsx examples/basic-gen.ts "畫出她在海邊的樣子" ./my-character.png sunset-beach
```

### 單張生成 — Python

```bash
python examples/basic-gen.py "anime girl at a cozy cafe, morning sunlight"
```

帶參考圖：

```bash
python examples/basic-gen.py "畫出她在海邊的樣子" ./my-character.png sunset-beach
```

### 批次生成

編輯 `examples/batch-gen.py` 裡的 `PROMPTS` dict，然後：

```bash
python examples/batch-gen.py
```

特點：
- 已存在的圖會自動跳過（斷點續跑）
- 每張生成後寫 JSON log
- 每張之間 sleep 3 秒避免打太快
- 結束顯示統計

## 進階技巧

### Negative prompt

在 prompt 最後加上 negative prompt 可以避免不想要的元素：

```
你的正面描述

## Negative prompt:
bad anatomy, extra fingers, deformed hands, western face, plastic skin
```

### 控制模型行為

`reasoning.effort` 控制模型花多少力氣思考：

- `"low"` — 生圖用這個就夠，快
- `"medium"` — 預設
- `"high"` — 需要複雜推理時用

### Token 過期處理

Token 通常幾小時就過期。批次腳本建議加重試邏輯：

```python
if resp.status == 401:
    print("Token 過期 — 請重新 codex login")
    sys.exit(1)
```

或是包一層自動重新登入（進階）。

## 包含的範例

| 檔案 | 語言 | 用途 |
| --- | --- | --- |
| [`examples/basic-gen.ts`](./examples/basic-gen.ts) | TypeScript | 最小可用的單張生成 |
| [`examples/basic-gen.py`](./examples/basic-gen.py) | Python | 最小可用的單張生成 |
| [`examples/batch-gen.py`](./examples/batch-gen.py) | Python | 批次生成 + log + 斷點續跑 |

## 隱私說明

範例裡沒有：

- 寫死的使用者路徑
- 私有 OAuth token
- 專案專屬 prompt 或角色設定
- 內部 bot 名稱

如果你的專案有角色設定圖、特定 negative prompt 模板、或其他內部資源，建議在自己的 repo 裡包一層 wrapper，引用這邊的核心邏輯。

## 限制

- Token 會過期，長時間批次需要處理 401。
- 圖片生成結果受 ChatGPT 內容政策限制。被擋的請求不會回傳圖片，只會拿到文字回應。
- `prompt_cache_key` 的快取行為由 API 端控制，不保證每次都命中。
- Streaming 回應的 partial_image 是不完整的 base64，不能直接存檔，要等 `output_item.done` 事件。
- base64 傳參考圖會讓 request body 很大。單張 PNG 大概 1-5 MB base64，多張參考圖記得注意 request 大小。

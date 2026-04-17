# 有效解決 Claude cache 被破壞的問題

[English README](./README.en.md)

如果你的 Claude 使用流程會在文字對話中夾帶圖片，實務上很容易把快取打亂，讓後面的 cache 命中率掉下來。最直接的做法，就是讓主 session 維持純文字，把圖片先轉成精簡的文字描述，再送進 prompt。

這篇 recipe 提供兩種做法：

1. **Claude Read hook**
   攔截本機圖片讀取，讓 `Read` 改去讀一份動態產生的文字描述檔。
2. **Discord 串接範例**
   先描述 Discord 附件，再把文字補回一般 prompt，而不是直接送圖片區塊。

## 為什麼這招有效

Anthropic 官方文件其實已經把關鍵講得很明白：

> “Changes to `tool_choice` or the presence/absence of images anywhere in the prompt will invalidate the cache, requiring a new cache entry to be created.”
>
> 來源：Anthropic Prompt caching docs
> https://platform.claude.com/docs/en/build-with-claude/prompt-caching

另外在 Vision 文件裡也有提到：

> “each request resends the full conversation history”
>
> 來源：Anthropic Vision docs
> https://platform.claude.com/docs/en/build-with-claude/vision

把這兩句放在一起看，意思就很直接了：

- 圖片本身會影響 cache 能不能繼續命中
- 多輪對話時，圖片如果一直留在歷史裡，request 也會越來越肥

所以這篇 recipe 的核心策略，就是先把圖片轉成精簡文字，再把文字送進主 session。這樣可以同時減少 cache 失效機率，也能把 request 大小壓下來。

## 內容包含

- `hooks/intercept-image-read.sh`
- `hooks/image-describe.mjs`
- `examples/claude-settings.json`
- `examples/discord-adapter.ts`

## 先準備這些

必要：

- `jq`
- `node`
- `gemini` CLI，且已登入可用

選配：

- `tesseract`，拿來補 OCR
- `sips`，在 macOS 上先做縮圖

## 核心做法

整體流程刻意壓得很簡單：

1. 判斷目標是不是圖片。
2. 如果本機支援快速縮圖，就先縮小。
3. 用 Gemini vision 產生精簡的語意描述。
4. 如果有 OCR，就一起補文字。
5. 把兩者寫成純文字檔。
6. 讓 Claude 讀這份文字檔，而不是原始圖片。

這樣主 session 就不用夾帶原始圖片區塊，通常能把 cache 表現維持得比較穩。

## 安裝 Claude Read hook

### 快速路徑

如果你已經裝好 `gemini`、`node`、`jq`：

```bash
cd hooks/claude-cache-safe-images
bash scripts/install.sh
bash scripts/doctor.sh
```

### 手動路徑

把這兩個 hook 檔案放到機器上的固定位置，然後在 Claude settings 裡把它註冊成 `PreToolUse(Read)` hook。

註冊範例：

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

可以參考 [`examples/claude-settings.json`](./examples/claude-settings.json)。

## Installer 會幫你做什麼

- 把 hook 複製到 `~/.claude/hooks/agent-cookbook/claude-cache-safe-images`
- 自動補上執行權限
- 如果 `~/.claude/settings.json` 不存在就建立
- 以 idempotent 方式註冊 `PreToolUse(Read)` hook

Installer 不會去改你其他不相干的 Claude 設定。

## 可調整的環境變數

`GEMINI_BIN`
: 預設是 `gemini`

`GEMINI_MODEL`
: 選填。不設的話，就沿用 Gemini CLI 目前的預設模型

`OCR_BIN`
: 預設是 `tesseract`。設成 `none` 可關閉 OCR

`MAX_WIDTH`
: 預設 `1400`

## Discord 串接範例

如果你的 agent 會從 Discord 收圖片，做法其實也一樣：

- 先抓附件
- 存成暫存檔
- 先轉文字描述
- 再把描述文字補進原本的 prompt

[`examples/discord-adapter.ts`](./examples/discord-adapter.ts) 提供的是一個最小可改寫版本，不綁任何特定的 session 架構。

## 直接拿去配 subagent 或 `codex exec`

如果你只想用「圖片先轉文字」這一步，其實不一定要掛 Claude hook。

### 直接 CLI 使用

```bash
node hooks/claude-cache-safe-images/hooks/image-describe.mjs ./screenshot.png
```

### 丟給 `codex exec`

```bash
IMG_TEXT="$(node hooks/claude-cache-safe-images/hooks/image-describe.mjs ./screenshot.png)"
codex exec "Treat the following as the screenshot content:\n\n$IMG_TEXT\n\nNow debug the issue."
```

### 丟給 subagent

做法也一樣：先把圖片轉成文字，再把那段文字放進 subagent prompt。這樣上層協調流程還是能保住比較好的 cache 表現，同時又留住足夠的視覺資訊。

## 隱私說明

這個公開版刻意避開：

- 寫死的使用者路徑
- 私有 OAuth 檔案
- 私有 client ID / secret
- 專案專屬 bot 名稱
- repo 專屬 import

如果你原本的版本有內部 OCR 工具，或是直接串私有 API，建議那些部分繼續留在私有環境，只把整合介面和整體做法公開出來。

## 限制

- OCR 品質會受你本機 OCR 工具影響。
- Gemini CLI 行為會受安裝版本與預設模型影響。
- 目前縮圖流程比較偏 macOS，因為 `sips` 很快，而且系統通常就有。
- 產生的暫存描述檔會刻意留在 temp 目錄，這樣 Claude hook 回傳之後還讀得到。

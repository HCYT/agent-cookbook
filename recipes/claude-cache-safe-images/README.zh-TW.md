# 有效解決 Claude cache 被破壞的問題

[English README](./README.md)

如果你的 Claude workflow 會在文字對話中混入圖片，實務上很容易讓 cache reuse 變差。最直接的解法就是讓主 session 保持純文字，把圖片先轉成短文字描述，再送進 prompt。

這篇 recipe 提供兩種做法：

1. **Claude Read hook**
   攔截本機圖片讀取，把 `Read` 轉向到一份動態產生的文字描述檔。
2. **Discord adapter 範例**
   先描述 Discord 附件，再把文字附加到正常 prompt，而不是直接送圖片 block。

## 內容包含

- `hooks/intercept-image-read.sh`
- `hooks/image-describe.mjs`
- `examples/claude-settings.json`
- `examples/discord-adapter.ts`

## 相依需求

必要：

- `jq`
- `node`
- `gemini` CLI，且已登入可用

選用：

- `tesseract` 作為 OCR fallback
- `sips`，在 macOS 上做預縮圖

## 核心做法

流程刻意保持簡單：

1. 判斷目標是不是圖片。
2. 如果本機支援便宜縮圖，就先縮小。
3. 用 Gemini vision 產生短語義描述。
4. 如果有 OCR，就一起補文字。
5. 把兩者寫成純文字檔。
6. 讓 Claude 讀這份文字檔，而不是原始圖片。

這樣主 session 就不需要攜帶 raw image blocks，通常能保留更穩定的 cache 行為。

## 安裝 Claude Read hook

### 快速路徑

如果你已經安裝好 `gemini`、`node`、`jq`：

```bash
bash scripts/install.sh
bash scripts/doctor.sh
```

### 手動路徑

把這兩個 hook 檔案放到你機器上的固定位置，然後在 Claude settings 中註冊成 `PreToolUse(Read)` hook。

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

## Installer 會做什麼

- 把 hook 複製到 `~/.claude/hooks/agent-cookbook/claude-cache-safe-images`
- 自動補上執行權限
- 如果 `~/.claude/settings.json` 不存在就建立
- 以 idempotent 方式註冊 `PreToolUse(Read)` hook

Installer 不會覆蓋你其他不相關的 Claude 設定。

## 可調整的環境變數

`GEMINI_BIN`
: 預設是 `gemini`

`GEMINI_MODEL`
: 選填。不設就使用 Gemini CLI 目前預設模型

`OCR_BIN`
: 預設是 `tesseract`。設成 `none` 可關閉 OCR

`MAX_WIDTH`
: 預設 `1400`

## Discord adapter 範例

如果你的 agent 是從 Discord 收圖，做法一樣成立：

- 先抓附件
- 存成暫存檔
- 先轉文字描述
- 再把描述文字補進原本的 prompt

[`examples/discord-adapter.ts`](./examples/discord-adapter.ts) 展示的是最小可改寫版本，不依賴任何特定 session 架構。

## 直接拿去配 subagent 或 `codex exec`

如果你只想要「圖片先轉文字」這一步，其實不一定要掛 Claude hook。

### 直接 CLI 使用

```bash
node recipes/claude-cache-safe-images/hooks/image-describe.mjs ./screenshot.png
```

### 丟給 `codex exec`

```bash
IMG_TEXT="$(node recipes/claude-cache-safe-images/hooks/image-describe.mjs ./screenshot.png)"
codex exec "Treat the following as the screenshot content:\n\n$IMG_TEXT\n\nNow debug the issue."
```

### 丟給 subagent

也是同樣模式：先把圖片轉成文字，再把那段文字放進 subagent prompt。這樣 orchestration layer 可以維持 cache-friendly，同時保留足夠的視覺資訊。

## 隱私說明

這個公開版刻意避開：

- 寫死的使用者路徑
- 私有 OAuth 檔案
- 私有 client ID / secret
- 專案專屬 bot 名稱
- repo 專屬 import

如果你原本的版本有內部 OCR 工具或直接打私有 API，建議那些仍留在私有環境，只公開整合介面與模式。

## 限制

- OCR 品質取決於你本機的 OCR engine。
- Gemini CLI 行為會受安裝版本與預設模型影響。
- 目前縮圖路徑偏 macOS，因為 `sips` 夠便宜而且預設就有。
- 產生的暫存描述檔會故意保留在 temp 目錄，讓 Claude hook 回傳後仍能讀到。

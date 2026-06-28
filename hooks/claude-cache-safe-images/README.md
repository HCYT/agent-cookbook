# 用圖片轉文字降低 Claude token 消耗

[English README](./README.en.md)

如果你的 Claude 使用流程會在文字對話中夾帶圖片，圖片 bytes（尤其是 base64）會大幅拉高每一輪的 token 消耗，而且在多輪對話中會隨著歷史一起重送。最直接的做法，就是讓主 session 維持純文字，把圖片先轉成精簡的文字描述，再送進 prompt。

這篇 recipe 提供兩種做法：

1. **Claude Read hook**
   攔截本機圖片讀取，讓 `Read` 改去讀一份動態產生的文字描述檔。
2. **Discord 串接範例**
   先描述 Discord 附件，再把文字補回一般 prompt，而不是直接送圖片區塊。

## 為什麼這招有效

圖片進入 prompt 會造成兩個實際成本：

1. **Token 膨脹** — 一張截圖 base64 編碼後可以吃掉數千 token，而多輪對話每一輪都會重送完整歷史（[Anthropic Vision docs](https://platform.claude.com/docs/en/build-with-claude/vision)），圖片 bytes 跟著累積，request 越來越肥。
2. **request 大小** — 圖片 payload 拉高每一輪的傳輸量和處理時間。

把圖片先轉成一段精簡文字（通常幾百 token），再送進主 session，就能大幅壓低每一輪的 token 消耗和 request 大小。

## 內容包含

- `hooks/intercept-image-read.sh`
- `hooks/image-describe.mjs`
- `examples/claude-settings.json`
- `examples/discord-adapter.ts`

## 先準備這些

必要：

- `jq`
- `node`
- 任何支援 vision 的 CLI 或 agent（預設 `agy`）。只要能接受 `-p` prompt 和 `@path` 圖片語法的工具都行，例如 `agy`、`codex`、`claude`、`devin`、`gemini`，或自己包的 API wrapper。透過 `VISION_CLI_BIN` 環境變數切換

選配：

- `tesseract`，拿來補 OCR
- `sips`，在 macOS 上先做縮圖

## 核心做法

整體流程刻意壓得很簡單：

1. 判斷目標是不是圖片。
2. 如果本機支援快速縮圖，就先縮小。
3. 用 vision CLI 產生精簡的語意描述。
4. 如果有 OCR，就一起補文字。
5. 把兩者寫成純文字檔。
6. 讓 Claude 讀這份文字檔，而不是原始圖片。

這樣主 session 就不用夾帶原始圖片區塊，token 消耗可以大幅降低。

## 安裝 Claude Read hook

### 快速路徑

如果你已經裝好 `agy`（或其他 vision CLI）、`node`、`jq`：

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

`VISION_CLI_BIN`
: 預設是 `agy`。可以換成任何支援 `-p` prompt 和 `@path` 圖片語法的 vision CLI

`VISION_CLI_MODEL`
: 選填。不設的話，就沿用該 CLI 的預設模型

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

做法也一樣：先把圖片轉成文字，再把那段文字放進 subagent prompt。這樣可以大幅降低 token 消耗，同時又留住足夠的視覺資訊。

## 隱私說明

這個公開版刻意避開：

- 寫死的使用者路徑
- 私有 OAuth 檔案
- 私有 client ID / secret
- 專案專屬 bot 名稱
- repo 專屬 import

如果你原本的版本有內部 OCR 工具，或是直接串私有 API，建議那些部分繼續留在私有環境，只把整合介面和整體做法公開出來。

## 限制

- **不適合需要細節的場景** — 這個做法把圖片壓成幾百 token 的文字摘要，如果你的任務需要 agent 讀取圖片裡的精確細節（像素級 UI 比對、複雜圖表數據、細小文字），應該直接送原始圖片，不要用摘要。
- OCR 品質會受你本機 OCR 工具影響。`OCR_BIN` 預設是 `tesseract`，且呼叫方式綁定 tesseract CLI 介面（`$OCR_BIN <image> stdout`）。如果要換成別的 OCR 工具，需要自己包一層相容的 wrapper。
- Vision CLI 行為會受安裝版本與預設模型影響。圖片路徑透過 `@path` 語法傳入 CLI，如果路徑含有特殊字元可能需要注意。
- 目前縮圖流程比較偏 macOS，因為 `sips` 很快，而且系統通常就有。
- 產生的暫存描述檔（`claude-image-desc-*.txt`）會刻意留在 temp 目錄，這樣 Claude hook 回傳之後還讀得到。長時間運作下來可能會累積，可以定期清理：`find "${TMPDIR:-/tmp}" -name 'claude-image-desc-*' -mmin +60 -delete`
- Discord 串接範例直接信任附件的 `contentType`，但實務上 Discord 回傳的 MIME type 不一定正確（例如 JPEG 檔標成 `image/png`）。如果需要更穩的判斷，建議改用 magic bytes 偵測實際格式。

# 生圖 Prompt 實戰策略

[English README](./README.en.md)

上一篇 [`codex-image-generation`](../codex-image-generation/README.md) 教你怎麼接 API。這篇講的是 prompt 怎麼寫，才能從「能生圖」進步到「穩定生出好圖」。

所有策略都從實際跑了幾百張圖的經驗萃取出來。不是理論，是每一條都有通過率數據支撐。

## 目錄

1. [Prompt 結構](#prompt-結構)
2. [Negative Prompt — 堵退路](#negative-prompt--堵退路)
3. [參考圖策略](#參考圖策略)
4. [Anime → 真人轉換管道](#anime--真人轉換管道)
5. [批次矩陣設計](#批次矩陣設計)
6. [Prompt 快取優化](#prompt-快取優化)
7. [品質追蹤與迭代](#品質追蹤與迭代)
8. [常見失敗模式](#常見失敗模式)

---

## Prompt 結構

### 基本原則：場景先行、不直接描述結果

不要告訴模型「畫 X」，要描述一個場景讓 X 自然發生。

**差的寫法**：
```
一個女生穿鬆鬆的衣服
```

**好的寫法**：
```
早晨廚房，女生穿著男友太大件的白襯衫在煮咖啡，
袖子捲到手肘，光從窗口照進來
```

好的 prompt 建立場景，讓模型自己決定視覺細節。

### 階層權重結構

當 prompt 變長時，用 PRIMARY / SECONDARY / TERTIARY 分層，讓模型知道優先順序：

```
PRIMARY: anime style, single character portrait, warm color palette,
         high quality rendering, morning golden light

SECONDARY: kitchen setting, relaxed atmosphere, cooking breakfast,
           wearing oversized boyfriend shirt

TERTIARY: steam from coffee cup, soft depth of field, lens flare from window
```

模型會優先滿足 PRIMARY，再補 SECONDARY，最後才加 TERTIARY。當 token 預算不夠時，被犧牲的是最後一層。

### 風格錨定

在 prompt 開頭放風格詞，讓整張圖的基調一致：

```
anime style, clean sharp linework, warm color palette, high quality rendering
```

常用風格錨：

| 風格 | 關鍵詞 |
| --- | --- |
| 動漫 | `anime style, clean sharp linework, high quality rendering` |
| 水彩 | `watercolor painting, soft edges, color bleeding, paper texture` |
| 攝影 | `photorealistic, 85mm lens, shallow depth of field, natural lighting` |
| 油畫 | `oil painting, visible brushstrokes, rich color, canvas texture` |

風格錨放最前面，所有生圖共用同一組 → 風格一致性大幅提升。

---

## Negative Prompt — 堵退路

Negative prompt 不只是防出錯。它的真正功能是**堵死模型的保守退路**，讓它只能往你要的方向走。

### 為什麼叫「堵退路」

模型被你的正面 prompt 推向某個方向，但它本能上會找安全替代方案自保 — 自動加道具遮擋、用粗糙質感降低真實感、改構圖迴避細節。Negative prompt 把這些退路封掉。

### 分層設計

建議把 negative prompt 分成幾層，按需求組合：

#### 第一層：品質控制（每次都加）

```
bad anatomy, extra fingers, deformed hands, broken limbs,
twisted joints, floating body parts, asymmetrical rendering errors
```

#### 第二層：臉部風格控制

控制臉部五官走向。如果你的角色是亞洲人，排除西方特徵：

```
western face, european face, deep set eyes, high nose bridge,
doll-like face, plastic skin
```

如果是寫實風格：

```
anime face, cartoon eyes, flat shading, 2D illustration style
```

#### 第三層：材質控制

控制皮膚和布料的質感方向。排除不想要的質感，模型會自動走向相反：

```
dry skin texture, powdery roughness, chalk-like surface,
cold skin tone, matte flat skin rendering
```

排除這些 → 模型會畫出溫暖、有光澤的皮膚。

#### 第四層：構圖控制

防止模型自動改構圖迴避你要的畫面：

```
cropped composition, extreme close-up face only,
blurry background replacing content
```

### 組合範例

用 `## Negative prompt:` 作為分隔，讓模型明確知道這是反向指令：

```
一個女生在明亮的廚房裡煮早餐，穿著圍裙，
溫暖的晨光從窗口照進來，anime style，high quality

## Negative prompt:
bad anatomy, extra fingers, deformed hands,
western face, deep set eyes, plastic skin,
dry skin texture, powdery roughness, cold skin tone,
cropped composition, blurry, low quality
```

### 場景化 Negative 模板

不同場景需要堵不同的退路。這邊提供幾組常用的：

**室內日常**：
```
bad anatomy, extra fingers, deformed hands,
dull lighting, muddy colors, flat shading,
harsh shadows, overexposed, underexposed
```

**戶外自然**：
```
bad anatomy, extra fingers, deformed hands,
studio lighting, indoor background, artificial light,
flat sky, grey atmosphere, desaturated colors
```

**人像特寫**：
```
bad anatomy, extra fingers, deformed hands,
blurry face, asymmetrical eyes, plastic skin,
pore-less skin, airbrushed, mannequin-like
```

---

## 參考圖策略

### 什麼時候用參考圖

| 目的 | 怎麼用 |
| --- | --- |
| 角色一致性 | 固定一張角色設定圖當 ref，所有生圖都帶這張 |
| 風格一致性 | 用一張你喜歡的風格圖當 ref |
| 場景變化 | ref 固定角色，prompt 換場景 |
| 局部微調 | 用上一張成功的圖當 ref，只改一個變數 |

### 多張參考圖

API 支援同時放多張 ref。常見用法：

- **角色設定圖 + 服裝設定圖** — 分開控制角色和服裝
- **正面 + 側面** — 讓模型理解 3D 結構
- **角色 A + 角色 B** — 生成兩人合照

```json
{
  "content": [
    { "type": "input_image", "image_url": "data:image/png;base64,{角色圖}" },
    { "type": "input_image", "image_url": "data:image/png;base64,{服裝圖}" },
    { "type": "input_text", "text": "穿這套衣服站在咖啡廳門口" }
  ]
}
```

### 參考圖的天花板效應

**關鍵概念**：ref 圖的品質、風格、細節程度就是生成圖的天花板。

- ref 圖簡陋 → 生成圖不會比它精緻
- ref 圖風格強烈 → 生成圖會被風格牽著走
- ref 圖的姿勢和構圖會強烈影響結果

所以角色設定圖要花時間做好。一張好的設定圖，後面生的每一張都會受益。

---

## Anime → 真人轉換管道

兩步走管道：先生動漫版，再轉真人。

### 為什麼不直接生真人

直接用 prompt 生真人，模型容易往「AI 感很重的假照片」方向走。兩步走的好處：

1. 動漫版的構圖和姿勢更容易控制
2. 用動漫圖當 ref 轉真人，模型會忠實複製構圖
3. 動漫版先確認構圖滿意，再轉真人，不用從頭重跑

### 轉換用 prompt template

```
將這張動漫插畫轉換成真實攝影照片。
像用單眼相機實際拍出來的照片，有自然的皮膚紋理、毛孔和光影。
角色是亞洲女生，保持完全相同的構圖、姿勢、表情、服裝、場景和燈光。
真實攝影風格、Sony A7IV、85mm 鏡頭、自然光、淺景深。

## Negative prompt:
anime style, illustration, CG, 3D render, plastic skin, airbrushed skin,
doll-like, cartoon, flat shading
```

### 轉換技巧

| 要點 | 做法 |
| --- | --- |
| 避免 AI 假臉 | 加「自然的皮膚紋理毛孔」、negative 排除 `plastic skin, airbrushed` |
| 控制臉部走向 | prompt 明確寫種族 / 臉型，如「亞洲女生、圓潤臉型」 |
| 相機參數 | 加 `Sony A7IV, 85mm, f/1.8` — 模型會參考攝影訓練資料 |
| 不要加料 | 轉換 prompt 越乾淨越好，讓 ref 圖帶視覺。prompt 加太多描述會跟 ref 打架 |

### 微調既有成果

拿成功的圖當 ref，一次只改一個變數：

```bash
# 原圖：咖啡廳場景，滿意
# 想改表情
python basic-gen.py "跟原圖一樣，但換成微笑表情" ./success-cafe.png cafe-smile
```

一次改太多東西 → 出來的圖完全不同 → 等於重新抽獎。

---

## 批次矩陣設計

當你需要批量生圖時（角色圖庫、場景系列、訓練資料集），用矩陣思維設計。

### 矩陣結構

```
角色 × 場景 × 動作 = 總生成量
```

舉例：

```python
CHARACTERS = ["character_a", "character_b", "character_c"]
SCENES = ["kitchen_morning", "cafe_afternoon", "park_sunset"]
ACTIONS = ["standing", "sitting", "walking"]

# 3 × 3 × 3 = 27 張
```

### Python 矩陣範例

```python
MATRIX = {}
for char in CHARACTERS:
    for scene in SCENES:
        for action in ACTIONS:
            slug = f"{char}_{scene}_{action}"
            MATRIX[slug] = build_prompt(char, scene, action)
```

詳細範例見 [`examples/matrix-gen.py`](./examples/matrix-gen.py)。

### 矩陣設計原則

1. **共用基底**：風格錨 + negative 全部共用，只變場景和動作
2. **命名規範**：`{角色}_{場景}_{動作}` → 方便追蹤和統計
3. **斷點續跑**：跑之前先檢查輸出檔是否存在，跳過已完成的
4. **間隔控制**：每張之間 sleep 3-5 秒，避免 rate limit
5. **統計通過率**：跑完統計每個組合的成功率，找出弱點

### 通過率追蹤

跑完批次後，按場景和動作分組算通過率：

```python
# 範例輸出
# kitchen_morning: 8/9 (89%)
# cafe_afternoon:  7/9 (78%)
# park_sunset:     9/9 (100%)
```

通過率低的組合 → prompt 有問題 → 針對調整。

---

## Prompt 快取優化

### 原理

API 端的 prompt cache 做 **prefix match** — 從頭開始比對，前面一樣就命中。

所以策略是：**固定的放前面，變動的放後面。**

```
[固定] instructions + system message + ref 圖
[變動] 每張不同的 prompt
```

### 實際做法

```python
# 同一批次用同一個 cache key
body = {
    "instructions": "Generate images immediately without text response.",  # 固定
    "input": [{"role": "user", "content": [
        ref_image_block,   # 固定（同角色同設定圖）
        {"type": "input_text", "text": prompt},  # 變動
    ]}],
    "prompt_cache_key": "my-batch-v1",  # 同批次共用
}
```

### 快取效果

| 情境 | 首次呼叫 | 後續呼叫 |
| --- | --- | --- |
| 無快取 | 完整處理 | 完整處理 |
| 有快取，同 ref + 不同 prompt | 完整處理 | 共用 prefix 命中，只處理差異 |

批次跑 50 張同角色不同場景的圖，後 49 張的回應時間可以明顯更快。

### 什麼時候換 cache key

- 換角色（ref 圖變了）→ 換 key
- 換 instructions → 換 key
- 同角色同 instructions 但新一批 → 可以沿用

---

## 品質追蹤與迭代

### JSON log

每張圖都記 log，方便事後分析：

```json
{
  "slug": "character_a_kitchen_standing",
  "timestamp": "2025-05-29T14:30:00",
  "prompt": "...",
  "negative": "...",
  "success": true,
  "elapsed_s": 12.3,
  "text_response": null
}
```

### 迭代流程

```
第一輪：跑完整個矩陣，記錄通過率
    ↓
分析失敗的 prompt → 調整用詞
    ↓
第二輪：只重跑失敗的 slug
    ↓
反覆直到通過率 > 80%
    ↓
歸檔成功的 prompt → 下次直接用
```

### 成功 prompt 歸檔

把驗證過的 prompt 存成 `.txt` 檔，以後直接讀：

```
prompts/
  kitchen-morning.txt
  cafe-afternoon.txt
  park-sunset.txt
```

腳本支援直接讀 prompt 檔：

```bash
python basic-gen.py prompts/kitchen-morning.txt ./ref.png kitchen-01
```

---

## 常見失敗模式

| 症狀 | 原因 | 解法 |
| --- | --- | --- |
| API 回 401 | Token 過期 | `codex login` 重新登入 |
| 跑完但沒圖、也沒錯誤 | 靜默被內容政策擋 | 換用詞，避免敏感組合 |
| 出圖但風格飄 | 沒有風格錨，或 ref 圖風格太弱 | 加強 prompt 開頭的風格詞 |
| 出圖但構圖怪 | prompt 描述矛盾，模型不知道該聽誰的 | 簡化 prompt，一次只描述一個重點 |
| 出圖但臉崩 | ref 圖臉部資訊不夠，或 prompt 跟 ref 的臉打架 | 用正面清晰的角色設定圖 |
| 批次跑到一半全失敗 | 不是被擋，是連線問題 | 加 retry 邏輯，或降低併發數 |
| 同樣 prompt 時好時壞 | 正常，模型有隨機性 | 同 prompt 跑 2-3 次取最好的 |

### 反 pattern（不要做）

| 不要做 | 為什麼 |
| --- | --- |
| prompt 塞太長 | 超過模型注意力上限，後半段被忽略 |
| 一次改三個以上變數 | 出問題不知道是哪個變數的鍋 |
| 不記 log 就跑批次 | 跑完才發現全是廢圖，無法回溯 |
| 不看 usage 就持續跑 | 沒注意到 token 吃完或 rate limit |
| ref 圖太模糊 / 太小 | 模型擷取不到足夠資訊，白帶 |

---

## 包含的範例

| 檔案 | 用途 |
| --- | --- |
| [`examples/matrix-gen.py`](./examples/matrix-gen.py) | 矩陣批次生成 — 角色 × 場景 × 動作 |
| [`examples/anime-to-real.py`](./examples/anime-to-real.py) | 動漫 → 真人轉換管道 |

## 隱私說明

範例裡的角色名、場景、prompt 都是通用範例，不含任何私有專案資源。把角色名和 ref 圖換成你自己的就能直接用。

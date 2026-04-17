# Contributing

[繁體中文](#繁體中文)

## English

This repository is organized by topic.

- one topic = one branch
- one topic = one pull request
- prefer squash merge
- do not push unrelated changes into `main`

### Recommended workflow

1. Create a branch for one topic only.
2. Put the topic under the correct section:
   - `hooks/`
   - `prompt-engineering/`
   - `context-engineering/`
3. Keep the topic self-contained when possible.
   A good topic folder usually contains its own:
   - `README.md`
   - `README.en.md`
   - `hooks/`, `examples/`, `scripts/`, `tests/` if needed
4. Open one PR for that topic.
5. Squash merge into `main`.

### Naming suggestions

- `feat/add-prompt-engineering-starter`
- `feat/add-context-memory-loading-recipe`
- `feat/add-hook-output-filtering`

---

## 繁體中文

這個 repo 之後會用「一個主題一個 PR」的方式往下長。

- 一個主題，一個 branch
- 一個主題，一個 PR
- 盡量用 squash merge
- 不要把不相干的內容一起塞進 `main`

### 建議流程

1. 先針對單一主題開一條 branch。
2. 依內容放到正確區塊：
   - `hooks/`
   - `prompt-engineering/`
   - `context-engineering/`
3. 如果可以，盡量讓主題資料夾自成一包。
   一個完整主題通常會有自己的：
   - `README.md`
   - `README.en.md`
   - `hooks/`、`examples/`、`scripts/`、`tests/`
4. 一個主題開一個 PR。
5. 合併時盡量用 squash merge，讓 `main` 歷史維持乾淨。

### branch 命名建議

- `feat/add-prompt-engineering-starter`
- `feat/add-context-memory-loading-recipe`
- `feat/add-hook-output-filtering`

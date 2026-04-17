# Contributing

[繁體中文](#繁體中文)

## English

This repository accepts outside pull requests, but we care more about clarity and fit than rigid structure.

## What we look for in accepted PRs

- the PR covers one topic only
- the topic clearly belongs in one section:
  - `hooks/`
  - `prompt-engineering/`
  - `context-engineering/`
- the contribution is useful as a cookbook entry, not just a random code dump
- the README explains the problem, the approach, and how to use it
- Chinese content is the default when the topic has user-facing docs
- English content exists as a companion when needed
- examples, scripts, or tests are included when they actually help
- unrelated cleanup is kept out of the PR

## Important

There is no single mandatory file shape for every topic.

Some topics may need:

- `README.md`
- `README.en.md`
- `hooks/`
- `examples/`
- `scripts/`
- `tests/`

Some topics may only need a README and one small example. That is fine.

The goal is not "make every folder look the same."
The goal is "make the topic easy to understand, easy to try, and easy to maintain."

## Suggested workflow

1. Open one branch for one topic.
2. Put it in the correct section.
3. Keep the PR focused.
4. Prefer squash merge into `main`.

## Branch naming ideas

- `feat/add-prompt-engineering-starter`
- `feat/add-context-memory-loading-recipe`
- `feat/add-hook-output-filtering`

---

## 繁體中文

這個 repo 可以收外部 PR，但我們在意的不是死板的格式，而是內容有沒有整理好、主題有沒有放對地方、別人看了能不能直接用。

## 我們會接受什麼樣的 PR

- 一個 PR 只處理一個主題
- 主題能明確歸到某個區塊：
  - `hooks/`
  - `prompt-engineering/`
  - `context-engineering/`
- 內容真的像 cookbook 條目，不是隨手丟一段程式碼上來
- README 有把「這在解什麼問題、怎麼做、怎麼用」講清楚
- 只要有對外文件，預設以繁體中文為主
- 有需要時再補英文作輔助版
- `examples/`、`scripts/`、`tests/` 是看內容需要，不是每篇都硬要湊
- 不要把不相干的清理、重構或順手修改一起混進同一個 PR

## 重要原則

這個 repo 沒有規定每個主題都要長得一模一樣。

有些主題可能會需要：

- `README.md`
- `README.en.md`
- `hooks/`
- `examples/`
- `scripts/`
- `tests/`

但有些主題可能只需要一份 README 加一個小範例，這樣也完全可以。

重點不是「每個資料夾都長得一樣」，而是：

- 這個主題好不好懂
- 別人能不能快速試
- 後續好不好維護

## 建議流程

1. 一個主題開一條 branch。
2. 放到正確的區塊。
3. PR 內容保持聚焦。
4. 合併時盡量用 squash merge 進 `main`。

## branch 命名建議

- `feat/add-prompt-engineering-starter`
- `feat/add-context-memory-loading-recipe`
- `feat/add-hook-output-filtering`

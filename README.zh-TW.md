# Agent Cookbook

[English README](./README.md)

給 coding agent 用的實戰 cookbook。重點不是框架，而是那些真的能降低成本、提高穩定性、改善操作體驗的小型腳本、hook、adapter、workflow。

這個 repo 目前只有第一個小篇章，之後可以持續擴充。

| Recipe | 解決什麼問題 |
| --- | --- |
| [`claude-cache-safe-images`](./recipes/claude-cache-safe-images/README.zh-TW.md) | 有效解決 Claude 因圖片輸入導致 cache 被破壞的問題 |

## 為什麼做這個 repo

很多 agent 操作優化都很實用，但規模太小，不值得包成完整框架；放在私人專案裡又很難分享。這個 cookbook 的目標就是把這些模式整理成可重用的腳本、範例與短教學。

## 你會在這裡找到什麼

- 可直接抄用的 hooks
- 最小可改寫的整合範例
- 偏實戰的安裝與設定方式
- 從私人系統抽離出來的公開安全版本

## 目前主題

第一篇 recipe 主題是：

**有效解決 Claude cache 被破壞的問題**

目前收錄兩種實用做法：

1. Claude `Read` hook：在圖片進入主 session 之前，先轉成文字描述。
2. Discord adapter 範例：先描述附件，再把文字補進 prompt，而不是直接丟 raw image blocks。

## 快速開始

如果你已經安裝好 `gemini`、`node`、`jq`，目前這篇 recipe 幾乎可以開箱即用：

```bash
git clone <repo-url>
cd agent-cookbook
bash scripts/install.sh
bash scripts/doctor.sh
```

這會自動把 Claude `Read` hook 裝到 `~/.claude/hooks/agent-cookbook/claude-cache-safe-images`，並幫你更新 `~/.claude/settings.json`。

## License

MIT

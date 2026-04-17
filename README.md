# Agent Cookbook

[English README](./README.en.md)

這是一份給 coding agent 用的實戰 cookbook。重點不在框架，而是那些真的能省成本、提高穩定性、讓操作流程更順手的小工具、hook、範例程式和工作方式。

目前這個 repo 先從第一篇小章節開始，之後會慢慢補上其他實用 recipe。

| Recipe | 解決什麼問題 |
| --- | --- |
| [`claude-cache-safe-images`](./recipes/claude-cache-safe-images/README.md) | 有效解決 Claude 因圖片輸入導致 cache 被破壞的問題 |

## 為什麼做這個 repo

很多跟 agent 操作有關的優化其實很有用，但規模又小到不值得另外做成完整框架；留在私人專案裡也不方便分享。這個 cookbook 的目標，就是把這些做法整理成可重用的腳本、範例和短教學。

## 你會在這裡找到什麼

- 可直接抄用的 hooks
- 最小可改寫的整合範例
- 偏實作導向的安裝與設定方式
- 從私人系統抽離出來的公開安全版本

## 目前主題

第一篇 recipe 主題是：

**有效解決 Claude cache 被破壞的問題**

目前先收兩種實用做法：

1. Claude `Read` hook：在圖片進主 session 前，先轉成文字描述。
2. Discord 串接範例：先描述附件，再把文字補進 prompt，而不是直接塞原始圖片區塊。

## 快速開始

如果你已經裝好 `gemini`、`node`、`jq`，這篇 recipe 基本上已經接近開箱即用：

```bash
git clone <repo-url>
cd agent-cookbook
bash scripts/install.sh
bash scripts/doctor.sh
```

這會自動把 Claude `Read` hook 安裝到 `~/.claude/hooks/agent-cookbook/claude-cache-safe-images`，並順手更新 `~/.claude/settings.json`。

## License

MIT

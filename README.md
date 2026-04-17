# Agent Cookbook

[English README](./README.en.md)

這是一份給 coding agent 用的實戰 cookbook。重點不是再做一套新框架，而是把那些真的有用、能省成本、能讓流程更穩的小工具、hook、範例程式整理起來。

目前先從第一篇小章節開始，之後會慢慢把其他實用 recipe 補進來。

## 目前目錄怎麼分

- [`hooks/`](./hooks/)：放可直接用的 hook、攔截器、工具腳本
- [`prompt-engineering/`](./prompt-engineering/)：放 prompt 模板、提示策略、提示組裝方式
- [`context-engineering/`](./context-engineering/)：放記憶、摘要、壓縮、上下文載入策略

## 目前收錄內容

| 分類 | Recipe | 解決什麼問題 |
| --- | --- | --- |
| Hooks | [`claude-cache-safe-images`](./hooks/claude-cache-safe-images/README.md) | 有效解決 Claude 因圖片輸入導致 cache 被破壞的問題 |

## 為什麼做這個 repo

很多跟 agent 操作有關的優化其實都很好用，只是規模小到不值得另外包成一個完整框架；但如果一直放在私人專案裡，又很難分享給別人。這個 cookbook 想做的事很單純，就是把這些做法整理成可重用的腳本、範例和短教學。

## 你會在這裡找到什麼

- 可直接抄用的 hooks
- 最小可改寫的整合範例
- 偏實戰的安裝與設定方式
- 從私人系統抽離出來的公開安全版本

## 目前主題

第一篇 recipe 主題放在 `hooks/` 底下：

**有效解決 Claude cache 被破壞的問題**

目前先整理兩種很實用的做法：

1. Claude `Read` hook：圖片進主 session 前，先轉成文字描述。
2. Discord 串接範例：先描述附件，再把文字補進 prompt，而不是直接塞原始圖片區塊。

## 快速開始

如果你已經裝好 `gemini`、`node`、`jq`，這篇 recipe 基本上已經很接近開箱即用了：

```bash
git clone <repo-url>
cd agent-cookbook
bash hooks/claude-cache-safe-images/scripts/install.sh
bash hooks/claude-cache-safe-images/scripts/doctor.sh
```

它會自動把 Claude `Read` hook 裝到 `~/.claude/hooks/agent-cookbook/claude-cache-safe-images`，也會順手幫你更新 `~/.claude/settings.json`。

## License

MIT

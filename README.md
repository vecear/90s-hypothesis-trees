# 90s Hypothesis Trees

> 「沒有感覺，只有證據。沒有故事，只有框架。沒有捷徑，只有系統。」
> — 90s.pm.investing

用科學方法管理投資假設的 GitHub 倉庫。每支追蹤標的以 YAML 格式儲存完整假設樹、三情景估值、每日監控狀態，並透過 AI Agent 自動比對最新資料 × Kill Condition，產出每日通報。

## 架構

```
90s-hypothesis-trees/
├── trees/
│   ├── _template/
│   │   └── tree.yaml              ← 複製此檔建立新標的
│   ├── TSLA/
│   │   ├── tree.yaml              ← 當前版本（HEAD）
│   │   ├── history/               ← 版本歷史（Kill Condition 不可事後修改）
│   │   │   └── v1.0.0-YYYY-MM-DD.yaml
│   │   └── monitors/              ← 每日監控報告歸檔
│   │       └── YYYY-MM-DD.md
│   └── NKE/…
├── scripts/
│   └── monitor.py                 ← 每日監控執行腳本
├── .github/workflows/
│   └── daily-monitor.yml          ← GitHub Actions 排程（可選，預設本地 schedule）
└── README.md
```

## 使用流程

### 1. 建立新假設樹

在 Claude Code 啟動 90s skill：

```
/90s setup TSLA
```

Skill 會執行 8 步 Framework Mode 產出完整假設樹，輸出 YAML 後：

```bash
cp trees/_template/tree.yaml trees/TSLA/tree.yaml
# 貼上 skill 產出的內容，commit
git add trees/TSLA/
git commit -m "feat(TSLA): initialize hypothesis tree v1.0.0"
```

### 2. 註冊每日監控

使用 Claude Code 的 `schedule` skill（本地 cron）：

```
/schedule create "90s monitor TSLA" --cron "0 6 * * 1-5" --tz "Asia/Taipei"
```

或啟用 GitHub Actions（需於 repo 設定 Secrets：`ANTHROPIC_API_KEY`、`SLACK_WEBHOOK_URL`、`EMAIL_*`）：

```bash
# 編輯 .github/workflows/daily-monitor.yml 開啟 cron
```

### 3. 每日通報

每個工作日台灣時間 06:00 自動觸發：
- 讀取 `trees/[TICKER]/tree.yaml`
- 抓取最新財報、新聞、分析師報告
- 逐葉比對 Kill Condition
- 更新 `current_status` 並 commit 新版本至 `history/`
- 輸出監控報告至 `monitors/YYYY-MM-DD.md`
- 推送至 Slack / Email

## 鐵律

- **Kill Condition 事後不可修改** — 已 commit 至 `history/` 的 YAML 永遠不變；只能建立新版本
- **每一筆變動都 commit** — Git 是假設樹的版本控制層，所有狀態變動留下歷史軌跡
- **樹倒了就離場** — H-0 的 Kill Condition 觸發時，不修剪、不微調、不心存僥倖

## 相關

- Skill 定義：`~/.claude/skills/90s-pm-investing.md`
- 方法論原點：[90s.pm.investing](https://90s.pm)

---

*用科學畫一棵樹，然後在看清真相的瞬間，做出屬於自己的判斷。*

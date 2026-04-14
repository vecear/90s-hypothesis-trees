"""90s Hypothesis Tree Daily Monitor

每日監控執行腳本。讀取 trees/[TICKER]/tree.yaml，呼叫 Claude API
執行證偽條件比對，輸出監控報告並更新狀態。

使用方式：
    python scripts/monitor.py TSLA
    python scripts/monitor.py --all

依賴：
    pip install anthropic pyyaml requests

環境變數：
    ANTHROPIC_API_KEY   Claude API key
    SLACK_WEBHOOK_URL   Slack 通報（可選）
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).resolve().parent.parent
TREES_DIR = REPO_ROOT / "trees"


def load_tree(ticker: str) -> dict:
    tree_path = TREES_DIR / ticker / "tree.yaml"
    if not tree_path.exists():
        raise FileNotFoundError(f"Tree not found: {tree_path}")
    with tree_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_monitor_report(ticker: str, report_md: str) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = TREES_DIR / ticker / "monitors"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today}.md"
    out_path.write_text(report_md, encoding="utf-8")
    return out_path


def run_monitor(ticker: str) -> None:
    """執行單一標的的每日監控。

    實際的 AI Agent 邏輯（抓取最新財報 / 新聞 / 分析師報告，
    交叉比對每片葉子的 Kill Condition）由 Claude Code 的 90s skill 處理。
    此腳本僅為排程觸發點 + YAML 讀寫骨架。
    """
    tree = load_tree(ticker)
    print(f"[{ticker}] Loaded tree v{tree.get('version')} "
          f"({len(tree.get('branches', []))} branches)")

    # TODO: 呼叫 Claude API + 外部資料源比對 Kill Condition
    # TODO: 更新 leaf current_status、scorecard
    # TODO: 推送 Slack / Email / Obsidian

    report = (
        f"# [{ticker}] Daily Tree Monitor — "
        f"{datetime.now().strftime('%Y-%m-%d')}\n\n"
        "_此為骨架輸出，實際監控邏輯待接上 Claude API。_\n"
    )
    out = save_monitor_report(ticker, report)
    print(f"[{ticker}] Report saved: {out}")


def main() -> int:
    parser = argparse.ArgumentParser(description="90s Hypothesis Tree Monitor")
    parser.add_argument("ticker", nargs="?", help="Ticker symbol (e.g., TSLA)")
    parser.add_argument("--all", action="store_true",
                        help="Monitor all tickers in trees/")
    args = parser.parse_args()

    if args.all:
        tickers = [p.name for p in TREES_DIR.iterdir()
                   if p.is_dir() and not p.name.startswith("_")]
        if not tickers:
            print("No tickers registered.")
            return 0
        for t in tickers:
            run_monitor(t)
        return 0

    if not args.ticker:
        parser.print_help()
        return 1

    run_monitor(args.ticker)
    return 0


if __name__ == "__main__":
    sys.exit(main())

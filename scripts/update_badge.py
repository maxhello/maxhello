#!/usr/bin/env python3
"""刷新 profile README 里的多邻国徽章段落。

数据源是公开的 maxhello.github.io 仓库快照(每天由该仓库的 duolingo.yml 定时更新),
本脚本不碰多邻国 API、不需要任何密钥 —— 只消费已发布的数据。
用法: python3 scripts/update_badge.py
本地 python.org 安装缺 CA 证书时: BADGE_INSECURE=1 python3 scripts/update_badge.py
"""
import json
import os
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta

DATA_URL = (
    "https://raw.githubusercontent.com/maxhello/maxhello.github.io/"
    "main/data/duolingo-history.json"
)
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
START = "<!-- duolingo-badge:start -->"
END = "<!-- duolingo-badge:end -->"
BLOCKS = "▁▂▃▄▅▆▇█"


def fetch_json(url):
    ctx = ssl._create_unverified_context() if os.environ.get("BADGE_INSECURE") else None
    with urllib.request.urlopen(url, context=ctx, timeout=30) as r:
        return json.load(r)


def sparkline(daily, days=14):
    """以明细最后一天为终点,取最近 N 个自然日的 xp 画字符条形(缺的天记 0)。"""
    if not daily:
        return ""
    end = datetime.strptime(max(daily), "%Y-%m-%d").date()
    xs = []
    for i in range(days - 1, -1, -1):
        d = (end - timedelta(days=i)).isoformat()
        xs.append((daily.get(d) or {}).get("xp", 0))
    top = max(xs) or 1
    return "".join(BLOCKS[round(x / top * (len(BLOCKS) - 1))] for x in xs)


def render(snap):
    return (
        f"🔥 **{snap['streak']}**-day streak"
        f" · ⚡ **{snap['totalXp']:,}** XP"
        f" · last 14 days {sparkline(snap.get('daily') or {})}"
        f" · updated {snap['date']}"
    )


def main():
    snap = fetch_json(DATA_URL)[-1]
    # 字段残缺就变红退出,绝不渲染误导性数字(与主站管道同一原则)
    for k in ("date", "streak", "totalXp"):
        if snap.get(k) is None:
            print(f"snapshot missing field: {k}", file=sys.stderr)
            sys.exit(1)

    with open(README, encoding="utf-8") as f:
        text = f.read()
    # 标记缺失会抛 ValueError → workflow 变红,防止徽章段落漂移
    i, j = text.index(START) + len(START), text.index(END)
    new = text[:i] + "\n" + render(snap) + "\n" + text[j:]
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("badge updated:", render(snap))
    else:
        print("no change")


if __name__ == "__main__":
    main()

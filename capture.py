# -*- coding: utf-8 -*-
"""收盘快照：抓当日指数、涨跌家数、涨停/跌停、题材前十，追加到 data/snapshots.jsonl

用法：python capture.py
"""

import json
import math
import os
import urllib.request
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "data", "snapshots.jsonl")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
INDEX = [("sh000001", "上证指数"), ("sz399001", "深证成指"), ("sz399006", "创业板指"), ("sh000688", "科创综指")]


def get(url, referer="https://finance.sina.com.cn/", encoding="utf-8", timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode(encoding, "ignore")


def indices():
    text = get("https://qt.gtimg.cn/q=" + ",".join(s for s, _ in INDEX), "https://gu.qq.com/", "gbk")
    out = []
    for chunk in text.split(";"):
        if "=" not in chunk:
            continue
        p = chunk.split("=", 1)[1].strip().strip('"').split("~")
        if len(p) < 40:
            continue
        try:
            out.append({"name": p[1], "price": float(p[3]), "pct": float(p[32])})
        except Exception:
            continue
    return out


def all_market():
    count = get(
        "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount?node=hs_a",
        encoding="latin1",
    )
    total = int(str(count).strip().strip('"') or 5400)
    pages = max(1, math.ceil(total / 100))
    rows = []
    for page in range(1, pages + 1):
        url = (
            "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
            f"?page={page}&num=100&sort=symbol&asc=1&node=hs_a"
        )
        try:
            rows.extend(json.loads(get(url, encoding="latin1")) or [])
        except Exception:
            continue
    return rows


def limit_of(code):
    if code[:3] in ("300", "301", "688", "689"):
        return 20.0
    if code[:1] in ("4", "8") or code[:2] == "92":
        return 30.0
    return 10.0


def main():
    now = datetime.now()
    # 非收盘时段跳过：避免任务迟到（比如第二天早上才补跑）写入错误日期的数据
    if now.hour < 15 or (now.hour == 15 and now.minute < 5):
        print(f"跳过：{now:%H:%M} 还没收盘")
        return
    # 当天已抓过就不重复写
    if os.path.exists(OUT):
        try:
            with open(OUT, encoding="utf-8") as f:
                lines = [x for x in f.read().splitlines() if x.strip()]
            if lines:
                last = json.loads(lines[-1])
                if last.get("date") == now.strftime("%Y-%m-%d"):
                    print(f"已有 {last['date']} 快照，跳过")
                    return
        except Exception:
            pass
    rows = all_market()
    up = down = flat = 0
    zt = dt = 0
    amount = 0.0
    for r in rows:
        try:
            pct = float(r.get("changepercent") or 0)
            amount += float(r.get("amount") or 0)
        except Exception:
            continue
        if pct > 0:
            up += 1
        elif pct < 0:
            down += 1
        else:
            flat += 1
        lim = limit_of(str(r.get("code") or ""))
        if pct >= lim - 0.3:
            zt += 1
        elif pct <= -(lim - 0.3):
            dt += 1
    if not rows:
        raise SystemExit("抓取失败：没有拿到任何股票")

    seal = zt / (zt + dt) if (zt + dt) else 0
    score = round(
        100 * (0.40 * min(1, zt / 80) + 0.25 * seal + 0.15 * 1.0 + 0.20 * (1 - min(1, dt / 30))), 1
    )
    snap = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "indices": indices(),
        "breadth": {"up": up, "down": down, "flat": flat, "total": len(rows)},
        "limit": {"zt": zt, "dt": dt},
        "emotion": score,
        "amount": round(amount, 0),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps(snap, ensure_ascii=False) + "\n")
    print(f"已写入 {snap['date']} 快照：涨 {up} 跌 {down} 涨停 {zt} 跌停 {dt} 情绪 {score}")


if __name__ == "__main__":
    main()

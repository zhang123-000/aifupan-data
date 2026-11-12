# aifupan-data · 云端收盘快照

每个交易日 15:30（北京时间）由 GitHub Actions 自动运行 `capture.py`，
把上证/深成/创业板/科创指数、涨跌家数、涨停跌停、情绪分写入 `data/snapshots.jsonl`。

**完全不需要本地电脑开机。**

## 数据格式

每行一条 JSON：

```json
{"date": "2026-11-12", "time": "15:30", "indices": [...], "breadth": {"up": 875, "down": 4634, "flat": 70, "total": 5500}, "limit": {"zt": 37, "dt": 6}, "emotion": 71.0, "amount": 15981xxxxx}
```

## 首次配置（三步）

1. 在 GitHub 新建**私有仓库**，名字随意（如 `aifupan-data`）
2. 把本目录推上去：

```bat
cd /d D:\Deepseek\aifupan-cloud
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/<你的用户名>/aifupan-data.git
git push -u origin main
```

3. 打开仓库 → **Actions** 标签 → 点 `收盘快照` → **Run workflow** 手动跑一次验证

## 验证

跑完后仓库里应该多一条 commit：`snapshot: 2026-11-12`

打开 `data/snapshots.jsonl` 能看到数据。

## 本地同步

本地只要把仓库拉下来即可：

```bat
cd /d D:\Deepseek\aifupan\data
git clone https://github.com/<你的用户名>/aifupan-data.git cloud
```

之后想同步最新数据：

```bat
cd /d D:\Deepseek\aifupan\data\cloud
git pull
```

## 说明

- GitHub 的定时任务可能延迟几分钟到几十分钟（免费额度排队），不影响数据正确性
- 周末和节假日也会跑，但抓到的是休市数据（涨跌为 0），可自行忽略
- 数据源：腾讯行情（指数）+ 新浪（全市场），都是公开接口

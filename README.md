# 研招网院校信息爬虫

抓取中国研究生招生信息网（研招网）院校库的招生单位列表，清洗后写入 SQLite，作为"可报考院校筛选"的数据底座。

## 数据

| 项 | 值 |
|---|---|
| 数据来源 | <https://yz.chsi.com.cn/sch/>（公开院校库页面） |
| 采集时间 | 2026-10-17 |
| 记录数 | **936 条** |
| 省份覆盖 | 31 个省 / 自治区 / 直辖市 |
| 字段 | 院校名称、所在地、院校网站（入库后另有 id、updated_at） |
| 分页方式 | 47 页 × 20 条，偏移参数 `start`，最后一页 16 条 |
| 请求策略 | 固定桌面 UA + Referer，单线程，每页间隔 2–5 秒 |

## 功能

- **多线程抓取**：生产者-消费者模型，`queue.Queue` 解耦 URL 生产与页面抓取
- **空响应重试**：站点偶发返回 200 但无院校列表的页面，自动重试 4 次（3s → 6s → 12s 退避）
- **增量写入 CSV**：按院校名称去重，重复运行不会重复堆积
- **SQLite 入库**：`INSERT ... ON CONFLICT DO UPDATE` 幂等写入，重复运行行数不变
- **结构化日志**：`dictConfig` 配置，控制台 + 文件双输出，按大小滚动
- **完整性校验**：抓取结果低于预期 95% 时写 ERROR 日志，避免"静默丢数据"

## 目录结构

```
校院信息爬虫/
├── bin/
│   └── run.py          # 爬取入口
├── conf/
│   └── settings.py     # （预留）
├── core/
│   └── spider.py       # 抓取 / 解析 / 队列 / 保存
├── db/
│   └── db_handle.py    # SQLite 建表、入库、查询
├── data/
│   ├── schools.csv     # 采集结果
│   └── schools.db      # 入库结果（不入版本库）
├── log/                # 日志目录（不入版本库）
├── tests/
│   └── test_spider.py  # 单元测试
├── lib/
│   └── common.py       # （预留）
├── conftest.py         # pytest 路径配置
├── settings.py         # 日志配置
└── requirements.txt
```

## 安装

```bash
python -m venv .venv
source .venv/Scripts/activate     # Windows Git Bash
pip install -r requirements.txt
```

依赖：`requests`、`lxml`、`pandas`、`pytest`

## 使用

```bash
# 1. 抓取（约 3-5 分钟，会写入 data/schools.csv）
python bin/run.py

# 2. 入库（读取 CSV，写入 data/schools.db，幂等）
python db/db_handle.py

# 3. 运行测试
python -m pytest -v
```

## 数据表

```sql
CREATE TABLE IF NOT EXISTS schools (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    school_name TEXT NOT NULL UNIQUE,       -- 院校名称，唯一约束防重复
    province    TEXT NOT NULL DEFAULT '未知',
    website     TEXT,                       -- 院校详情页
    updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    CHECK (length(school_name) > 0)
);

CREATE INDEX IF NOT EXISTS idx_schools_province ON schools(province);
```

按省查询会走索引：

```
EXPLAIN QUERY PLAN SELECT * FROM schools WHERE province = '广东';
-- SEARCH schools USING INDEX idx_schools_province (province=?)
```

## 合规声明

- 仅访问**公开**的院校列表页面，不登录、不涉及个人数据
- **低频**抓取：单线程，每页间隔 2–5 秒，全量仅 47 次请求
- 数据仅用于个人学习与择校研究，**不用于商业用途**
- 若站点明确要求停止抓取，应立即停止并删除本地数据

## 已知限制

- **只有院校层信息**：没有专业、考试科目、分数线、报录比
- 研招网专业目录跳转各校独立网站，结构不统一，无法用同一套解析规则采集（留待后续迭代）
- 站点偶发返回无数据页面，靠重试兜底；极端情况下仍可能缺页，此时日志中会有「放弃」和「数据可能不完整」告警
- 未做增量更新：每次运行都是全量重抓（UPSERT 保证不重复）

## 踩过的坑

记录在这里，一是备忘，二是说明这些看似"能跑"的代码是怎么变得可靠的。

| 现象 | 根因 | 解决 |
|---|---|---|
| 47 页只拿到 260 条 | **随机 UA** 命中 iPhone/iPad 时，站点返回移动版 SPA 页面，静态 HTML 里没有院校列表 | 固定桌面 UA |
| 同一页时好时坏 | 空响应被当成"这页没数据"，静默跳过 | 空响应视为失败，指数退避重试 4 次 + 逐页日志 |
| 消费线程可能卡死 | `parse` 抛异常时 `task_done()` 不执行，`join()` 永不返回 | `try/except/finally` 保证 `task_done()` |
| 换目录运行就报错 | CSV/DB 用了相对路径，依赖当前工作目录 | 用 `BASE_DIR` 拼绝对路径 + `makedirs` |
| 重复入库会翻倍 | 只用 CSV 去重，数据库层没有约束 | `UNIQUE(school_name)` + `ON CONFLICT DO UPDATE` |

## 数据核对

```bash
# CSV 行数（含表头应为 937）
wc -l data/schools.csv

# 数据库行数与省份分布
python -c "import sqlite3; c=sqlite3.connect('data/schools.db'); print(c.execute('SELECT COUNT(*) FROM schools').fetchone()); print(c.execute('SELECT province, COUNT(*) FROM schools GROUP BY province ORDER BY 2 DESC').fetchall())"
```

import os
import sys
import sqlite3
import logging.config
import pandas as pd
BASE_DIR=os.path.dirname(os.path.dirname(__file__))#__file__获得文件绝对路径,os获取父级
sys.path.append(BASE_DIR)
import settings
logging.config.dictConfig(settings.LOG_CONFIG)#加载字典
logger=logging.getLogger("logger_console")


def _绝对路径(路径: str) -> str:
    """把相对路径转成基于项目根目录的绝对路径，并确保父目录存在"""
    if not os.path.isabs(路径):
        路径 = os.path.join(BASE_DIR, 路径)
    父目录 = os.path.dirname(路径)
    if 父目录:
        os.makedirs(父目录, exist_ok=True)
    return 路径

def _连接(数据库路径: str) -> sqlite3.Connection:
    """打开数据库连接（内部负责路径转换）"""
    return sqlite3.connect(_绝对路径(数据库路径))
    
# 表格:
# id school_name province(所在地) website(校院网站) updated_at(时间)
def 初始化(数据库路径: str) -> None:
    """建表 + 建索引 + 设 PRAGMA（注意 PRAGMA 要在事务外）"""
    conn=_连接(数据库路径)
    conn.execute("PRAGMA journal_mode=WAL")#只要执行一次就永久执行
    conn.execute("PRAGMA foreign_keys=ON")#每次新建一个链接就要写一个
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        school_name TEXT NOT NULL UNIQUE,
        province TEXT NOT NULL DEFAULT '未知',
        website TEXT,
        updated_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
        CHECK (length(school_name) > 0));
        """ )
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_schools_province ON schools(province);
        """)
    conn.commit()
    conn.close()

def 批量入库(记录: list[tuple], 数据库路径: str) -> int:
    """executemany + ON CONFLICT，返回入库条数"""
    conn=_连接(数据库路径)
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        with conn:
            入库前 = conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0]
            conn.executemany("""INSERT INTO schools (school_name, province, website) 
                             VALUES (?, ?, ?) 
                             ON CONFLICT(school_name) DO UPDATE SET
                             province =excluded.province,
                             website    = excluded.website,
                             updated_at = datetime('now','localtime')
                             """,
                             记录)
            入库后 = conn.execute("SELECT COUNT(*) FROM schools").fetchone()[0]
            return 入库后 - 入库前
    except sqlite3.Error as e:
        logger.error(f"入库失败,已回滚:{e}")
        return 0
    finally:
        conn.close()
        

def 按省份查询(省: str, 数据库路径: str) -> list[tuple]:
    """走索引的查询"""
    conn=_连接(数据库路径)
    conn.execute("PRAGMA foreign_keys=ON")
    cur=conn.execute("SELECT * FROM schools WHERE province=?",(省,))
    结果=cur.fetchall()
    return 结果
def 统计(数据库路径: str) -> list[tuple]:
    """各省数量，按数量降序"""
    conn=_连接(数据库路径)
    try:
        cur = conn.execute("""
            SELECT province AS 省份, COUNT(*) AS 数量
            FROM schools GROUP BY province ORDER BY 数量 DESC
        """)
        return cur.fetchall()
    finally:
        conn.close()
# SELECT COUNT(*) FROM schools = 936
# 再跑一次入库 → 还是 936，不报错
# EXPLAIN QUERY PLAN 能看到 USING INDEX
# 提示：先用 python -c "import sqlite3; ..." 或一个 20 行的临时脚本，把建表跑通，再写完整文件。别一次写 100 行然后调半天。
if __name__ == "__main__":
    for _ in [1,2,3,4]:
        路径= _绝对路径(r"data\\schools.db")
        csv路径 = _绝对路径(r"data\\schools.csv")
        df = pd.read_csv(csv路径, encoding="utf-8-sig")
        print("CSV 列名:", list(df.columns))  
        初始化(数据库路径=路径)
        记录 = list(df[["院校名称", "所在地", "院校网站"]].itertuples(index=False, name=None))
        print("待入库:", len(记录))
        
        增加=批量入库(记录,路径)
        print(增加)
        print("总数:", 统计(路径))
        print("广东:", 按省份查询("广东", 路径)[:3])
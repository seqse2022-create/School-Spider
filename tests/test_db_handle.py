from db.db_handle import 初始化,批量入库,按省份查询
import sqlite3

def test_初始化_build(tmp_path):
    path = tmp_path / "schools.db"
    初始化(str(path))
    conn=sqlite3.connect(str(path))
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()#你没讲如何查看数据库里已存在的表,我问其他ai的
    table_names = [r[0] for r in tables if not r[0].startswith("sqlite_")]
    assert "schools" in table_names
    assert len(table_names) == 1
    rows = conn.execute("PRAGMA index_list(schools);").fetchall()
    idx_name=[r[1] for r in rows]
    assert "idx_schools_province" in idx_name
    
def test_批量入库_重复(tmp_path):
    path = tmp_path / "schools.db"
    初始化(str(path))
    记录 = [("北京大学", "北京", "https://a"),("中山大学", "中山", "https://b")]
    assert 批量入库(记录,str(path)) == 2
    assert 批量入库(记录,str(path)) == 0
    conn=sqlite3.connect(str(path))
    cur = conn.execute("SELECT * FROM schools;").fetchall()
    assert len(cur) == 2

def test_按省份查询(tmp_path):
    path = tmp_path / "schools.db"
    初始化(str(path))
    记录 = [("芝麻大学", "广东", "https://a"),("养殖大学", "广东", "https://b"),("烧鸭大学", "北京", "https://c")]
    批量入库(记录,path)
    result = 按省份查询("广东",str(path))
    for i in result :
        assert i[2] == "广东"
        assert i[1] in {"养殖大学" , "芝麻大学"}
    assert len(按省份查询("广东",str(path))) == 2
# 结果:
# =============================================== short test summary info ===============================================
# FAILED tests/test_db_handle.py::test_初始化_build - AssertionError: assert 2 == 1
# FAILED tests/test_db_handle.py::test_批量入库_重复 - AssertionError: assert 2 == 0
# FAILED tests/test_db_handle.py::test_按省份查询 - AssertionError: assert '芝麻大学' == '养殖大学'
# ============================================= 3 failed, 6 passed in 0.60s =============================================
# PS F:\xian_mu\xianmu\111\git.demo\校院信息爬虫> python -m pytest -v
# ================================================= test session starts =================================================
# platform win32 -- Python 3.12.8, pytest-9.1.1, pluggy-1.6.0 -- F:\python\python.exe
# cachedir: .pytest_cache
# rootdir: F:\xian_mu\xianmu\111\git.demo\校院信息爬虫
# plugins: platformdirs-4.12.2
# collected 9 items

# tests/test_db_handle.py::test_初始化_build PASSED                                                                [ 11%]
# tests/test_db_handle.py::test_批量入库_重复 FAILED                                                               [ 22%]
# tests/test_db_handle.py::test_按省份查询 PASSED                                                                  [ 33%]
# tests/test_spider.py::test_parse_school_list_正常解析 PASSED                                                     [ 44%]
# tests/test_spider.py::test_parse_school_list_空输入 PASSED                                                       [ 55%]
# tests/test_spider.py::test_parse_school_list_没有条目 PASSED                                                     [ 66%]
# tests/test_spider.py::test_save_incremental_去重 PASSED                                                          [ 77%]
# tests/test_spider.py::test_fetch_one_page_空响应重试后放弃 PASSED                                                [ 88%]
# tests/test_spider.py::test_fetch_one_page_首次成功不重试 PASSED                                                  [100%]

# ====================================================== FAILURES =======================================================
# ____________________________________________________ test_批量入库_重复 _____________________________________________________

# tmp_path = WindowsPath('C:/Users/SEQSE/AppData/Local/Temp/pytest-of-SEQSE/pytest-4/test_批量入库_重复0')

#     def test_批量入库_重复(tmp_path):
#         path = tmp_path / "schools.db"
#         初始化(str(path))
#         记录 = [("北京大学", "北京", "https://a"),("中山大学", "中山", "https://b")]
#         assert 批量入库(记录,str(path)) == 2
# >       assert 批量入库(记录,str(path)) == 0
# E       AssertionError: assert 2 == 0
# E        +  where 2 = 批量入库([('北京大学', '北京', 'https://a'), ('中山大学', '中山', 'https://b')], 'C:\\Users\\SEQSE\\AppData\\Local\\Temp\\pytest-of-SEQSE\\pytest-4\\test_批量入库_重复0\\schools.db')
# E        +    where 'C:\\Users\\SEQSE\\AppData\\Local\\Temp\\pytest-of-SEQSE\\pytest-4\\test_批量入库_重复0\\schools.db' = str(WindowsPath('C:/Users/SEQSE/AppData/Local/Temp/pytest-of-SEQSE/pytest-4/test_批量入库_重复0/schools.db'))

# tests\test_db_handle.py:22: AssertionError
# =============================================== short test summary info ===============================================
# FAILED tests/test_db_handle.py::test_批量入库_重复 - AssertionError: assert 2 == 0
# ============================================= 1 failed, 8 passed in 0.58s =============================================
# PS F:\xian_mu\xianmu\111\git.demo\校院信息爬虫>

# 从这就能检查出代码的问题了,第2个检测的函数当时为了偷懒用了len(结果),就算有去重把数据拦截了,也会输出增加条数
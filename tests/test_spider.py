"""spider 模块单元测试。"""
#代码是直接复制的,因为是你给的完整代码,没让我写,但每一行我会去看,其实也没啥复杂的,要我写我也会
import pandas as pd

from core.spider import parse_school_list, save_incremental  #通过根目录的conftest.py,让spider找到core.spider,我有疑问就是不能用os拼出绝对路径然后添加到环境变量吗就像run.py那样,换言之run.py能不能像这个一样在根目录建一个空文件夹这样导入呢

SAMPLE_HTML = """
<div class="sch-item">
  <a class="name js-yxk-yxmc text-decoration-none" href="/sch/schoolInfo--schId-1.dhtml">北京大学</a>
  <div class="sch-department">北京</div>
</div>
<div class="sch-item">
  <a class="name js-yxk-yxmc text-decoration-none" href="/sch/schoolInfo--schId-2.dhtml">清华大学</a>
  <div class="sch-department">北京</div>
</div>
"""
#上面的是测试答案吧,看看爬取结果对不对,但着这是静态的,但要是网页结果改了呢,那样测试没通过但能正常使用

def test_parse_school_list_正常解析():#前面有test_会自动被spider运行
    """两个 sch-item 应解析出两条记录，字段和拼接后的网址都正确。"""
    rows = parse_school_list(SAMPLE_HTML, "https://yz.chsi.com.cn/sch/?start=0")

    assert len(rows) == 2
    assert rows[0]["院校名称"] == "北京大学"
    assert rows[0]["所在地"] == "北京"
    assert rows[0]["院校网站"] == "https://yz.chsi.com.cn/sch/schoolInfo--schId-1.dhtml"


def test_parse_school_list_空输入():
    """空字符串应返回空列表，不能抛异常。"""
    assert parse_school_list("", "https://example.com") == []


def test_parse_school_list_没有条目():
    """页面正常但没有 sch-item 时返回空列表（这就是移动版页面的情况）。"""
    assert parse_school_list("<html><body>查询无结果</body></html>", "https://e.com") == []


def test_save_incremental_去重(tmp_path):
    """同样的数据写两次，第二次新增 0 条，文件里仍然只有 1 行。"""
    path = tmp_path / "schools.csv"
    data = [{"院校名称": "北京大学", "所在地": "北京", "院校网站": "u1"}]

    assert save_incremental(data, str(path)) == 1
    assert save_incremental(data, str(path)) == 0

    df = pd.read_csv(path, encoding="utf-8-sig")
    assert len(df) == 1
#=============================================================
#还有问题,这里有两个函数,分别把原函数改假,那是第一个函数运行完就改回去,还是等测试代码运行完再改回去
import core.spider as spider #我不明白上面不是导入了吗,为啥还要导入,是不是上面导入的是特定的函数,这是整个文件\
def test_fetch_one_page_空响应重试后放弃(monkeypatch):
    """连续空响应时，应重试 max_attempts 次后放弃，返回空列表。"""
    调用记录 = []

    def 假的fetch_page(url, **kwargs):
        调用记录.append(url)
        return "<html><body>查询无结果</body></html>", url

    # 把真的网络请求换掉
    monkeypatch.setattr(spider, "fetch_page", 假的fetch_page)#指定函数fetch_page,替换为假的fetch_page
    # 把等待跳过，否则测试要真的等 3+6+12 = 21 秒
    monkeypatch.setattr(spider.time, "sleep", lambda *_: None)#把sleep换为空

    结果 = spider.fetch_one_page("http://fake", max_attempts=3)

    assert 结果 == []
    assert len(调用记录) == 3        # 确实重试了 3 次


def test_fetch_one_page_首次成功不重试(monkeypatch):
    """第一次就拿到有效页面时，只应请求 1 次。"""
    调用记录 = []

    def 假的fetch_page(url, **kwargs):
        调用记录.append(url)
        return SAMPLE_HTML, url#这个SAMPLE_HTML哪来的,干嘛用的,他是如何得到有效界面的

    monkeypatch.setattr(spider, "fetch_page", 假的fetch_page)
    monkeypatch.setattr(spider.time, "sleep", lambda *_: None)

    结果 = spider.fetch_one_page("http://fake")

    assert len(结果) == 2            # SAMPLE_HTML 里有两所
    assert len(调用记录) == 1        # 没有多余请求
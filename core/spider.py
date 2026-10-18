from lxml import etree
import requests
import pandas as pd
import time
import random
from queue import Queue,Empty
from threading import Thread
import os
from urllib.parse import urlencode,urljoin
from collections.abc import Iterator
import logging.config
import settings
logging.config.dictConfig(settings.LOG_CONFIG)#加载字典
logger=logging.getLogger("logger_console")
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
会话=requests.session()

def 获取网页(
    网址: str,
    超时: int = 5,
    最大重试: int = 3,
    重试间隔: float = 1.0,
    代理: str | None = None,

) -> tuple[str | None, str | None]:
    
    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    if 代理:
        proxies = {"http":代理,"https":代理}
    else:
        proxies=None
    
    for 尝试 in range(最大重试):
        try:
            headers = {
            # UA：浏览器身份标识，必须加
            "User-Agent": UA,
            "Referer":"https://yz.chsi.com.cn/sch/",
            }
            resp=会话.get(网址,headers=headers,timeout=超时,proxies=proxies)
            当前页面=resp.url
            if resp.status_code == 200:
                return resp.text,当前页面
            if resp.status_code == 404:
                return None,None
            if resp.status_code in (403,500):
                logger.warning(f"服务器无响应,重试第{尝试+1}次尝试")
                time.sleep(重试间隔*(2**尝试))
                continue
            resp.raise_for_status()
            return resp.text,当前页面
        except (requests.Timeout, requests.ConnectionError):
            logger.warning(f"第 {尝试+1} 次失败，重试... {网址}")
            time.sleep(重试间隔 * (2 ** 尝试))
    return None,None
            
            



def 解析院校列表(html: str, 当前页面: str) -> list[dict]:
    if not html:
        return []
    tree = etree.HTML(html)
    院校列表 = []
    qull_list = tree.xpath('//div[@class="sch-item"]')
    for i in qull_list:
        院校名字 = i.xpath('.//a[@class="name js-yxk-yxmc text-decoration-none"]/text()')
        所有地址文本 = i.xpath('.//div[@class="sch-department"]/text()')
        院校导航页_片段 = i.xpath('.//a[@class="name js-yxk-yxmc text-decoration-none"]/@href')
        
        院校名字 = 院校名字[0].strip() if 院校名字 else ""
        院校地址 = next((t.strip() for t in 所有地址文本 if t.strip()), "")
        院校导航页_片段 = 院校导航页_片段[0].strip() if 院校导航页_片段 else ""
        院校导航页_整合 = urljoin(当前页面, 院校导航页_片段)
        
        院校列表.append({
            "院校名称": 院校名字,
            "所在地": 院校地址,
            "院校网站": 院校导航页_整合,
        })
    return 院校列表
def 抓一页(网址:str,最大重试:int=4)->list[dict]:
    """抓一页,空响应视为失败并重试.返回解析出的校院列表"""
    for 次 in range(最大重试):
        html,真实地址 = 获取网页(网址)
        if html:
            行 = 解析院校列表(html,真实地址)
            if 行:
                return 行
            logger.warning(f"空响应 start={网址} 第{次+1}次 长度={len(html)}")
        else:
            logger.warning(f"获取失败 {网址} 第{次+1}次")
        time.sleep(3*(2**次))
    logger.error(f"放弃 {网址}：重试 {最大重试} 次仍为空")
    return []


def 生产者(网址迭代器: Iterator[str], 待爬队列: Queue) -> None:
    """把 URL 放进队列"""
    
    for i in 网址迭代器:
        待爬队列.put(i)


def 消费者(待爬队列: Queue, 结果队列: Queue,代理:str = None) -> None:
    """从队列取 URL，爬取，解析，结果放结果队列"""
    while True:
        try:
            待爬网址=待爬队列.get(timeout=1)
        except Empty:
            break
        try:
            结果 = 抓一页(待爬网址)
            if 结果:
                结果队列.put(结果)
        except Exception:
            logger.exception(f"消费者异常{待爬网址}")
        finally:
            待爬队列.task_done()
            



def 多线程爬取(起始网址: str, 参数名="page",最大页数: int = 10, 线程数: int = 5,代理:str = None) -> list[dict]:
    待爬队列=Queue()
    结果队列=Queue()
    网址迭代器=偏移量迭代器(起始网址,参数名,最大页数)
    t1=Thread(target=生产者,args=(网址迭代器,待爬队列))
    t1.start()
    for _ in range(线程数):
        t2=Thread(target=消费者,args=(待爬队列,结果队列,代理),daemon=True)
        t2.start()
    待爬队列.join()
    院校结果=[]
    while True:
        try:
            结果=结果队列.get(timeout=1)
            院校结果.extend(结果)
        except Empty:
            break
    return 院校结果



def 增量保存(新数据: list[dict], 文件路径: str) -> int:
    """
    增量写入 CSV，不重复存储。
    
    返回：
        实际新增的条数
    """
    if not os.path.isabs(文件路径):
        文件路径 = os.path.join(BASE_DIR, 文件路径)
    os.makedirs(os.path.dirname(文件路径), exist_ok=True)   # 目录不存在就建
    新df=pd.DataFrame(新数据)
    if os.path.exists(文件路径):
        旧df=pd.read_csv(文件路径,encoding="utf-8-sig")
        合并去重=pd.concat([旧df,新df]).drop_duplicates(
            subset=["院校名称"],keep="first"
        )
        合并去重.to_csv(文件路径,encoding="utf-8-sig",index=False)
        条数=len(合并去重)-len(旧df)
        return 条数
    else:
        
        新df.to_csv(文件路径,encoding="utf-8-sig",index=False)
        条数=len(新df)
        return 条数
    
def 翻页迭代器(基础网址, 参数名="page", 最大页数=50) -> Iterator[str]:
    """生成每一页的 URL"""
    for i in range(1,最大页数+1):
        params = {参数名:i,"size":20}
        url = urljoin(基础网址,"?"+urlencode(params))
        yield url
def 偏移量迭代器(基础网址, 参数名="start", 最大页数=50) -> Iterator[str]:
    """生成每一页的 URL"""
    e=0
    for _ in range(1,最大页数+1):
        
        params = {参数名:e}
        url = urljoin(基础网址,"?"+urlencode(params))
        e=e+20
        yield url
def main(网址:str,参数:str,最大页数:int,线程数:int,保存地址:str):
    结果=多线程爬取(网址,参数,最大页数,线程数)
    新增=增量保存(结果,保存地址)
    期望 = 46*20+16
    logger.info(f"本次抓到 {len(结果)} 条，新增 {新增} 条")
    if len(结果) < 期望 * 0.95:
        logger.error(f"数据可能不完整：{len(结果)} / 期望约 {期望}")

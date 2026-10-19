"""研招网院校库爬虫：抓取院校列表、解析、增量保存。"""

from lxml import etree
import requests
import pandas as pd
import time
import random
from queue import Queue, Empty
from threading import Thread
import os
from urllib.parse import urlencode, urljoin
from collections.abc import Iterator
import logging.config

import settings

logging.config.dictConfig(settings.LOG_CONFIG)
logger = logging.getLogger("logger_console")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSION = requests.session()

# 固定桌面 UA：随机 UA 会命中移动端版本，站点返回无列表的 SPA 页面
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_page(
    url: str,
    timeout: int = 5,
    max_retries: int = 3,
    retry_interval: float = 1.0,
    proxy: str | None = None,
) -> tuple[str | None, str | None]:
    """请求单个页面。

    Args:
        url: 目标页面地址。
        timeout: 单次请求超时秒数。
        max_retries: 最大尝试次数。
        retry_interval: 重试基础间隔，按指数退避。
        proxy: 可选代理地址。

    Returns:
        (html, real_url)；失败时返回 (None, None)。
    """
    proxies = {"http": proxy, "https": proxy} if proxy else None

    for attempt in range(max_retries):
        try:
            headers = {
                "User-Agent": UA,
                "Referer": "https://yz.chsi.com.cn/sch/",
            }
            resp = SESSION.get(url, headers=headers, timeout=timeout, proxies=proxies)
            real_url = resp.url
            if resp.status_code == 200:
                return resp.text, real_url
            if resp.status_code == 404:
                return None, None
            if resp.status_code in (403, 500):
                logger.warning(f"服务器无响应，第 {attempt + 1} 次重试：{url}")
                time.sleep(retry_interval * (2**attempt))
                continue
            resp.raise_for_status()
            return resp.text, real_url
        except (requests.Timeout, requests.ConnectionError):
            logger.warning(f"第 {attempt + 1} 次失败，重试... {url}")
            time.sleep(retry_interval * (2**attempt))
    return None, None


def parse_school_list(html: str, real_url: str) -> list[dict]:
    """解析一页院校列表。

    Args:
        html: 页面 HTML 文本。
        real_url: 该页的真实地址（用于拼接相对链接）。

    Returns:
        院校字典列表，每项含 院校名称 / 所在地 / 院校网站。
    """
    if not html:
        return []
    tree = etree.HTML(html)
    schools: list[dict] = []
    for item in tree.xpath('//div[@class="sch-item"]'):
        name = item.xpath('.//a[@class="name js-yxk-yxmc text-decoration-none"]/text()')
        address_texts = item.xpath('.//div[@class="sch-department"]/text()')
        href = item.xpath('.//a[@class="name js-yxk-yxmc text-decoration-none"]/@href')

        name = name[0].strip() if name else ""
        province = next((t.strip() for t in address_texts if t.strip()), "")
        href = href[0].strip() if href else ""
        school_url = urljoin(real_url, href)

        schools.append(
            {
                "院校名称": name,
                "所在地": province,
                "院校网站": school_url,
            }
        )
    return schools


def fetch_one_page(url: str, max_attempts: int = 4) -> list[dict]:
    """抓取一页并把「空响应」当作失败重试。

    站点在部分请求下会返回 200 但没有院校列表的页面，直接解析会静默丢数据。

    Args:
        url: 页面地址。
        max_attempts: 最大尝试次数。

    Returns:
        解析出的院校列表；重试耗尽返回空列表。
    """
    for attempt in range(max_attempts):
        html, real_url = fetch_page(url)
        if html:
            rows = parse_school_list(html, real_url)
            if rows:
                return rows
            logger.warning(f"空响应 {url} 第 {attempt + 1} 次，长度={len(html)}")
        else:
            logger.warning(f"获取失败 {url} 第 {attempt + 1} 次")
        time.sleep(3 * (2**attempt))
    logger.error(f"放弃 {url}：重试 {max_attempts} 次仍为空")
    return []


def producer(url_iter: Iterator[str], url_queue: Queue) -> None:
    """把 URL 迭代器中的地址逐个放进队列。"""
    for url in url_iter:
        url_queue.put(url)


def consumer(url_queue: Queue, result_queue: Queue, proxy: str = None) -> None:
    """从队列取 URL，抓取解析后把结果放进结果队列。

    无论成败都必须 task_done()，否则主线程 join() 永远不返回。
    """
    while True:
        try:
            url = url_queue.get(timeout=1)
        except Empty:
            break
        try:
            result = fetch_one_page(url)
            if result:
                result_queue.put(result)
        except Exception:
            logger.exception(f"消费者异常：{url}")
        finally:
            url_queue.task_done()
        time.sleep(random.uniform(2, 5))


def crawl_pages(
    base_url: str,
    param_name: str = "page",
    max_pages: int = 10,
    threads: int = 5,
    proxy: str = None,
) -> list[dict]:
    """多线程爬取多页。

    Args:
        base_url: 起始地址。
        param_name: 分页参数名。
        max_pages: 最大页数。
        threads: 消费者线程数。
        proxy: 可选代理。

    Returns:
        所有页面合并后的院校列表。
    """
    url_queue: Queue = Queue()
    result_queue: Queue = Queue()
    url_iter = offset_iter(base_url, param_name, max_pages)

    t1 = Thread(target=producer, args=(url_iter, url_queue))
    t1.start()
    for _ in range(threads):
        t2 = Thread(target=consumer, args=(url_queue, result_queue, proxy), daemon=True)
        t2.start()

    url_queue.join()

    all_schools: list[dict] = []
    while True:
        try:
            result = result_queue.get(timeout=1)
            all_schools.extend(result)
        except Empty:
            break
    return all_schools


def save_incremental(new_records: list[dict], file_path: str) -> int:
    """增量写入 CSV，按院校名称去重。

    Args:
        new_records: 本次抓到的记录。
        file_path: 目标 CSV；相对路径按项目根目录解析。

    Returns:
        实际新增的条数。
    """
    if not os.path.isabs(file_path):
        file_path = os.path.join(BASE_DIR, file_path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    new_df = pd.DataFrame(new_records)
    if os.path.exists(file_path):
        old_df = pd.read_csv(file_path, encoding="utf-8-sig")
        merged = pd.concat([old_df, new_df]).drop_duplicates(
            subset=["院校名称"], keep="first"
        )
        merged.to_csv(file_path, encoding="utf-8-sig", index=False)
        return len(merged) - len(old_df)

    new_df.to_csv(file_path, encoding="utf-8-sig", index=False)
    return len(new_df)


def page_iter(base_url: str, param_name: str = "page", max_pages: int = 50) -> Iterator[str]:
    """按页码生成每一页的 URL。"""
    for i in range(1, max_pages + 1):
        params = {param_name: i, "size": 20}
        yield urljoin(base_url, "?" + urlencode(params))


def offset_iter(base_url: str, param_name: str = "start", max_pages: int = 50) -> Iterator[str]:
    """按偏移量生成每一页的 URL（每页 20 条）。"""
    offset = 0
    for _ in range(1, max_pages + 1):
        params = {param_name: offset}
        yield urljoin(base_url, "?" + urlencode(params))
        offset += 20


def main(
    base_url: str,
    param_name: str,
    max_pages: int,
    threads: int,
    save_path: str,
) -> None:
    """爬取入口：抓取、保存、校验完整性。"""
    result = crawl_pages(base_url, param_name, max_pages, threads)
    added = save_incremental(result, save_path)

    expected = 46 * 20 + 16  # 47 页，最后一页 16 条
    logger.info(f"本次抓到 {len(result)} 条，新增 {added} 条")
    if len(result) < expected * 0.95:
        logger.error(f"数据可能不完整：{len(result)} / 期望约 {expected}")

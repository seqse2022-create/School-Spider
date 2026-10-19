"""爬虫入口。"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core.spider import main

if __name__ == "__main__":
    main(
        "https://yz.chsi.com.cn/sch/",
        param_name="start",
        max_pages=47,
        threads=1,
        save_path=r"data\schools.csv",
    )

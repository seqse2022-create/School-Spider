#因为运行代码脚本在bin所以bin为顶级包,只能绝对导入,可以用sys将项目文件导入环境,就可以用相对导入了
import os
import sys
BASE_DIR=os.path.dirname(os.path.dirname(__file__))#__file__获得文件绝对路径,os获取父级
sys.path.append(BASE_DIR)
from core.spider import main
if __name__ =="__main__":
    main("https://yz.chsi.com.cn/sch/",参数="start",最大页数=47,线程数=1,保存地址=r"data\\schools.csv")
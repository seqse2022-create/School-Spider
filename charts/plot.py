import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False  
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

csv_path = os.path.join(BASE_DIR, "data", "schools.csv")

def 各省招生单位数量统计():
    df=pd.read_csv(csv_path,encoding="utf-8-sig")
    counts = df["所在地"].value_counts()  
    counts=counts.sort_values(ascending=True, kind="stable")#默认返回新对象，不修改原对象
    plt.figure(figsize=(8, 10))        # 加高画布
    plt.yticks(fontsize=9)             # 字号调小
    bars =plt.barh(counts.index, counts.values)
    plt.bar_label(bars, fmt="%d", padding=2)#加数值标签
    plt.xlabel("招生单位数量")
    plt.ylabel("招生单位")
    plt.title("各省招生单位数量")
    plt.tight_layout()  
    png_path = os.path.join(BASE_DIR, "charts", "各省招生单位数量.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    
def 院校名称类型占比():
    def 分类(name):
        if "研究院" in name: return "研究院"
        elif "研究所" in name: return "研究所"
        elif "大学" in name: return "大学"
        elif "学院" in name: return "学院"
        return "其他"
    df=pd.read_csv(csv_path,encoding="utf-8-sig")
    counts = df["院校名称"].map(分类).value_counts()
    #上分类数据,下画图
    plt.rcParams['font.size'] = 20
    plt.figure(figsize=(8, 10))        # 加高画布
    plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%")#正式画图
    plt.title("全国院校类型占比")
    png_path = os.path.join(BASE_DIR, "charts", "院校类型占比.png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    
def 全国VS北京_院校名称类型占比(含北京: bool = False):
    def 分类(name):
        if "研究院" in name: return "研究院"
        elif "研究所" in name: return "研究所"
        elif "大学" in name: return "大学"
        elif "学院" in name: return "学院"
        return "其他"
    #将北京和全国分为两组并统计各院校数量
    df=pd.read_csv(csv_path,encoding="utf-8-sig")
    bj_group = df[df["所在地"] == "北京"]
    if 含北京:
        country_group = df
        文件名 = "包括北京"
        标签 = "全国（含北京）"
    else:
        country_group = df[df["所在地"] != "北京"]
        文件名 = "不包括北京"
        标签 = "全国（不含北京）"
    bj_counts = bj_group["院校名称"].map(分类).value_counts()
    cn_counts = country_group["院校名称"].map(分类).value_counts()
    
    
    类别=["研究院","研究所","大学","学院","其他"]
    bj_counts = bj_counts.reindex(类别).fillna(0)## 按给定顺序重排；缺的补 NaN
    cn_counts = cn_counts.reindex(类别).fillna(0)
    x = np.arange(len(类别))
    #数值计算,我应该搞成函数的
    bj_pct = bj_counts / bj_counts.sum() * 100     # 北京内部的占比
    cn_pct = cn_counts / cn_counts.sum() * 100     # 外省内部的占比
    plt.bar(x - 0.2, bj_pct, width=0.4, label="北京")
    plt.bar(x + 0.2, cn_pct, width=0.4, label="全国")
    plt.xticks(x, 类别)
    plt.legend()
    plt.ylabel("占比(%)")
    plt.title(f"北京与{标签}各类高校对比")
    png_path = os.path.join(BASE_DIR, "charts", f"北京与全国各类高校对比({文件名}).png")
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    全国VS北京_院校名称类型占比(True)
    全国VS北京_院校名称类型占比(False)
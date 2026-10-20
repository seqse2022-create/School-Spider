# 写一个协程 fetch(name: str, delay: float) -> str：

# 打印 开始 {name}
# 用块 2 等待 delay 秒
# 打印 完成 {name}
# 返回 name
# 写一个主协程 main()：

# 用块 5 记录起点
# 用块 3 同时跑三个 fetch：A=1秒、B=2秒、C=3秒
# 打印 gather 返回的结果列表
# 打印总耗时，保留 1 位小数
# 用块 4 启动 main()，放在 if __name__ == "__main__": 下面
#任务一:
# import asyncio
# import time
# async def fetch_name(name,delay:float=None)->str:
#     print(f"开始{name}")
#     await asyncio.sleep(delay)
#     print(f"完成{name}")
#     return name
# async def main():
#     start=time.perf_counter()
#     result=await asyncio.gather(fetch_name(name="A",delay=1),fetch_name(name="B",delay=2),fetch_name(name="C",delay=3))
#     print(result)
#     end=time.perf_counter()
#     print(f"总耗时:{end-start:.1f}")
# if __name__ == "__main__":
#     asyncio.run(main())
##任务2
# import asyncio
# import time
# async def fetch_name(name,delay:float=None)->str:
#     print(f"开始{name}")
#     await asyncio.sleep(delay)
#     print(f"完成{name}")
#     return name
# async def main():
#     result=[]
#     start=time.perf_counter()
#     A_result=await fetch_name(name="A",delay=1)
#     B_result=await fetch_name(name="B",delay=2)
#     C_result=await fetch_name(name="C",delay=3)
#     result.extend([A_result[0],B_result[0],C_result[0]])
#     print(resuit)
#     end=time.perf_counter()
#     print(f"总耗时:{end-start:.1f}")
# if __name__ == "__main__":
#     asyncio.run(main())

#最终任务:
# 写协程 fetch_page(index: int) -> int：

# await asyncio.sleep(random.uniform(2, 5)) 模拟一次请求
# 返回 index
# 写 main()：

# 记录起点
# 用块 7 造出 47 个协程的列表
# 用块 8 + asyncio.gather 并发跑完
# 打印 拿到了 {len(结果)} 页
# 打印总耗时（1 位小数）
# if __name__ == "__main__": asyncio.run(main())


import asyncio
import time
import random
async def fetch_page(index: int) -> int:
    print(index)
    await asyncio.sleep(random.uniform(2, 5))
    return index
async def main(max_page):
    start=time.perf_counter()
    result_list=await asyncio.gather(*[fetch_page(i) for i in range(max_page)])
    print(f"拿到了{len(result_list)}页")
    end=time.perf_counter()
    print(result_list)
    print(f"耗时为{end-start:.1f}秒")
if __name__ == "__main__": 
    asyncio.run(main(47))


    

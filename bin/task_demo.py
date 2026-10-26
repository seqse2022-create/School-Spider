import asyncio
import time
async def work(name: str, delay: float) -> str:
    print(f"开始{name}")
    await asyncio.sleep(delay)
    return name

async def main():
    task = asyncio.create_task(work("A",2))
    print(f"{task.done()}我创建完就继续了")
    await asyncio.sleep(3)
    print(f"{task.done()}")
    print(f"{task.result()}")
if __name__ == "__main__":
    asyncio.run(main())
#未跑预测:run启动后先创建协程work,但因为asyncio.create_task不阻塞的特性,work会运行但cpu还在占用,所以不会先打印开始{name},而是继续
#运行主函数的f"{task.done()}我创建完就继续了",然后主函数开始睡,cpu切换到work运行,打印f"开始{name}",然后睡眠,因为work只睡2秒,主函数
#睡两秒,所以work先结束运行,返回name,紧接着主函数醒过来,运行print(f"{task.done()}")得到完成的提示然后运行print(f"{task.result()}")不等待得到答案
# 运行结果:
# False我创建完就继续了
# 开始A
# True
# A
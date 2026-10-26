import asyncio
import time
async def read_lines(count: int, delay: float):
    for i in range(count):
        await  asyncio.sleep(delay)
        yield f"第{i}行" 
        
class Timer :
    async def __aenter__(self):
        self.start=time.perf_counter()
        return self  
    async def __aexit__(self, exc_type, exc, tb):
        self.end = time.perf_counter()
        print(f"用时{self.end-self.start}")
#_aexit__ 的返回值有特殊含义：返回真值 = "异常我已经处理了，别再抛出去",所以正确写法：不 return，或 return False



async def main():
    async with Timer():
        async for line in read_lines(5, 0.5):
            print(line)
            
if __name__ == "__main__":
    asyncio.run(main())

#跑前预测:当程序遇到第一个sleep时创建一个后台计时器,cpu不等,继续下一次循环,可以看做所有循环同时计时总用时0.5
#结果:
# 第0行
# 第1行
# 第2行
# 第3行
# 第4行
# 用时2.5446776999742724
#预测失败猜想   yield f"第{i}行" 每遍历取值一次,代码才返回一个值,阻塞了代码的运行
#验证:如果猜想成立

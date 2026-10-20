import asyncio
import time
import random


async def fetch_page(index: int) -> int:
    async with 闸门:
        print(index)
        await asyncio.sleep(random.uniform(2, 5))
        return index
    
    
async def main(max_page):
    闸门 = asyncio.Semaphore(5)
    start=time.perf_counter()
    result_list=await asyncio.gather(*[fetch_page(i) for i in range(max_page)])
    print(f"拿到了{len(result_list)}页")
    end=time.perf_counter()
    print(result_list)
    print(f"耗时为{end-start:.1f}秒")
    
    
if __name__ == "__main__": 
    asyncio.run(main(47))

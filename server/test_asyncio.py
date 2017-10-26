import asyncio
import time

ITERS = 800

async def go():
    deltas = 0
    delta = 0
    t2 = None
    t1 = None
    for _ in range(0, ITERS):
        t1 = time.time()
        await asyncio.sleep(0.01 - delta)
        t2 = time.time()
        delta = t2 - t1 - 0.01
        deltas += abs(delta)

    print('avg deviation: {}'.format(deltas / ITERS))


def go_2():
    deltas = 0
    delta = 0
    t2 = None
    t1 = None
    for _ in range(0, ITERS):
        t1 = time.time()
        time.sleep(0.01 - delta)
        t2 = time.time()
        delta = t2 - t1 - 0.01
        deltas += abs(delta)

    print('avg native deviation: {}'.format(deltas / ITERS))

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(go())
    loop.close()
    go_2()


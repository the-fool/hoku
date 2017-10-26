import asyncio
import time
import multiprocessing as mp
import threading
import queue

META_ITERS = 1000
ITERS = 1000


async def putter(q, loop):
    for _ in range(META_ITERS):
        for _ in range(ITERS):
            await q.put(loop.time())


async def getter(q, loop):
    meta_deltas = 0
    for _ in range(META_ITERS):
        t1 = time.time()
        for _ in range(ITERS):
            foo = await q.get()
        t2 = time.time()
        meta_deltas += ((t2 - t1) / ITERS)

    meta_deltas /= META_ITERS

    print('avg wait: {}'.format(meta_deltas))
    return foo


def th_putter(q):
    for _ in range(META_ITERS):
        for _ in range(ITERS):
            q.put(time.time())


def th_getter(q):
    meta_deltas = 0
    for _ in range(META_ITERS):
        t1 = time.time()
        for _ in range(ITERS):
            foo = q.get()
        t2 = time.time()
        meta_deltas += ((t2 - t1) / ITERS)

    meta_deltas /= META_ITERS

    print('avg th wait: {}'.format(meta_deltas))
    return foo


def mp_putter(q):
    for _ in range(META_ITERS):
        for _ in range(ITERS):
            q.put(time.time())


def mp_getter(q):
    meta_deltas = 0
    for _ in range(META_ITERS):
        t1 = time.time()
        for _ in range(ITERS):
            foo = q.get()
        t2 = time.time()
        meta_deltas += ((t2 - t1) / ITERS)

    meta_deltas /= META_ITERS

    print('avg mp wait: {}'.format(meta_deltas))
    return foo


def go():
    loop = asyncio.get_event_loop()

    q = asyncio.Queue()

    loop.run_until_complete(asyncio.gather(putter(q, loop), getter(q, loop)))

    loop.close()

    q = queue.Queue()

    t_p = threading.Thread(target=th_putter, args=(q, ))
    t_g = threading.Thread(target=th_getter, args=(q, ))

    t_p.start()
    t_g.start()

    t_p.join()
    t_g.join()

    q = mp.Queue()

    mp_put = mp.Process(target=mp_putter, args=(q, ))
    mp_get = mp.Process(target=mp_getter, args=(q, ))

    mp_put.start()
    mp_get.start()

    mp_put.join()
    mp_get.join()

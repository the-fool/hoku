import asyncio
import time

from socket import socketpair
import socket

ITERS = 40000


async def get_data_plain(loop):
    rsock, wsock = socketpair()

    r, w = await asyncio.open_unix_connection(sock=rsock, loop=loop)
    # Simulate the reception of data from the network
    t = time.time()
    for _ in range(0, ITERS):
        loop.call_soon(wsock.send, 'abc'.encode())
        data = await r.read(4)
    t2 = time.time()

    print('Plain avg: {}'.format((t2 - t) / ITERS))


def go():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_data_plain(loop))
    loop.close()

import time
import logging
import asyncio


async def metronome(cbs, bpm_queue, bpm=120):
    ts = 0
    steps = 4
    offset = 0

    logging.info('Creating Metronome at bpm {} - steps {}'.format(bpm, steps))

    while True:
        sleep_time = max(0, (60 / bpm / steps - offset))
        await asyncio.sleep(sleep_time)

        # start timer
        t = time.time()

        # monotonic timestamp increment
        ts += 1

        # send the 'tick' to all listeners
        for cb in cbs:
            await cb(ts)

        # check if the bpm has changed
        if not bpm_queue.empty():
            bpm = await bpm_queue.get()

        # calc offset
        offset = time.time() - t

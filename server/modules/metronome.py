import time
import logging
import asyncio


class Metronome:
    def __init__(self, cbs=[], bpm=120, steps=4):
        logging.info(
            'Creating Metronome at bpm {}'.format(bpm))
        self.bpm = bpm
        self.steps = steps
        self.cbs = cbs

    def set_bpm(self, new_bpm):
        self.bpm = new_bpm

    async def run(self):
        ts = 0
        offset = 0

        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - offset))
            await asyncio.sleep(sleep_time)

            # start timer
            t = time.time()

            # monotonic timestamp increment
            ts += 1

            # send the 'tick' to all listeners
            for cb in self.cbs:
                await cb(ts)

            # calc offset
            offset = time.time() - t

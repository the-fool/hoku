import time
import logging


class Metronome:
    def __init__(self, pipes, bpm=110, steps=4):
        self.ts = 0  # unique timestamp -- just an incrementing int!
        self.bpm = bpm
        self.pipes = pipes
        self.steps = steps
        logging.debug(
            "Metronome starting: BPM {}, STEPS {}".format(bpm, steps))

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            t = time.time()
            for pipe in self.pipes:
                pipe.send(self.ts)
            self.ts = self.ts + 1
            sleep_offset = time.time() - t


import asyncio


async def metronome(qs, bpm_queue):
    ts = 0
    bpm = 120
    steps = 4
    offset = 0
    while True:
        sleep_time = max(0, (60 / bpm / steps - offset))
        ts += 1
        await asyncio.sleep(sleep_time)
        async for q in qs:
            await q.put(ts)
    if not bpm_queue.empty:
        pass

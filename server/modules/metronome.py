import time
import logging
from ctypes import CFUNCTYPE, c_int

CB_CTYPE = CFUNCTYPE(None, c_int)


class Metronome:
    def __init__(self, pipes, cbs, cbs_length, bpm=110, steps=4):
        self.ts = 0  # unique timestamp -- just an incrementing int!
        self.bpm = bpm
        self.pipes = pipes
        self.steps = steps
        self.cbs_length = cbs_length
        self.cbs = cbs
        logging.debug("Metronome starting: BPM {}, STEPS {}".format(bpm, steps))

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            t = time.time()
            cbs = self.cbs[:self.cbs_length.value]
            for cb in cbs:
                cb(self.ts)
                # self.worker_queue.put({'task': cb, 'args': [self.ts]})
            self.ts = self.ts + 1
            sleep_offset = time.time() - t

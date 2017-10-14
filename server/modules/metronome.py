import time
import logging
from ctypes import CFUNCTYPE, c_int

CB_CTYPE = CFUNCTYPE(None, c_int)


class Metronome:
    def __init__(self, cbs, cbs_length, worker_queue, bpm=110, steps=4):
        self.ts = 0  # unique timestamp -- just an incrementing int!
        self.bpm = bpm
        self.steps = steps
        self.cbs_length = cbs_length
        self.cbs = cbs
        self.worker_queue = worker_queue
        logging.debug("Metronome starting: BPM {}, STEPS {}".format(bpm, steps))

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            logging.debug("Metronome BEAT {}".format(self.ts))
            t = time.time()
            cbs = self.cbs[:self.cbs_length.value]
            for cb in cbs:
                cb(self.ts)
                # self.worker_queue.put({'task': cb, 'args': [self.ts]})
            self.ts = self.ts + 1
            sleep_offset = time.time() - t

import time


class Metronome:
    def __init__(self, cbs, worker_queue, bpm=110, steps=4):
        self.ts = 0  # unique timestamp -- just an incrementing int!
        self.bpm = bpm
        self.steps = steps
        self.cbs = cbs
        self.worker_queue = worker_queue

    def register_cb(self, cb):
        self.cbs.append(cb)

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            t = time.time()
            for cb in self.cbs:
                self.worker_queue.put({'task': cb, 'args': [self.ts]})
            self.ts = self.ts + 1
            sleep_offset = time.time() - t

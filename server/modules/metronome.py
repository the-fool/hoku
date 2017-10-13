import time


class Metronome:
    def __init__(self, cbs, worker, bpm=110, steps=4):
        self.ts = 0  # unique timestamp -- just an incrementing int!
        self.bpm = bpm
        self.steps = steps
        self.cbs = cbs
        self.worker = worker

    def register_cb(self, cb):
        self.cbs.append(cb)

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            t = time.time()
            self.worker.add_all(self.cbs, self.ts)
            self.ts = self.ts + 1
            sleep_offset = time.time() - t

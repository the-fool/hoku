import time
import threading


class Metronome:
    def __init__(self, worker, bpm=110, steps=4):
        self.ts = 0
        self.bpm = bpm
        self.steps = steps
        self.lock = threading.Lock()
        self.cbs = set()
        self.worker = worker

    def register_cb(self, cb):
        with self.lock:
            self.cbs.add(cb)

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            t = time.time()
            with self.lock:
                self.worker.add_all([task for task in self.cbs], self.ts)
            self.ts = self.ts + 1
            sleep_offset = time.time() - t

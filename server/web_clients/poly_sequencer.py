import multiprocessing


class PolySequencer:
    def __init__(self, clock_pipe, msg, notes=[]):
        self.notes = multiprocessing.Manager().list(notes)
        self.msg = msg
        self.clock_pipe = clock_pipe

    def start(self):
        while True:
            ts = self.clock_pipe.recv()
            self.beat(ts)

    def beat(self, ts):
        pass
        # print(ts)
        # do instrument cb

    def set_notes(self, new_notes):
        print(new_notes)

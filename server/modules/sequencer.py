import logging

# DEPRECATED!  Synchronous, bad, old!

class Sequencer:
    def __init__(self, worker_pipe, on_trigger_msgs, clock_pipe, notes):
        self.off_note = 0
        self.step = 0
        self.clock_pipe = clock_pipe
        self.notes = notes
        self.worke_pipe = worker_pipe
        self.on_trigger_msgs = on_trigger_msgs

    def start(self):
        logging.debug('Mono sequencer starting')
        while True:
            ts = self.clock_pipe.recv()
            self.beat(ts)

    def beat(self, ts):
        # when note is == 0, hold
        # when note is < 0, rest

        note = self.notes[self.step]

        # we either have a note, or a rest -- do note off!
        if note is not 0:
            for msg in self.on_trigger_msgs:
                task = {
                    'instrument_name': msg[0],
                    'method': msg[2],
                    'payload': [self.off_note, self.step]
                }
                self.worke_pipe.send(task)

        # we have a note -- play it!
        if note > 0:
            self.off_note = note
            for msg in self.on_trigger_msgs:
                task = {
                    'instrument_name': msg[0],
                    'method': msg[1],
                    'payload': [note, self.step]
                }
                self.worke_pipe.send(task)

        self.step = (self.step + 1) % len(self.notes)

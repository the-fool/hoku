from ctypes import CFUNCTYPE, c_int, Structure

import logging

CB_CTYPE = CFUNCTYPE(None, c_int, c_int)


class OnStepCbs(Structure):
    _fields_ = [('on', CB_CTYPE), ('off', CB_CTYPE)]


class Sequencer:
    def __init__(self, clock_pipe, cbs, cbs_length, notes):
        self.off_note = 0
        self.step = 0
        self.clock_pipe = clock_pipe
        self.notes = notes
        self.cbs = cbs
        self.cbs_length = cbs_length

    def start(self):
        logging.debug('Mono sequencer starting')
        while True:
            ts = self.clock_pipe.recv()
            self.beat(ts)

    def beat(self, ts):
        # when note is == 0, hold
        # when note is < 0, rest

        note = self.notes[self.step]

        # make a local copy
        l = self.cbs_length.value
        cbs = self.cbs[:l]

        # we either have a note, or a rest -- do note off!
        if note is not 0:
            for cb in cbs:
                cb.off(self.off_note, self.step)

        # we have a note -- play it!
        if note > 0:
            self.off_note = note
            for cb in cbs:
                cb.on(note, self.step)

        self.step = (self.step + 1) % len(self.notes)

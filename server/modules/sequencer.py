from ctypes import CFUNCTYPE, c_int, Structure

CB_CTYPE = CFUNCTYPE(c_int, c_int, c_int)


class OnStepCbs(Structure):
    _fields_ = [('on', CB_CTYPE), ('off', CB_CTYPE)]


class Sequencer:
    def __init__(self, cbs, cbs_length, notes):
        self.off_note = 0
        self.step = 0
        self.notes = notes
        self.cbs = cbs
        self.cbs_length = cbs_length

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
                cb.off(note=self.off_note, step=self.step)

        # we have a note -- play it!
        if note > 0:
            self.off_note = note
            for cb in cbs:
                cb.on(note=note, step=self.step)

        self.step = (self.step + 1) % len(self.notes)

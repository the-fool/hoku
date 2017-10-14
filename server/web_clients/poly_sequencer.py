import multiprocessing


class PolySequencer:
    def __init__(self, instrument_cb, notes=[]):
        self.notes = multiprocessing.Manager().list(notes)
        self.cb = instrument_cb

    def beat(self, note, step):
        print(note, step)
        # do instrument cb

    def set_notes(self, new_notes):
        print(new_notes)

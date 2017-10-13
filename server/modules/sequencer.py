class Sequencer:
    def __init__(self, cbs, notes):
        self.off_note = 0
        self.step = 0
        self.notes = notes
        self.on_step_cbs = cbs

    def beat(self, ts):
        note = self.notes[self.step]
        # make a local copy
        cbs = list(self.on_step_cbs)
        if note is not 0:
            for cb in cbs:
                # when note is == 0, hold
                # when note is < 0, rest
                off = cb.get('off', None)
                if off:
                    off(note=self.off_note, step=self.step)
        if note > 0:
            self.off_note = note
            for cb in cbs:
                on = cb.get('on', None)
                if on:
                    on(note=note, step=self.step)
        self.step = (self.step + 1) % len(self.notes)

import random


class Sequencer:
    def __init__(self, cbs, notes=None):
        self.off_note = 0
        self.step = 0
        self.notes = notes or [random.randrange(20, 80, 2) for _ in range(32)]
        self.on_step_cbs = cbs

    def beat(self, ts):
        note = self.notes[self.step]
        if note is not 0:
            for cb in self.on_step_cbs:
                # when note is == 0, hold
                # when note is < 0, rest
                off = cb.get('off', None)
                if off:
                    off(note=self.off_note, step=self.step)
        if note > 0:
            self.off_note = note
            for cb in self.on_step_cbs:
                on = cb.get('on', None)
                if on:
                    on(note=note, step=self.step)
        self.step = (self.step + 1) % len(self.notes)

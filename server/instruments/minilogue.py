from .base import BaseInstrument


class Minilogue(BaseInstrument):
    AMP_ATTACK = 16
    AMP_DECAY = 17
    EG_ATTACK = 20
    EG_DECAY = 21
    VOICE_MODE = 27
    CUTOFF = 43
    RESONANCE = 44
    LFO_RATE = 24
    LFO_INT = 26

    def amp_decay(self, value):
        self._control(self.AMP_DECAY, value)

    def eg_decay(self, value):
        self._control(self.EG_DECAY, value)

    def cutoff(self, value):
        self._control(self.CUTOFF, value)

    def resonance(self, value):
        self._control(self.RESONANCE, value)

    def beat_on(self, note, step=0):
        self.note_on(note=note)

    def beat_off(self, note, step=0):
        self.note_off(note=note)

    def voice_mode(self, val):
        self._control(self.VOICE_MODE, val)

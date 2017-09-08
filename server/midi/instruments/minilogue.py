from .base import BaseInstrument


class Minilogue(BaseInstrument):
    VOICE_MODE = 27
    CUTOFF = 43
    RESONANCE = 44
    LFO_RATE = 24
    LFO_INT = 26

    def cutoff(self, value):
        self._control(self.CUTOFF, value)

    def resonance(self, value):
        self._control(self.RESONANCE, value)

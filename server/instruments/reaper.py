from .base import BaseInstrument


class Reaper(BaseInstrument):
    MINI_1_VOL = 9
    MINI_1_VERB = 10
    MINI_1_DIST = 11

    MINI_2_VOL = 15
    MINI_2_VERB = 12
    MINI_2_DIST = 13

    DRUM_VERB = 14

    def mini_1_vol(self, value):
        self._control(self.MINI_1_VOL, int(value))

    def mini_2_vol(self, value):
        self._control(self.MINI_2_VOL, int(value))

    def mini_1_dist(self, value):
        self._control(self.MINI_1_DIST, value)

    def mini_2_dist(self, value):
        self._control(self.MINI_2_DIST, value)

    def mini_1_verb(self, value):
        self._control(self.MINI_1_VERB, value)

    def mini_2_verb(self, value):
        self._control(self.MINI_2_VERB, value)

    def drum_verb(self, value):
        self._control(self.DRUM_VERB, value)

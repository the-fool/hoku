import logging

base = 60

rhythm_house = [
    [1, 0, 0, 0, 1, 0, 0, 0] * 2,
    [0, 0, 1, 0, 0, 0, 1, 0] * 2,
    [0, 0, 0, 1] * 4,
    [1, 0, 0, 1, 0, 0, 1, 0] * 2
]  # yapf: disable

rhythm_assault = [
    [1] * 16,
    [1] * 16,
    [1] * 16,
    [1, 0, 0, 1, 0, 0, 1, 0] * 2
]  # yapf: disable

all_rhythms = [
    rhythm_house,
    rhythm_assault,
    rhythm_house,
    rhythm_assault
]


class Drummer:
    def __init__(self, midi_devs=[]):
        self.midi_devs = midi_devs
        self.family = 0
        self.elements = [True] * 4

    def set_family(self, x):
        logging.info('New beat family: {}'.format(x))
        self.family = x

    def set_elements(self, els):
        logging.info('New beat elements: {}'.format(els))
        for i, _ in enumerate(self.elements):
            self.elements[i] = els[i]

    async def on_beat(self, ts):
        rhythm = all_rhythms[self.family]
        step = ts % 16
        base_note = base + self.family * 4
        for i, el in enumerate(rhythm):
            
            if self.elements[i] and el[step] is not 0:
                for drum_machine in self.midi_devs:
                    drum_machine.note_on(base_note + i)

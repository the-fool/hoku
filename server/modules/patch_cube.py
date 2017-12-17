import logging


class PatchCube:
    def __init__(self, instruments=[]):
        self.patch = 0
        self.instruments = instruments

    def set_patch(self, x):
        logging.info('New patch: {}'.format(x))
        if (self.patch is not x):
            self.patch = x
            self.bcast()

    def bcast(self):
        for i in self.instruments:
            i.program_change(self.patch)

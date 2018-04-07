import logging
from server.observable import observable_factory

class PatchCube:
    def __init__(self, instruments=[]):
        self.patch = 0
        self.instruments = instruments
        self.on_change, self.on_change_emit = observable_factory(
            self.patch)

    async def set_patch(self, x):
        logging.info('New patch: {}'.format(x))
        if (self.patch is not x):
            self.patch = x
            self.bcast()

            await self.on_change_emit(self.patch)

    def bcast(self):
        print('PATCHING', self.patch)
        for i in self.instruments:
            i.program_change(self.patch)

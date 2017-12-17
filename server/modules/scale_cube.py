import logging
import json
from server.observable import observable_factory

IONIAN = [0, 2, 4, 5, 7, 9, 11]

AEOLIAN = [0, 2, 3, 5, 7, 8, 10]

DORIAN = [0, 2, 3, 5, 7, 9, 11]

PHRYGIAN = [0, 1, 5, 7, 8, 10, 11]

LOCRIAN = [0, 2, 3, 4, 7, 8, 9]

MYXO = [0, 2, 4, 5, 7, 9, 10]

# six scales

SCALES = [IONIAN, AEOLIAN, DORIAN, PHRYGIAN, LOCRIAN, MYXO]


def msg_maker(scale_index):
    return json.dumps({'scale': scale_index})


class ScaleCube:
    """
    The Power Cube of Scales
    """

    def __init__(self, scales=SCALES, init_scale=0):
        self.scales = scales
        self.scale_index = init_scale
        self.scale = scales[init_scale]
        self.on_scale_change, self.on_scale_change_emit = observable_factory(
            self.scale)
        self.ws_msg_producer, self.emit = observable_factory(
            msg_maker(init_scale))

    async def set_scale(self, index):
        logging.info('Scale Cube changing to {}'.format(index))
        self.scale_index = index
        self.scale = self.scales[index]

        await self.on_scale_change_emit(self.scale)
        await self.emit(msg_maker(index))

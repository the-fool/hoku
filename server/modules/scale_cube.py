import logging
import json
from server.observable import observable_factory

IONIAN = [0, 2, 4, 5, 7, 9, 11]

AEOLIAN = [0, 2, 3, 5, 7, 8, 10]

LOCRIAN = [0, 1, 3, 5, 6, 8, 10]

WHOLE_TONE = [0, 2, 4, 6, 8, 10, 12]

GYPSY = [0, 2, 3, 6, 7, 8, 11]

PERSIAN = [0, 1, 4, 5, 6, 8, 11]

# six scales

SCALES = [IONIAN, AEOLIAN, WHOLE_TONE, GYPSY, LOCRIAN, PERSIAN]


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
        print('Scale Cube changing to {}'.format(index))
        self.scale_index = index
        self.scale = self.scales[index]

        await self.on_scale_change_emit(self.scale)
        await self.emit(msg_maker(index))

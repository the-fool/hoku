from server.observable import observable_factory
from server.util import scale
import json


def msg_maker(bpm: int):
    return json.dumps({'current_bpm': bpm})


bpm_range = (30, 190)


def scale_it(val):
    """
    The ws client does not know the actual bpm -- it sends a value from 0 to 1
    """
    return scale(val, 0, 1, bpm_range[0], bpm_range[1])


class MetronomeChanger:
    def __init__(self, init_bpm, on_change_cb):
        self.on_change_cb = on_change_cb
        self.obs, self.emit = observable_factory(msg_maker(init_bpm))

    async def ws_consumer(self, kind, payload, uuid):
        if kind == 'change':
            self.on_change_cb(scale_it(payload))
            await self.emit(msg_maker(payload))

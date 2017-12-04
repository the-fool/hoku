from server.observable import observable_factory
import json


def msg_maker(bpm: int):
    return json.dumps({'current_bpm': bpm})


class MetronomeChanger:
    def __init__(self, init_bpm, on_change_cb):
        self.on_change_cb = on_change_cb
        self.obs, self.emit = observable_factory(msg_maker(init_bpm))

    async def ws_consumer(self, kind, payload, uuid):
        if kind == 'change':
            self.on_change_cb(payload)
            self.emit(msg_maker(payload))

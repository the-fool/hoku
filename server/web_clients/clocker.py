import json
from server.observable import observable_factory


def clocker_factory():
    obs, emit = observable_factory()

    async def metronome_cb(ts):
        nonlocal emit
        """
        Passed to metronome
        """
        msg = json.dumps({'tick': ts})
        await emit(msg)

    async def clocker_ws_consumer(kind, payload, uuid):
        pass

    return obs, metronome_cb, clocker_ws_consumer

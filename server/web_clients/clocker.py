import json
from server.observable import observable_factory

"""
Send clock info to WebSocket clients
"""


def clocker_factory():
    obs, emit = observable_factory()

    async def metronome_cb(ts):
        nonlocal emit
        """
        Passed to metronome
        When called with ts, the observable emits a payload
        """
        msg = json.dumps({'tick': ts})
        await emit(msg)

    async def clocker_ws_consumer(kind, payload, uuid):
        pass

    return obs, metronome_cb, clocker_ws_consumer

import json
from server.observable import observable_factory


class Clocker:
    """
    Exposes an observable which emits a tick of the clock
    """

    def __init__(self):
        self.obs, self.emit = observable_factory()

    async def metronome_cb(self, ts):
        msg = json.dumps({'tick': ts})
        await self.emit(msg)

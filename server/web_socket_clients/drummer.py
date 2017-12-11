import json
from server.observable import observable_factory


class DrummerChanger:
    def __init__(self, drummer):
        self.drummer = drummer
        self.obs, self.emit = observable_factory(self.msg())

    async def ws_consumer(self, kind, payload, uuid):
        if kind == 'change_family':
            self.drummer.set_family(payload)
        elif kind == 'change_elements':
            self.drummer.set_elements(payload)

        await self.emit(self.msg())

    def msg(self):
        return json.dumps({
            'family': self.drummer.family,
            'elements': self.drummer.elements
        })

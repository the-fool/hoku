from server.observable import observable_factory
import json


def msg_maker(x: int):
    return json.dumps({'patch': x})


class CubeOfPatchChanger:
    def __init__(self, patch_cube):
        self.patch_cube = patch_cube
        self.obs, self.emit = observable_factory(self.msg_maker())

    async def ws_consumer(self, kind, payload, uuid):
        if kind == 'change':
            await self.patch_cube.set_patch(payload)
        await self.emit(self.msg_maker())

    def msg_maker(self):
        return json.dumps({'patch': self.patch_cube.patch})

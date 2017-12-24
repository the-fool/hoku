from server.observable import observable_factory
import json


def msg_maker(x: int):
    return json.dumps({'scale': x})


class CubeOfScaleChanger:
    def __init__(self, scale_cube):
        self.scale_cube = scale_cube
        self.obs, self.emit = observable_factory(
            msg_maker(scale_cube.scale_index))

    async def ws_consumer(self, kind, payload, uuid):
        if kind == 'change':
            await self.scale_cube.set_scale(payload)
        # await self.emit(msg_maker(self.scale_cube.scale_index))

    async def coro(self):
        producer_q, dispose = await self.scale_cube.on_scale_change()

        while True:
            try:
                await producer_q.get()
                await self.emit(msg_maker(self.scale_cube.scale_index))
            except:
                dispose()

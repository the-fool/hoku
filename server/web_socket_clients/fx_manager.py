from server.observable import observable_factory
import json


def msg_maker(fx_name, value):
    return json.dumps({'fx_name': fx_name, 'value': value})


class FxManager:
    def __init__(self, cbs={}):
        """
        cbs are a dict, keyed by a string name
        the callback takes a single value
        """
        self.cbs = cbs
        self.obs, self.emit = observable_factory()

    async def ws_consumer(self, kind, payload, uuid):
        cb = self.cbs.get(kind, None)
        if cb is None:
            return

        cb(payload)

        # echo to all subscribers
        self.emit(msg_maker(kind, payload))

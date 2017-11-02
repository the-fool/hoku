from server.observable import observable_factory
import json


def metronome_changer_factory(bpm_queue, bpm):
    obs, emit = observable_factory(bpm)

    async def ws_consumer(kind, payload, uuid):
        nonlocal bpm_queue

        if kind == 'change':
            await bpm_queue.put(payload)
            msg = json.dumps({'current_bpm': payload})
            await emit(msg)

    return obs, ws_consumer

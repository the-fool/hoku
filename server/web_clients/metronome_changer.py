from server.observable import observable_factory
import json


def msg_maker(bpm: int):
    return json.dumps({'current_bpm': bpm})


def metronome_changer_factory(bpm_queue, bpm):
    msg = msg_maker(bpm)
    obs, emit = observable_factory(msg)

    async def ws_consumer(kind, payload, uuid):
        nonlocal bpm_queue

        if kind == 'change':
            await bpm_queue.put(payload)
            msg = msg_maker(payload)
            await emit(msg)

    return obs, ws_consumer

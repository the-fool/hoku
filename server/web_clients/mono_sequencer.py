from server.observable import observable_factory
import json


def msg_maker(bpm: int):
    return json.dumps({'current_notes': bpm})


def set_list_item(l, i, v):
    try:
        l[i] = v
    except IndexError:
        for _ in range(i - len(l) + 1):
            l.append(None)
        l[i] = v


def mono_sequencer_factory(notes):
    msg = msg_maker(notes)
    obs, emit = observable_factory(msg)

    async def ws_consumer(kind, payload, uuid):
        nonlocal notes

        if kind == 'change':
            for i, x in enumerate(payload):
                set_list_item(notes, i, x)
            del notes[len(payload):]
            msg = msg_maker(payload)
            await emit(msg)

    return obs, ws_consumer

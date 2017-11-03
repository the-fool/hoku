from server.observable import observable_factory
import json


def color_mono_sequencer_factory(length=16):
    def msg_maker():
        return json.dumps({
            'action': 'state',
            'payload': {
                'rhythm': note_rhythm,
                'pitches': note_pitches
            }
        })

    note_pitches = (60, 60, 60, 60)
    note_rhythm = [-1] * length
    real_notes = [-1] * length
    obs, emit = observable_factory(msg_maker())

    def update_notes():
        for i, n in enumerate(note_rhythm):
            # 0 and -1 are special cases (not mapped)
            val = note_pitches[n] if n > 0 else n
            real_notes[i] = val

    async def metro_cb(ts):
        rhythm_index = ts % length
        note_index = note_rhythm[rhythm_index]
        msg = json.dumps({
            'action': 'beat',
            'payload': {
                'rhythm_index': rhythm_index,
                'note_index': note_index
            }
        })
        await emit(msg)

    async def ws_consumer(kind, payload, uuid):
        index = payload['index']
        value = payload['value']

        if kind == 'pitch':
            note_pitches[index] = value

        elif kind == 'rhythm':
            note_rhythm[index] = value
        else:
            # unknown
            return

        update_notes()
        await emit(msg_maker())

    return obs, ws_consumer, metro_cb, real_notes

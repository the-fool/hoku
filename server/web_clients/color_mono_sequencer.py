from server.observable import observable_factory
import json


# OO implementation
class ColorMonoSequencer:
    def __init__(self, pitches=(60, 60, 60, 60), length=16):
        self.pitches = pitches
        self.length = length
        self.rhythm = [-1] * length
        self.real_notes = [-1] * length
        self.obs, self.emit = observable_factory(self.msg_maker())

    def msg_maker(self):
        return json.dumps({
            'action': 'state',
            'payload': {
                'rhythm': self.rhythm,
                'pitches': self.pitches
            }
        })

    def update_notes(self):
        for i, n in enumerate(self.rhythm):
            # 0 and -1 are special cases (not mapped)
            val = self.pitches[n] if n > 0 else n
            self.real_notes[i] = val

    async def metro_cb(self, ts):
        rhythm_index = ts % self.length
        note_index = self.rhythm[rhythm_index]
        msg = json.dumps({
            'action': 'beat',
            'payload': {
                'rhythm_index': rhythm_index,
                'note_index': note_index
            }
        })
        await self.emit(msg)

    async def ws_consumer(self, kind, payload, uuid):

        if kind == 'pitch':
            index = payload['index']
            value = payload['value']
            self.pitches[index] = value

        elif kind == 'rhythm':
            index = payload['index']
            value = payload['value']
            self.rhythm[index] = value
        elif kind == 'state':
            # this one is OK -- it just passes through so as to receive the state
            pass
        else:
            # unknown
            return

        self.update_notes()
        await self.emit(self.msg_maker())


# Functional implementation
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

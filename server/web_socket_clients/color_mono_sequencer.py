from server.observable import observable_factory
import json

BASE_DO = 60


# OO implementation
class ColorMonoSequencer:
    """
    Responsible for interfacing with a remote client

    It has 2 public methods:

    1) A metronome callback
      - on metronome ticks, it sends a message with a note & beat index out to clients

    2) A WebSocket callback
      - on websocket messages from the client, it updates the notes

    It exposes a list of notes (real_notes) with the sequencer,
    which in turn is responsible for translating notes into midi messages
    """

    def __init__(self, scale_cube, base_do=BASE_DO, length=16):

        self.scale_cube = scale_cube

        # optimization
        self._prev_scale = scale_cube.scale_index

        self.base_do = base_do
        self.length = length

        # the rhythm of the colors
        # -1 is rest, 0 hold, 1+ different colors
        self.rhythm = [-1] * length
        self._real_notes = [-1] * length
        self.obs, self.emit = observable_factory(self.msg_maker())

    def msg_maker(self):
        return json.dumps({
            'payload': {
                'rhythm': self.rhythm,
            }
        })

    def get_notes(self):
        # if the scale cube has been changed, we need to update notes
        if self._prev_scale is not self.scale_cube.scale_index:
            self._prev_scale = self.scale_cube.scale_index
            self.update_notes()
        return self._real_notes

    def update_notes(self):

        for i, n in enumerate(self.rhythm):
            # 0 and -1 are special cases (not mapped)
            if n > 0:
                scaleIndex = (n - 1) % 7

                scaleMultiplier = (n - 1) // 7

                pitch = self.scale_cube.scale[scaleIndex] + self.base_do + (
                    12 * scaleMultiplier)

            else:
                # if rhythm is 0 or -1, those special codes map to pitch
                pitch = n

            self._real_notes[i] = pitch

    async def ws_consumer(self, kind, payload, uuid):
        if kind == 'rhythm':
            index = payload['index']
            value = payload['value']
            self.rhythm[index] = value
        elif kind == 'state':
            # this one is OK -- it just passes through so as to receive the state
            pass
        else:
            # unknown
            return

        print('got', payload)
        print('new rhythm', self.rhythm)
        await self.on_change()

    async def set_rhythm(self, new_rhythm):
        for i, _ in enumerate(self.rhythm):
            self.rhythm[i] = new_rhythm[i]

        await self.on_change()

    async def on_change(self):
        self.update_notes()
        print('real notes', self._real_notes)
        await self.emit(self.msg_maker())

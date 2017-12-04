from server.observable import observable_factory
import json


# OO implementation
class ColorSequencer:
    """
    Responsible for interfacing with a remote client

    It has 2 public methods:

    2) A WebSocket callback
      - on websocket messages from the client, it updates the notes

    It exposes a list of notes with the sequencer, which in turn is responsible for translating notes into midi messages
    """

    def __init__(self,
                 scale_cube,
                 base_do=60,
                 length=16):
        self.scale_cube = scale_cube

        # optimization
        self._prev_scale = scale_cube.scale

        self.base_do = base_do
        self.length = length

        # the rhythm of the colors
        # -1 is rest, 0 hold, 1+ different colors
        self.rhythm = [-1] * length
        self._real_notes = [base_do] * length
        self.obs, self.emit = observable_factory(self.msg_maker())

    def msg_maker(self):
        # returns state of the color sequencer, which is just the rhythm array
        return json.dumps({
            'payload': {
                'rhythm': self.rhythm
            }
        })

    @property
    def notes(self):
        # if the scale cube has been changed, we need to update notes
        if self._prev_scale is not self.scale_cube.scale:
            self._prev_scale = self.scale_cube.scale
            self.update_notes()
        return self._real_notes

    def update_notes(self):
        for i, n in enumerate(self.rhythm):
            # 0 and -1 are special cases (not mapped)
            if n > 0:
                scaleIndex = (n - 1) % 7
                scaleMultiplier = (n - 1) // 7
                pitch = self.scale[scaleIndex] + self.base_do + (
                    12 * scaleMultiplier)
            else:
                # if rhythm is 0 or -1, those special codes map to pitch
                pitch = n

            self._real_notes[i] = pitch

    async def msg_consumer(self, kind, payload, uuid):

        if kind == 'rhythm':
            index = payload['index']
            value = payload['value']
            self.rhythm[index] = value
        elif kind == 'state':
            # a request for state just falls through
            pass
        else:
            # unknown -- do nothing!
            return

        self.update_notes()
        await self.emit(self.msg_maker())

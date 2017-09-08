import mido


class BaseInstrument:
    def __init__(self, output_name, channel=0):
        self.outport = mido.open_output(output_name)
        self.channel = channel

    @staticmethod
    def midify(x):
        if not isinstance(x, int):
            x = int(x)

        if x < 0:
            x = 0
        if x > 127:
            x = 127
        return x

    def note_on(self, note, velocity=127):
        self._note('note_on', note, velocity)

    def note_off(self, note, velocity=127):
        self._note('note_off', note, velocity)

    def _note(self, kind, note, velocity):
        note = BaseInstrument.midify(note)
        velocity = BaseInstrument.midify(velocity)
        self._out_msg(kind, note=note, velocity=velocity)

    def _control(self, control, value):
        control = BaseInstrument.midify(control)
        value = BaseInstrument.midify(value)
        self._out_msg('control_change', control=control, value=value)

    def _out_msg(self, kind, **kwargs):
        m = mido.Message(kind, **kwargs)
        self.outport.send(m)

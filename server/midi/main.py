import mido
from .instruments.minilogue import Minilogue
# get the minilogue
outport = mido.open_output('minilogue:minilogue MIDI 2 20:1')


def send_ctr_message(cc, value):

    print('here')
    m = mido.Message('control_change', control=cc, value=value)

    print('after constructing message')
    outport.send(m)


class MidiProxy:
    def __init__(self, minilogue_1='minilogue:minilogue MIDI 2 20:1'):
        self.minilogue_1 = Minilogue(minilogue_1)

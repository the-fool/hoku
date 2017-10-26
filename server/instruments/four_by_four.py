from . import Minilogue, NordElectro2

MIDI_OUTPUTS = [
    'MIDI4x4:MIDI4x4 MIDI 1 20:0', 'MIDI4x4:MIDI4x4 MIDI 2 20:1',
    'MIDI4x4:MIDI4x4 MIDI 3 20:2', 'MIDI4x4:MIDI4x4 MIDI 4 20:3'
]

instruments = {
    'minilogue_1': Minilogue(MIDI_OUTPUTS[0]),
    'minilogue_2': Minilogue(MIDI_OUTPUTS[1]),
    'nord': NordElectro2(MIDI_OUTPUTS[2])
}

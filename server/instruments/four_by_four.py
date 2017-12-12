from . import Minilogue, Reaper

MIDI_OUTPUTS = [
    'MIDI4x4:MIDI4x4 MIDI 1 20:0', 'MIDI4x4:MIDI4x4 MIDI 2 20:1',
    'MIDI4x4:MIDI4x4 MIDI 3 20:2', 'MIDI4x4:MIDI4x4 MIDI 4 20:3'
]

instrument_dict = {
    'minilogue_1': Minilogue(MIDI_OUTPUTS[0]),
    'minilogue_2': Minilogue(MIDI_OUTPUTS[1]),
    'reaper': Reaper(MIDI_OUTPUTS[2])
}

instruments = [
    instrument_dict['minilogue_1'],
    instrument_dict['minilogue_2'],
    instrument_dict['reaper']
]

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib as GObject

from .instruments import Minilogue, NordElectro2
from .web_servers import run_ws_server, run_http_server
from .microbit import MyMicrobit
from .modules import Sequencer, Metronome,\
    SEQUENCER_CB_CTYPE, OnStepCbs, METRONOME_CB_CTYPE
from .worker import Worker
from .web_clients import MetaBalls, particles_cb, PolySequencer

import json
import multiprocessing as mp
import sys
import logging

MBIT_VOZUZ = 'DE:ED:5C:B4:E3:73'
MBIT_GUPAZ = 'D5:38:B0:2D:BF:B6'
DONGLE_ADDR = '5C:F3:70:81:F3:66'

MIDI_OUTPUTS = [
    'MIDI4x4:MIDI4x4 MIDI 1 20:0', 'MIDI4x4:MIDI4x4 MIDI 2 20:1',
    'MIDI4x4:MIDI4x4 MIDI 3 20:2', 'MIDI4x4:MIDI4x4 MIDI 4 20:3'
]


def noop_2ary(a, b):
    pass


def run():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(processName)s %(message)s')

    minilogue_1 = Minilogue(MIDI_OUTPUTS[2])
    minilogue_2 = Minilogue(MIDI_OUTPUTS[1])
    nord = NordElectro2(MIDI_OUTPUTS[0])

    #
    # set up all the shared memory stuff
    # -- manager things are not performance critical
    #

    seq_cb_pool = mp.Array(OnStepCbs, 64)
    seq_cb_pool_length_i = 0
    seq_cb_pool_length = mp.Value('i', seq_cb_pool_length_i)

    met_cb_pool = mp.Array(METRONOME_CB_CTYPE, 64)
    met_cb_pool_length_i = 0
    met_cb_pool_length = mp.Value('i', met_cb_pool_length_i)

    sequencer_notes = mp.Array('i', LCD)

    #
    # Metronome write pipes
    #

    ws_server_pipe_w, ws_server_pipe_r = mp.Pipe()
    mono_sequencer_pipe_w, mono_sequencer_pipe_r = mp.Pipe()
    poly_sequencer_pipe_w, poly_sequencer_pipe_r = mp.Pipe()

    metronome_write_pipes = [
        ws_server_pipe_w,
        mono_sequencer_pipe_w,
        poly_sequencer_pipe_w
    ] # yapf: disable

    #
    # Build our modules, using the shared memory things
    #

    # yapf: disable
    metronome = Metronome(
        pipes=metronome_write_pipes,
        cbs=met_cb_pool,
        cbs_length=met_cb_pool_length)

    mono_sequencer = Sequencer(
        cbs=seq_cb_pool,
        cbs_length=seq_cb_pool_length,
        clock_pipe=mono_sequencer_pipe_r,
        notes=sequencer_notes)
    # yapf: enable

    #
    # Build our web client handlers
    #

    metaball = MetaBalls(instrument_cb=minilogue_1.voice_mode)
    poly_sequencer = PolySequencer(nord.note_on)

    #
    # Add the metronome cbs
    #

    metronome_cbs = [poly_sequencer.beat]
    for i, cb in enumerate(metronome_cbs):
        met_cb_pool[i] = METRONOME_CB_CTYPE(cb)
        met_cb_pool_length_i += 1
    met_cb_pool_length.value = met_cb_pool_length_i

    #
    # Add the sequencer cbs
    #

    # yapf: disable
    sequencer_cb_tuples = [(metaball.beat, noop_2ary),
                           (minilogue_1.beat_on, minilogue_1.beat_off),
                           (minilogue_2.beat_on, minilogue_2.beat_off)]
    # yapf: enable

    for i, cb_tuple in enumerate(sequencer_cb_tuples):
        seq_cb_pool[i].on = SEQUENCER_CB_CTYPE(cb_tuple[0])
        seq_cb_pool[i].off = SEQUENCER_CB_CTYPE(cb_tuple[1])
        seq_cb_pool_length_i += 1
    seq_cb_pool_length.value = seq_cb_pool_length_i

    #
    # WebSocket server behaviors
    #

    behaviors = {
        'particles': particles_cb(minilogue_1),
        'metaball': lambda data: metaball.set_data_points(data),
        'bulls-eye': poly_sequencer.set_notes
    }

    #
    # Create the processes
    #

    ws_p = mp.Process(target=run_ws_server, args=(ws_server_pipe_r, behaviors))
    metronome_p = mp.Process(target=metronome.loop, args=())
    http_p = mp.Process(target=run_http_server, args=())
    mono_sequencer_p = mp.Process(target=mono_sequencer.start)

    ws_p.start()
    metronome_p.start()
    http_p.start()
    mono_sequencer_p.start()

    #
    # Do the microbit things:
    #

    vozuz = microbit_init(MBIT_VOZUZ)
    gupaz = microbit_init(MBIT_GUPAZ)
    if vozuz is None or gupaz is None:
        logging.error('Failed to find either vozuz or gupaz')
    else:
        try:
            vozuz.subscribe_uart(vozuz_uart)
        except:
            logging.debug('Failed to subscribe to mbit UART')
            sys.exit(1)

        #
        # dbus time!
        # -- the dbus is for our bluetooth event subscriptions
        #

        run_dbus_loop()

    #
    # Done!
    # now just go to sleep, for the sub-processes should never exit!
    #

    try:
        ws_p.join()
        metronome_p.join()
        http_p.join()
    except (KeyboardInterrupt, ):
        for i in range(127):
            minilogue_1.note_off(i)
        sys.exit()


#   -- End main script --
#
#
# Function and sub-routine defs
# They are used in the imperative configuration up above
#


def run_dbus_loop():
    """
    Start the dbus loop
    """
    global loop

    DBusGMainLoop(set_as_default=True)
    loop = GObject.MainLoop()
    loop.run()


def vozuz_uart(l, data, sig):
    """
    Callback routine for the vozuz mbit
    Vozuz is the colored rotating thing
    """
    print(data.get('Value', None))
    # val = int(''.join(chr(c) for c in data['Value']))
    # val = abs(val)
    # val = translate(val, 0, 180, 0, 127)
    # minilogue_1.cutoff(val)


# Get Innocuous!
LCD = [60, 60, 58, 58, 60, 60, 58, 58, 60, 60, 58, 63, -1, 63, 58, 58]


def microbit_init(address):
    # Do the microbit things:
    try:
        mbit = MyMicrobit(device_addr=address, adapter_addr=DONGLE_ADDR)
    except:
        logging.debug('Failed to find mbit {}'.format(address))
        return None
    if not mbit.connect():
        logging.debug('Failed to connect to {}'.format(address))
        return None
    return mbit

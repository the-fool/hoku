from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib as GObject

from .instruments.four_by_four import instruments
from .web_servers import run_ws_server, run_http_server
from .microbit import MyMicrobit
from .modules import Sequencer, Metronome, MidiWorker
from .web_clients import MetaBalls, particles_cb, PolySequencer

import multiprocessing as mp
import sys
import logging

MBIT_VOZUZ = 'DE:ED:5C:B4:E3:73'
MBIT_GUPAZ = 'D5:38:B0:2D:BF:B6'
DONGLE_ADDR = '5C:F3:70:81:F3:66'


def noop_2ary(a, b):
    pass


def run():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(processName)s %(message)s')

    midi_worker_pipe_r, midi_worker_pipe_w = mp.Pipe(duplex=False)
    midi_worker = MidiWorker(p=midi_worker_pipe_r, instruments=instruments)

    #
    # set up all the shared memory stuff
    # -- manager things are not performance critical
    #

    sequencer_notes = mp.Array('i', LCD)

    #
    # Metronome write pipes
    #

    ws_server_pipe_r, ws_server_pipe_w = mp.Pipe(duplex=False)
    mono_sequencer_pipe_r, mono_sequencer_pipe_w = mp.Pipe(duplex=False)
    poly_sequencer_pipe_r, poly_sequencer_pipe_w = mp.Pipe(duplex=False)
    metaball_pipe_r, metaball_pipe_w = mp.Pipe(duplex=False)

    metronome_write_pipes = [
        ws_server_pipe_w,
        mono_sequencer_pipe_w,
        poly_sequencer_pipe_w,
        metaball_pipe_w
    ]  # yapf: disable

    #
    # Build our modules, using the shared memory things
    #

    # yapf: disable
    metronome = Metronome(pipes=metronome_write_pipes)

    mono_sequencer_msgs = [
        ('minilogue_1', 'beat_on', 'beat_off'),
        ('minilogue_2', 'beat_on', 'beat_off')
    ]

    mono_sequencer = Sequencer(
        worker_pipe=midi_worker_pipe_w,
        on_trigger_msgs=mono_sequencer_msgs,
        clock_pipe=mono_sequencer_pipe_r,
        notes=sequencer_notes)
    # yapf: enable

    #
    # Build our web client handlers
    #

    metaball_web_client_pipe_w, metaball_web_client_pipe_r = mp.Pipe()

    metaball = MetaBalls(
        clock_pipe=metaball_pipe_r,
        worker_pipe=midi_worker_pipe_w,
        msg={'instrument_name': 'minilogue_1',
             'method': 'voice_mode'},
        client_pipe=metaball_web_client_pipe_r)

    poly_sequencer = PolySequencer(
        clock_pipe=poly_sequencer_pipe_r,
        msg={'instrument_name': 'nord',
             'method': 'note_on'})

    #
    # Add the sequencer cbs
    #

    #
    # WebSocket server behaviors
    #

    behaviors = {
        'particles': particles_cb(midi_worker_pipe_w),
        'metaball': lambda data: metaball_web_client_pipe_w.send(data),
        'bulls-eye': poly_sequencer.set_notes
    }

    #
    # Create the processes
    #

    processes = [(run_ws_server, (ws_server_pipe_r, behaviors)),
                 (metaball.start, ()),
                 (metronome.loop, ()),
                 (run_http_server, ()),
                 (midi_worker.start_consuming, ()),
                 (mono_sequencer.start, ()),
                 (poly_sequencer.start, ())]  # yapf: disable

    process_objs = [mp.Process(target=p[0], args=p[1]) for p in processes]

    for p in process_objs:
        p.start()

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
        for p in process_objs:
            p.join()
    except (KeyboardInterrupt, ):
        for i in range(127):
            for instrument in instruments.values():
                instrument.note_off(i)
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

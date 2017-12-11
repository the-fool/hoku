import asyncio

import threading

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib as GObject
# from .instruments.four_by_four import instruments

from .microbit import MyMicrobit

from .web_servers import ws_server_factory

from .web_socket_clients import Clocker, MetronomeChanger,\
    ColorMonoSequencer as CMS,\
    CubeOfScaleChanger,\
    CubeOfPatchChanger,\
    DrummerChanger

from .modules import Metronome,\
    MonoSequencer,\
    ScaleCube,\
    PatchCube,\
    Drummer

import logging

MBIT_VOZUZ = 'DE:ED:5C:B4:E3:73'
MBIT_GUPAZ = 'D5:38:B0:2D:BF:B6'
DONGLE_ADDR = '5C:F3:70:81:F3:66'

starting_bpm = 120


def main():
    logging.basicConfig(
        level=logging.INFO, format='%(relativeCreated)6d %(message)s')

    # instruments = {}

    scale_cube = ScaleCube()
    scale_changer = CubeOfScaleChanger(scale_cube)

    patch_cube = PatchCube(instruments=[])
    patch_changer = CubeOfPatchChanger(patch_cube)

    # make COLOR_MONO_SEQUENCER
    cms1 = CMS(scale_cube)

    cms2 = CMS(scale_cube)

    # make MONO_SEQUENCER

    # fast
    mono_seq_1 = MonoSequencer(cms2.notes, instruments=[])

    # slow
    slow_factor = 2
    mono_seq_2 = MonoSequencer(
        cms1.notes, instruments=[], time_multiplier=16 / slow_factor)

    # make CLOCKER
    clocker = Clocker()

    # make DRUMMER
    drummer = Drummer()
    drummer_changer = DrummerChanger(drummer=drummer)


    # make particles
    # particles_ws_consumer = particles_factory(midi_q)

    # Set up metronome
    metronome_cbs = [
        clocker.metronome_cb,
        mono_seq_1.on_beat,
        mono_seq_2.on_beat,
        drummer.on_beat
    ]

    metronome = Metronome(metronome_cbs, starting_bpm)

    metro_changer = MetronomeChanger(
        init_bpm=starting_bpm, on_change_cb=metronome.set_bpm)

    # hash of {path: (consumer, producer)}
    ws_behaviors = {
        'clocker': (None, clocker.obs),
        # 'particles': (particles_ws_consumer, None),
        'metronome_changer': (metro_changer.ws_consumer, metro_changer.obs),
        'scale': (scale_changer.ws_consumer, scale_changer.obs),
        'patch': (patch_changer.ws_consumer, patch_changer.obs),
        'cms1': (cms1.ws_consumer, cms1.obs),
        'cms2': (cms2.ws_consumer, cms2.obs),
        'drummer': (drummer_changer.ws_consumer, drummer_changer.obs)
    }

    ws_server_coro = ws_server_factory(behaviors=ws_behaviors)

    coros = [ws_server_coro, metronome.run()]

    loop = asyncio.get_event_loop()

    # Set Up mbits
    gupaz_cb = make_gupaz_uart_cb(scale_cube, loop)
    vozuz_cb = make_vozuz_uart_cb(scale_cube, loop)
    # setup_mbits(gupaz_cb)

    # and run the dbus loop
    # t = threading.Thread(target=run_dbus_loop)
    # t.start()

    loop.run_until_complete(asyncio.gather(*coros))

    loop.close()


def run_dbus_loop():
    """
    Start the dbus loop
    """
    DBusGMainLoop(set_as_default=True)
    loop = GObject.MainLoop()
    loop.run()


def microbit_init(address):
    # Do the microbit things:
    try:
        logging.info('Attempting to connect to {}'.format(address))
        mbit = MyMicrobit(device_addr=address, adapter_addr=DONGLE_ADDR)

        logging.info('Successfully connected to {}!'.format(address))
    except:
        logging.error('Failed to find mbit {}'.format(address))
        return None
    if not mbit.connect():
        logging.error('Failed to connect to {}'.format(address))
        return None
    return mbit


def setup_mbits(gupaz_uart_cb, vozuz_uart_cb):

    gupaz = microbit_init(MBIT_GUPAZ)
    vozuz = microbit_init(MBIT_VOZUZ)
    gupaz.subscribe_uart(gupaz_uart_cb)
    vozuz.subscribe_uart(vozuz_uart_cb)


def make_gupaz_uart_cb(scale_cube, loop):
    def cb(l, data, x):
        try:
            (kind, payload) = [int(chr(c)) for c in data['Value']]
            if kind == 0:
                logging.info('Power Cube of Scale: DISCONNECTED')
            elif kind == 1:
                logging.info(
                    'Power Cube of Scale: CONNECTED at {}'.format(payload))
                asyncio.ensure_future(scale_cube.set_scale(payload), loop=loop)

        except Exception as e:
            print(e)
            print('error', data)

    return cb


def make_vozuz_uart_cb(patch_cube, loop):
    def cb(l, data, x):
        try:
            (kind, payload) = [int(chr(c)) for c in data['Value']]
            if kind == 0:
                logging.info('Power Cube of Scale: DISCONNECTED')
            elif kind == 1:
                logging.info(
                    'Power Cube of Scale: CONNECTED at {}'.format(payload))
                asyncio.ensure_future(patch_cube.set_patch(payload), loop=loop)

        except Exception as e:
            print(e)
            print('error', data)

    return cb

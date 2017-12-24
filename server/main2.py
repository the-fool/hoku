import asyncio
import sys
import threading

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib as GObject

from .util import scale

from .microbit import MyMicrobit

from .web_servers import ws_server_factory

from .web_socket_clients import Clocker, MetronomeChanger,\
    ColorMonoSequencer as CMS,\
    CubeOfScaleChanger,\
    CubeOfPatchChanger,\
    DrummerChanger,\
    FxManager

from .modules import Metronome,\
    MonoSequencer,\
    ScaleCube,\
    PatchCube,\
    Drummer

from .instruments.four_by_four import instruments
from .table import LedTCPServer

import logging

MBIT_VOZUZ = 'DE:ED:5C:B4:E3:73'
MBIT_GUPAZ = 'D5:38:B0:2D:BF:B6'
DONGLE_ADDR = '5C:F3:70:81:F3:66'

starting_bpm = 120

loop = asyncio.get_event_loop()

BLE = True
LED = True


def parse_argv():
    global BLE
    global LED
    argv = sys.argv
    for arg in argv:
        if arg == '--no-ble':
            # no ble
            BLE = False
        elif arg == '--no-table':
            LED = False


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parse_argv()

    scale_cube = ScaleCube()
    scale_changer = CubeOfScaleChanger(scale_cube)

    patch_cube = PatchCube(instruments=instruments[:2])
    patch_changer = CubeOfPatchChanger(patch_cube)

    fx_cbs = make_fx_cbs()

    mini_1_fx = FxManager(fx_cbs['mini_1'])
    mini_2_fx = FxManager(fx_cbs['mini_2'])
    reaper_fx = FxManager(fx_cbs['reaper'])

    # make COLOR_MONO_SEQUENCER
    cms1 = CMS(scale_cube)
    cms2 = CMS(scale_cube)

    # make MONO_SEQUENCER

    # fast
    mono_seq_1 = MonoSequencer(cms2.get_notes, instruments=[instruments[0]])

    # slow
    mono_seq_2 = MonoSequencer(
        cms1.get_notes, instruments=[instruments[1]], time_multiplier=16)

    # make CLOCKER
    clocker = Clocker()

    # make DRUMMER
    drummer = Drummer(midi_devs=[instruments[1]])
    drummer_changer = DrummerChanger(drummer=drummer)

    # make particles
    # particles_ws_consumer = particles_factory(midi_q)

    if LED:
        table_server = LedTCPServer(
            loop=loop,
            scale_cube=scale_cube,
            patch_cube=patch_cube,
            color_seqs=[cms2, cms1])
    # Set up metronome
    metronome_cbs = [
        clocker.metronome_cb, mono_seq_1.on_beat, mono_seq_2.on_beat,
        drummer.on_beat
    ]

    if LED:
        metronome_cbs.append(table_server.metro_cb)

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
        'drummer': (drummer_changer.ws_consumer, drummer_changer.obs),
        'fx_mini_1': (mini_1_fx.ws_consumer, mini_1_fx.obs),
        'fx_mini_2': (mini_2_fx.ws_consumer, mini_2_fx.obs),
        'fx_reaper': (reaper_fx.ws_consumer, reaper_fx.obs),
    }

    ws_server_coro = ws_server_factory(behaviors=ws_behaviors)

    coros = [scale_changer.coro(), patch_changer.coro(), ws_server_coro, metronome.run()]

    if LED:
        coros.extend(table_server.coros)

    # Set Up mbits
    if BLE:
        gupaz_cb = make_gupaz_uart_cb(scale_cube, loop)
        vozuz_cb = make_vozuz_uart_cb(patch_cube, loop)
        setup_mbits(vozuz_cb, gupaz_cb)

        # and run the dbus loop
        t = threading.Thread(target=run_dbus_loop)
        t.start()

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


def setup_mbits(vozuz_uart_cb, gupaz_uart_cb):

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

            print(kind, payload)
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
            print(kind, payload)
        except Exception as e:
            print(e)
            print('error', data)

    return cb


def make_fx_cbs():
    if len(instruments) < 3:
        # no instruments connected
        return

    reaper = instruments[2]

    def scale_it(cb):
        def scaled(x):
            cb(scale(x, 0, 1, 0, 127))

        return scaled

    def make_mini_cbs(i):
        mini = instruments[i]
        return {
            'cutoff': scale_it(mini.cutoff),
            'attack': scale_it(mini.eg_attack),
            'release': scale_it(mini.amp_release),
            'decay': scale_it(mini.amp_decay),
            'volume': scale_it(mini.level),
            'reverb': scale_it(getattr(reaper, 'mini_{}_verb'.format(i + 1))),
            'distortion':
            scale_it(getattr(reaper, 'mini_{}_dist'.format(i + 1)))
        }

    reaper_cbs = {'drum_reverb': scale_it(reaper.drum_verb)}

    return {
        'mini_1': make_mini_cbs(0),
        'mini_2': make_mini_cbs(1),
        'reaper': reaper_cbs
    }

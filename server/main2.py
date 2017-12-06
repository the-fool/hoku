import asyncio

import threading

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib as GObject
# from .instruments.four_by_four import instruments

from .microbit import MyMicrobit

from .web_servers import ws_server_factory

from .web_clients import ColorMonoSequencer as CMS

from .web_socket_clients import Clocker, MetronomeChanger

from .modules import Metronome,\
    MonoSequencer,\
    ScaleCube,\
    ColorSequencer

import logging

MBIT_VOZUZ = 'DE:ED:5C:B4:E3:73'
MBIT_GUPAZ = 'D5:38:B0:2D:BF:B6'
DONGLE_ADDR = '5C:F3:70:81:F3:66'

starting_bpm = 120


def main():
    logging.basicConfig(
        level=logging.INFO, format='%(relativeCreated)6d %(message)s')

    # instruments = {}

    # make COLOR_MONO_SEQUENCER
    cms = CMS(rhythm=[-1] * 16)

    scale_cube = ScaleCube()
    # make MONO_SEQUENCER
    notes_1 = [-1] * 16  # the notes in the sequence, a bar of rests

    mono_seq_1 = MonoSequencer(notes_1, instruments=[])
    mono_seq_2 = MonoSequencer(cms.notes, instruments=[])

    # make CLOCKER
    clocker = Clocker()

    # make particles
    # particles_ws_consumer = particles_factory(midi_q)

    # Set up metronome
    metronome_cbs = [
        clocker.metronome_cb, mono_seq_1.on_beat, mono_seq_2.on_beat,
        cms.metro_cb
    ]
    metronome = Metronome(metronome_cbs, starting_bpm)

    metro_changer = MetronomeChanger(
        init_bpm=starting_bpm, on_change_cb=metronome.set_bpm)

    # hash of {path: (consumer, producer)}
    ws_behaviors = {
        'clocker': (None, clocker.obs),
        'scale': (None, scale_cube.ws_msg_producer),
        # 'particles': (particles_ws_consumer, None),
        'metronome_changer': (metro_changer.ws_consumer, metro_changer.obs),
        'colormonosequencer': (cms.ws_consumer, cms.obs)
    }

    ws_server_coro = ws_server_factory(behaviors=ws_behaviors)

    coros = [ws_server_coro, metronome.run()]

    loop = asyncio.get_event_loop()

    # Set Up mbits
    gupaz_cb = make_gupaz_uart_cb(scale_cube, loop)
    setup_mbits(gupaz_cb)
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


def setup_mbits(gupaz_uart_cb):
    gupaz = microbit_init(MBIT_GUPAZ)

    gupaz.subscribe_uart(gupaz_uart_cb)


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

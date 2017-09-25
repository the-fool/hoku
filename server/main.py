from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from .instruments.minilogue import Minilogue
from .web_servers import run_ws_server, run_http_server
from .microbit import MyMicrobit
from .client_pool import ClientPool
from .modules import Sequencer
from .modules import Metronome
from .worker import Worker
from .web_clients import MetaBalls, particles_cb

import json
import threading
import sys
import logging

MBIT_VOZUZ = 'DE:ED:5C:B4:E3:73'
MBIT_GUPAZ = 'D5:38:B0:2D:BF:B6'
DONGLE_ADDR = '5C:F3:70:81:F3:66'


def run_dbus_loop():
    global loop
    DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()
    loop.run()


def vozuz_uart(l, data, sig):
    print(data.get('Value', None))
    # val = int(''.join(chr(c) for c in data['Value']))
    # val = abs(val)
    # val = translate(val, 0, 180, 0, 127)
    # minilogue_1.cutoff(val)


LCD = [60, 60, 58, 58, 60, 60, 58, 58, 60, 60, 58, 63, -1, 63, 58, 58]


def broadcast_sequencer_to_clients(client_pool):
    return lambda note, step: client_pool.broadcast(
        json.dumps({'note': note, 'step': step}))


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


def run():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(threadName)s %(message)s')

    client_pool = ClientPool()

    minilogue_1 = Minilogue('MIDI4x4:MIDI4x4 MIDI 3 20:2')
    minilogue_2 = Minilogue('MIDI4x4:MIDI4x4 MIDI 4 20:3')

    worker = Worker()

    metronome = Metronome(worker)

    sequencer = Sequencer(notes=LCD)

    metaball = MetaBalls(minilogue_1.voice_mode)

    metronome.register_cb(sequencer.beat)

    sequencer.register_cb({'on': broadcast_sequencer_to_clients(client_pool)})
    sequencer.register_cb({'on': metaball.beat})
    sequencer.register_cb({
        'on': minilogue_1.beat_on,
        'off': minilogue_1.beat_off
    })
    sequencer.register_cb({
        'on': minilogue_2.beat_on,
        'off': minilogue_2.beat_off
    })

    behaviors = {
        'particles': particles_cb(minilogue_1),
        'metaball': lambda data: metaball.set_data_points(data)
    }

    clock_t = threading.Thread(target=metronome.loop, args=(), daemon=True)
    ws_t = threading.Thread(
        target=run_ws_server, args=(client_pool, behaviors), daemon=True)
    http_t = threading.Thread(target=run_http_server, args=(), daemon=True)
    worker_t = threading.Thread(target=worker.consume, args=(), daemon=True)

    ws_t.start()
    http_t.start()
    clock_t.start()
    worker_t.start()

    # Do the microbit things:
    vozuz = microbit_init(MBIT_VOZUZ)
    gupaz = microbit_init(MBIT_GUPAZ)
    if vozuz is None or gupaz is None:
        sys.exit(1)
    try:
        vozuz.subscribe_uart(vozuz_uart)
    except:
        logging.debug('Failed to subscribe to mbit UART')
        sys.exit(1)

    run_dbus_loop()
    try:
        ws_t.join()
        clock_t.join()
        http_t.join()
        worker_t.join()
    except (KeyboardInterrupt, ):
        for i in range(127):
            minilogue_1.note_off(i)
        sys.exit()

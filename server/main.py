from bluezero import microbit, tools, constants, dbus_tools
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from .instruments.minilogue import Minilogue
from .ws_server import run_ws_server
from .http_server import run_http_server

from .client_pool import ClientPool

import time
import random
import json
import threading
import sys
import logging


sequencer = None
worker = None
metronome = None

metaball = None


class Metaball:
    def __init__(self, instrument_cb):
        self.n_steps = 8
        self.instrument_cb = instrument_cb
        self.data = [0] * self.n_steps

    def set_data_point(self, i, v):
        self.data[i] = v

    def set_data_points(self, data):
        self.data = [0] * self.n_steps
        for d in data:
            self.data[d['i']] = d['value']

    def beat(self, note, step):
        step = step % self.n_steps
        val = self.data[step] * 100
        self.instrument_cb(val)




class MyMicrobit(microbit.Microbit):
    UART_SRV = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
    UART_DATA = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uart_data = self.ubit.add_characteristic(self.UART_SRV,
                                                       self.UART_DATA)

    def _accel_notify_cb(self):
        print('Accel subscribed!!!')
        return 1

    def subscribe_uart(self, cb):
        self._uart_data.resolve_gatt()

        path = dbus_tools.get_dbus_path(
            characteristic=self.UART_DATA,
            device='DE:ED:5C:B4:E3:73',
            adapter='5C:F3:70:81:F3:66')

        obj = dbus_tools.get_dbus_obj(path)

        iface = dbus_tools.get_dbus_iface(constants.DBUS_PROP_IFACE, obj)

        iface.connect_to_signal('PropertiesChanged', cb)
        obj.StartNotify(
            reply_handler=self._accel_notify_cb,
            error_handler=dbus_tools.generic_error_cb,
            dbus_interface=constants.GATT_CHRC_IFACE)

    def subscribe_accel(self, user_callback):
        self._accel_data.resolve_gatt()
        accel_path = dbus_tools.get_dbus_path(
            characteristic='E95DCA4B-251D-470A-A062-FA1922DFA9A8',
            device='DE:ED:5C:B4:E3:73',
            adapter='5C:F3:70:81:F3:66')

        accel_obj = dbus_tools.get_dbus_obj(accel_path)
        accel_iface = dbus_tools.get_dbus_iface(constants.DBUS_PROP_IFACE,
                                                accel_obj)
        accel_iface.connect_to_signal('PropertiesChanged', user_callback)
        accel_obj.StartNotify(
            reply_handler=self._accel_notify_cb,
            error_handler=dbus_tools.generic_error_cb,
            dbus_interface=constants.GATT_CHRC_IFACE)


def find_mbit(name):
    adapter_addr = '5C:F3:70:81:F3:66'
    if name == 'vozuz':
        device_addr = 'DE:ED:5C:B4:E3:73'
    try:
        return MyMicrobit(device_addr=device_addr, adapter_addr=adapter_addr)
    except:
        return None


def connect_mbit(m):
    try:
        m.ubit.rmt_device.connect()
        time.sleep(3)
        return True
    except:
        return False


def setup_dbus_loop():
    DBusGMainLoop(set_as_default=True)


def run_dbus_loop():
    global loop
    loop = GLib.MainLoop()
    loop.run()


def quit_dbus_loop():
    global loop
    loop.quit()


def log_vozuz(l, data, sig):
    x = tools.bytes_to_xyz(data['Value'])[0]
    print('x', x)
    x = x * 60 + 60
    print('res', x)
    minilogue_1.cutoff(x)
    print('got: {}'.format(tools.bytes_to_xyz(data['Value'])))


def vozuz_uart(l, data, sig):
    val = int(''.join(chr(c) for c in data['Value']))
    val = abs(val)
    val = translate(val, 0, 180, 0, 127)
    minilogue_1.cutoff(val)


# BEGIN MAIN
def connect_to_vozuz():
    print('Finding VOZUZ')
    vozuz = find_mbit(name='vozuz')
    if vozuz is None:
        print('Failed to find VOZUZ')
        exit(1)

        print('Connecting to VOZUZ')
    if not connect_mbit(vozuz):
        print('Failed to connect to VOZUZ')
        exit(1)

    print('Subscribing to uart')
    vozuz.subscribe_uart(vozuz_uart)

    print('Setting up dbus loop')
    setup_dbus_loop()

    print('Running main loop')
    run_dbus_loop()


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return int(rightMin + (valueScaled * rightSpan))


def cent_to_midi(value):
    return translate(value, 0, 100, 0, 127)


def particles_cb(data):
    cut = cent_to_midi(data['x'])
    res = cent_to_midi(data['y'])

    minilogue_1.amp_decay(cut)
    minilogue_1.eg_decay(res)


behaviors = {
    'particles': particles_cb,
    'metaball': lambda data: metaball.set_data_points(data)
}

LCD = [60, 60, 58, 58, 60, 60, 58, 58, 60, 60, 58, 63, -1, 63, 58, 58]


class Sequencer:
    def __init__(self, notes=None):
        self.off_note = 0
        self.step = 0
        self.notes = notes or [random.randrange(20, 80, 2) for _ in range(32)]
        self.on_step_cbs = []
        self.lock = threading.Lock()

    def beat(self, ts):
        with self.lock:
            note = self.notes[self.step]
            if note is not 0:
                for cb in self.on_step_cbs:
                    # when note is == 0, hold
                    # when note is < 0, rest
                    off = cb.get('off', None)
                    if off:
                        off(note=self.off_note, step=self.step)
            if note > 0:
                self.off_note = note
                for cb in self.on_step_cbs:
                    on = cb.get('on', None)
                    if on:
                        on(note=note, step=self.step)
            self.step = (self.step + 1) % len(self.notes)

    def register_cb(self, cb):
        """
        cb is a dict with 2 callables with args (note: int, step: int)
        'on' & 'off' are the keys
        """
        with self.lock:
            self.on_step_cbs.append(cb)

    def change_note(self, i, note):
        with self.lock:
            self.notes[i] = note


class Worker:
    def __init__(self):
        self.cv = threading.Condition()
        self.q = []

    def consume(self):
        while True:
            local_q = []
            with self.cv:
                while len(self.q) == 0:
                    self.cv.wait()
                local_q = [task for task in self.q]
                self.q = []
            for task in local_q:
                task['cb'](*task['args'], **task['kwargs'])

    def add(self, task, *args, **kwargs):
        with self.cv:
            self.q.append({'cb': task, 'args': args, 'kwargs': kwargs})
            self.cv.notify_all()

    def add_all(self, tasks, *args, **kwargs):
        with self.cv:
            self.q.extend([{
                'cb': task,
                'args': args,
                'kwargs': kwargs
            } for task in tasks])
            self.cv.notify_all()


class Metronome:
    def __init__(self, worker, bpm=110, steps=4):
        self.ts = 0
        self.bpm = bpm
        self.steps = steps
        self.lock = threading.Lock()
        self.cbs = set()
        self.worker = worker

    def register_cb(self, cb):
        with self.lock:
            self.cbs.add(cb)

    def loop(self):
        sleep_offset = 0
        while True:
            sleep_time = max(0, (60 / self.bpm / self.steps - sleep_offset))
            time.sleep(sleep_time)
            t = time.time()
            with self.lock:
                self.worker.add_all([task for task in self.cbs], self.ts)
            self.ts = self.ts + 1
            sleep_offset = time.time() - t


def metaball_cb(minilogue):
    def do_it(val):
        minilogue.voice_mode(val)

    return do_it


def broadcast_sequencer_to_clients(client_pool):
    return lambda (note, step): client_pool.broadcast(
        json.dumps({'note': note, 'step': step}))


def run():
    global minilogue_1
    global sequencer
    global worker
    global metronome
    global metaball

    client_pool = ClientPool()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(threadName)s %(message)s')

    minilogue_1 = Minilogue('minilogue:minilogue MIDI 2 20:1')
    worker = Worker()
    metronome = Metronome(worker)
    sequencer = Sequencer(notes=LCD)

    metaball = Metaball(metaball_cb(minilogue_1))
    metronome.register_cb(sequencer.beat)

    sequencer.register_cb({'on': broadcast_sequencer_to_clients(client_pool)})
    sequencer.register_cb({'on': metaball.beat})
    sequencer.register_cb({
        'on': minilogue_1.beat_on,
        'off': minilogue_1.beat_off
    })

    clock_t = threading.Thread(target=metronome.loop, args=(), daemon=True)
    ws_t = threading.Thread(
        target=run_ws_server, args=(client_pool, behaviors), daemon=True)
    http_t = threading.Thread(target=run_http_server, args=(), daemon=True)
    worker_t = threading.Thread(target=worker.consume, args=(), daemon=True)

    ws_t.start()
    http_t.start()
    clock_t.start()
    worker_t.start()

    connect_to_vozuz()
    try:
        ws_t.join()
        clock_t.join()
        http_t.join()
        worker_t.join()
    except (KeyboardInterrupt, ):
        for i in range(127):
            minilogue_1.note_off(i)
        sys.exit()

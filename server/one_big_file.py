from bluezero import microbit, tools, constants, dbus_tools
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from urllib.parse import urlparse, parse_qs
import math
import time
import random
import mido
import json
import threading
import sys
import http.server
import socketserver
import logging

HTTP_PORT = 5555
WS_PORT = 4444

CLIENT_LOCK = threading.Lock()
clients = set()

socketserver.TCPServer.allow_reuse_address = True

# ACCEL_SRV = 'E95D0753-251D-470A-A062-FA1922DFA9A8'
# ACCEL_DATA = 'E95DCA4B-251D-470A-A062-FA1922DFA9A8'

sequencer = None
worker = None
metronome = None

metaball = None


class ClientPool:
    def __init__(self):
        self.pool = set()
        self.lock = threading.Lock()

    def add(self, client):
        with self.lock:
            self.pool.add(client)

    def remove(self, client):
        with self.lock:
            self.pool.remove(client)

    def get(self, client):
        p = []
        with self.lock:
            p = [c for c in self.pool]
        return p


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


class BaseInstrument:
    def __init__(self, output_name, channel=0):
        self.outport = mido.open_output(output_name)
        self.channel = channel

    @staticmethod
    def midify(x):
        if not isinstance(x, int):
            x = int(x)

        if x < 0:
            x = 0
        if x > 127:
            x = 127
        return x

    def note_on(self, note, velocity=127):
        note = BaseInstrument.midify(note)
        velocity = BaseInstrument.midify(velocity)
        self._out_msg('note_on', note=note, velocity=velocity)

    def note_off(self, note):
        note = BaseInstrument.midify(note)
        self._out_msg('note_off', note=note)

    def _control(self, control, value):
        control = BaseInstrument.midify(control)
        value = BaseInstrument.midify(value)
        self._out_msg('control_change', control=control, value=value)

    def _out_msg(self, kind, **kwargs):
        m = mido.Message(kind, **kwargs)
        self.outport.send(m)


class Minilogue(BaseInstrument):
    AMP_ATTACK = 16
    AMP_DECAY = 17
    EG_ATTACK = 20
    EG_DECAY = 21
    VOICE_MODE = 27
    CUTOFF = 43
    RESONANCE = 44
    LFO_RATE = 24
    LFO_INT = 26

    def amp_decay(self, value):
        self._control(self.AMP_DECAY, value)

    def eg_decay(self, value):
        self._control(self.EG_DECAY, value)

    def cutoff(self, value):
        self._control(self.CUTOFF, value)

    def resonance(self, value):
        self._control(self.RESONANCE, value)

    def beat_on(self, note, step):
        self.note_on(note=note)

    def beat_off(self, note, step):
        self.note_off(note=note)

    def voice_mode(self, val):
        self._control(self.VOICE_MODE, val)


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        self._set_headers()
        self.wfile.write(b'<html><body><h1>POST!</h1></body></html>')


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


class Handler(WebSocket):
    def parse_url(self):
        qs = parse_qs(urlparse(self.request.path).query)
        self.name = qs.get('name', None)[0]

    def handleConnected(self):
        logging.debug('{} connected'.format(self.request.path))
        self.parse_url()
        with CLIENT_LOCK:
            clients.add(self)

    def handleClose(self):
        with CLIENT_LOCK:
            clients.remove(self)
        logging.debug('{} closed'.format(self))

    def handleMessage(self):
        data = json.loads(self.data)
        logging.debug('{}'.format(data))
        behaviors[self.name](data)


def broadcast_clients(msg=''):
    local_clients = []
    with CLIENT_LOCK:
        local_clients = [x for x in clients]
    for client in local_clients:
        client.sendMessage(msg)


def broadcast_sequencer_to_clients(note, step):
    broadcast_clients(json.dumps({'note': note, 'step': step}))


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


def run_ws():
    server = SimpleWebSocketServer(
        '0.0.0.0', 4444, Handler, selectInterval=0.005)
    logging.debug('Server starting...')
    server.serveforever()
    logging.debug('Server exited unexpectedly ...')


def run_http():
    httpd = socketserver.TCPServer(("0.0.0.0", HTTP_PORT), HttpHandler)
    logging.debug("serving at port {}".format(HTTP_PORT))
    httpd.serve_forever()


def metaball_cb(minilogue):
    def do_it(val):
        #minilogue.amp_decay(val + 20)
        minilogue.voice_mode(val)

    return do_it


def run():
    global minilogue_1
    global sequencer
    global worker
    global metronome
    global metaball

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(relativeCreated)6d %(threadName)s %(message)s')

    minilogue_1 = Minilogue('minilogue:minilogue MIDI 2 20:1')
    worker = Worker()
    metronome = Metronome(worker)
    sequencer = Sequencer(notes=LCD)

    metaball = Metaball(metaball_cb(minilogue_1))
    metronome.register_cb(sequencer.beat)

    sequencer.register_cb({'on': broadcast_sequencer_to_clients})
    sequencer.register_cb({'on': metaball.beat})
    sequencer.register_cb({
        'on': minilogue_1.beat_on,
        'off': minilogue_1.beat_off
    })

    clock_t = threading.Thread(target=metronome.loop, args=(), daemon=True)
    ws_t = threading.Thread(target=run_ws, args=(), daemon=True)
    http_t = threading.Thread(target=run_http, args=(), daemon=True)
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

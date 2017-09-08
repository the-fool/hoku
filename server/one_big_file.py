from bluezero import microbit, tools, constants
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import time
import random
import mido
import json
import threading

import http.server
import socketserver

loop = None
HTTP_PORT = 5555
WS_PORT = 4444
clients = []
socketserver.TCPServer.allow_reuse_address = True

minilogue_1 = None

# ACCEL_SRV = 'E95D0753-251D-470A-A062-FA1922DFA9A8'
# ACCEL_DATA = 'E95DCA4B-251D-470A-A062-FA1922DFA9A8'


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
        self._note('note_on', note, velocity)

    def note_off(self, note, velocity=127):
        self._note('note_off', note, velocity)

    def _note(self, kind, note, velocity):
        note = BaseInstrument.midify(note)
        velocity = BaseInstrument.midify(velocity)
        self._out_msg(kind, note=note, velocity=velocity)

    def _control(self, control, value):
        control = BaseInstrument.midify(control)
        value = BaseInstrument.midify(value)
        self._out_msg('control_change', control=control, value=value)

    def _out_msg(self, kind, **kwargs):
        m = mido.Message(kind, **kwargs)
        self.outport.send(m)


class Minilogue(BaseInstrument):
    VOICE_MODE = 27
    CUTOFF = 43
    RESONANCE = 44
    LFO_RATE = 24
    LFO_INT = 26

    def cutoff(self, value):
        self._control(self.CUTOFF, value)

    def resonance(self, value):
        self._control(self.RESONANCE, value)


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        self._set_headers()
        self.wfile.write(b'<html><body><h1>POST!</h1></body></html>')


class MyMicrobit(microbit.Microbit):
    def _accel_notify_cb(self):
        print('Accel subscribed!!!')
        return 1

    def subscribe_accel(self, user_callback):
        accel_obj = tools.get_dbus_obj(constants.BLUEZ_SERVICE_NAME,
                                       self.accel_data_path)
        accel_iface = tools.get_dbus_iface(constants.DBUS_PROP_IFACE,
                                           accel_obj)
        accel_iface.connect_to_signal('PropertiesChanged', user_callback)
        accel_obj.StartNotify(
            reply_handler=self._accel_notify_cb,
            error_handler=tools.generic_error_cb,
            dbus_interface=constants.GATT_CHRC_IFACE)


def find_mbit(name):
    try:
        return MyMicrobit(name=name)
    except:
        return None


def connect_mbit(mbit):
    try:
        mbit.connect()
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

    print('Subscribing to accel')
    vozuz.subscribe_accel(lambda l, data, sig: print('got: {}'.format(tools.bytes_to_xyz(data['Value']))))

    print('Setting up dbus loop')
    setup_dbus_loop()

    print('Running main loop')
    run_dbus_loop()


def parse(data):
    d = json.loads(data)
    return d


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


class Handler(WebSocket):
    def handleConnected(self):
        print(self.address, 'connected')
        clients.append(self)

    def handleClose(self):
        clients.remove(self)
        print(self.address, 'closed')

    def handleMessage(self):
        data = parse(self.data)
        print(data)
        cut = cent_to_midi(data['x'])
        res = cent_to_midi(data['y'])

        minilogue_1.cutoff(cut)
        minilogue_1.resonance(res)

class Looper:
    def __init__(self, bpm=240):
        self.bpm = bpm

    def loop(self):
        time.sleep(60 / self.bpm)
        note = random.randint(-15, 15)
        minilogue_1.note_off(note=60 + note)
        minilogue_1.note_on(note=60 + note)
        self.loop()


def run_ws():
    server = SimpleWebSocketServer(
        '0.0.0.0', 4444, Handler, selectInterval=0.01)
    print('Server starting...')
    server.serveforever()
    print('Server exited unexpectedly ...')


def run_http():
    httpd = socketserver.TCPServer(("", HTTP_PORT), HttpHandler)
    print("serving at port", HTTP_PORT)
    httpd.serve_forever()


def run():
    global minilogue_1
    minilogue_1 = Minilogue('minilogue:minilogue MIDI 2 20:1')

    looper = Looper()
    loop = threading.Thread(target=looper.loop, args=())
    ws = threading.Thread(target=run_ws, args=())
    http = threading.Thread(target=run_http, args=())
    ws.start()
    http.start()
    loop.start()

    ws.join()
    loop.join()
    http.join()

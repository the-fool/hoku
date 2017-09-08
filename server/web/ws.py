from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from server.midi.main import MidiProxy
import json

clients = []

CUTOFF = 43
RESONNANCE = 44


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


def centToMidi(value):
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
        cut = centToMidi(data['x'])
        res = centToMidi(data['y'])

        proxy.minilogue_1.cutoff(cut)
        proxy.minilogue_1.resonance(res)


def run():
    server = SimpleWebSocketServer(
        '0.0.0.0', 4444, Handler, selectInterval=0.01)
    print('Server starting...')
    server.serveforever()
    print('Server exited unexpectedly ...')

import asyncio
import logging
import serial_asyncio


class Protocol(asyncio.Protocol):
    def __init__(self, on_data_cb):
        super(Protocol, self)
        self.on_data_cb = on_data_cb

    def connection_made(self, transport):
        self.transport = transport
        logging.info('Connection to Arduino: {}'.format(transport))
        transport.serial.rts = False

    def data_received(self, data):
        for b in data:
            x = int.from_bytes([b], byteorder='big')
            print(x)
            # search for delimiter
            self.on_data_cb(x)

    def connection_lost(self, exc):
        logging.info('Arduino port closed')


class Slidey:
    def __init__(self, scale_cube, loop, instruments=[]):
        self.instruments = instruments
        self.prev_note = 0
        self.prev_x = 0
        self.scale_cube = scale_cube

        self.coro = serial_asyncio.create_serial_connection(
            loop,
            lambda: Protocol(self.on_note_change),
            '/dev/slidey',
            baudrate=9600)

    def on_note_change(self, x):
        if x is self.prev_x:
            return

        note = self.get_note(x)

        if x > 0:
            self.note_on(note)

        if self.prev_x > 0:
            self.note_off(self.prev_note)
        self.prev_x = x
        self.prev_note = note

    def note_on(self, note):
        print('note', note)
        for i in self.instruments:
            i.note_on(note, channel=3)

    def note_off(self, note):
        for i in self.instruments:
            i.note_off(note, channel=3)

    def get_note(self, x):
        return 60 + self.scale_cube.scale[x - 1 % 7]

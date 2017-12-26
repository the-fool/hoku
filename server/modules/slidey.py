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
        print(data)
        # search for delimiter
        self.on_data_cb(data)

    def connection_lost(self, exc):
        logging.info('Arduino port closed')


class Slidey:
    def __init__(self, scale_cube, loop, instruments=[]):
        self.instruments = instruments
        self.prev_note = 0
        self.scale_cube = scale_cube

        self.coro = serial_asyncio.create_serial_connection(
            loop,
            lambda: Protocol(self.on_note_change),
            '/dev/ttyACM2',
            baudrate=9600)

    def on_note_change(self, x):
        if x is self.prev_note:
            return

        if x > 0:
            self.note_on(x)

        if self.prev_note > 0:
            self.note_off(self.prev_note)

        self.prev_note = x

    def note_on(self, x):
        note = self.get_note(x)
        for i in self.instruments:
            i.note_on(note)

    def note_off(self, x):
        note = self.get_note(x)
        for i in self.instruments:
            i.note_off(note)

    def get_note(self, x):
        return self.scale_cube.scale[x - 1 % 7]

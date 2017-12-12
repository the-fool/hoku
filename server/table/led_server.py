import asyncio
import logging
import serial_asyncio
from server.modules.opc_client import OpcClientAsync

RED = (189, 22, 63)
WHITE = (240, 240, 240)
BLUE = (121, 31, 117)
GOLD = (242, 202, 33)
GREEN = (35, 100, 52)
PINK = (239, 53, 111)
PURPLE = (139, 0, 139)
TEAL = (52, 161, 152)
GREY = (10, 10, 10)

N_0 = WHITE
N_1 = PURPLE
N_2 = RED
N_3 = GOLD
N_4 = BLUE
N_5 = GREEN
N_6 = PINK
N_7 = TEAL

COLORS = [N_0, N_1, N_2, N_3, N_4, N_5, N_6, N_7]

L = 16
PETAL_STRIP = 12
NUM_VASE_LED = 2


class Protocol(asyncio.Protocol):
    def __init__(self, msg_sz, on_data_cb):
        super(Protocol, self)
        self.on_data_cb = on_data_cb
        self.sz = msg_sz
        self.msg = []

    def connection_made(self, transport):
        self.transport = transport
        logging.info('Connection to Arduino: {}'.format(transport))
        transport.serial.rts = False

    def data_received(self, data):
        self.msg.extend(data)
        if (len(self.msg) >= self.sz):
            self.on_data_cb(self.msg[:self.sz])
            self.msg = self.msg[self.sz:]

    def connection_lost(self, exc):
        logging.info('Arduino port closed')


class LedTCPServer(asyncio.Protocol):
    def __init__(
            self,
            loop,
            scale_cube,
            patch_cube,
            color_seqs,  # array
            fadecandy_host='127.0.0.1',
            ws_server_host='127.0.0.1'):
        self.client = OpcClientAsync(loop, '{}:7890'.format(fadecandy_host))
        self.scale_cube = scale_cube
        self.patch_cube = patch_cube

        self.old_scale = self.get_scale()
        self.old_patch = self.get_patch()

        self.color_seqs = color_seqs

        self.rhythm_index = 0
        self.petals = [[False] * 16] * 2
        self.pitches = [[0] * 16] * 2

        self.loop = loop

        pixel_step = {

            # There are 1 less petal strips than num petals
            'petal_strips': [[GREY] * PETAL_STRIP] * 15,
            'vases': [[[GREY] * NUM_VASE_LED] * 16] * 2
        }

        self.pixels = [pixel_step] * 16

        coro = serial_asyncio.create_serial_connection(
            loop,
            lambda: Protocol(64, self.on_recv_sensor_data),
            '/dev/ttyACM0',
            baudrate=9600)
        loop.run_until_complete(coro)

    async def metro_cb(self, ts):
        self.rhythm_index = ts % 16

        if self.scale_or_patch_diff():
            self.old_scale = self.get_scale()
            self.old_patch = self.get_patch()
            self.compute_pixels()

        await self.send_pixels()

    def scale_or_patch_diff(self):
        return self.old_scale is not self.get_scale() or\
            self.old_patch is not self.get_patch()

    def get_scale(self):
        return self.scale_cube.scale_index

    def get_patch(self):
        return self.patch_cube.patch

    def compute_pixels(self):
        """
        Computes a 16 * N matrix of pixels
        one list of N pixel items per each step in the sequence
        """
        for step in range(0, 16):
            self.compute_petal_strips(step)
            self.compute_vases(step)

    def compute_petal_strips(self, step):
        scale = self.get_scale()
        color = COLORS[scale + 1]

        for strip in self.pixels[step]['petal_strips']:
            for i, _ in enumerate(strip):
                strip[i] = color

    def compute_vases(self, step):
        for channel_index, vase_channel in enumerate(
                self.pixels[step]['vases']):
            for vase_index, vase in enumerate(vase_channel):
                for i, _ in enumerate(vase):
                    x = self.notes[channel_index][vase_index]
                    vase[i] = x

    def on_recv_sensor_data(self, data):
        logging.debug('LDCServer: Got sensor data {}'.format(data))
        for channel in range(2):
            for i in range(16):
                self.petals[channel][i] = data[channel * 32 + i]
                self.pitches[channel][i] = data[32 + channel * 32 + i]

        self.compute_pixels()

        asyncio.ensure_future(self.send_pixels(), loop=self.loop)
        asyncio.ensure_future(self.update_color_seqs(), loop=self.loop)

    async def update_color_seqs(self):
        def to_cms_rhythm(channel):
            """
            Checks petal state to determine if the note is a rest or not
            """
            return [
                x if self.petals[channel][i] else -1
                for i, x in enumerate(self.pitches[channel])
            ]

        for i, x in enumerate(self.color_seqs):
            new_rhythm = to_cms_rhythm(i)
            await x.set_rhythm(new_rhythm)

    async def send_pixels(self):
        pixel_step = self.pixls[self.rhythm_index]
        await self.client.put_pixels([])

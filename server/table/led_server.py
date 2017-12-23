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

DIM_FACTOR = 0.55
N_0 = WHITE

N_1 = PURPLE
N_2 = RED
N_3 = GOLD
N_4 = BLUE
N_5 = GREEN
N_6 = PINK
N_7 = TEAL

COLORS = [N_0, N_1, N_2, N_3, N_4, N_5, N_6, N_7, N_1, N_2, N_3, N_4, N_5]

L = 16

N_LEDS_IN_PETAL_STRIP = 6
N_LEDS_IN_VASE = 1
N_LEDS_IN_YURT_PANEL = 3

# petal strips start at pin 0
PETAL_STRIP_PIN = 0
PETAL_STRIP_OFFSET = PETAL_STRIP_PIN * 64

# vases start at pin 4

VASE_1_PIN = 4
VASE_2_PIN = 5
VASE_1_OFFSET = 64 * VASE_1_PIN
VASE_2_OFFSET = 64 * VASE_2_PIN

# yurt starts at pin 6
YURT_PIN = 6
YURT_OFFSET = 6 * 64
GRAY_ARRAY = [(GREY)] * 512


class Protocol(asyncio.Protocol):
    def __init__(self, msg_sz, delim, on_data_cb):
        super(Protocol, self)
        self.on_data_cb = on_data_cb
        self.sz = msg_sz
        self.delim = delim
        self.msg = []

    def connection_made(self, transport):
        self.transport = transport
        logging.info('Connection to Arduino: {}'.format(transport))
        transport.serial.rts = False

    def data_received(self, data):
        print(data)
        self.msg.extend(data)
        # search for delimiter
        for i, x in enumerate(self.msg):
            if x == self.delim:
                # are we at the end of a message?
                if i == self.sz:
                    print('HERE', i, self.msg)
                    self.on_data_cb(self.msg[:self.sz])
                    self.msg = self.msg[self.sz:]
                else:
                    # we missed a packet -- throw away the remains
                    self.msg = self.msg[i + 1:]

    def connection_lost(self, exc):
        logging.info('Arduino port closed')


def pixel_step_factory():
    return {
        # There are 16 yurt panels
        'yurt': [GREY for _ in range(16)],

        # There are 1 less petal strips than num vases
        'petal_strips': [GREY for _ in range(N_LEDS_IN_PETAL_STRIP)],

        # there are 2 channels of 16 vases
        'vases': [[GREY for _ in range(16)] for _ in range(2)]
    }  # yapf: disable


class LedTCPServer(asyncio.Protocol):
    def __init__(
            self,
            loop,
            scale_cube,
            patch_cube,
            color_seqs,  # array
            fadecandy_host='127.0.0.1',
            ws_server_host='127.0.0.1'):
        self.client = OpcClientAsync(
            loop, '{}:7890'.format(fadecandy_host), verbose=False)

        asyncio.ensure_future(self.client.set_interpolation(False), loop=loop)

        self.scale_cube = scale_cube
        self.patch_cube = patch_cube

        self.color_seqs = color_seqs

        self.ts = 0
        self.rhythm_index = 0
        self.pitches = [[0 for _ in range(16)], [0 for _ in range(16)]]
        self.loop = loop

        # dict of pixel info
        self.pixels = pixel_step_factory()

        # buffer of all pixels the fadecandy can handle
        self.pixel_array = [GREY] * 512

        coro1 = serial_asyncio.create_serial_connection(
            loop,
            lambda: Protocol(16, 127, self.channel_1_sensor),
            '/dev/ttyACM0',
            baudrate=9600)

        coro2 = serial_asyncio.create_serial_connection(
            loop,
            lambda: Protocol(16, 127, self.channel_2_sensor),
            '/dev/ttyACM1',
            baudrate=9600)

        self.coros = [coro1, coro2]

    async def metro_cb(self, ts):
        self.ts = ts
        self.rhythm_index = ts % 16
        self.do_pixels()
        await self.send_pixels()

    def get_scale(self):
        return self.scale_cube.scale_index

    def get_patch(self):
        return self.patch_cube.patch

    def is_vase_activated(self, channel, index):
        return self.get_pitch(channel, index) > 0

    def get_pitch(self, channel_index, step_index):
        return self.pitches[channel_index][step_index]

    def do_pixels(self):
        """
        Dos a 16 * N matrix of pixels
        one list of N pixel items per each step in the sequence
        """
        self.do_yurt_pixels()
        self.do_petal_strip_pixels()
        self.do_vase_pixels()

    def do_petal_strip_pixels(self):
        color = self.get_color()

        petal_strips = self.pixels['petal_strips']
        for i, _ in enumerate(petal_strips):
            petal_strips[i] = color

    def do_vase_pixels(self):
        for channel_i, vase_channel in enumerate(self.pixels['vases']):
            for vase_i, _ in enumerate(vase_channel):
                pitch = self.get_pitch(channel_i, vase_i)

                if pitch > 0:
                    # pitch is an intoned note
                    new_color = COLORS[pitch]
                else:
                    # pitch is a rest
                    new_color = GREY

                vase_channel[vase_i] = new_color

    def do_yurt_pixels(self):
        yurt = self.pixels['yurt']
        for pane_i, _ in enumerate(yurt):
            if pane_i == self.rhythm_index:
                yurt[pane_i] = self.get_color()
            else:
                yurt[pane_i] = GREY

    def get_color(self):
        scale = self.get_scale()
        color = COLORS[scale + 1]
        return color

    def on_recv_sensor_data(self, channel, data):
        logging.debug('LDCServer: Got sensor data {}'.format(data))

        print(data)
        for i in range(16):
            self.pitches[channel][i] = data[i]

        self.do_pixels()

        asyncio.ensure_future(self.send_pixels(), loop=self.loop)
        asyncio.ensure_future(self.update_color_seqs(), loop=self.loop)

    def channel_1_sensor(self, data):
        self.on_recv_sensor_data(0, data)

    def channel_2_sensor(self, data):
        self.on_recv_sensor_data(1, data)

    async def update_color_seqs(self):
        def to_cms_rhythm(channel):
            """
            Checks petal state to determine if the note is a rest or not
            """
            ret = []
            for i, x in enumerate(self.pitches[channel]):
                if x > 0:
                    ret.append(x)
                else:
                    ret.append(-1)
            return ret

        for i, color_seq in enumerate(self.color_seqs):
            new_rhythm = to_cms_rhythm(i)
            await color_seq.set_rhythm(new_rhythm)
            print('set', new_rhythm)

    async def send_pixels(self):
        self.do_pixel_array()

        # await self.client.put_pixels(GRAY_ARRAY)

        await self.client.put_pixels(self.pixel_array)

    def dim(self, color):
        def _dim(c):
            return max(0, c * DIM_FACTOR)
        return (_dim(color[0]), _dim(color[1]), _dim(color[2]))

    def do_pixel_array(self):
        petal_strips = self.pixels['petal_strips']
        vases = self.pixels['vases']
        yurt = self.pixels['yurt']

        # compute petal strips
        for i in range(N_LEDS_IN_PETAL_STRIP):
            self.pixel_array[i + PETAL_STRIP_OFFSET] = petal_strips[i]

        # compute vases
        for vase_index, vase_color in enumerate(vases[0]):
            if self.rhythm_index is vase_index:
                self.pixel_array[vase_index + VASE_1_OFFSET] = vase_color
            else:
                self.pixel_array[vase_index + VASE_1_OFFSET] = self.dim(vase_color)

        for vase_index, vase_color in enumerate(vases[1]):
            if (self.ts // 16) % 16 is vase_index:
                self.pixel_array[vase_index + VASE_2_OFFSET] = vase_color
            else:
                self.pixel_array[vase_index + VASE_2_OFFSET] = self.dim(vase_color)

        for index, yurt_color in enumerate(yurt):
            for j in range(N_LEDS_IN_YURT_PANEL):
                self.pixel_array[j + (index * N_LEDS_IN_YURT_PANEL) + YURT_OFFSET] = yurt_color


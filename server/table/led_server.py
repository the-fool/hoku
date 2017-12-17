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

COLORS = [N_0, N_1, N_2, N_3, N_4, N_5, N_6, N_7, N_1, N_2, N_3, N_4, N_5]

L = 16
N_PETAL_STRIP = 12
N_VASE = 2
N_YURT_PANEL = 1

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
                    self.on_data_cb(self.msg[:self.sz])
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
        'petal_strips': [[GREY for _ in range(N_PETAL_STRIP)] for _ in range(16)],

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
        self.client = OpcClientAsync(loop, '{}:7890'.format(fadecandy_host), verbose=False)

        asyncio.ensure_future(self.client.set_interpolation(False), loop=loop)
        self.scale_cube = scale_cube
        self.patch_cube = patch_cube

        self.old_scale = self.get_scale()
        self.old_patch = self.get_patch()

        self.color_seqs = color_seqs

        self.rhythm_index = 0
        self.pitches = [[0 for _ in range(16)], [0 for _ in range(16)]]
        self.loop = loop

        # dict of pixel info
        self.pixels = [pixel_step_factory() for _ in range(16)]

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
        self.rhythm_index = ts % 16

        if self.scale_or_patch_diff():
            self.old_scale = self.get_scale()
            self.old_patch = self.get_patch()
        self.do_pixels()

        await self.send_pixels()

    def scale_or_patch_diff(self):
        return self.old_scale is not self.get_scale() or\
            self.old_patch is not self.get_patch()

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
        for step in range(0, 16):
            self.do_yurt_pixels(step)
            self.do_petal_strip_pixels(step)
            self.do_vase_pixels(step)

    def do_petal_strip_pixels(self, step):
        color = self.get_color()

        for strip in self.pixels[step]['petal_strips']:
            for i, _ in enumerate(strip):
                strip[i] = color

    def do_vase_pixels(self, step):
        for channel_i, vase_channel in enumerate(self.pixels[step]['vases']):
            for vase_i, _ in enumerate(vase_channel):
                pitch = self.get_pitch(channel_i, step)

                if pitch > 0:
                    # pitch is an intoned note
                    new_color = COLORS[pitch]
                else:
                    # pitch is a rest
                    new_color = GREY

                vase_channel[vase_i] = new_color

    def do_yurt_pixels(self, step):
        yurt = self.pixels[step]['yurt']
        for pane_i, _ in enumerate(yurt):
            if pane_i == step:
                yurt[pane_i] = self.get_color()
            else:
                yurt[pane_i] = GREY

    def get_color(self):
        scale = self.get_scale()
        color = COLORS[scale + 1]
        return color

    def on_recv_sensor_data(self, channel, data):
        logging.debug('LDCServer: Got sensor data {}'.format(data))

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

    async def send_pixels(self):
        pixel_step = self.pixels[self.rhythm_index]
        self.do_pixel_array(pixel_step)
        await self.client.put_pixels(GRAY_ARRAY)

        await self.client.put_pixels(self.pixel_array)
    def do_pixel_array(self, pixel_step):
        # petal strips start at pin 0
        PETAL_STRIP_PIN = 0

        # vases start at pin 4

        VASE_1_PIN = 4
        VASE_2_PIN = 5

        # yurt starts at pin 5
        YURT_PIN = 6

        petal_strips = pixel_step['petal_strips']
        vases = pixel_step['vases']
        yurt = pixel_step['yurt']

        def get_petal_strip_offset(index):
            strips_per_pin = 4
            pin = index // strips_per_pin + PETAL_STRIP_PIN
            pin_offset = pin * 64
            base_offset = N_PETAL_STRIP * (index % strips_per_pin)
            return pin_offset + base_offset

        def get_vase_offset(channel):
            pin_offset = VASE_1_PIN + channel * 64
            return pin_offset

        def get_yurt_offset():
            return YURT_PIN * 64

        # compute petal strips
        for index, petal_strip in enumerate(petal_strips):
            offset = get_petal_strip_offset(index)
            for i in range(N_PETAL_STRIP):
                self.pixel_array[i + offset] = petal_strip[i]

        # compute vases
        for channel_index, vase_channel in enumerate(vases):
            offset = get_vase_offset(channel_index)
            for vase_index, vase in enumerate(vase_channel):
                self.pixel_array[vase_index + offset] = vase

        yurt_offset = get_yurt_offset()
        for index, yurt in enumerate(yurt):
            self.pixel_array[index + yurt_offset] = yurt


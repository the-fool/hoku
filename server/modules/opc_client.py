import asyncio
import socket
import struct
import sys

"""
Main server for controlling LED FadeCandy server
"""


class OpcClientAsync:
    def __init__(self, loop, server_ip_port, verbose=True):
        """Create an OPC client object which sends pixels to an OPC server.

        server_ip_port should be an ip:port or hostname:port as a single string.
        For example: '127.0.0.1:7890' or 'localhost:7890'

        There are two connection modes:
        * In long connection mode, we try to maintain a single long-lived
          connection to the server.  If that connection is lost we will try to
          create a new one whenever put_pixels is called.  This mode is best
          when there's high latency or very high framerates.
        * In short connection mode, we open a connection when it's needed and
          close it immediately after.  This means creating a connection for each
          call to put_pixels. Keeping the connection usually closed makes it
          possible for others to also connect to the server.

        A connection is not established during __init__.  To check if a
        connection will succeed, use can_connect().

        If verbose is True, the client will print debugging info to the console.

        """
        self.verbose = verbose
        self.host, self.port = server_ip_port.split(':')
        self.port = int(self.port)
        self.socket = None  # will be None when we're not connected
        self.loop = loop

    def debug(self, m):
        if self.verbose:
            print('    %s' % str(m))

    async def ensure_connected(self):
        """Set up a connection if one doesn't already exist.

        Return True on success or False on failure.

        """
        if self.socket:
            self.debug('_ensure_connected: already connected, doing nothing')
            return True

        try:
            self.debug('_ensure_connected: trying to connect...')
            _, self.socket = await asyncio.open_connection(
                self.host, self.port, loop=self.loop)
            self.debug('_ensure_connected:    ...success')
            return True
        except:
            self.debug('_ensure_connected:    ...failure')
            self.socket = None
            return False

    def disconnect(self):
        """Drop the connection to the server, if there is one."""
        self.debug('disconnecting')
        if self.socket:
            self.socket.close()
        self.socket = None

    async def can_connect(self):
        """Try to connect to the server.

        Return True on success or False on failure.

        If in long connection mode, this connection will be kept and re-used for
        subsequent put_pixels calls.

        """
        return await self.ensure_connected()

    async def put_pixels(self, pixels, channel=0):
        """Send the list of pixel colors to the OPC server on the given channel.

        channel: Which strand of lights to send the pixel colors to.
            Must be an int in the range 0-255 inclusive.
            0 is a special value which means "all channels".

        pixels: A list of 3-tuples representing rgb colors.
            Each value in the tuple should be in the range 0-255 inclusive.
            For example: [(255, 255, 255), (0, 0, 0), (127, 0, 0)]
            Floats will be rounded down to integers.
            Values outside the legal range will be clamped.

        Will establish a connection to the server as needed.

        On successful transmission of pixels, return True.
        On failure (bad connection), return False.

        The list of pixel colors will be applied to the LED string starting
        with the first LED.  It's not possible to send a color just to one
        LED at a time (unless it's the first one).

        """
        self.debug('put_pixels: connecting')
        is_connected = await self.ensure_connected()
        if not is_connected:
            self.debug('put_pixels: not connected.  ignoring these pixels.')
            return False

        # build OPC message
        len_hi_byte = int(len(pixels) * 3 / 256)
        len_lo_byte = (len(pixels) * 3) % 256
        command = 0  # set pixel colors from openpixelcontrol.org

        header = struct.pack("BBBB", channel, command, len_hi_byte,
                             len_lo_byte)

        pieces = [
            struct.pack("BBB",
                        min(255, max(0, int(r))),
                        min(255, max(0, int(g))), min(255, max(0, int(b))))
            for r, g, b in pixels
        ]

        if sys.version_info[0] == 3:
            # bytes!
            message = header + b''.join(pieces)
        else:
            # strings!
            message = header + ''.join(pieces)

        self.debug('put_pixels: sending pixels to server')
        try:
            self.socket.write(message)
            await self.socket.drain()
        except Exception as e:
            print(e)
            self.debug('put_pixels: connection lost.  could not send pixels.')
            self.socket = None
            return False

        return True

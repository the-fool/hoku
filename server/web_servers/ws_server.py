import threading
import json
import logging

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from urllib.parse import urlparse, parse_qs


def wsHandler(client_pool, behaviors):
    class Handler(WebSocket):
        def parse_url(self):
            qs = parse_qs(urlparse(self.request.path).query)
            self.name = qs.get('name', None)[0]

        def handleConnected(self):
            logging.debug('{} connected'.format(self.request.path))
            self.parse_url()
            client_pool.add(self)

        def handleClose(self):
            client_pool.remove(self)
            logging.debug('{} closed'.format(self))

        def handleMessage(self):
            data = json.loads(self.data)
            logging.debug('{}'.format(data))
            behaviors[self.name](data)


def run_ws_server(client_pool, behaviors, port=4444):
    server = SimpleWebSocketServer(
        '0.0.0.0', port, wsHandler(client_pool, behaviors), selectInterval=0.005)
    logging.debug('Server starting...')
    server.serveforever()
    logging.debug('Server exited unexpectedly ...')

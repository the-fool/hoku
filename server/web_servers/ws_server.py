import json
import logging

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from urllib.parse import urlparse, parse_qs
import threading


def wsHandler(lock, client_pool, behaviors):
    class Handler(WebSocket):
        def parse_url(self):
            qs = parse_qs(urlparse(self.request.path).query)
            self.name = qs.get('name', [None])[0]

        def handleConnected(self):
            logging.debug('{} connected'.format(self.request.path))
            self.parse_url()
            logging.debug('Appending {}'.format(self.name))
            with lock:
                client_pool.append(self)

        def handleClose(self):
            with lock:
                client_pool.remove(self)
            logging.debug('{} closed'.format(self))

        def handleMessage(self):
            data = json.loads(self.data)
            # logging.debug('{}'.format(data))
            behaviors[self.name](data)

    return Handler


def run_ws_server(read_pipe, behaviors, port=4444):
    lock = threading.Lock()
    client_pool = []

    server = SimpleWebSocketServer(
        '0.0.0.0',
        port,
        wsHandler(lock, client_pool, behaviors),
        selectInterval=0.005)

    #
    # Broadcaster Thread
    #

    broadcaster_t = threading.Thread(
        target=bcast_clock_to_clients, args=(client_pool, lock, read_pipe))
    broadcaster_t.start()

    logging.debug('WS Server at port {}'.format(port))
    server.serveforever()
    logging.debug('Server exited unexpectedly ...')
    broadcaster_t.join()


def bcast_clock_to_clients(clients, lock, pipe):
    logging.debug('Broadcaster thread started...')
    while True:
        ts = pipe.recv()
        msg = json.dumps({'ts': ts})
        with lock:
            for c in clients:
                c.sendMessage(msg)

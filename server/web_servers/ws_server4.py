import asyncio
import websockets
import json
import logging
import uuid


def main(behaviors):
    """
    Main entrypoint

    Producers is a hash map of {string: observable}
    Consumers is a list of records {path: string, coro: coroutine}

    The consumer coroutine takes (kind, payload, uuid) -- all strings
    """
    port = 7700
    logging.info('Creating ws server handler at 0.0.0.0:{}'.format(port))
    return websockets.serve(make_handler(behaviors), '0.0.0.0', port)


def make_handler(behaviors):
    connections = set()

    async def producer_handler(websocket, path):
        nonlocal behaviors
        _, producer_obs = behaviors.get(path, (None, None))

        if producer_obs is None:
            return

        producer_queue, dispose = await producer_obs(uuid=websocket.uuid)

        while True:
            try:
                message = await producer_queue.get()
                logging.debug('Going to send {}'.format(message))
                await websocket.send(message)
            except:
                dispose()

    async def consumer_handler(websocket, path):
        nonlocal behaviors
        consumer_coro, _ = behaviors.get(path, (None, None))

        if consumer_coro is None:
            return

        logging.info('Consumer at path: {} -- {}'.format(path, consumer_coro))
        while True:
            msg = await websocket.recv()

            try:
                data = json.loads(msg)
            except:
                logging.error('JSON error parsing {}'.format(msg))
                continue

            kind = data.get('kind', None)
            payload = data.get('payload', None)

            logging.debug('Got: {} {}'.format(kind, payload))
            await consumer_coro(
                kind=kind, payload=payload, uuid=websocket.uuid)

    async def handler(websocket, path):
        nonlocal connections

        # assign a new uuid to the websocket object
        websocket.uuid = uuid.uuid4().hex

        # add the connection
        connections.add(websocket)

        # drop the first char, which is a root slash
        path = path[1:]

        logging.info(
            'WS Server: new connection -- {} at {}'.format(websocket, path))
        logging.info(
            'WS Server: Current # connections: {}'.format(len(connections)))

        consumer_task = asyncio.ensure_future(
            consumer_handler(websocket, path))
        producer_task = asyncio.ensure_future(
            producer_handler(websocket, path))

        # These tasks will return once the WebSocket closes
        # (or another uncaught exception is thrown)
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.ALL_COMPLETED, )

        # We should cancel the remaining tasks
        for task in pending:
            task.cancel()

        logging.info('Disconnecting: {}'.format(websocket))
        connections.remove(websocket)
        logging.info('Current # connections: {}'.format(len(connections)))

    return handler

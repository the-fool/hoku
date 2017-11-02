import asyncio
import websockets
import json
import logging
import uuid


def make_handler(consumers, producers):
    connections = set()

    async def producer_handler(websocket, path):
        nonlocal producers
        producer_obs = producers.get(path, None)

        if producer_obs is None:
            return

        producer_q, dispose = producer_obs(uuid=websocket.uuid)

        while True:
            try:
                message = await producer_q.get()
                logging.info('Going to send {}'.format(message))
                await websocket.send(message)
            except:
                dispose()

    async def consumer_handler(websocket, path):
        nonlocal consumers

        filtered_consumers = [
            c['coro'] for c in consumers if c['path'] == path
        ]
        logging.info(
            'Consumers at path: {} -- {}'.format(path, filtered_consumers))
        while True:
            msg = await websocket.recv()

            try:
                data = json.loads(msg)
            except:
                logging.error('JSON error parsing {}'.format(msg))
                continue

            kind = data.get('kind', None)
            payload = data.get('payload', None)

            logging.info('Got: {} {}'.format(kind, payload))
            for consumer in filtered_consumers:
                await consumer(kind=kind, payload=payload, uuid=websocket.uuid)

    async def handler(websocket, path):
        nonlocal connections

        websocket.uuid = uuid.uuid4().hex

        connections.add(websocket)

        # drop the first char, which is a root slash
        path = path[1:]

        logging.info('New connection: {} at {}'.format(websocket, path))

        logging.info('Current # connections: {}'.format(len(connections)))

        consumer_task = asyncio.ensure_future(
            consumer_handler(websocket, path))
        producer_task = asyncio.ensure_future(
            producer_handler(websocket, path))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED, )

        for task in pending:
            task.cancel()
        logging.info('Disconnecting: {}'.format(websocket))
        connections.remove(websocket)
        logging.info('Current # connections: {}'.format(len(connections)))

    return handler


def main(consumers, producers):
    logging.info('Creating ws server handler')
    return websockets.serve(
        make_handler(consumers, producers), '0.0.0.0', 7700)


def run_standalone():
    from ..observable import observable_factory
    test_prod_obs, test_prod_emit = observable_factory()

    async def test_producer_cb(payload):
        payload += 1000
        await test_prod_emit(json.dumps({'broadcast': payload}))

    async def test_consumer(kind, payload, uuid):
        print(kind, payload)
        await test_prod_emit(
            json.dumps({
                'echo': kind,
                'data': payload
            }), uuid=uuid)
        await asyncio.sleep(2)
        await test_producer_cb(payload)

    logging.basicConfig(
        level=logging.INFO,
        format='%(relativeCreated)6d %(processName)s %(message)s')

    producers = {'test': test_prod_obs}
    consumers = [{'path': 'test', 'coro': test_consumer}]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(producers=producers, consumers=consumers))
    loop.run_forever()


if __name__ == '__main__':
    run_standalone()

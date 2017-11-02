import json
import asyncio
import logging
from .ws_server4 import main


def run_standalone():
    """
    TESTING purposes!

    Only if we want to run this server out of the whole system
    This mocks up dependencies
    """
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
        format='%(relativeCreated)6d %(message)s')

    producers = {'test': test_prod_obs}
    consumers = [{'path': 'test', 'coro': test_consumer}]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(producers=producers, consumers=consumers))
    loop.run_forever()


if __name__ == '__main__':
    run_standalone()

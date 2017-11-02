import asyncio
import logging
from uuid import uuid4


def observable_factory():
    subscriptions = []

    def make_dispose(uuid):
        def dispose():
            nonlocal subscriptions
            subscriptions = [s for s in subscriptions if s['uuid'] != uuid]
            logging.info('Unsubscribed {}'.format(uuid))

        return dispose

    def subscribe(uuid=None):
        uuid = uuid if uuid is not None else uuid4().hex

        nonlocal subscriptions

        q = asyncio.Queue()
        subscriptions.append({'uuid': uuid, 'q': q})
        return q, make_dispose(uuid)

    async def emit(msg, uuid=None):
        nonlocal subscriptions

        logging.info('Emitting {}'.format(msg))
        logging.info('Num subs: {}'.format(len(subscriptions)))

        for sub in subscriptions:
            if uuid is None or sub['uuid'] == uuid:
                await sub['q'].put(msg)

    return subscribe, emit

import asyncio
import logging
from uuid import uuid4


def observable_factory():
    subscriptions = []
    last_emission = None

    def make_dispose(uuid):
        def dispose():
            nonlocal subscriptions
            subscriptions = [s for s in subscriptions if s['uuid'] != uuid]
            logging.info('Unsubscribed {}'.format(uuid))

        return dispose

    async def subscribe(uuid=None):
        nonlocal subscriptions
        nonlocal last_emission

        uuid = uuid if uuid is not None else uuid4().hex

        q = asyncio.Queue()
        subscriptions.append({'uuid': uuid, 'q': q})

        # add last emission for replay value
        # this gets new subscribers up to speed on the current state!
        if last_emission is not None:
            await q.put(last_emission)

        return q, make_dispose(uuid)

    async def emit(msg, uuid=None):
        nonlocal last_emission
        nonlocal subscriptions

        # If the msg is a broadcast, store the most recent message
        if uuid is None:
            last_emission = msg

        logging.info('Emitting {}'.format(msg))
        logging.info('Num subs: {}'.format(len(subscriptions)))

        for sub in subscriptions:
            if uuid is None or sub['uuid'] == uuid:
                await sub['q'].put(msg)

    return subscribe, emit

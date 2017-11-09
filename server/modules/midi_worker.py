import logging
import asyncio


def midi_worker_factory(instruments):
    q = asyncio.Queue()

    async def midi_worker_coro():
        nonlocal instruments
        nonlocal q

        logging.info('Midi Worker starting')

        while True:
            task = await q.get()
            name = task.get('instrument_name', None)
            instrument = instruments.get(name, None)
            if not instrument:
                logging.error('Error: missing instrument {}'.format(name))
                continue
            method_name = task.get('method', None)
            method = getattr(instrument, method_name, None)
            if not method:
                logging.error('Error: missing method {}'.format(method_name))
                continue
            payload = task.get('payload', None)
            if not payload:
                logging.error('Error: missing payload')
                continue

            method(*payload)

    return q, midi_worker_coro()

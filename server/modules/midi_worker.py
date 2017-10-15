import logging


class MidiWorker:
    def __init__(self, q, instruments):
        self.q = q
        self.instruments = instruments
        self.i = 0

    def check_qsize(self):
        self.i += 1

        if self.i == 300:
            self.i = 0
            qsize = self.q.qsize()
            if qsize > 50:
                logging.debug('WARNING! Worker Q size {}'.format(qsize))

    def start_consuming(self):
        logging.debug('Midi Worker starting')
        while True:
            self.check_qsize()
            task = self.q.get()
            #  logging.debug('Worker got: {}'.format(task))

            name = task.get('instrument_name', None)
            instrument = self.instruments.get(name, None)
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

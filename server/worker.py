import logging

class Worker:
    def __init__(self, q):
        self.q = q

    def consume(self):
        while True:
            task = self.q.get()
            cb = task.get('cb', None)
            args = task.get('args', [])
            kwargs = task.get('kwargs', {})
            logging.debug("Worker got: {}, args: {}, kwargs: {}".format(cb, args, kwargs))
            if cb:
                cb(*args, **kwargs)

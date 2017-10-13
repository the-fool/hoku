class Worker:
    def __init__(self, q):
        self.q = q

    def consume(self):
        while True:
            task = self.q.get()
            cb = task.get('cb', None)
            args = task.get('args', [])
            kwargs = task.get('kwargs', {})

            if cb:
                cb(*args, **kwargs)

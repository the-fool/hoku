import threading


class Worker:
    def __init__(self):
        self.cv = threading.Condition()
        self.q = []

    def consume(self):
        while True:
            local_q = []
            with self.cv:
                while len(self.q) == 0:
                    self.cv.wait()
                local_q = [task for task in self.q]
                self.q = []
            for task in local_q:
                task['cb'](*task['args'], **task['kwargs'])

    def add(self, task, *args, **kwargs):
        with self.cv:
            self.q.append({'cb': task, 'args': args, 'kwargs': kwargs})
            self.cv.notify_all()

    def add_all(self, tasks, *args, **kwargs):
        with self.cv:
            self.q.extend([{
                'cb': task,
                'args': args,
                'kwargs': kwargs
            } for task in tasks])
            self.cv.notify_all()

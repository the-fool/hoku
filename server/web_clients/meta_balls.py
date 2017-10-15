import threading
import logging


class MetaBalls:
    def __init__(self, clock_pipe, worker_pipe, client_pipe, msg):
        self.lock = threading.Lock()
        self.n_steps = 8
        self.msg = msg
        self.worker_pipe = worker_pipe
        self.clock_pipe = clock_pipe
        self.data = [0] * self.n_steps
        self.client_pipe = client_pipe

    def start(self):
        clock_reader = threading.Thread(target=self.clock_reader)
        clock_reader.start()

        while True:
            data = self.client_pipe.recv()
            with self.lock:
                self.set_data_points(data)
        logging.error('MetaBalls unexpectedly exited')

    def set_data_point(self, i, v):
        self.data[i] = v

    def set_data_points(self, data):
        self.data = [0] * self.n_steps
        for d in data:
            self.data[d['i']] = d['value']

    def beat(self, step):
        step = step % self.n_steps
        with self.lock:
            val = self.data[step] * 100
        self.msg.update({'payload': [val]})
        self.worker_pipe.send(self.msg)

    def clock_reader(self):
        while True:
            ts = self.clock_pipe.recv()
            self.beat(ts)

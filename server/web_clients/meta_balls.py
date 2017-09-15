class MetaBalls:
    def __init__(self, instrument_cb):
        self.n_steps = 8
        self.instrument_cb = instrument_cb
        self.data = [0] * self.n_steps

    def set_data_point(self, i, v):
        self.data[i] = v

    def set_data_points(self, data):
        self.data = [0] * self.n_steps
        for d in data:
            self.data[d['i']] = d['value']

    def beat(self, note, step):
        step = step % self.n_steps
        val = self.data[step] * 100
        self.instrument_cb(val)

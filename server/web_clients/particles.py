from ..util import cent_to_midi


def particles_cb(worker_queue, instrument_name='minilogue_1'):
    def do_it(data):
        x = cent_to_midi(data['x'])
        y = cent_to_midi(data['y'])

        tasks = [{
            'instrument_name': instrument_name,
            'method': 'amp_decay',
            'payload': [x]
        }, {
            'instrument_name': instrument_name,
            'method': 'eg_decay',
            'payload': [y]
        }]

        for task in tasks:
            worker_queue.put(task)

    return do_it

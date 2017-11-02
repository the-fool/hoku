from ..util import cent_to_midi


def particles_cb(worker_pipe, instrument_name='minilogue_1'):
    def do_it(data):
        x = cent_to_midi(data['x'])
        y = cent_to_midi(data['y'])

        tasks = [{
            'instrument_name': instrument_name,
            'method': 'eg_decay',
            'payload': [x]
        }, {
            'instrument_name': instrument_name,
            'method': 'resonance',
            'payload': [y]
        }]

        for task in tasks:
            worker_pipe.send(task)

    return do_it


def particles_factory(midi_worker_q, instrument_name='minilogue_1'):
    async def ws_consumer(kind, payload, uuid):
        nonlocal midi_worker_q
        nonlocal instrument_name

        x = cent_to_midi(payload['x'])
        y = cent_to_midi(payload['y'])

        tasks = [{
            'instrument_name': instrument_name,
            'method': 'eg_decay',
            'payload': [x]
        }, {
            'instrument_name': instrument_name,
            'method': 'resonance',
            'payload': [y]
        }]

        for task in tasks:
            await midi_worker_q.put(task)

    return ws_consumer

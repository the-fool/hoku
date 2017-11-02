import asyncio
import websockets
import random
import json
import logging
import math
import time
import threading

PADDING = 80
bug_pool_lock = threading.Lock()
ARENA_SIZE = (1800, 900)

connections = set()
bugs = []

PITCH_TO_SCALE = [60, 62, 64, 65, 67, 69, 71]
state_queue = asyncio.Queue()


def bug_factory(kind, pitch):
    x, y = random_pos()
    return {
        'pk': 'pk{}'.format(int((time.monotonic()) * 100)),
        'kind': kind,
        'pitch': PITCH_TO_SCALE[pitch],
        'deg': random.randint(0, 360),
        'rot_vel': random.random() * 2 - 1,
        'vel': 0.1,
        'x': x,
        'y': y,
        'targetX': x,
        'targetY': y,
        'joined': 0,
        'to_ding': True,
        'dinging': False,
        'to_die': False,
        'to_remove': False,
        'when_donged': 0,
        'duration': 0.5
    }


DELTA_VELOCITY = 0.001
C_VELOCITY = 0.01
DEFAULT_VELOCITY = 3
DELTA_DEGREE = 2


def bug_kind_to_instrument(kind):
    if kind == 0:
        return 'minilogue_1'
    elif kind == 1:
        return 'minilogue_2'
    elif kind == 2:
        return 'nord'


def random_pos():
    x = random.randint(0 + PADDING, ARENA_SIZE[0] - PADDING)
    y = random.randint(0 + PADDING, ARENA_SIZE[1] - PADDING)
    return (x, y)


def tick_bugs():
    global bugs
    global bug_pool_lock

    with bug_pool_lock:
        for agent in bugs:
            if agent['to_remove']:
                remove_bug(agent)
                continue
            x = agent['x']
            y = agent['y']

            if x <= PADDING or x >= (ARENA_SIZE[0] - PADDING):
                agent['deg'] = (180 + agent['deg']) % 360

            if y <= PADDING or y >= (ARENA_SIZE[1] - PADDING):
                agent['deg'] = (180 + agent['deg']) % 360

            v = agent['vel']
            d = agent['deg']

            new_x = (
                v * math.sin(math.radians(d)) + agent['x']) % ARENA_SIZE[0]
            new_y = (
                v * math.cos(math.radians(d)) + agent['y']) % ARENA_SIZE[1]

            if agent['vel'] > 0.2:
                agent['vel'] -= (agent['vel'] - 0.1) * C_VELOCITY
            if agent['to_ding']:
                agent['deg'] = (agent['deg'] + random.randint(45, 225)) % 360
                agent['vel'] = DEFAULT_VELOCITY

            agent['x'] = new_x
            agent['y'] = new_y


def get_midi_events():
    global bugs
    global bug_pool_lock

    def needs_note_off(t, agent):
        return (agent['to_die']) or (agent['dinging']
                                     and agent['when_donged'] <
                                     (t - agent['duration']))

    def warrants_midi_event(t, agent):
        if not agent:
            return False
        if needs_note_off(t, agent):
            return True
        if agent['to_ding']:
            return True
        return False

    def to_msg(t, agent):
        def method_name(agent):
            print(agent['to_die'])
            if agent['to_die']:

                agent['to_remove'] = True
                print('NOTE_OFF')
                return 'note_off'

            if needs_note_off(t, agent):
                agent['dinging'] = False
                print('NOTE_OFF')
                return 'note_off'

            elif agent['to_ding']:
                agent['to_ding'] = False
                agent['dinging'] = True
                agent['when_donged'] = t
                print('NOTE_ON')
                return 'note_on'

            raise 'what is going on? {}'.format(agent)

        return {
            'instrument_name': bug_kind_to_instrument(agent['kind']),
            'method': method_name(agent),
            'payload': [agent['pitch']]
        }

    with bug_pool_lock:
        t = time.time()
        return [to_msg(t, x) for x in bugs if warrants_midi_event(t, x)]


async def worker(midi_worker_pipe, loop):
    global bugs
    while True:
        await asyncio.sleep(1 / 60)

        if state_queue.qsize() > 10:
            logging.info('Queue maxed out -- going to sleep!')
            await asyncio.sleep(1)
            continue

        await loop.run_in_executor(None, tick_bugs)
        msg = json.dumps({'agents': bugs})
        await state_queue.put(msg)

        midi_events = get_midi_events()
        for e in midi_events:
            midi_worker_pipe.send(e)


async def state_broadcaster():
    global connections
    while True:

        msg = await state_queue.get()

        futures = [c.send(msg) for c in connections if not c.is_bug]

        if len(futures) > 0:
            await asyncio.wait(futures)
        else:
            await asyncio.sleep(1)


async def consumer_handler(websocket):
    while True:
        msg = await websocket.recv()
        await dispatcher(msg, websocket)


async def dispatcher(data, websocket):
    global bug_pool_lock

    try:
        data = json.loads(data)
    except:
        logging.error('Error converting {} to json'.format(data))
        return

    kind = data.get('kind', None)
    payload = data.get('payload', None)

    logging.info('dispatching: {} {}'.format(kind, payload))
    if kind == 'ping':
        await websocket.send('pong')

    elif kind == 'create':
        if websocket.bug_pk is not None:
            pass
            # return
        bug = bug_factory(**payload)
        bugs.append(bug)
        websocket.bug_pk = bug['pk']
        msg = json.dumps({'id': bug['pk']})
        await websocket.send(msg)

    elif kind == 'ding':
        process_bug(websocket.bug_pk, ding_bug)

    elif kind == 'die':
        print('bug dying')
        logging.info('Bug dying')
        process_bug(websocket.bug_pk, set_to_die)


def process_bug(pk, cb):
    global bugs
    global bug_pool_lock

    with bug_pool_lock:
        for b in bugs:
            if b['pk'] == pk:
                cb(b)


def set_to_die(b):
    b['to_die'] = True


def remove_bug(b):
    global bugs
    bugs.remove(b)


def ding_bug(b):
    b['to_ding'] = True


async def handler(websocket, path):
    global connections
    global bug_pool_lock

    if path == '/':
        websocket.is_bug = True
        websocket.bug_pk = None
    elif path == '/petri':
        websocket.is_bug = False
    connections.add(websocket)
    logging.info('New connection: {}'.format(websocket))

    try:
        while True:
            await consumer_handler(websocket)
    except Exception as e:
        print(e)
        logging.info('Disconnecting: {}'.format(e))
        connections.remove(websocket)
        if websocket.is_bug:
            process_bug(websocket.bug_pk, remove_bug)


def main(midi_worker_pipe):
    loop = asyncio.get_event_loop()
    try:
        ticker_coro = worker(midi_worker_pipe, loop)
        broadcaster_coro = state_broadcaster()
        ws_server = websockets.serve(handler, '0.0.0.0', 7700)
        loop.run_until_complete(
            asyncio.gather(ticker_coro, ws_server, broadcaster_coro))
        loop.run_forever()
    except KeyboardInterrupt:
        print("Exiting program...")


def run_as_standalone():
    from ..modules.midi_worker import MidiWorker
    # from ..instruments.four_by_four import instruments
    import multiprocessing as mp

    instruments = {}
    p_r, p_w = mp.Pipe(duplex=False)
    midi_worker = MidiWorker(p_r, instruments)

    p = mp.Process(target=midi_worker.start_consuming)
    p.start()

    logging.basicConfig(
        level=logging.INFO,
        format='%(relativeCreated)6d %(processName)s %(message)s')
    main(p_w)


if __name__ == '__main__':
    run_as_standalone()

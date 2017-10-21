import asyncio
import websockets
import threading
import time
import random
import json
import logging
import queue
import math


class Pool:
    def __init__(self):
        self.pool = set()
        self.lock = threading.Lock()

    def add(self, agent):
        with self.lock:
            self.pool.add(agent)

    def remove(self, agent):
        with self.lock:
            self.pool.remove(agent)

    def get(self):
        with self.lock:
            return self.pool.copy()

    def process(self, cb):
        with self.lock:
            return cb(self.pool)


ARENA_SIZE = (1200, 700)

PITCH_TO_SCALE = [58, 60, 62, 63, 65, 67, 69, 70]


def bug_factory(kind, pitch):
    x, y = random_pos()
    return {
        'pk': int((time.monotonic()) * 100),
        'kind': kind,
        'pitch': PITCH_TO_SCALE[pitch],
        'deg': random.randint(0, 360),
        'vel': DEFAULT_VELOCITY,
        'x': x,
        'y': y,
        'targetX': x,
        'targetY': y,
        'joined': 0,
        'to_ding': False,
        'dinging': False,
        'when_donged': 0,
        'duration': 0.5
    }


DELTA_VELOCITY = 0.001
C_VELOCITY = 0.01
DEFAULT_VELOCITY = 3
DELTA_DEGREE = 2


def tick_bugs(pool):
    for i in pool:

        if not i.is_agent:
            continue

        agent = i.agent
        if not agent:
            continue

        if agent['vel'] > 0.2:
            agent['vel'] -= (agent['vel'] - 0.1) * C_VELOCITY
        if agent['to_ding']:
            agent['deg'] = (agent['deg'] + random.randint(45, 225)) % 360
            agent['vel'] = DEFAULT_VELOCITY

        v = agent['vel']
        d = agent['deg']

        agent['x'] = (v * math.cos(d) + agent['x']) % ARENA_SIZE[0]
        agent['y'] = (v * math.sin(d) + agent['y']) % ARENA_SIZE[1]


def bug_kind_to_instrument(kind):
    if kind == 0:
        return 'minilogue_1'
    elif kind == 1:
        return 'minilogue_2'


def get_midi_events(pool):
    t = time.time()

    def needs_note_off(agent):
        return agent['dinging'] and agent['when_donged'] < (
            t - agent['duration'])

    def warrants_midi_event(agent):
        if not agent:
            return False
        if needs_note_off(agent):
            return True
        if agent['to_ding']:
            return True
        return False

    def to_msg(agent):
        def method_name(agent):
            if needs_note_off(agent):
                agent['dinging'] = False
                print('NOTE_OFF')
                return 'note_off'

            if agent['to_ding']:
                agent['to_ding'] = False
                agent['dinging'] = True
                agent['when_donged'] = t
                print('NOTE_ON')
                return 'note_on'
            else:
                print('ERROR')
                raise 'what is going on? {}'.format(agent)

        return {
            'instrument_name': bug_kind_to_instrument(agent['kind']),
            'method': method_name(agent),
            'payload': [agent['pitch']]
        }

    return [to_msg(x.agent) for x in pool if warrants_midi_event(x.agent)]


class Worker(threading.Thread):
    def __init__(self, agent_pool, midi_worker_pipe, q):
        threading.Thread.__init__(self)
        self.pool = agent_pool
        self.midi_worker_pipe = midi_worker_pipe
        self.state_queue = q

    def run(self):
        while True:
            # 60 fps
            time.sleep(1 / 60)

            if self.state_queue.qsize() > 10:
                continue

            self.pool.process(tick_bugs)
            agents = self.pool.process(map_pool_to_game_state)
            self.state_queue.put(json.dumps({'agents': agents}))

            midi_events = self.pool.process(get_midi_events)

            for e in midi_events:
                self.midi_worker_pipe.send(e)


def random_pos():
    x = random.randint(0, ARENA_SIZE[0])
    y = random.randint(0, ARENA_SIZE[1])
    return (x, y)


def map_pool_to_game_state(pool):
    agents = [x.agent for x in pool if x.agent]
    return agents


connections = set()
bugs = set()


def tick_bugs2():
    global bugs
    for agent in bugs:
        if agent['vel'] > 0.2:
            agent['vel'] -= (agent['vel'] - 0.1) * C_VELOCITY
        if agent['to_ding']:
            agent['deg'] = (agent['deg'] + random.randint(45, 225)) % 360
            agent['vel'] = DEFAULT_VELOCITY

        v = agent['vel']
        d = agent['deg']

        agent['x'] = (v * math.cos(d) + agent['x']) % ARENA_SIZE[0]
        agent['y'] = (v * math.sin(d) + agent['y']) % ARENA_SIZE[1]


def get_midi_events2():
    global bugs

    t = time.time()

    def needs_note_off(agent):
        return agent['dinging'] and agent['when_donged'] < (
            t - agent['duration'])

    def warrants_midi_event(agent):
        if not agent:
            return False
        if needs_note_off(agent):
            return True
        if agent['to_ding']:
            return True
        return False

    def to_msg(agent):
        def method_name(agent):
            if needs_note_off(agent):
                agent['dinging'] = False
                print('NOTE_OFF')
                return 'note_off'

            if agent['to_ding']:
                agent['to_ding'] = False
                agent['dinging'] = True
                agent['when_donged'] = t
                print('NOTE_ON')
                return 'note_on'
            else:
                print('ERROR')
                raise 'what is going on? {}'.format(agent)

        return {
            'instrument_name': bug_kind_to_instrument(agent['kind']),
            'method': method_name(agent),
            'payload': [agent['pitch']]
        }

    return [to_msg(x) for x in bugs if warrants_midi_event(bugs)]


worker_event = asyncio.Event()


async def worker(midi_worker_pipe):
    global agents
    while True:
        await asyncio.sleep(1 / 60)
        tick_bugs2
        worker_event.set()
        midi_events = get_midi_events2()
        for e in midi_events:
            midi_worker_pipe.send(e)


async def producer_handler():
    state = await worker_event.wait()
    worker_event.clear()
    await asyncio.wait([c.send(state) for c in connections if not c.is_bug])


async def consumer_handler(websocket, path):
    while True:
        msg = await websocket.recv()
        await dispatcher(msg, websocket)


async def dispatcher(data, websocket):
    try:
        data = json.loads(data)
    except:
        logging.error('Error converting {} to json'.format(data))
        return

    kind = data.get('kind', None)
    payload = data.get('payload', None)

    logging.info('dispatching: {} {}'.format(kind, payload))
    if kind == 'ping':
        update_heartbeat(websocket)
        await websocket.send('pong')

    elif kind == 'create':
        bug = bug_factory(**payload)
        bugs.add(bug)
        websocket.bug_pk = bug['pk']
        msg = json.dumps({'id': bug['pk']})
        await websocket.send(msg)

    elif kind == 'ding':
        for b in bugs:
            if b['pk'] == websocket.bug_pk:
                b['to_ding'] = True


async def handler(websocket, path):
    global connections
    if path == '/':
        websocket.is_bug = True
    elif path == '/Petri':
        websocket.is_bug = False
    connections.add(websocket)

    try:
        consumer_task = asyncio.ensure_future(consumer_handler(websocket))
        producer_task = asyncio.ensure_future(producer_handler(websocket))

        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED, )
    except:
        connections.remove(websocket)
        if websocket.is_bug:
            for b in bugs:
                if b['pk'] == websocket.bug_pk:
                    bugs.remove(b)


class MainServer(threading.Thread):
    def __init__(self, worker, loop, pool, q):
        threading.Thread.__init__(self)
        self.worker = worker
        self.state_queue = q
        self.loop = loop
        self.pool = pool

    def run(self):
        while True:
            petri_state = self.state_queue.get()
            self.broadcast_state(petri_state)

    async def producer(self):
        while True:
            petri_state = self.state.queue.get()
            return petri_state

    async def handler(self, websocket, path):
        websocket.agent = None
        if path == '/':
            websocket.is_agent = True
            self.pool.add(websocket)
        elif path == '/petri':
            websocket.is_agent = False
            self.pool.add(websocket)
        else:
            logging.error('Error: Incorrect path {}'.format(path))
            return
        try:
            while True:
                x = await websocket.recv()
                logging.info('Got: {}'.format(x))
                self.dispatch(x, websocket)
        except:
            self.pool.remove(websocket)

    def broadcast(self, data, pred=lambda _: True):
        def _broadcast(pool):
            for x in pool:
                if pred(x):
                    self.unicast(x, data)

        self.pool.process(_broadcast)

    def broadcast_state(self, data):
        self.broadcast(data, lambda ws: not ws.is_agent)

    def unicast(self, websocket, data):
        if not websocket.open:
            logging.info('Closing websocket')
            self.pool.remove(websocket)
            return

        coro = websocket.send(data)
        try:
            asyncio.run_coroutine_threadsafe(coro, self.loop)
        except:
            logging.error('ERROR in sending')
            self.pool.remove(websocket)
            websocket.close()

    def dispatch(self, data, websocket):
        try:
            data = json.loads(data)
        except:
            logging.error('Error converting {} to json'.format(data))
            return

        kind = data.get('kind', None)
        payload = data.get('payload', None)

        logging.info('dispatching: {} {}'.format(kind, payload))
        if kind == 'ping':
            update_heartbeat(websocket)
            self.unicast(websocket, 'pong')

        elif kind == 'create':
            bug = bug_factory(**payload)
            websocket.agent = bug
            msg = json.dumps({'id': bug['pk']})
            self.unicast(websocket, msg)

        elif kind == 'ding':
            websocket.agent['to_ding'] = True


def update_heartbeat(ws):
    ws.heartbeat = time.time()


def main(midi_worker_pipe):
    q = queue.Queue()
    loop = asyncio.get_event_loop()
    pool = Pool()
    worker = Worker(pool, midi_worker_pipe, q)
    server = MainServer(worker, loop, pool, q)
    try:
        worker.start()
        server.start()
        ws_server = websockets.serve(server.handler, '0.0.0.0', 7700)
        loop.run_until_complete(ws_server)
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

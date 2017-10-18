import asyncio
import websockets
import threading
import time
import random
import json
import logging
import queue


class WsPool:
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


def tick_bugs(pool):
    pass


def bug_kind_to_instrument(kind):
    if kind == 0:
        return 'minilogue_1'
    elif kind == 1:
        return 'minilogue_2'


def get_midi_events(pool):
    t = time.time()

    def needs_note_off(agent):
        return agent['dinging'] and agent['when_donged'] < (t - agent['duration'])

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
    def __init__(self, pool, midi_worker_pipe, q):
        threading.Thread.__init__(self)
        self.pool = pool
        self.midi_worker_pipe = midi_worker_pipe
        self.state_queue = q

    def get_petri_state(self):
        def reduce_it(pool):
            i = 0
            for x in pool:
                i += getattr(x.agent, 'pk', 0)
            return i

        return self.pool.process(reduce_it)

    def run(self):
        while True:
            # 60 fps
            time.sleep(1 / 60)

            if self.state_queue.qsize() < 10:
                self.pool.process(tick_bugs)
                agents = self.pool.process(map_pool_to_game_state)
                self.state_queue.put({'agents': agents})

            midi_events = self.pool.process(get_midi_events)

            for e in midi_events:
                self.midi_worker_pipe.send(e)


ARENA_SIZE = (600, 500)


def random_pos():
    x = random.randint(0, ARENA_SIZE[0])
    y = random.randint(0, ARENA_SIZE[1])
    return (x, y)


def bug_factory(kind, pitch):
    x, y = random_pos()
    return {
        'pk': int((time.monotonic()) * 100),
        'kind': kind,
        'pitch': pitch,
        'heartbeat': time.time(),
        'deg': random.randint(0, 360),
        'vel': 0,
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


def update_heartbeat(agent):
    agent['heartbeat'] = time.time()


def map_pool_to_game_state(pool):
    agents = [x.agent for x in pool if x.agent]
    return agents


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
            logging.info('petri state: {}'.format(petri_state))
            self.broadcast(json.dumps(petri_state))

    async def handler(self, websocket, path):
        websocket.agent = None
        self.pool.add(websocket)
        try:
            while True:
                x = await websocket.recv()
                logging.info('Got: {}'.format(x))
                self.dispatch(x, websocket)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.pool.remove(websocket)

    def broadcast(self, data):
        def _broadcast(pool):
            for x in pool:
                self.unicast(x, data)

        self.pool.process(_broadcast)

    def unicast(self, websocket, data):
        coro = websocket.send(data)
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def dispatch(self, data, websocket):
        try:
            data = json.loads(data)
        except:
            logging.error('Error converting {} to json'.format(data))
            return

        kind = data.get('kind', None)
        payload = data.get('payload', None)

        if kind == 'ping':
            agent = websocket.agent
            if agent:
                update_heartbeat(agent)

            self.unicast(websocket, 'pong')

        elif kind == 'create':
            bug = bug_factory(**payload)
            websocket.agent = bug
            msg = json.dumps({'id': bug['pk']})
            self.unicast(websocket, msg)

        elif kind == 'ding':
            websocket.agent['to_ding'] = True


def main(midi_worker_pipe):
    q = queue.Queue()
    loop = asyncio.get_event_loop()
    pool = WsPool()
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
    from ..instruments.four_by_four import instruments
    import multiprocessing as mp

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

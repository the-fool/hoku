import asyncio
import websockets
import threading
import time
import random


class Worker(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def get(self):
        self.data = random.randint(0, 10)
        return self.data


class MainServer(threading.Thread):
    def __init__(self, worker, loop):
        threading.Thread.__init__(self)
        self.connected = set()
        self.worker = worker
        self.loop = loop

    def run(self):
        while True:
            data = self.worker.get()
            print(data)
            if data:
                self.broadcast('{"GPS": "%s"}' % data)

            time.sleep(0.04)
        

    async def handler(self, websocket, path):
        self.connected.add(websocket)
        try:
            await websocket.recv()
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected.remove(websocket)

    def broadcast(self, data):
        for websocket in self.connected:
            print("Sending data: %s" % data)
            coro = websocket.send(data)
            future = asyncio.run_coroutine_threadsafe(coro, self.loop)


def main():
    loop = asyncio.get_event_loop()
    worker = Worker()
    server = MainServer(worker, loop)
    try:
        worker.start()
        server.start()
        ws_server = websockets.serve(server.handler, '0.0.0.0', 7700)
        loop.run_until_complete(ws_server)
        loop.run_forever()
    except KeyboardInterrupt:
        print("Exiting program...")


if __name__ == '__main__':
    main()

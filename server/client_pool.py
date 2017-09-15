import threading


class ClientPool:
    def __init__(self):
        self.pool = set()
        self.lock = threading.Lock()

    def add(self, client):
        with self.lock:
            self.pool.add(client)

    def remove(self, client):
        with self.lock:
            self.pool.remove(client)

    def get(self, client):
        with self.lock:
            return [c for c in self.pool]

    def broadcast(self, msg=''):
        clients = []
        with self.lock:
            clients = [c for c in self.pool]
        for client in clients:
            client.sendMessage(msg)

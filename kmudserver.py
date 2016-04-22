import logging

from miniboa import TelnetServer
from pymongo import MongoClient
from kitem import KItem
from kcontainer import KContainer
from kconnection import KConnection
# from kcharacter import KCharacter
from time import time


class KMudServer(TelnetServer):

    def __init__(self):
        TelnetServer.__init__(self,
                              port=2525,
                              address='',
                              on_connect=self.on_connect,
                              on_disconnect=self.on_disconnect,
                              timeout=0.001)
        self.server_run = True
        self.items = self.load_items()
        self.containers = self.load_containers()
        self.connections = []
        self.characters = []
        self.global_timers = []
        self.timer_tick = time()

    def load_containers(self):
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud
        docs = db.containers.find()
        containers = {}
        for doc in docs:
            container = KContainer(doc['_id'], doc['name'])
            if 'points' in doc:
                container.points = doc['points']
            if 'parent_id' in doc:
                container.parent_id = doc['parent_id']
            if 'description' in doc:
                container.desc = doc['description']
            if 'name' in doc:
                container.name = doc['name']
            containers[container._id] = container
        logging.info('Loaded {} containers.'.format(len(containers)))

        # Link parent and child containers
        for _id, con in containers.items():
            if con.parent_id:
                containers[con.parent_id].children.append(_id)

        return containers

    def load_items(self):
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud
        docs = db.items.find()
        items = {}
        for doc in docs:
            item = KItem(doc['_id'], doc['location_id'],
                         doc['category'], doc['name'])
            item.properties = doc['properties']
            items[item.id] = item
        logging.info('Loaded {} items.'.format(len(items)))
        return items

    def run(self):
        while self.server_run is True:
            self.poll()
            self.process_input()
            self.process_clients()
            self.process_timers()

    def process_timers(self):
        for timer in self.global_timers:
            # Process timers that do not repeat
            if (time() - timer.start_time >= timer.duration and
                    timer.onetime):
                self.global_timers.remove(timer)
                timer.die()
            # Process repeating timers every 1 seconds
            # (Duration == -1)
            elif timer.duration == -1 and time() - self.timer_tick > 1.0:
                self.timer_tick = time()
                remove = timer.callback(timer.args)
                if remove:
                    self.global_timers.remove(timer)

    def process_clients(self):
        pass
        for character in self.characters:
            if character.logging_in():
                character.login()

    def process_input(self):
        for conn in self.connections:
            if conn.client.active and conn.client.cmd_ready:
                conn.process_input()

        for character in self.characters:
            if character.client.active and character.client.cmd_ready:
                character.process_input()

    def on_connect(self, client):
        logging.info('New connection from {}'.format(client.addrport()))
        conn = KConnection(client, self.connections,
                           self.characters,
                           self.global_timers,
                           self.items,
                           self.containers)
        conn.send('Welcome to KMud.\nPlease enter username.\n', prompt=True)
        self.connections.append(conn)
        logging.info('{} total connections'.format(len(self.connections)))

    def on_disconnect(self, client):
        pass


if __name__ == '__main__':
    # Create the telnet server with a port, address,
    # a new connection function and closed connection function
    logging.basicConfig(filename='/tmp/kmud.log', level=logging.DEBUG)
    kmud_server = KMudServer()
    logging.info('Listening for connections on port {}.'.
                 format(kmud_server.port))
    kmud_server.run()

    # Server has shut down
    logging.info("Server shutdown")

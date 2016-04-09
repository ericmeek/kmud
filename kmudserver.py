#
# <one line to give the program's name and a brief idea of what it does.>
# Copyright (C) 2016  <copyright holder> <email>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
#

import logging

from miniboa import TelnetServer
from pymongo import MongoClient
from kitem import KItem
from kcontainer import KContainer

class KMudServer(TelnetServer):
    def __init__(self):
        TelnetServer.__init__(self,
            port=2525,
            address='',
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
            timeout=0.001)
        self.server_run = True
        self.item_dict = self.load_item_dict()
        self.container_dict = self.load_container_dict()
        self.connection_list = []
        self.timer_tick = None
        
    def load_container_dict(self):
        client = MongoClient()
        db = client.kmud
        docs = db.containers.find()
        container_dict = {}
        for doc in docs:
            container = KContainer(doc['_id'], doc['name'])
            if 'points' in doc:
                container.points = doc['points']
            if 'parent_id' in doc:
                container.parent_id = doc['parent_id']
            if 'description' in doc:
                container.desc = doc['description']
            container_dict[container.id] = container
        logging.info('Loaded {} containers.'.format(len(container_dict)))
        return container_dict

    def load_item_dict(self):
        client = MongoClient()
        db = client.kmud
        docs = db.items.find()
        item_dict = {}
        for doc in docs:
            item = KItem(doc['_id'], doc['location_id'],
                         doc['category'], doc['name'])
            item.properties = doc['properties']
            item_dict[item.id] = item
        logging.info('Loaded {} items.'.format(len(item_dict)))
        return item_dict

    def run(self):
        while self.server_run is True:
            self.poll()
            self.process_input()
#            self.process_clients()
#            self.process_timers()

    def process_timers(self):
        for timer in KTimerList:
            # Process timers that do not repeat
            if (time() - timer.start >= timer.duration and
                not timer.repeatable):
                    KTimerList.remove(timer)
                    timer.callback(timer.args)
            # Process repeating timers every 1 seconds
            # (Duration == -1)
            elif timer.duration == -1 and time() - self.timer_tick > 1.0:
                self.timer_tick = time()
                remove = timer.callback(timer.args)
                if remove:
                    KTimerList.remove(timer)

    def process_clients(self):
        for id, character in iter(KCharacterList.items()):
            if character.status == KCharacterStatus.LOGIN:
                character.login()

    def process_input(self):
        for conn in KConnectionList:
            if conn.client.active and conn.client.cmd_ready:
                conn.process_input()

        for id, char in iter(KCharacterList.items()):
            if char.client.active and char.client.cmd_ready:
                char.process_input()

    def on_connect(self, client):
        logging.info('New connection from {}'.format(client.addrport()))
        conn = KConnection(client)
        conn.send('Welcome to KMud.\nPlease enter username.\n', Prompt=True)
        conn.status = KConnectionStatus.VERIFY_USERNAME
        KConnectionList.append(conn)  # Append the new KUser to user list
        logging.info('{} total connections'.format(len(KConnectionList)))

    def on_disconnect(self, client):
        pass


if __name__ == '__main__':
    # Create the telnet server with a port, address,
    # a new connection function and closed connection function
    logging.basicConfig(filename='/tmp/kmud.log', level=logging.DEBUG)
    kmud_server = KMudServer()
    logging.info('Listening for connections on port {}.'.
                 format(kmud_server.port))
#    kmud_server.run()

    # Server has shut down
    logging.info("Server shutdown")


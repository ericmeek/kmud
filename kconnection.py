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

from enum import Enum
from kclient import KClient
from pymongo import MongoClient
from kcharacter import KCharacter
from kcharacter import KCharStatus

class KConnStatus(Enum):
    VERIFY_USERNAME = 1001
    VERIFY_PASSWORD = 1002
    CHOOSE_CHARACTER = 1003

class KConnection(KClient):
    def __init__(self, client, connections,
                 characters, global_timers,
                 items, containers):
        KClient.__init__(self, client)
        self.status = KConnStatus.VERIFY_USERNAME
        self.connections = connections
        self.characters = characters
        self.global_timers = global_timers
        self.items = items
        self.containers = containers
        self.properties = {}

    def verify_username(self, username):
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud

        doc = db.users.find_one({'username': username})
        return True if doc else False

    def get_user_id(self, username):
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud

        doc = db.users.find_one({'username': username})
        return doc['_id']

    def verify_password(self, password):
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud

        doc = db.users.find_one({'_id': self.id, 'password': password})
        return True if doc else False

    def show_characters(self):
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud

        self.properties['characters'] = {}

        docs = db.characters.find({'user_id': self.id})
        count = 1
        for doc in docs:
            self.properties['characters'][count] = doc['_id']
            self.send('{}) {} {}\n'.format(count,
                                           doc['first_name'],
                                           doc['surname']),
                      prompt=False)
            count += 1
        self.send_prompt()

    def choose_character(self, cmd):
        try:
            cmd = int(cmd)
        except:
            cmd = 0
        if cmd in self.properties['characters']:
            self._id = self.properties['characters'][cmd]
            del self.properties['characters']
            return True
        else:
            return False

    def process_input(self):
        cmd = self.client.get_command()
        if self.status == KConnStatus.VERIFY_USERNAME:
            if self.verify_username(cmd):
                self.send('Please enter password.\n')
                self.status = KConnStatus.VERIFY_PASSWORD
                self.id = self.get_user_id(cmd)
            else:
                self.send('Not a valid username.\n',
                          prompt=False)
                self.send('Please enter username.\n')
        elif self.status == KConnStatus.VERIFY_PASSWORD:
            if self.verify_password(cmd):
                self.send('Please choose your character.\n',
                          prompt=False)
                self.show_characters()
                self.status = KConnStatus.CHOOSE_CHARACTER
            else:
                self.send('Not a valid username/password combination.\n',
                          prompt=False)
                self.send('Please enter username.\n')
                self.id = None
                self.status = KConnStatus.VERIFY_USERNAME
        elif self.status == KConnStatus.CHOOSE_CHARACTER:
            if self.choose_character(cmd):
                self.send('Logging onto KMud, please wait...\n',
                          prompt=False)
                character = KCharacter(self.client, self._id,
                                       self.characters,
                                       self.global_timers,
                                       self.items,
                                       self.containers)
                character.status = KCharStatus.LOGIN
                self.connections.remove(self)
                self.characters[character.id] = character
            else:
                self.send('Not a valid character selection.\n',
                          prompt=False)
                self.send('Please choose your character.\n',
                          prompt=False)
                self.show_characters()
                self.status = KConnStatus.CHOOSE_CHARACTER
        else:
            self.send('Unknown command')


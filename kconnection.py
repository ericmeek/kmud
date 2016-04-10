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

from kclient import KClient
from pymongo import MongoClient
from kenum import KConnectionStatus

class KConnection(KClient):
    def __init__(self, client, connection_list, global_timers):
        KClient.__init__(self, client)
        self.status = KConnection.VERIFY_USERNAME
        self.connection_list = connection_list
        self.timer_list = global_timers
        
    def verify_username(self, username):
        client = MongoClient()
        db = client.kmud

        doc = db.users.find_one({'username': username})
        return True if doc else False

    def get_user_id(self, username):
        client = MongoClient()
        db = client.kmud

        doc = db.users.find_one({'username': username})
        return list(doc)['_id']

    def verify_password(self, password):
        client = MongoClient()
        db = client.kmud

        doc = db.users.find_one({'_id': self.id, 'password': password})
        return True if doc else False

    def show_characters(self):
        client = MongoClient()
        db = client.kmud
        
        self.properties['characters'] = {}

        docs = db.characters.find({'user_id': self.id})
        count = 1
        for doc in docs:
            self.properties['characters'][count] = doc['_id']
            self.send('{}) {} {}\n'.format(count, doc['first_name'],
                                           doc['surname']))
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
        if self.status == KConnectionStatus.VERIFY_USERNAME:
            if self.verify_username(cmd):
                self.send('Please enter password.\n', Prompt=True)
                self.status = KConnectionStatus.VERIFY_PASSWORD
                self.id = self.get_user_id(cmd)
            else:
                self.send('Not a valid username.\n')
                self.send('Please enter username.\n', Prompt=True)
        elif self.status == KConnectionStatus.VERIFY_PASSWORD:
            if self.verify_password(cmd):
                self.send('Please choose your character.\n')
                self.show_characters()
                self.status = KConnectionStatus.CHOOSE_CHARACTER
            else:
                self.send('Not a valid username/password combination.\n')
                self.send('Please enter username.\n', Prompt=True)
                self.id = None
                self.status = KConnectionStatus.VERIFY_USERNAME
        elif self.status == KConnectionStatus.CHOOSE_CHARACTER:
            if self.choose_character(cmd):
                self.send('Logging onto KMud, please wait...\n')
                character = KCharacter(self.client, self._id,
                                       self.timer_list)
                character.status = KCharacterStatus.LOGIN
                KConnectionList.remove(self)
                KCharacterList[character.id] = character
            else:
                self.send('Not a valid character selection.\n')
                self.send('Please choose your character.\n')
                self.show_characters()
                self.status = KConnectionStatus.CHOOSE_CHARACTER
        else:
            self.send('Unknown command', Prompt=True)


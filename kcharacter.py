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

import os
import sys
from kenum import KCharState
from kclient import KClient
from ktimer import KTimer

CARD_DIRECTIONS = {'n': [0, 1], 'north': [0,1], 'e': [1, 0], 'east': [1, 0],
                   's': [0,-1], 'south': [0, -1], 'w': [-1, -0], 'west': [-1, -0],
                   'ne': [1, 1], 'northeast': [1, 1], 'nw': [-1, 1], 'northwest': [-1, 1],
                   'se': [1, -1], 'southeast': [1, -1], 'sw': [-1, -1],
                   'southwest': [-1, -1]}


class KCharacter(KClient):
    def __init__(self, client, _id, global_timers):
        KClient.__init__(self, client, _id)

        self.timers = []
        self.global_timers = global_timers
        self.states = []
        self.location = None
        self.surname = None
        self.first_name = None
        self.command = {
            'look': self.process_look,
            'rest': self.process_rest,
            'walk': self.process_rest,
            'show': self.process_show,
            'stop': self.process_stop,
            'restart': self.process_restart
        }
        self.holding = {
            'right hand': None,
            'left hand': None,
            'hands': None
        }
        self.wearing = {
            'torso': None,
            'left foot': None,
            'right foot': None,
            'feet': None
        }
    def name(self):
        return "{} {}".format(self.first_name, self.surname)

    def restart(self, args):
        os.execv('/vagrant/KMud/KMud.py', sys.argv)

    def process_stop(self, args):
        try:
            last_state = self.states.pop()
            if last_state == KCharState.WALKING:
                pass
        except:
            self.send('Stop what?\n')
            return

    def process_look(self, args):
        if len(args) == 0:
            return self.show_room()
        elif (args[0] in [self.first_name.lower(), 'self', 'me'] and
              len(args) == 1):
            return self.show_self()
        elif ''.join(args[0:]) == self.name().lower():
            return self.show_self()
        else:
            self.send('Uknown command.\n')

    def process_rest(self, args):
        duration = float(args[0])
        timer = KTimer(self,
                       False,
                       self.cb_stop_resting,
                       time(),
                       duration)
        self.timers[timer.id] = timer
        KTimerList.append(timer)
        self.send('You start resting.\n', Prompt=True)

    def process_walk(self, cmd):
        if KCharState.WALKING in self.states:
            self.send('You are already walking.\n', Prompt=True)
            return
        direction = cmd[0]
        if direction in CARD_DIRECTIONS:
            timer = KTimer(self.id,
                        -1,
                        time(),
                        self.cb_walking,
                        True,
                        direction)
            KTimerList.append(timer)
            self.timers[timer._id] = timer
            self.send('You start walking {}.\n'.format(direction), Prompt=True)
            self.states.append(KCharState.WALKING)
        else:
            self.send('Unknown command\n',Prompt=True)

    def process_show(self, args):
        if len(args) == 1:
            if args[0] == 'coord':
                self.send('{},{}\n'.format(self.location['coord'].x,
                                           self.location['coord'].y),
                          Prompt=True)
                return True
        self.send('Unknown command.\n', Prompt=True)

    def login(self):
        """
        On character login:
            1) Show room
        """
        self.load()
        self.show_room()

    def load(self):
        """
        Load character from database
        """
        client = MongoClient()
        db = client.kmud
        character = db.characters.find_one({'_id': self.id})
        self.first_name = character['first_name']
        self.surname = character['surname']
        self.location['id'] = character['location']['id']
        self.location['coord'] = KCoordinate(
            character['location']['coord'][0],
            character['location']['coord'][1])

        self.holding = {}
        if 'holding' in character:
            for key, val in character['holding'].items():
                self.holding[key] = val

        self.wearing = {}
        if 'wearing' in character:
            for key, val in character['wearing'].items():
                self.wearing[key] = val

    def show_room(self, in_room=True):
        """
        Show the room
        """
        # Load room description
        client = MongoClient()
        db = client.kmud
        location = db.containers.find_one({'_id': self.location['id']})
        self.send('{} {}\n'.format('You are in ' if in_room else 'You see ',
                                   location['description']))
        self.send_prompt()
        self.status = KCharacterStatus.IDLE
        return True

    def show_self(self):
        items = list(self.wearing.items())
        desc = '\n{} {}\n\n'.format(self.first_name, self.surname)
        desc += 'You are wearing '
        if len(items) == 0:
            desc += 'nothing!'
            self.send(desc, Prompt=True)
            return True
        else:
            for i in range(len(items)):
                if i == 0 and len(items) == 1:
                    desc += 'a {}.'.format(KItemList[items[i][1]].name)
                elif i == 0:
                    desc += 'a {}'.format(KItemList[items[i][1]].name)
                elif i == len(items) - 1:
                    desc += ' and a {}.'.format(KItemList[items[i][1]].name)
                else:
                    desc += ', a {}'.format(KItemList[items[i][1]].name)
            self.send('{}\n'.format(desc), Prompt=True)
            return True

    def cb_stop_resting(self, *args):
        self.send('\nYou stop resting.\n', Prompt=True)

    def cb_walking(self, args):
        """
        Callback for character moving timer
        """
        direction = args[0]
        # Get the coordinates to add/subtract based on direction
        coord = KCoordinate(CARD_DIRECTIONS[direction][0],
                            CARD_DIRECTIONS[direction][1])
        # Find characters location on next step
        next_step = self.location['coord'] + coord
        # Determine if the next step will place character out of location
        if not next_step.in_container(self.location['id']):
            self.send('\nYou stop as you are leaving the area.\n', Prompt=True)
            self.states.remove(KCharState.WALKING)
            return True
        else:
            self.location['coord'] = next_step
            return False

    def process_input(self):
        cmd = self.client.get_command().strip().lower().split()
        if len(cmd) < 1:
            self.send_prompt()
            return
        else:
            cmd, args = cmd[0], cmd[1:]
            if cmd in self.comm:
                self.comm[cmd](args)
            else:
                self.send('Unknown command\n', Prompt=True)

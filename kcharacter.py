import os
import sys
from enum import Enum
from time import time
from pymongo import MongoClient
from kclient import KClient
from ktimer import KTimer
from kcoordinate import KCoordinate

WALK_RATE = 1.3
CARD_DIRECTIONS = {'north': [0,WALK_RATE], 'east': [WALK_RATE, 0], 'south': [0, -WALK_RATE], 'west': [-WALK_RATE, 0],
                   'northeast': [WALK_RATE, WALK_RATE], 'northwest': [-WALK_RATE, WALK_RATE],
                   'southeast': [WALK_RATE, -WALK_RATE], 'southwest': [-WALK_RATE, -WALK_RATE]}

SYNONYMS = {'look': ['l','lo'],
            'north': ['n'],
            'east': ['e'],
            'west': ['w'],
            'south': ['s'],
            'northeast': ['ne'],
            'northwest': ['nw'],
            'southeast': ['se'],
            'southwest': ['sw']}

class KCharState(Enum):

    WALKING = 1001
    RUNNING = 1002

class KCharStatus(Enum):

    LOGIN = 1001
    IDLE = 1002

class KCharacter(KClient):
    def __init__(self, client, _id, characters,
                 global_timers, items, containers):
        KClient.__init__(self, client, _id)

        self.items = items
        self.characters = characters
        self.timers = []
        self.global_timers = global_timers
        self.containers = containers
        self.states = []
        self.location = {}
        self.surname = None
        self.first_name = None
        self.commands = {
            'look': self.process_look,
            'rest': self.process_rest,
            'walk': self.process_walk,
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

    def logging_in(self):
        return True if self.status == KCharStatus.LOGIN else False

    def name(self):
        return "{} {}".format(self.first_name, self.surname)

    def restart(self, args):
        os.execv('/vagrant/KMud/KMud.py', sys.argv)


    def synonymize(self, cmds):
        modified_cmds = []
        for cmd in cmds:
            if cmd in self.commands:
                modified_cmds.append(cmd)
            else:
                for key, val in SYNONYMS.items():
                    if cmd in val:
                        modified_cmds.append(key)
                        break
                else:
                    modified_cmds.append(cmd)
        print(modified_cmds)
        return modified_cmds

    def has_timer(self, timer_name):
        for timer in self.timers:
            if timer.name == timer_name:
                return True
        return False

    def get_timer(self, timer_name):
        for timer in self.timers:
            if timer.name == timer_name:
                return timer
        return None

    def process_stop(self, args):
        try:
            last_timer = self.timers.pop()
            if last_timer.name == 'walk':
                self.global_timers.remove(last_timer)
                self.send('You stop walking.\n')
            elif last_timer.name == 'resting':
                self.global_timers.remove(last_timer)
                self.send('You stop resting.\n')
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
            self.send('Look at what?\n')

    def process_rest(self, args):
        if self.has_timer('resting'):
            self.send('You are already resting.\n')
        else:
            duration = float(args[0])
            timer = KTimer('resting',
                        self,
                        True,
                        time(),
                        self.cb_resting,
                        duration)
            self.global_timers.append(timer)
            self.timers.append(timer)
            self.send('You start resting.\n')

    def cb_resting(self, timer):
        self.timers.remove(timer)
        self.send('\nYou stop resting.\n')


    def process_walk(self, cmd):
        if self.has_timer('walk'):
            self.send('You are already walking.\n')
            return
        direction = cmd[0]
        if direction in CARD_DIRECTIONS:
            timer = KTimer('walk',
                           self,
                        False,
                        time(),
                        self.cb_walking,
                        -1,
                        direction)
            self.global_timers.append(timer)
            self.timers.append(timer)
            self.send('You start walking {}.\n'.format(direction))
            self.states.append(KCharState.WALKING)
        else:
            self.send('Unknown command\n',prompt=True)


    def cb_walking(self, args):
        """
        Callback for character moving timer
        """
        direction = args[0]
        print('Current: {},{}'.format(self.location['coord'].x,
                                      self.location['coord'].y))
        print('Direction: {}'.format(direction))
        # Get the coordinates to add/subtract based on direction
        coord = KCoordinate(CARD_DIRECTIONS[direction][0],
                            CARD_DIRECTIONS[direction][1],
                            self.containers)
        # Find characters location on next step
        print('Adding: {},{}'.format(coord.x,coord.y))
        next_step = self.location['coord'] + coord
        # Determine if the next step will place character in a parent container
        if not next_step.in_container(self.location['id']):
            self.send('\nYou are leaving {} and entering {}.\n'.
                      format(self.containers[self.location['id']].name,
                      self.containers[self.containers[self.location['id']].parent_id].name))
            self.location['id'] = self.containers[self.location['id']].parent_id
        # Determine if the next step will place character in a child container
        elif next_step.entering_container(self.location['id']):
            new_container_id = next_step.entering_container(self.location['id'])
            self.location['id'] = new_container_id
            self.send('\nYou enter {}.\n'.format(self.containers[self.location['id']].name))
        self.location['coord'] = next_step

    def process_show(self, args):
        if len(args) == 1:
            if args[0] == 'coord':
                self.send('{},{}\n'.format(self.location['coord'].x,
                                           self.location['coord'].y),
                          prompt=True)
                return True
            elif args[0] == 'timers':
                count = 1
                for timer in self.timers:
                    self.send('{} {}\n'.format(count, timer.name), prompt=False)
                    count += 1
                self.send_prompt()
            else:
                self.send('Show what?\n')

    def process_restart(self):
        pass

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
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud
        character = db.characters.find_one({'_id': self.id})
        self.first_name = character['first_name']
        self.surname = character['surname']
        self.location['id'] = character['location']['_id']
        self.location['coord'] = KCoordinate(
            character['location']['coord'][0],
            character['location']['coord'][1],
            self.containers
        )

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
        client = MongoClient('mongodb://192.168.0.107:27017/')
        db = client.kmud
        location = db.containers.find_one({'_id': self.location['id']})
        self.send('{} {}.\n'.format('You are in' if in_room else 'You see',
                                   location['description']))
        self.status = KCharStatus.IDLE
        return True

    def show_self(self):
        items = list(self.wearing.items())
        desc = '\n{} {}\n\n'.format(self.first_name, self.surname)
        desc += 'You are wearing '
        if len(items) == 0:
            desc += 'nothing!\n'
            self.send(desc)
            return True
        else:
            for i in range(len(items)):
                if i == 0 and len(items) == 1:
                    desc += 'a {}.'.format(self.items[items[i][1]].name)
                elif i == 0:
                    desc += 'a {}'.format(self.items[items[i][1]].name)
                elif i == len(items) - 1:
                    desc += ' and a {}.'.format(self.items[items[i][1]].name)
                else:
                    desc += ', a {}'.format(self.items[items[i][1]].name)
            self.send('{}\n'.format(desc))
            return True


    def process_input(self):
        cmd = self.client.get_command().strip().lower().split()
        cmd = self.synonymize(cmd)
        if len(cmd) < 1:
            self.send_prompt()
            return
        else:
            cmd, args = cmd[0], cmd[1:]
            if cmd in self.commands:
                self.commands[cmd](args)
            else:
                self.send('Unknown command\n')

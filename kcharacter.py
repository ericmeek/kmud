import os
import sys
import math
from enum import Enum
from time import time
from pymongo import MongoClient
from kclient import KClient
from ktimer import KTimer
from kcoordinate import KCoordinate

# from kcontainer import KContainer

WALK_RATE = 1.3

CARD_DIRECTIONS = {'north': [0, WALK_RATE], 'east': [WALK_RATE, 0],
                   'south': [0, -WALK_RATE], 'west': [-WALK_RATE, 0],
                   'northeast': [WALK_RATE, WALK_RATE],
                   'northwest': [-WALK_RATE, WALK_RATE],
                   'southeast': [WALK_RATE, -WALK_RATE],
                   'southwest': [-WALK_RATE, -WALK_RATE]}

SYNONYMS = {'look': ['l', 'lo'],
            'north': ['n'],
            'east': ['e'],
            'west': ['w'],
            'south': ['s'],
            'northeast': ['ne'],
            'northwest': ['nw'],
            'southeast': ['se'],
            'southwest': ['sw']}


class KCharStatus(Enum):

    LOGIN = 1001
    IDLE = 1002


class KCharacter(KClient):
    def __init__(self, client, _id, characters,
                 global_timers, items, containers):
        KClient.__init__(self, client, _id)

        # Global attributes

        self.characters = characters
        self.global_timers = global_timers
        self.containers = containers  # dict

        self.items = items
        self.timers = []
        self.container_id = None
        self.coordinates = None
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

    def is_character(self):
        return True

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

    def show_room(self, in_room=True):
        """
        Show the room
        """
        # Load room description
        # client = MongoClient('mongodb://192.168.0.107:27017/')
        # db = client.kmud

        # Show stored container description
        # location = db.containers.find_one({'_id': self.location._id})
        self.send('{} {}.\n'.
                  format('You are in' if in_room else 'You see',
                         self.containers[self.container_id].name),
                  prompt=False)

        # Show other characters in area
        # Close by you see Lukrani, Jack and Ronald.
        # A little farther away you see Amy.
        chars_close_by = []
        chars_farther_away = []
        # Loop through all other characters and
        # find all within 3 meters (close by)
        # and all within 9 meters (little farther)
        print(self.characters)
        for char in self.characters:
            if char._id == self._id:
                continue
            if char.distance_from(self) <= 3:
                print("{} is {} away.".format(char.first_name,
                                              char.distance_from(self)))
                chars_close_by.append(char.first_name)
            elif char.distance_from(self) <= 9:
                print("{} is {} away.".format(char.first_name,
                                              char.distance_from(self)))
                chars_farther_away.append(char)
            else:
                print("{} is {} away.".format(char.first_name,
                                              char.distance_from(self)))
        # TODO Check for multiple chars and fix comma
        if len(chars_close_by) > 0:
            self.send('Nearby you see {}\n'.
                      format(", ".join(chars_close_by)), prompt=False)

        if len(chars_farther_away) > 0:
            self.send('A bit away you see {}\n',
                      format(", ".join(chars_farther_away)), prompt=False)

        self.status = KCharStatus.IDLE
        self.send_prompt()
        return True

    def distance_from(self, obj):
        return math.hypot(
            self.coordinates.x - obj.coordinates.x,
            self.coordinates.y - obj.coordinates.y)

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
        if len(cmd) == 0:
            self.send("Walk where?\n", prompt=True)
            return

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
        else:
            self.send('Unknown command\n', prompt=True)

    def cb_walking(self, args):
        """
        Callback for character moving timer
        """
        direction = args[0]
        print('Current: {},{}'.format(self.coordinates.x,
                                      self.coordinates.y))
        print('Direction: {}'.format(direction))
        # Get the coordinates to add/subtract based on direction
        loc = KCoordinate(CARD_DIRECTIONS[direction][0],
                          CARD_DIRECTIONS[direction][1])
        # Find characters location on next step
        print('Adding: {},{}'.format(loc.x, loc.y))
        next_step = self.coordinates + loc
        # Determine if the next step will place character
        # in a parent container
        current_con = self.containers[self.container_id]
        if not next_step.in_container(current_con):
            parent_con = self.containers[current_con.parent_id]
            self.send('\nYou are leaving {} and entering {}.\n'.
                      format(current_con.name, parent_con.name))
            self.container_id = parent_con._id
        # Determine if the next step will place character
        # in a child container
        elif next_step.entering_container(current_con.children):
            new_container = next_step.entering_container(current_con.children)
            self.container_id = new_container._id
            self.send('\nYou enter {}.\n'.format(new_container.name))
        self.coordinates = next_step

    def process_show(self, args):
        if len(args) == 1:
            if args[0] == 'coord':
                self.send('{},{}\n'.format(self.coordinates.x,
                                           self.coordinates.y),
                          prompt=True)
                return True
            elif args[0] == 'timers':
                count = 1
                for timer in self.timers:
                    self.send('{} {}\n'.format(count, timer.name),
                              prompt=False)
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
        character = db.characters.find_one({'_id': self._id})

        self.first_name = character['first_name']
        self.surname = character['surname']
        self.container_id = character['location']['_id']
        self.coordinates = KCoordinate(character['location']['coord'][0],
                                       character['location']['coord'][1])
        self.holding = {}
        if 'holding' in character:
            for key, val in character['holding'].items():
                self.holding[key] = val

        self.wearing = {}
        if 'wearing' in character:
            for key, val in character['wearing'].items():
                self.wearing[key] = val

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

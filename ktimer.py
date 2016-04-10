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

from kobject import KObject

class KTimer(KObject):
    def __init__(self, char, onetime, callback, start_time, duration, *args):
        KObject.__init__(self, _id=None)

        self.args = args
        self.onetime = onetime
        self.callback = callback
        self.start_time = start_time
        self.duration = duration
        self.char = char
        self._id = self.state_save()

    def state_save(self):
        client = MongoClient()
        db = client.kmud
        collection = db.timers
        
        timer = {'char': self.char.id,
                 'duration': self.duration,
                 'start': self.start,
                 'onetime': self.onetime,
                 'args': self.args}
        
        return collection.insert_one(timer).inserted_id


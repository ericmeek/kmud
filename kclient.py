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

class KClient(KObject):
    def __init__(self, client, _id=None):
        KObject.__init__(self, _id)

        self.status = None
        self.client = client

    def is_client(self):
        return True
    
    def send_prompt(self):
        self.client.send('>')
        
    def send(self, data, prompt=False):
        self.client.send(data)
        if prompt:
            self.client.send('>')
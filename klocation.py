#!/usr/bin/python3

import matplotlib.path as mplPath
import numpy as np
import math


class KLocation:
    def __init__(self, x, y, containers=None, _id=None):
        self.x = x
        self.y = y
        self._id = _id
        self.containers = containers

    def __add__(self, other):
        return KLocation(self.x + other.x, self.y + other.y,
                         self.containers)

    def in_container(self, con_id):
        # TODO container list converted to list
        # con = self.containers[con_id]
        points = con_id.points

        npArray = np.array(points)
        bbPath = mplPath.Path(npArray)

        if bbPath.contains_point((self._x, self._y)):
            return True
        else:
            return False

    def entering_container(self, con_id):
        for container in self.containers[con_id].children:
            if self.in_container(container.id):
                return container.id
        return False

    def distance(self, max_dist, obj):
        if obj.is_character():
            dist = math.hypot(self.x - obj.location.x, self.y - obj.location.y)
            return dist

    def within(self, max_dist, obj):
        if object.is_character():
            dist = math.hypot(self.x, obj.x, self.y, obj.y)
            print("{}: {}".format(self.first_name, dist))
            if dist < max_dist:
                return True
            else:
                return False

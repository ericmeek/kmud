#!/usr/bin/python3

import matplotlib.path as mplPath
import numpy as np

class KCoordinate:
    def __init__(self, x, y, containers):
        self._x = x
        self._y = y
        self.containers = containers

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = val

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = val

    def __add__(self, other):
        return KCoordinate(self.x + other.x, self.y + other.y,
                           self.containers)

    def in_container(self, con_id):
        con = self.containers[con_id]
        points = con.points

        npArray = np.array(points)
        bbPath = mplPath.Path(npArray)

        #print(self._x, self._y)
        #print(bbPath)

        if bbPath.contains_point((self._x, self._y)):
            return True
        else:
            return False

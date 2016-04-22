#!/usr/bin/python3

import matplotlib.path as mplPath
import numpy as np


class KCoordinate:
    def __init__(self, x, y, _id=None):
        self.x = x
        self.y = y
        self._id = _id

    def __add__(self, other):
        return KCoordinate(self.x + other.x, self.y + other.y)

    def in_container(self, con):
        npArray = np.array(con.points)
        bbPath = mplPath.Path(npArray)

        # print(self._x, self._y)
        # print(bbPath)

        if bbPath.contains_point((self.x, self.y)):
            return True
        else:
            return False

    def entering_container(self, conts):
        for con in conts:
            if self.in_container(con):
                return con
        return False

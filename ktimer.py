from pymongo import MongoClient

from kobject import KObject

class KTimer(KObject):
    def __init__(self, name, char, onetime, start_time,
                 callback, duration, *args):
        KObject.__init__(self, _id=None)

        self.name = name
        self.args = args
        self.onetime = onetime
        self.callback = callback
        self.start_time = start_time
        self.duration = duration
        self.char = char
        self._id = self.state_save()

    def die(self):
        self.callback(self)

    def state_save(self):
        client = MongoClient()
        db = client.kmud
        collection = db.timers

        timer = {'char': self.char.id,
                 'duration': self.duration,
                 'start': self.start_time,
                 'onetime': self.onetime,
                 'args': self.args}

        return collection.insert_one(timer).inserted_id


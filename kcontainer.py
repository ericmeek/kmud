from kobject import KObject


class KContainer(KObject):
    def __init__(self, _id, name):
        KObject.__init__(self, _id)

        self.desc = None
        self.parent_id = None
        self.points = None
        self.name = None
        self.children = []

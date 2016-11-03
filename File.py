import os


class File:
    def __init__(self, path):
        self.path = path
        self.creation_time = os.path.getctime(path)
        self.last_modification_time = os.path.getmtime(path)
        self.type = None  # used to indicate type of file modification when occured

    def update_instance(self):
        # it's possible that the file get deleted while we run and don't update data
        if os.path.exists(self.path) is False:
            return 0

        modification_time = os.path.getmtime(self.path)
        if modification_time == self.last_modification_time:
            self.type = None
            return 0
        else:
            self.type = "m"
            return 1

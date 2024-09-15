class Event:
    def __init__(self, eid, event, date, time):
        self.eid = eid
        self.event = event
        self.date = date
        self.time = time

    def __str__(self):
        return [self.eid, self.event, self.date, self.time]

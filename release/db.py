import sqlite3
import datetime
from event import Event

class dbapi:
    def __init__(self):
        self.db = sqlite3.connect('events.db')

        self.db.execute('''
        CREATE TABLE IF NOT EXISTS events (
            eid INTEGER PRIMARY KEY,
            event TEXT,
            date TEXT,
            time TEXT)''')

        self.db.execute('''
        CREATE TABLE IF NOT EXISTS routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency TEXT NOT NULL,
            day_of_week INTEGER,
            day_of_month INTEGER,
            time TEXT NOT NULL,
            description TEXT NOT NULL
        )
        ''')

    def add(self, eid, event, date, time):
        self.db.execute('INSERT INTO events (eid, event, date, time) VALUES (?, ?, ?, ?)', (eid, event, date, time))
        self.db.commit()

    def remove(self, eid):
        self.db.execute('DELETE FROM events WHERE eid = ?', (eid,))
        self.db.commit()

    def get_events(self):
        cursor = self.db.execute('SELECT * FROM events ORDER BY date, time')
        events = []
        for row in cursor:
            event = Event(row[0], row[1], row[2], row[3])
            events.append(event)
        return events

    def get_event_by_id(self, event_id):
        cursor = self.db.execute('SELECT eid, event, date, time FROM events WHERE eid = ?', (event_id,))
        events = []
        for row in cursor:
            event = Event(row[0], row[1], row[2], row[3])
            events.append(event)
        return events

    def update_event(self, event_id, new_event, new_date, new_time):
        self.db.execute('UPDATE events SET event = ?, date = ?, time = ? WHERE eid = ?', (new_event, new_date, new_time, event_id))
        self.db.commit()

    def get_all_eid(self):
        cursor = self.db.execute('SELECT eid FROM events')
        eid_set = set()
        for row in cursor:
            eid_set.add(row[0])
        return eid_set

    def generate_new_eid(self, eid_set):
        for tentative_number in range(len(eid_set) + 1):
            if tentative_number not in eid_set:
                eid = tentative_number
                break
        return eid

    ############################ 周期性任务相关函数 ############################

    def add_routine(self, frequency, day_of_week, day_of_month, time, description):
        self.db.execute('''
        INSERT INTO routines (frequency, day_of_week, day_of_month, time, description)
        VALUES (?, ?, ?, ?, ?)
        ''', (frequency, day_of_week, day_of_month, time, description))
        self.db.commit()

    def get_routines(self):
        cursor = self.db.execute('SELECT * FROM routines')
        events = []
        for row in cursor:
            events.append(row)
        return events

    def clear_routines(self):
        self.db.execute('DELETE FROM routines')
        self.db.commit()

    def delete_routine(self, frequency, description):
        self.db.execute('DELETE FROM routines WHERE frequency = ? AND description = ?', (frequency, description))
        self.db.commit()

    def get_next_event(self, frequency, description):
        events = []
        with self.db:
            result = self.db.execute("""
                SELECT * FROM events
                WHERE event=? AND date >= DATE('now')
                ORDER BY date ASC, time ASC LIMIT 1
            """, (description,))

            for row in result:
                event = Event(row[0], row[1], row[2], row[3])
                events.append(event)

        return events

    def check_and_add_next_routine(self):
        today = datetime.date.today()

        routines = self.get_routines()
        for routine in routines:
            # 获取周期任务
            frequency, day_of_week, day_of_month, time, description = routine[1], routine[2], routine[3], routine[4], routine[5]
            if frequency == 'weekly':
                next_date = self._get_next_weekly_date(today, day_of_week)
            elif frequency == 'monthly':
                next_date = self._get_next_monthly_date(today, day_of_month)

            # 当前任务是否已经存在，如果不存在，添加任务
            check_cursor = self.db.execute('SELECT * FROM events WHERE date = ? AND time = ? AND event = ?', (next_date, time, description))
            check_list = [i for i in check_cursor]
            if not check_list:
                eid_set = self.get_all_eid()
                eid = self.generate_new_eid(eid_set)
                self.add(eid, description, next_date, time)

    def _get_next_weekly_date(self, current_date, day_of_week):
        days_ahead = day_of_week - current_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return current_date + datetime.timedelta(days=days_ahead)

    def _get_next_monthly_date(self, current_date, day_of_month):
        year = current_date.year
        month = current_date.month

        if current_date.day > day_of_month:
            month += 1
            if month > 12:
                month = 1
                year += 1

        try:
            next_date = datetime.date(year, month, day_of_month)
        except ValueError:
            next_date = datetime.date(year, month + 1, 1)

        return next_date


    ############################################################################

    def close(self):
        self.db.close()

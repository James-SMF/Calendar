import datetime, heapq, calendar, os
from db import dbapi

class diary_hist:
    def __init__(self, path, index_file):
        self.path = path
        self.index_file = index_file
        self.db = dbapi()

        ################### Index File Format #######################
        # YYYYmm data1 data2
        # YYYYmm data1 data2
        #############################################################

    # 用户上线之后，补全过去几个月的日记汇总
    def add_hist_diary(self):
        this_month = datetime.date.today()
        this_month = this_month.year * 100 + this_month.month

        if not os.path.isfile(self.index_file):
            latest_update_month = str(this_month)
        else:
            date_list = []
            with open(self.index_file, 'r') as f:
                for line in f:
                    date = line.split()[0]
                    num_date = int(date)
                    heapq.heappush(date_list, -num_date)

            latest_update_month = str(-heapq.heappop(date_list))
            latest_update_month = self.get_next_date_str(latest_update_month)

        while latest_update_month <= str(this_month):
            cur_month_diary = self.pack_month_diary(latest_update_month)

            with open(self.path + '/' + latest_update_month + '.txt', 'w') as f:
                for line in cur_month_diary:
                    f.write(line[1] + '\n\n' + line[2] + '\n\n')

            # 后期可能会往这里加东西
            with open(self.index_file, 'a') as f:
                f.write(latest_update_month + '\n')

            latest_update_month = self.get_next_date_str(latest_update_month)

    def add_diary_by_month(self, month):
        month_diary = self.db.get_diary_by_month(month)
        month_file = self.path + '/' + month + '.txt'
        with open(month_file, 'w') as f:
            for line in month_diary:
                f.write(line[1] + '\n\n' + line[2] + '\n\n')

    def pack_month_diary(self, date_str):
        year, month = int(date_str[:4]), int(date_str[4:])
        last_day_of_the_month = calendar.monthrange(year, month)[1]
        first_day, last_day = datetime.date(year, month, 1), datetime.date(year, month, last_day_of_the_month)
        month_diary = self.db.get_diary_by_range(first_day, last_day)
        return month_diary      # list of lists, where l[2] is the content

    def get_next_date_str(self, date_str):
        year, month = int(date_str[:4]), int(date_str[4:])
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        return str(next_year) + str(next_month).zfill(2)


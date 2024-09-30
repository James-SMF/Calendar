import tkinter as tk
from tkcalendar import DateEntry  # ??DateEntry
from tkinter import messagebox
import datetime, re

class ScheduleApp:
    def __init__(self, root, db):
        self.db = db
        self.root = root
        self.root.title("奶奶的日程提醒")
        self.root.geometry("700x750")
        self.root.option_add('*Button.foreground', 'black')
        self.BACKGROUND_COLOR = '#ecece7'
        self.root.configure(background=self.BACKGROUND_COLOR)

        # 创建小部件
        self.create_widgets()

        # 刷新事件列表
        self.refresh_events()


    def create_widgets(self):
        button_frame = tk.Frame(self.root, bg=self.BACKGROUND_COLOR)
        button_frame.pack()

        add_routine_button = tk.Button(button_frame, text="Add Recurring Event", command=self.open_add_routine_window, fg='black', bg=self.BACKGROUND_COLOR)
        add_routine_button.pack(side=tk.LEFT, padx=10)

        delete_routine_button = tk.Button(button_frame, text="Delete Recurring Event", command=self.open_delete_routine_window, fg='black', bg=self.BACKGROUND_COLOR)
        delete_routine_button.pack(side=tk.LEFT, padx=10)

        refresh_frame = tk.Frame(self.root, bg=self.BACKGROUND_COLOR)
        refresh_frame.pack()

        refresh_button = tk.Button(refresh_frame, text="Refresh", command=self.add_recurring_and_refresh, bg=self.BACKGROUND_COLOR)
        refresh_button.pack(ipady=15, pady=10)

        tk.Label(self.root, text="Select Date:", bg=self.BACKGROUND_COLOR).pack()
        self.date_entry = DateEntry(self.root, date_pattern="yyyy-mm-dd")
        self.date_entry.pack()

        tk.Label(self.root, text="Time (HH:MM):", bg=self.BACKGROUND_COLOR).pack()
        self.time_entry = tk.Entry(self.root)
        self.time_entry.pack()

        tk.Label(self.root, text="Description:", bg=self.BACKGROUND_COLOR).pack()
        self.desc_entry = tk.Entry(self.root)
        self.desc_entry.pack()

        add_button = tk.Button(self.root, text="Add Event", command=self.add_event, bg=self.BACKGROUND_COLOR)
        add_button.pack()

        self.events_frame = tk.Frame(self.root, bg=self.BACKGROUND_COLOR)
        self.events_frame.pack()


    def time_event_check(self, time, description):
        time = re.sub(r'：', r':', time)

        if time.isnumeric():
            if int(time) > 24 or int(time) < 0:
                messagebox.showerror("Error", "Time must be between 0 and 24")
                return (None, None)

            time += ":00"

        def count_chinese_characters(txt):
            count = 0
            for c in txt:
                if '\u4e00' <= c <= '\u9fff':
                    count += 1
            return count

        chinese_char = count_chinese_characters(description)
        non_chinese_char = len(description) - chinese_char
        weighted_len_of_description = chinese_char * 1.5 + non_chinese_char


        if weighted_len_of_description > 25:
            messagebox.showerror("Error", "Description too long!")
            return (None, None)

        return time, description


    def add_event(self):
        date = self.date_entry.get()  # 获取选中的日期
        time = self.time_entry.get()

        time, description = self.time_event_check(time, self.desc_entry.get())

        if not time and not description:
            return

        eid_set = self.db.get_all_eid()
        eid = self.db.generate_new_eid(eid_set)

        self.db.add(eid, description, date, time)

        self.time_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.refresh_events()

    def add_recurring_and_refresh(self):
        self.db.check_and_add_next_routine()
        self.refresh_events()

    def refresh_events(self):
        # 先删掉现有的
        for widget in self.events_frame.winfo_children():
            widget.destroy()

        current_date = datetime.datetime.now().date()

        # 获取事件（根据时间排序）
        events = self.db.get_events()
        count = 0

        for idx, event in enumerate(events):
            event_frame = tk.Frame(self.events_frame, bg=self.BACKGROUND_COLOR)
            event_frame.grid(row=idx, column=0, sticky='w', pady=3)

            # 检查过期/临期事件
            event_date = datetime.datetime.strptime(event.date, "%Y-%m-%d").date()
            days_until_event = (event_date - current_date).days

            if event_date < current_date:
                text_color = '#3487f3'
                remaining_text = "(已过期)"
            elif 0 <= days_until_event <= 5:
                text_color = '#859224'
                remaining_text = f"(剩余 {days_until_event} 天)"
            else:
                text_color = 'black'
                remaining_text = f"(剩余 {days_until_event} 天)"

            event_label = tk.Label(event_frame, text=f"{remaining_text} {event.date} {event.time}  {event.event}", anchor='w', fg=text_color, bg=self.BACKGROUND_COLOR)
            event_label.grid(row=0, column=0, sticky='w', padx=3)

            delete_button = tk.Button(event_frame, text="Delete", command=lambda e_id=event.eid: self.delete_event(e_id), bg=self.BACKGROUND_COLOR)
            delete_button.grid(row=0, column=1, padx=3)

            update_button = tk.Button(event_frame, text="Update", command=lambda e_id=event.eid: self.update_event(e_id), bg=self.BACKGROUND_COLOR)
            update_button.grid(row=0, column=2, padx=3)

            note_button = tk.Button(event_frame, text="Note", command=lambda e_id=event.eid: self.update_event(e_id), bg=self.BACKGROUND_COLOR)
            update_button.grid(row=0, column=2, padx=3)
            count += 1

            # 最多显示接下来15条事件，专注当下
            if count > 15:
                break

    def delete_event(self, event_id):
        self.db.remove(event_id)
        self.refresh_events()

    def update_event(self, event_id):
        ''' 更新事件 '''
        event_data = self.db.get_event_by_id(event_id)
        if event_data:
            evt = event_data[0]
            original_date, original_time, original_description = evt.date, evt.time, evt.event
        else:
            messagebox.showerror("Error", "Event not found!")
            return

        update_window = tk.Toplevel(self.root)
        update_window.title("Update Event")

        tk.Label(update_window, text="New Date:").pack()
        new_date_entry = DateEntry(update_window, date_pattern="yyyy-mm-dd")  # DateEntry
        new_date_entry.set_date(original_date)
        new_date_entry.pack()

        tk.Label(update_window, text="New Time (HH:MM):").pack()
        new_time_entry = tk.Entry(update_window)
        new_time_entry.insert(0, original_time)
        new_time_entry.pack()

        tk.Label(update_window, text="New Event Description:").pack()
        new_desc_entry = tk.Entry(update_window)
        new_desc_entry.insert(0, original_description)
        new_desc_entry.pack()

        update_button = tk.Button(update_window, text="Update", command=lambda: self.perform_update(event_id, new_desc_entry.get(), new_date_entry.get(), new_time_entry.get(), update_window))
        update_button.pack()

    def perform_update(self, event_id, description, new_date, new_time, update_window):
        new_time, description = self.time_event_check(new_time, description)

        if not new_time and not description:
            return

        self.db.update_event(event_id, description, new_date, new_time)
        update_window.destroy()
        self.refresh_events()

    ############################ 周期性任务相关函数 ############################

    def open_add_routine_window(self):

        '''打开添加周期性任务的窗口'''

        routine_window = tk.Toplevel(self.root)
        routine_window.title("Add Recurring Event")

        tk.Label(routine_window, text="Description:").pack()
        desc_entry = tk.Entry(routine_window)
        desc_entry.pack()

        tk.Label(routine_window, text="Time (HH:MM):").pack()
        time_entry = tk.Entry(routine_window)
        time_entry.pack()

        tk.Label(routine_window, text="Frequency:").pack()
        frequency_var = tk.StringVar(value="weekly")
        weekly_radiobutton = tk.Radiobutton(routine_window, text="Weekly", variable=frequency_var, value="weekly")
        weekly_radiobutton.pack()
        monthly_radiobutton = tk.Radiobutton(routine_window, text="Monthly", variable=frequency_var, value="monthly")
        monthly_radiobutton.pack()

        tk.Label(routine_window, text="Day of Week (1: Mon - 7: Sun) or Day of Month:").pack()
        day_entry = tk.Entry(routine_window)
        day_entry.pack()

        confirm_button = tk.Button(routine_window, text="Confirm",
                                   command=lambda: self.add_routine(frequency_var.get(), day_entry.get(), time_entry.get(), desc_entry.get(), routine_window))
        confirm_button.pack()

        self.refresh_events()

    def add_routine(self, frequency, day, time, description, window):
        if not day.isdigit():
            messagebox.showerror("Input Error", "Day must be a number.")
            return

        time, description = self.time_event_check(time, description)

        if not time and not description:
            return

        day = int(day)
        if frequency == "weekly":
            if day < 1 or day > 7:
                messagebox.showerror("Input Error", "Day of the week must be between 1 and 7.")
                return
            self.db.add_routine(frequency="weekly", day_of_week=day, day_of_month=None, time=time, description=description)
        elif frequency == "monthly":
            if day < 1 or day > 31:
                messagebox.showerror("Input Error", "Day of the month must be between 1 and 31.")
                return
            self.db.add_routine(frequency="monthly", day_of_week=None, day_of_month=day, time=time, description=description)

        # 这个 bug 搞了好久。原理是这样的，生成按钮的时候，add routine的函数没有运行，那如果在那个时候
        # check and add那啥routine了，会发生什么？在event数据库中会有数据存入，而显示呢，并没有显示。
        # 当这个add routine函数实际被运行的时候，会检查到这个事件已经在event里了，所以不会进行储存
        # 这时候就会造成问题。
        self.add_recurring_and_refresh()
        window.destroy()

    def open_delete_routine_window(self):
        delete_routine_window = tk.Toplevel(self.root)
        delete_routine_window.title("Delete Recurring Event")

        routines = self.db.get_routines()
        self.selected_routines = []

        checklist_frame = tk.Frame(delete_routine_window)
        checklist_frame.pack()

        if not routines:
            tk.Label(delete_routine_window, text="No recurring events found.").pack()
        else:
            for routine in routines:
                var = tk.BooleanVar()
                self.selected_routines.append((var, routine))
                checkbox_text = f"{routine[5]} ({routine[1]})"  # 事件 频率
                tk.Checkbutton(checklist_frame, text=checkbox_text, variable=var).pack(anchor='w')

        button_frame = tk.Frame(delete_routine_window)
        button_frame.pack(pady=10)

        delete_button = tk.Button(button_frame, text="仅删除Routine",
                                  command=lambda: self.delete_selected_routines(delete_routine_window))
        delete_button.pack(side=tk.LEFT, padx=10)

        delete_with_event_button = tk.Button(button_frame, text="同时从日程中删除",
                                        command=lambda: self.delete_selected_routines(
                                            delete_routine_window, delete_from_events=True
                                        )
                                    )
        delete_with_event_button.pack(side=tk.LEFT, padx=10)


    def delete_selected_routines(self, window, delete_from_events=False):
        """ 删除玩家选中的周期性事件 """
        to_delete = [routine for var, routine in self.selected_routines if var.get()]

        if not to_delete:
            return

        for routine in to_delete:
            frequency, description = routine[1], routine[5]
            self.db.delete_routine(frequency, description)

            if delete_from_events:
                if next_event := self.db.get_next_event(frequency, description):
                    self.db.remove(next_event[0].eid)

        window.destroy()
        self.refresh_events()

    ############################################################################

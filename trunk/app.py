import tkinter as tk
from tkcalendar import DateEntry
from tkinter import messagebox, font, ttk
from diary import diary_hist
import datetime, re

class ScheduleApp:
    def __init__(self, root, db):
        self.db = db
        self.diary_sync = diary_hist('./diary_hist', './diary_hist/index.txt')
        self.root = root
        self.root.title("朱振亿日程提醒")
        self.root.geometry("900x780")
        self.root.option_add('*Button.foreground', 'black')
        self.BACKGROUND_COLOR = '#ecece7'
        style = ttk.Style(self.root)
        style.theme_use('clam')
        self.root.configure(background=self.BACKGROUND_COLOR)

        # 创建小部件
        self.create_widgets()

        # 刷新事件列表
        self.add_recurring_and_refresh()

        # 更新历史日记
        self.diary_sync.add_hist_diary()

        # 用于diary部分传参
        self.diary_window = None
        self.diary_text = None
        self.current_date = datetime.date.today()


    def create_widgets(self):
        '''创建启动窗口'''
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10, padx=50)

        add_recurring_button = tk.Button(button_frame, text="Add Recurring Event", command=self.open_add_routine_window)
        add_recurring_button.grid(row=0, column=1, padx=(225,0))

        delete_recurring_button = tk.Button(button_frame, text="Delete Recurring Event", command=self.open_delete_routine_window)
        delete_recurring_button.grid(row=0, column=2)

        diary_button = tk.Button(button_frame, text="Diary", command=self.open_diary_window)
        diary_button.grid(row=0, column=60, padx=(165, 0), ipady=10)

        #  button_frame.grid_columnconfigure(3, weight=10)

        ######################################################################

        refresh_frame = tk.Frame(self.root, bg=self.BACKGROUND_COLOR)
        refresh_frame.pack()

        refresh_button = tk.Button(refresh_frame, text="Refresh", command=self.add_recurring_and_refresh, bg=self.BACKGROUND_COLOR)
        refresh_button.pack(ipady=15, pady=10)

        tk.Label(self.root, text="Select Date:", bg=self.BACKGROUND_COLOR).pack()
        self.date_entry = DateEntry(self.root, date_pattern="yyyy-mm-dd")
        self.date_entry.pack()
        self.date_entry.focus_set()

        tk.Label(self.root, text="Time (HH:MM):", bg=self.BACKGROUND_COLOR).pack()
        self.time_entry = tk.Entry(self.root)
        self.time_entry.pack()

        tk.Label(self.root, text="Description:", bg=self.BACKGROUND_COLOR).pack()
        self.desc_entry = tk.Entry(self.root)
        self.desc_entry.pack()

        add_button = tk.Button(self.root, text="Add Event", command=self.add_event, bg=self.BACKGROUND_COLOR)
        add_button.pack(ipady=5, pady=10)

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
        self.add_recurring_and_refresh()

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
                remaining_text = "( 已过期 )"
            elif 2 <= days_until_event <= 5:
                text_color = '#859224'
                remaining_text = f"( {days_until_event} 天后 )"
            elif days_until_event == 1:
                text_color = '#859224'
                remaining_text = "( 明天 )"
            elif days_until_event == 0:
                text_color = '#a47fde'
                remaining_text = "( 今天 )"
            else:
                text_color = 'black'
                remaining_text = f"( {days_until_event} 天后 )"

            event_label = tk.Label(event_frame, text=f"{remaining_text} {event.date} {event.time}  {event.event}", anchor='w', fg=text_color, bg=self.BACKGROUND_COLOR)
            event_label.grid(row=0, column=0, sticky='w', padx=3)

            delete_button = tk.Button(event_frame, text="Delete", command=lambda e_id=event.eid: self.delete_event(e_id), bg=self.BACKGROUND_COLOR)
            delete_button.grid(row=0, column=1, padx=3)

            update_button = tk.Button(event_frame, text="Update", command=lambda e_id=event.eid: self.update_event(e_id), bg=self.BACKGROUND_COLOR)
            update_button.grid(row=0, column=2, padx=3)

            note_button = tk.Button(event_frame, text="Note", command=lambda e_id=event.eid: self.update_event(e_id), bg=self.BACKGROUND_COLOR)
            update_button.grid(row=0, column=2, padx=3)
            count += 1

            # 最多显示接下来12条事件，专注当下
            if count > 11:
                break

    def delete_event(self, event_id):
        self.db.remove(event_id)
        self.add_recurring_and_refresh()

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

        style = ttk.Style(update_window)
        style.theme_use('clam')

        tk.Label(update_window, text="New Date:").pack()
        new_date_entry = DateEntry(update_window, date_pattern="yyyy-mm-dd")  # DateEntry
        new_date_entry.set_date(original_date)
        new_date_entry.pack()
        new_date_entry.focus_set()


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
        self.add_recurring_and_refresh()

    ############################ 周期性任务相关函数 ############################

    def open_add_routine_window(self):

        '''打开添加周期性任务的窗口'''

        routine_window = tk.Toplevel(self.root)
        routine_window.title("Add Recurring Event")
        routine_window.geometry("350x300")

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
        time, description = self.time_event_check(time, description)

        if not time and not description:
            return

        day_list = day.split(",")
        for d in day_list:
            if not d.isdigit():
                messagebox.showerror("Input Error", "Day must be a number.")
                return

            d = int(d)

            if frequency == "weekly":
                if d < 1 or d > 7:
                    messagebox.showerror("Input Error", "day of the week must be between 1 and 7.")
                    return
                self.db.add_routine(frequency="weekly", day_of_week=d, day_of_month=None, time=time, description=description)
            elif frequency == "monthly":
                if d < 1 or d > 31:
                    messagebox.showerror("Input Error", "day of the month must be between 1 and 31.")
                    return
                self.db.add_routine(frequency="monthly", day_of_week=None, day_of_month=d, time=time, description=description)

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
            seen = set()
            for routine in routines:
                var = tk.BooleanVar()
                self.selected_routines.append((var, routine))
                checkbox_text = f"{routine[5]} ({routine[1]})"  # 事件 频率
                if checkbox_text not in seen:
                    tk.Checkbutton(checklist_frame, text=checkbox_text, variable=var).pack(anchor='w')
                seen.add(checkbox_text)

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

            # TODO：同时从日程表中删除时，遍历并删除所有同名的recurring事件
            if delete_from_events:
                if next_event := self.db.get_next_event(frequency, description):
                    for e in next_event:
                        self.db.remove(e.eid)

        window.destroy()
        self.refresh_events()

    ############################################################################

    ############################### Diary ######################################

    def on_key_press(self, event, text_widget):
        # 捕捉中文括号的输入
        if event.char == '（':
            text_widget.insert(tk.INSERT, '（')
            return "break"
        elif event.char == '）':
            text_widget.insert(tk.INSERT, '）')
            return "break"


    def back_to_today(self, date_entry):
        # save current date changes
        date_on_manifest = date_entry.get_date()
        self.save_diary_changes(date_on_manifest)

        # back to today
        self.diary_text.delete("1.0", tk.END)
        self.current_date = datetime.date.today()
        self.insert_diary_text_by_date(self.current_date)
        date_entry.set_date(self.current_date)


    def _on_open_diary_window(self):
        diary_window = tk.Toplevel(self.root)
        diary_window.title("Diary")
        diary_window.geometry("750x800")

        diary_frame = tk.Frame(diary_window, width=900, height=800, bg=self.BACKGROUND_COLOR)
        diary_frame.pack()
        diary_frame.pack_propagate(False)

        style = ttk.Style(diary_frame)
        style.theme_use('clam')

        # 设置日记日期
        date_label = tk.Label(diary_frame, text="Select Date:")
        date_label.pack(pady=(10, 0))

        date_frame = tk.Frame(diary_frame)
        date_frame.pack()

        # 日期选择
        date_entry = DateEntry(date_frame, width=12, background='#AAFFAA',
                               foreground='black', borderwidth=2, date_pattern="yyyy-mm-dd")
        date_entry.grid(row=0, column=1, padx=(235, 100))

        # 快速回到今日
        back_to_today_button = tk.Button(date_frame, text="Back to Today",
                                          command=lambda: self.back_to_today(date_entry))
        back_to_today_button.grid(row=0, column=2, padx=(20, 0))

        # 设置两个按钮：Save Changes 和 discard Changes
        button_frame = tk.Frame(diary_frame)
        button_frame.pack(pady=10)

        save_changes_button = tk.Button(button_frame, text="Save Changes",
                                        command=lambda: self.save_diary_changes(date_entry.get()))
        save_changes_button.pack(side=tk.LEFT, padx=10)

        discard_changes_button = tk.Button(button_frame, text="discard Changes",
                                          command=lambda: self.discard_diary_changes())
        discard_changes_button.pack(side=tk.LEFT, padx=10)

        # 添加滚动条
        scrollbar = tk.Scrollbar(diary_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 设置日记字体
        diary_text = tk.Text(diary_frame, width=70, height=45, yscrollcommand=scrollbar.set, undo=True)
        custom_font = font.Font(family="Microsoft YaHei", size=16, weight="bold")
        diary_text.config(font=custom_font)
        diary_text.bind("<KeyPress>", lambda event: self.on_key_press(event, diary_text))
        diary_text.pack()

        return diary_window, diary_text, date_entry


    def insert_diary_text_by_date(self, date):
        diary = self.db.get_diary_by_date(date)

        if diary:
            for row in diary:
                self.diary_text.insert(tk.END, row[2] + "\n")

    def open_diary_window(self):
        '''打开日记的窗口，并默认显示今日日记'''

        # Construct the window
        self.diary_window, self.diary_text, self.date_entry = self._on_open_diary_window()

        # 先把修改前的日记储存到一个cursor中
        #  cursor = self.db.get_all_diary()

        # 把目标日期的日记写入到textbox中并显示出来
        # 测试用
        # self.current_date = datetime.date(2024, 10, 14)
        self.current_date = datetime.date.today()
        self.insert_diary_text_by_date(self.current_date)

        # 当用户选择日期之后，立即显示那天的日记
        self.date_entry.bind("<<DateEntrySelected>>", self.load_diary_by_date)
        self.diary_text.bind("<KeyPress>", lambda event: self.on_key_press(event, self.diary_text))
        #  self.diary_window.bind("<Command-z>", lambda event: self.diary_text.edit_undo())
        #  self.diary_window.bind("<Command-Shift-z>", lambda event: self.diary_text.edit_redo())

        # Close the window and save the diary
        self.diary_window.protocol("WM_DELETE_WINDOW", lambda: self.close_diary(self.diary_window, self.diary_text))

    def close_diary(self, window, text_widget):
        # When the window is closed, save the changes to the db using the add_diary function
        # bug: 这里应该分类讨论。如果用户当前停留在今日，关闭了界面，那么就可以直接保存
        # 如果用户关闭界面的时候停留在别的日期，那么就不要保存。但是在切换日期的时候应该有
        # 保存的逻辑
        current_date = self.date_entry.get_date()
        if current_date == self.current_date:
            self.save_diary_changes(self.current_date)
        window.destroy()

    def load_diary_by_date(self, event):
        '''通过更改current date这个变量来实现日期修改'''
        self.save_diary_changes(self.current_date)
        self.diary_text.delete("1.0", tk.END)
        self.current_date = self.date_entry.get_date()
        self.insert_diary_text_by_date(self.current_date)

    def save_diary_changes(self, date):
        self.db.delete_diary(date)
        self.db.add_diary(date, self.diary_text.get("1.0", tk.END).strip())

    def discard_diary_changes(self):
        self.diary_text.delete("1.0", tk.END)
        self.insert_diary_text_by_date(self.current_date)


    ############################################################################

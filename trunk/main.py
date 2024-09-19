import tkinter as tk
from db import dbapi
from app import ScheduleApp

if __name__ == "__main__":
    root = tk.Tk()

    # 数据库，启动！
    db = dbapi()

    # GUI，启动！
    app = ScheduleApp(root, db)
    root.mainloop()

    # 数据库，关闭！
    db.close()

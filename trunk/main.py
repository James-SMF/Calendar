import tkinter as tk
from db import dbapi
from app import ScheduleApp

if __name__ == "__main__":
    root = tk.Tk()
    db = dbapi()
    app = ScheduleApp(root, db)
    root.mainloop()
    db.close()

"""
BMI Calculator - Advanced Tier
Oasis Infobyte Internship - Python Programming Track

Features:
- GUI built with tkinter
- Input validation (non-numeric and negative values rejected)
- Colour-coded BMI result
- Multi-user support (records saved per named user)
- History stored in SQLite database
- BMI trend graph using matplotlib
- Error handling for database read/write failures
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_FILE = "bmi_data.db"


# ---------------------------------------------------------------
# BMI logic
# ---------------------------------------------------------------
def calculate_bmi(weight_kg, height_m):
    """BMI = weight / (height squared)."""
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi):
    """Return (category, colour) for a BMI value."""
    if bmi < 18.5:
        return "Underweight", "#2980b9"   # blue
    elif bmi < 25:
        return "Normal", "#27ae60"        # green
    elif bmi < 30:
        return "Overweight", "#e67e22"    # orange
    else:
        return "Obese", "#c0392b"         # red


def validate_inputs(name, weight_text, height_text):
    """
    Validate user input.
    Returns (weight, height) as floats, or raises ValueError with a
    helpful message.
    """
    if not name.strip():
        raise ValueError("Please enter a user name.")

    try:
        weight = float(weight_text)
        height = float(height_text)
    except ValueError:
        raise ValueError("Weight and height must be numbers (example: 70 and 1.75).")

    if weight <= 0 or height <= 0:
        raise ValueError("Weight and height must be positive numbers.")
    if height > 3:
        raise ValueError("Height must be in metres (example: 1.75), not centimetres.")
    if weight > 500:
        raise ValueError("Weight looks too large. Please enter weight in kg.")

    return weight, height


# ---------------------------------------------------------------
# Database
# ---------------------------------------------------------------
def init_db():
    """Create the table if it does not exist."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                weight REAL NOT NULL,
                height REAL NOT NULL,
                bmi REAL NOT NULL,
                category TEXT NOT NULL,
                recorded_at TEXT NOT NULL
            )
            """
        )


def save_record(user_name, weight, height, bmi, category):
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT INTO records (user_name, weight, height, bmi, category, recorded_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_name, weight, height, bmi, category,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def get_records(user_name):
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute(
            "SELECT recorded_at, weight, height, bmi, category FROM records "
            "WHERE user_name = ? ORDER BY recorded_at",
            (user_name,),
        )
        return cur.fetchall()


def get_all_users():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.execute("SELECT DISTINCT user_name FROM records ORDER BY user_name")
        return [row[0] for row in cur.fetchall()]


# ---------------------------------------------------------------
# GUI
# ---------------------------------------------------------------
class BMIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BMI Calculator")
        self.geometry("560x640")
        self.resizable(False, False)

        self._build_widgets()
        self._refresh_users()

    def _build_widgets(self):
        pad = {"padx": 12, "pady": 5}

        title = tk.Label(self, text="BMI Calculator", font=("Arial", 20, "bold"))
        title.pack(pady=(14, 6))

        form = tk.Frame(self)
        form.pack(fill="x", **pad)

        tk.Label(form, text="User name:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=4)
        self.name_box = ttk.Combobox(form, width=28, font=("Arial", 11))
        self.name_box.grid(row=0, column=1, pady=4, padx=8)

        tk.Label(form, text="Weight (kg):", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=4)
        self.weight_entry = tk.Entry(form, width=30, font=("Arial", 11))
        self.weight_entry.grid(row=1, column=1, pady=4, padx=8)

        tk.Label(form, text="Height (m):", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=4)
        self.height_entry = tk.Entry(form, width=30, font=("Arial", 11))
        self.height_entry.grid(row=2, column=1, pady=4, padx=8)

        buttons = tk.Frame(self)
        buttons.pack(pady=8)
        tk.Button(buttons, text="Calculate", width=14, font=("Arial", 11, "bold"),
                  command=self.on_calculate).grid(row=0, column=0, padx=6)
        tk.Button(buttons, text="View Trend Graph", width=16, font=("Arial", 11),
                  command=self.on_show_graph).grid(row=0, column=1, padx=6)

        self.result_label = tk.Label(self, text="Your BMI result will appear here",
                                     font=("Arial", 14, "bold"), fg="gray")
        self.result_label.pack(pady=10)

        tk.Label(self, text="History", font=("Arial", 12, "bold")).pack()

        columns = ("date", "weight", "height", "bmi", "category")
        self.table = ttk.Treeview(self, columns=columns, show="headings", height=8)
        headings = {"date": "Date", "weight": "Weight", "height": "Height",
                    "bmi": "BMI", "category": "Category"}
        widths = {"date": 150, "weight": 70, "height": 70, "bmi": 70, "category": 110}
        for col in columns:
            self.table.heading(col, text=headings[col])
            self.table.column(col, width=widths[col], anchor="center")
        self.table.pack(padx=12, pady=6, fill="x")

        self.name_box.bind("<<ComboboxSelected>>", lambda e: self._load_history())

    # ---- helpers ----
    def _refresh_users(self):
        try:
            self.name_box["values"] = get_all_users()
        except sqlite3.Error as err:
            messagebox.showerror("Database error", f"Could not load users:\n{err}")

    def _load_history(self):
        name = self.name_box.get().strip()
        for row in self.table.get_children():
            self.table.delete(row)
        if not name:
            return
        try:
            for date, weight, height, bmi, category in get_records(name):
                self.table.insert("", "end",
                                  values=(date, weight, height, f"{bmi:.2f}", category))
        except sqlite3.Error as err:
            messagebox.showerror("Database error", f"Could not read records:\n{err}")

    # ---- button actions ----
    def on_calculate(self):
        name = self.name_box.get()
        try:
            weight, height = validate_inputs(
                name, self.weight_entry.get(), self.height_entry.get()
            )
        except ValueError as err:
            messagebox.showwarning("Invalid input", str(err))
            return

        bmi = calculate_bmi(weight, height)
        category, colour = classify_bmi(bmi)
        self.result_label.config(text=f"BMI: {bmi:.2f}  ({category})", fg=colour)

        try:
            save_record(name.strip(), weight, height, bmi, category)
        except sqlite3.Error as err:
            messagebox.showerror("Database error", f"Could not save the record:\n{err}")
            return

        self._refresh_users()
        self._load_history()

    def on_show_graph(self):
        name = self.name_box.get().strip()
        if not name:
            messagebox.showwarning("No user", "Please enter or select a user name first.")
            return
        try:
            records = get_records(name)
        except sqlite3.Error as err:
            messagebox.showerror("Database error", f"Could not read records:\n{err}")
            return

        if len(records) < 2:
            messagebox.showinfo("Not enough data",
                                "Save at least 2 records for this user to see a trend.")
            return

        win = tk.Toplevel(self)
        win.title(f"BMI Trend - {name}")
        win.geometry("640x420")

        fig = Figure(figsize=(6.4, 4.0), dpi=100)
        ax = fig.add_subplot(111)
        dates = [r[0][5:16] for r in records]   # MM-DD HH:MM
        values = [r[3] for r in records]
        ax.plot(dates, values, marker="o", color="#2c3e50")
        ax.axhspan(18.5, 25, alpha=0.15, color="green", label="Normal range")
        ax.set_title(f"BMI trend for {name}")
        ax.set_xlabel("Date")
        ax.set_ylabel("BMI")
        ax.legend()
        ax.tick_params(axis="x", rotation=30)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


if __name__ == "__main__":
    try:
        init_db()
    except sqlite3.Error as err:
        print(f"Could not initialise database: {err}")
    app = BMIApp()
    app.mainloop()
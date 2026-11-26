import tkinter as tk
from tkinter import messagebox
import secrets
import string
import pyperclip

# ================= COLORS =================

BG = "#080D1C"
CARD = "#111A30"
CARD2 = "#202A40"
FIELD = "#0B1428"
BORDER = "#293858"
TEXT = "#F3F5FF"
MUTED = "#94A3C5"
PURPLE = "#8657FF"
HOVER = "#A184FF"
AQUA = "#20E6D0"
GREEN = "#25DDA5"
YELLOW = "#FFBD59"
RED = "#FF6480"

FONT = "Segoe UI"
MONO = "Consolas"

MIN_LENGTH = 8
MAX_LENGTH = 64
AMBIGUOUS = "0O1lI"
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


# ================= PASSWORD LOGIC =================

def build_pools(upper, lower, digits, symbols, exclude):

    pools = []

    if upper:
        pools.append(string.ascii_uppercase)
    if lower:
        pools.append(string.ascii_lowercase)
    if digits:
        pools.append(string.digits)
    if symbols:
        pools.append(SYMBOLS)

    if exclude:
        pools = [
            "".join(c for c in pool if c not in AMBIGUOUS)
            for pool in pools
        ]

    return [p for p in pools if p]


def generate_password(length, pools):

    if not MIN_LENGTH <= length <= MAX_LENGTH:
        raise ValueError("Password length must be between 8 and 64.")

    if len(pools) < 2:
        raise ValueError("Please select at least 2 character types.")

    if length < len(pools):
        raise ValueError("Length is too short for selected types.")

    chars = [secrets.choice(pool) for pool in pools]

    all_chars = "".join(pools)

    chars.extend(
        secrets.choice(all_chars)
        for _ in range(length - len(chars))
    )

    secrets.SystemRandom().shuffle(chars)

    return "".join(chars)


def password_strength(password):

    score = 0

    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 20
    if len(password) >= 16:
        score += 15

    kinds = sum([
        any(c.isupper() for c in password),
        any(c.islower() for c in password),
        any(c.isdigit() for c in password),
        any(c in SYMBOLS for c in password)
    ])

    score = min(100, score + kinds * 11)

    if score < 50:
        return "WEAK", RED, score
    if score < 80:
        return "MEDIUM", YELLOW, score

    return "STRONG", GREEN, score


# ================= ROUNDED BUTTON =================

class RoundButton(tk.Canvas):

    def __init__(self, parent, text, command,
                 bg=PURPLE, hover=HOVER, width=200,
                 height=45, size=11, parent_bg=CARD):

        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="hand2"
        )

        self.command = command
        self.bg_color = bg
        self.hover_color = hover

        self.shape = self.create_rounded(
            1, 1, width - 1, height - 1,
            fill=bg, outline=bg
        )

        self.create_text(
            width / 2, height / 2,
            text=text,
            fill=TEXT,
            font=(FONT, size, "bold")
        )

        self.bind("<Enter>", self.enter)
        self.bind("<Leave>", self.leave)
        self.bind("<Button-1>", self.click)

    def create_rounded(self, x1, y1, x2, y2, **kwargs):

        r = 12

        points = [
            x1+r,y1, x2-r,y1, x2,y1,
            x2,y1+r, x2,y2-r, x2,y2,
            x2-r,y2, x1+r,y2, x1,y2,
            x1,y2-r, x1,y1+r, x1,y1
        ]

        return self.create_polygon(
            points, smooth=True, **kwargs
        )

    def enter(self, event):
        self.itemconfig(
            self.shape,
            fill=self.hover_color,
            outline=self.hover_color
        )

    def leave(self, event):
        self.itemconfig(
            self.shape,
            fill=self.bg_color,
            outline=self.bg_color
        )

    def click(self, event):
        self.command()


# ================= CUSTOM CHECKBOX =================

class CheckRow(tk.Frame):

    def __init__(self, parent, text, variable):

        super().__init__(parent, bg=CARD, cursor="hand2")

        self.variable = variable

        self.box = tk.Canvas(
            self, width=24, height=24,
            bg=CARD, highlightthickness=0
        )
        self.box.pack(side="left")

        self.label = tk.Label(
            self, text=text,
            bg=CARD, fg=TEXT,
            font=(FONT, 10),
            cursor="hand2"
        )
        self.label.pack(side="left", padx=8)

        for widget in (self, self.box, self.label):
            widget.bind("<Button-1>", self.toggle)

        self.variable.trace_add(
            "write", lambda *args: self.draw()
        )

        self.draw()

    def toggle(self, event=None):
        self.variable.set(not self.variable.get())

    def draw(self):

        self.box.delete("all")

        if self.variable.get():

            self.box.create_rectangle(
                2, 2, 22, 22,
                fill=PURPLE, outline=PURPLE
            )

            self.box.create_line(
                6, 12, 10, 16, 18, 7,
                fill=TEXT, width=2
            )

        else:

            self.box.create_rectangle(
                2, 2, 22, 22,
                fill=FIELD, outline=BORDER
            )


# ================= MAIN APPLICATION =================

class PasswordApp(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title("Midnight Aurora | Password Generator")
        self.configure(bg=BG)
        self.history = []

        # Adapt window size to available screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        self.window_width = min(850, sw - 30)
        self.window_height = min(900, sh - 90)

        self.geometry(
            f"{self.window_width}x{self.window_height}"
        )

        self.minsize(
            min(560, self.window_width),
            min(560, self.window_height)
        )

        self.var_upper = tk.BooleanVar(value=True)
        self.var_lower = tk.BooleanVar(value=True)
        self.var_digits = tk.BooleanVar(value=True)
        self.var_symbols = tk.BooleanVar(value=True)
        self.var_exclude = tk.BooleanVar(value=False)

        self.var_length = tk.IntVar(value=20)

        self._build_ui()

    # ================= CARD =================

    def card(self, parent, title):

        frame = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        frame.pack(
            fill="x",
            padx=22,
            pady=3
        )

        tk.Label(
            frame,
            text=title,
            bg=CARD,
            fg=HOVER,
            font=(FONT, 10, "bold")
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 6)
        )

        return frame

    # ================= BUILD UI =================

    def _build_ui(self):

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=4)

        # HEADER
        tk.Label(
            main,
            text="PASSWORD GENERATOR",
            bg=BG,
            fg=TEXT,
            font=(FONT, 22, "bold")
        ).pack(pady=(7, 0))

        tk.Label(
            main,
            text="Create powerful, random and secure passwords",
            bg=BG,
            fg=MUTED,
            font=(FONT, 10)
        ).pack(pady=(1, 5))

        # LENGTH
        card = self.card(main, "01  |  PASSWORD LENGTH")

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=12, pady=(0, 6))

        self.length_label = tk.Label(
            row,
            textvariable=self.var_length,
            bg=CARD,
            fg=AQUA,
            font=(MONO, 21, "bold"),
            width=3
        )
        self.length_label.pack(side="left")

        self.slider = tk.Scale(
            row,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            orient="horizontal",
            variable=self.var_length,
            bg=CARD,
            fg=TEXT,
            troughcolor=FIELD,
            activebackground=PURPLE,
            highlightthickness=0,
            showvalue=False,
            bd=0,
            length=260
        )
        self.slider.pack(side="left", fill="x", expand=True, padx=8)

        self.spin = tk.Spinbox(
            row,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            width=4,
            textvariable=self.var_length,
            font=(MONO, 12, "bold"),
            bg=FIELD,
            fg=TEXT,
            buttonbackground=CARD,
            relief="flat",
            justify="center",
            command=self.validate_length
        )
        self.spin.pack(side="right")

        self.spin.bind(
            "<Return>",
            lambda e: self.validate_length()
        )
        self.spin.bind(
            "<FocusOut>",
            lambda e: self.validate_length()
        )

        # CHARACTER TYPES - TWO COLUMNS
        card = self.card(main, "02  |  CHARACTER TYPES")

        grid = tk.Frame(card, bg=CARD)
        grid.pack(fill="x", padx=16, pady=(0, 8))

        options = [
            ("Uppercase (A-Z)", self.var_upper, 0, 0),
            ("Lowercase (a-z)", self.var_lower, 0, 1),
            ("Numbers (0-9)", self.var_digits, 1, 0),
            ("Symbols (!@#$)", self.var_symbols, 1, 1),
            ("Exclude ambiguous (0 O 1 l I)",
             self.var_exclude, 2, 0)
        ]

        for label, variable, r, c in options:

            CheckRow(
                grid, label, variable
            ).grid(
                row=r, column=c,
                sticky="w",
                padx=5,
                pady=3
            )

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # GENERATE BUTTON
        RoundButton(
            main,
            "⚡  GENERATE PASSWORD",
            self.on_generate,
            width=600,
            height=42,
            size=13,
            parent_bg=BG
        ).pack(fill="x", padx=22, pady=5)

        # RESULT
        card = self.card(main, "03  |  YOUR PASSWORD")

        self.result_var = tk.StringVar()

        self.result_entry = tk.Entry(
            card,
            textvariable=self.result_var,
            font=(MONO, 15, "bold"),
            justify="center",
            state="readonly",
            readonlybackground=FIELD,
            fg=AQUA,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER
        )

        self.result_entry.pack(
            fill="x", padx=15, ipady=7, pady=3
        )

        # STRENGTH
        strength_row = tk.Frame(card, bg=CARD)
        strength_row.pack(fill="x", padx=15, pady=3)

        tk.Label(
            strength_row,
            text="PASSWORD STRENGTH",
            bg=CARD,
            fg=MUTED,
            font=(FONT, 9, "bold")
        ).pack(side="left")

        self.strength_label = tk.Label(
            strength_row,
            text="NOT GENERATED",
            bg=CARD,
            fg=MUTED,
            font=(FONT, 10, "bold")
        )
        self.strength_label.pack(side="right")

        self.bar = tk.Canvas(
            card,
            height=9,
            bg=FIELD,
            highlightthickness=0
        )
        self.bar.pack(fill="x", padx=15, pady=(1, 6))

        self.score = 0
        self.bar_color = FIELD

        self.bar.bind(
            "<Configure>",
            lambda e: self.update_bar()
        )

        # COPY
        copy_row = tk.Frame(card, bg=CARD)
        copy_row.pack(fill="x", padx=15, pady=(0, 6))

        RoundButton(
            copy_row,
            "COPY TO CLIPBOARD",
            self.on_copy,
            bg=CARD2,
            hover="#293A60",
            width=205,
            height=34,
            size=10
        ).pack(side="left")

        self.copy_status = tk.Label(
            copy_row,
            text="",
            bg=CARD,
            fg=GREEN,
            font=(FONT, 9, "bold")
        )
        self.copy_status.pack(side="left", padx=12)

        # HISTORY
        card = self.card(main, "04  |  LAST 5 PASSWORDS")

        self.history_list = tk.Listbox(
            card,
            height=3,
            font=(MONO, 11, "bold"),
            bg=FIELD,
            fg=AQUA,
            relief="flat",
            highlightthickness=0,
            selectbackground=PURPLE,
            selectforeground=TEXT,
            activestyle="none"
        )

        self.history_list.pack(
            fill="x",
            padx=15,
            pady=(0, 10)
        )

        # FOOTER
        tk.Label(
            main,
            text="MIDNIGHT AURORA PRO  |  OASIS INFOBYTE INTERNSHIP",
            bg=BG,
            fg=MUTED,
            font=(FONT, 8, "bold")
        ).pack(pady=(2, 5))

    # ================= VALIDATION =================

    def validate_length(self):

        try:
            value = int(self.var_length.get())
        except (ValueError, tk.TclError):
            value = 16

        self.var_length.set(
            max(MIN_LENGTH, min(MAX_LENGTH, value))
        )

    # ================= STRENGTH BAR =================

    def update_bar(self):

        self.bar.delete("all")

        width = self.bar.winfo_width()

        if width <= 1:
            return

        self.bar.create_rectangle(
            0, 0, width, 9,
            fill=FIELD, outline=FIELD
        )

        if self.score:

            fill_width = width * self.score / 100

            self.bar.create_rectangle(
                0, 0, fill_width, 9,
                fill=self.bar_color,
                outline=self.bar_color
            )

    def update_strength(self, password):

        label, color, score = password_strength(password)

        self.strength_label.config(
            text=label,
            fg=color
        )

        self.score = score
        self.bar_color = color

        self.update_bar()

    # ================= HISTORY =================

    def add_history(self, password):

        self.history.insert(0, password)
        self.history = self.history[:5]

        self.history_list.delete(0, tk.END)

        for i, item in enumerate(self.history, 1):

            self.history_list.insert(
                tk.END,
                f"{i:02d}.  {item}"
            )

    # ================= COPY STATUS =================

    def show_copied(self, text="Copied to clipboard"):

        self.copy_status.config(
            text="✓ " + text
        )

        self.after(
            2500,
            lambda: self.copy_status.config(text="")
        )

    # ================= GENERATE =================

    def on_generate(self):

        self.validate_length()

        pools = build_pools(
            self.var_upper.get(),
            self.var_lower.get(),
            self.var_digits.get(),
            self.var_symbols.get(),
            self.var_exclude.get()
        )

        try:

            password = generate_password(
                self.var_length.get(),
                pools
            )

        except ValueError as error:

            messagebox.showwarning(
                "Cannot Generate",
                str(error)
            )
            return

        self.result_var.set(password)

        self.update_strength(password)
        self.add_history(password)

        try:
            pyperclip.copy(password)
            self.show_copied("Copied automatically")

        except Exception:
            self.show_copied("Copy manually")

    # ================= MANUAL COPY =================

    def on_copy(self):

        password = self.result_var.get()

        if not password:

            messagebox.showinfo(
                "Nothing to Copy",
                "Generate a password first."
            )
            return

        try:

            pyperclip.copy(password)
            self.show_copied()

        except Exception:

            try:
                self.clipboard_clear()
                self.clipboard_append(password)
                self.update()
                self.show_copied()

            except tk.TclError:

                messagebox.showerror(
                    "Clipboard Error",
                    "Could not access clipboard."
                )


# ================= RUN =================

if __name__ == "__main__":

    app = PasswordApp()
    app.mainloop()
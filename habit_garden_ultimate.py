import json, random, threading, time
from pathlib import Path
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from plyer import notification
    NOTIFY = True
except:
    NOTIFY = False

DATA_FILE = Path("garden.json")

STAGES = [
    (0, "Seed 🌰", "#fde68a"),
    (2, "Sprout 🌱", "#bbf7d0"),
    (5, "Bush 🌿", "#86efac"),
    (9, "Tree 🌳", "#34d399"),
    (14, "Bloom 🌸", "#f9a8d4"),
]

MOTIVATION = [
    "Small steps every day build big forests.",
    "Consistency beats intensity.",
    "Your future self will thank you.",
    "One habit today = one leaf tomorrow."
]

def load_garden():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"habits": {}, "badges": [], "checkins": [], "history": []}

def save_garden(g):
    DATA_FILE.write_text(json.dumps(g, indent=2))

def stage_for(level):
    for lvl, name, color in reversed(STAGES):
        if level >= lvl:
            return name, color
    return STAGES[0][1], STAGES[0][2]

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Habit Garden — Ultimate 🌿")
        self.root.geometry("1100x650")
        self.garden = load_garden()

        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._draw_gradient()

        self.frame = tk.Frame(self.canvas, bg="#020617")
        self.window = self.canvas.create_window((0,0), window=self.frame, anchor="nw")

        self.header = tk.Frame(self.frame, bg="#020617")
        self.header.pack(fill="x", padx=20, pady=10)

        tk.Label(self.header, text="Digital Habit Garden", fg="#22c55e", bg="#020617",
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(self.header, text="Grow habits like plants 🌱", fg="#94a3b8", bg="#020617",
                 font=("Segoe UI", 11)).pack(side="left", padx=12)

        self.main = tk.Frame(self.frame, bg="#020617")
        self.main.pack(fill="both", expand=True, padx=20, pady=10)

        self.left = tk.Frame(self.main, bg="#020617")
        self.left.pack(side="left", fill="both", expand=True)

        self.right = tk.Frame(self.main, bg="#020617")
        self.right.pack(side="right", fill="y", padx=(10,0))

        self.cards = tk.Frame(self.left, bg="#020617")
        self.cards.pack(fill="both", expand=True)

        self.chart_frame = tk.Frame(self.left, bg="#020617")
        self.chart_frame.pack(fill="x", pady=(10,0))

        self._buttons()
        self.render()
        self._start_reminders()

        self.canvas.bind("<Configure>", self._resize)

    def _draw_gradient(self):
        self.canvas.delete("grad")
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        for i in range(0, h, 2):
            color = f"#{int(2 + i*0.02)%16:01x}1{int(4 + i*0.01)%16:01x}6"
            self.canvas.create_rectangle(0, i, w, i+2, fill=color, outline="", tags="grad")

    def _resize(self, e):
        self.canvas.coords(self.window, 0, 0)
        self.canvas.itemconfig(self.window, width=e.width)
        self._draw_gradient()

    def _buttons(self):
        def btn(text, cmd, color="#22c55e"):
            b = tk.Button(self.right, text=text, command=cmd, bg=color, fg="#020617",
                          font=("Segoe UI", 11, "bold"), relief="flat", padx=14, pady=10)
            b.pack(fill="x", pady=6)
        btn("🌱 Add Habit", self.add_habit)
        btn("💧 Mark Done", self.mark_done)
        btn("📊 Weekly Chart", self.show_chart, color="#38bdf8")
        btn("💾 Save", self.save)
        btn("❌ Exit", self.root.quit, color="#ef4444")

    def render(self):
        for w in self.cards.winfo_children():
            w.destroy()
        for name, h in self.garden["habits"].items():
            stage, color = stage_for(h["level"])
            card = tk.Frame(self.cards, bg=color, bd=0)
            card.pack(fill="x", pady=8, padx=8)
            tk.Label(card, text=name, bg=color, fg="#020617", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=10, pady=(8,0))
            tk.Label(card, text=f"{stage} | Level {h['level']} | Streak {h.get('streak',0)}",
                     bg=color, fg="#020617", font=("Segoe UI", 10)).pack(anchor="w", padx=10, pady=(0,8))

    def add_habit(self):
        name = simpledialog.askstring("Add Habit", "Habit name:")
        if not name: return
        if name in self.garden["habits"]:
            messagebox.showerror("Error", "Habit exists.")
            return
        self.garden["habits"][name] = {"level": 0, "streak": 0, "last_done": None}
        self.render()

    def mark_done(self):
        if not self.garden["habits"]:
            return
        name = simpledialog.askstring("Mark Done", "Which habit?")
        if not name or name not in self.garden["habits"]:
            messagebox.showerror("Error", "Habit not found.")
            return
        h = self.garden["habits"][name]
        today = date.today().isoformat()
        if h["last_done"] == today:
            messagebox.showinfo("Info", "Already done today 🌿")
            return
        growth = 1 + random.choice([0,1])
        h["level"] += growth
        h["streak"] = h["streak"] + 1 if h["last_done"] else 1
        h["last_done"] = today
        self.garden.setdefault("history", []).append({"date": today, "habit": name, "delta": growth})
        if NOTIFY:
            notification.notify(title="Habit Garden", message=random.choice(MOTIVATION), timeout=5)
        self.render()

    def show_chart(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()
        data = {}
        for item in self.garden.get("history", []):
            data[item["date"]] = data.get(item["date"], 0) + item["delta"]
        if not data:
            messagebox.showinfo("No data", "No history yet.")
            return
        dates = list(data.keys())[-7:]
        values = [data[d] for d in dates]

        fig = Figure(figsize=(5,2.5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, values)
        ax.set_title("Weekly Growth")
        ax.set_ylabel("Growth")

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x")

    def save(self):
        save_garden(self.garden)
        messagebox.showinfo("Saved", "Garden saved 💾")

    def _start_reminders(self):
        if not NOTIFY: return
        def loop():
            while True:
                time.sleep(60*60*6)  # every 6 hours
                notification.notify(title="Habit Garden", message="Time to water your plants 🌱", timeout=5)
        threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

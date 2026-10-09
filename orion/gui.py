"""O.R.I.O.N. HUD — a small Tkinter window built around the O.R.I.O.N. artwork.

Tk must own the main thread, so the assistant runs in a worker thread and
the two sides talk through queues. Typed commands work alongside voice.
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path

from . import DISPLAY_NAME

ASSETS = Path(__file__).resolve().parent / "assets"

# Palette sampled from the O.R.I.O.N. cover: deep space navy, electric blue, chrome.
BG = "#050b1a"
PANEL = "#0a1530"
CHROME = "#dfe6f2"
BLUE = "#3aa0ff"
MUTED = "#6b7a99"
STATE_COLORS = {"listening": BLUE, "thinking": "#ffc14d", "speaking": "#7cf2c8", "idle": MUTED}


class HudUI:
    def __init__(self) -> None:
        self._events: queue.Queue = queue.Queue()
        self._typed: queue.Queue[str] = queue.Queue()
        self._closed = threading.Event()
        self._state = "idle"
        self._pulse = 0

        self.root = tk.Tk()
        self.root.title(f"{DISPLAY_NAME} — AI Voice Assistant")
        self.root.configure(bg=BG)
        self.root.geometry("440x780")
        self.root.minsize(380, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._build()

    # -------------------------------------------------------------- layout

    def _build(self) -> None:
        font = ("Helvetica", 11)
        try:
            self._icon = tk.PhotoImage(file=str(ASSETS / "orion_icon.png"))
            self.root.iconphoto(True, self._icon)
            self._logo = tk.PhotoImage(file=str(ASSETS / "orion_logo.png"))
            tk.Label(self.root, image=self._logo, bg=BG, bd=0).pack(pady=(12, 4))
        except tk.TclError:  # image support missing: fall back to a text title
            tk.Label(self.root, text=DISPLAY_NAME, fg=CHROME, bg=BG,
                     font=("Helvetica", 30, "bold")).pack(pady=(20, 0))
            tk.Label(self.root, text="A I   V O I C E   A S S I S T A N T", fg=BLUE, bg=BG,
                     font=("Helvetica", 11)).pack()

        status_row = tk.Frame(self.root, bg=BG)
        status_row.pack(fill="x", padx=16, pady=(6, 4))
        self.dot = tk.Canvas(status_row, width=16, height=16, bg=BG, highlightthickness=0)
        self.dot.pack(side="left")
        self._dot_id = self.dot.create_oval(3, 3, 13, 13, fill=MUTED, outline="")
        self.status_label = tk.Label(status_row, text="", fg=CHROME, bg=BG, font=font, anchor="w")
        self.status_label.pack(side="left", padx=8)

        # Bottom widgets are packed first so the transcript, which expands,
        # never pushes them out of a small window.
        tk.Label(self.root, text="Powered by AMG · Ascension Media Group", fg=MUTED, bg=BG,
                 font=("Helvetica", 9)).pack(side="bottom", pady=(4, 10))

        entry_row = tk.Frame(self.root, bg=BG)
        entry_row.pack(side="bottom", fill="x", padx=16, pady=(6, 4))
        self.entry = tk.Entry(entry_row, bg=PANEL, fg=CHROME, insertbackground=CHROME, font=font,
                              relief="flat", highlightbackground="#1c2c55", highlightcolor=BLUE,
                              highlightthickness=1)
        self.entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.entry.bind("<Return>", self._submit)
        tk.Button(entry_row, text="Send", command=self._submit, bg=BLUE, fg="white",
                  activebackground="#1f7fe0", relief="flat", padx=14).pack(side="left", padx=(8, 0))

        log_frame = tk.Frame(self.root, bg=PANEL, highlightbackground="#1c2c55", highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=16, pady=4)
        scroll = tk.Scrollbar(log_frame)
        scroll.pack(side="right", fill="y")
        self.log_box = tk.Text(log_frame, height=8, bg=PANEL, fg=CHROME, font=font, wrap="word", bd=0,
                               padx=10, pady=8, state="disabled", yscrollcommand=scroll.set,
                               highlightthickness=0)
        self.log_box.pack(fill="both", expand=True)
        scroll.config(command=self.log_box.yview)
        self.log_box.tag_configure("orion", foreground="#8fd3ff")
        self.log_box.tag_configure("user", foreground=CHROME)
        self.log_box.tag_configure("label", font=("Helvetica", 9, "bold"))
        self.log_box.tag_configure("info", foreground=MUTED)
        self.log_box.tag_configure("error", foreground="#ff8a8a")

    # ------------------------------------------- UI interface (any thread)

    def start(self) -> None:
        pass

    def status(self, text: str, state: str = "idle") -> None:
        self._events.put(("status", text, state))

    def log(self, who: str, text: str) -> None:
        self._events.put(("log", who, text))

    def read_text(self, prompt: str = "") -> str | None:
        """Block the worker until a command is typed; None when the window closes."""
        while not self._closed.is_set():
            try:
                return self._typed.get(timeout=0.2)
            except queue.Empty:
                continue
        return None

    def poll_text(self) -> str | None:
        try:
            return self._typed.get_nowait()
        except queue.Empty:
            return None

    @property
    def closed(self) -> bool:
        return self._closed.is_set()

    def close(self) -> None:
        if self._closed.is_set():
            return
        self._closed.set()
        self.root.destroy()

    # -------------------------------------------------- Tk thread internals

    def _submit(self, _event=None) -> None:
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, "end")
            self._typed.put(text)

    def _append(self, who: str, text: str) -> None:
        self.log_box.configure(state="normal")
        if who in ("orion", "user"):
            label = DISPLAY_NAME if who == "orion" else "YOU"
            self.log_box.insert("end", f"{label}\n", (who, "label"))
            self.log_box.insert("end", f"{text}\n\n", who)
        else:
            self.log_box.insert("end", f"{text}\n\n", who)
        self.log_box.configure(state="disabled")
        self.log_box.see("end")

    def _drain(self) -> None:
        while True:
            try:
                kind, a, b = self._events.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                self.status_label.configure(text=a)
                self._state = b
            elif kind == "log":
                self._append(a, b)
            elif kind == "quit":
                self.root.after(1500, self.close)

    def _tick(self) -> None:
        if self._closed.is_set():
            return
        self._drain()
        # Gentle pulse on the status light while active.
        self._pulse = (self._pulse + 1) % 20
        color = STATE_COLORS.get(self._state, MUTED)
        size = 3 if self._state == "idle" or self._pulse < 10 else 1
        self.dot.coords(self._dot_id, size, size, 16 - size, 16 - size)
        self.dot.itemconfigure(self._dot_id, fill=color)
        self.root.after(60, self._tick)

    def run(self, worker) -> None:
        """Run ``worker()`` in the background and the window in this thread."""
        def target():
            try:
                worker()
            finally:
                self._events.put(("quit", None, None))

        threading.Thread(target=target, daemon=True, name="orion-assistant").start()
        self.entry.focus_set()
        self._tick()
        self.root.mainloop()
        self._closed.set()  # window closed: let the worker's loop finish

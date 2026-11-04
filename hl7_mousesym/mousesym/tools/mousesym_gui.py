#!/usr/bin/env python3
"""
mousesym_gui.py – grafikus tesztprogram a Mousesym egérvezérlőhöz.

Csak a Python standard könyvtárát használja (tkinter), Windows-on a
python.org-os telepítő része. Indítás:

    python mousesym_gui.py
    (vagy dupla kattintás a fájlon / mousesym_gui.pyw néven konzolablak nélkül)

Funkciók:
  * kapcsolódás (IP, port, parancskulcs – HMAC hitelesítés)
  * "képernyő" mező: kattintásra mozgatás / bal / jobb / dupla / középső
    kattintás az adott százalékos helyre, húzás mód, görgő
  * koordináták kézi megadása, gyorsgombok (sarkok, közép)
  * gomb lenyomás / felengedés, egyedi kattintási idő
  * beépített tesztsorozatok (sarkok, kattintások, beragadt gomb, hibás parancsok)
  * szabad parancs küldése, automatikus STATUS-frissítés, napló

A hálózati forgalom külön szálon fut, így az ablak sosem fagy le.
"""
import json
import os
import queue
import socket
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mousesym_client import MousesymClient, MousesymError  # noqa: E402

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".mousesym_gui.json")
ASPECTS = {"16:9": 16 / 9, "16:10": 16 / 10, "4:3": 4 / 3, "21:9": 21 / 9, "5:4": 5 / 4}
MODES = [("move", "Mozgatás"), ("click", "Bal katt."), ("rclick", "Jobb katt."),
         ("dbl", "Dupla katt."), ("mclick", "Középső"), ("drag", "Húzás")]


# =========================================================================
# Hálózati munkaszál
# =========================================================================
class Worker(threading.Thread):
    """Egyetlen szál birtokolja a TCP-kapcsolatot; a GUI feladatokat küld neki."""

    def __init__(self, events):
        super().__init__(daemon=True)
        self.jobs = queue.Queue()
        self.events = events          # (típus, adat) üzenetek a GUI felé
        self.client = None
        self.params = None
        self.drag_lock = threading.Lock()
        self.drag_pos = None
        self.drag_pending = False
        self.stop_test = threading.Event()

    # ---- GUI oldali API ----------------------------------------------
    def submit(self, fn, *args):
        self.jobs.put((fn, args))

    def send(self, cmd):
        self.submit(self._cmd, cmd)

    def drag_move(self, x, y):
        """Húzás közbeni mozgás: csak a legutolsó pozíció megy ki (összevonás)."""
        with self.drag_lock:
            self.drag_pos = (x, y)
            if self.drag_pending:
                return
            self.drag_pending = True
        self.submit(self._flush_drag)

    # ---- szál oldal ---------------------------------------------------
    def emit(self, kind, data=None):
        self.events.put((kind, data))

    def run(self):
        while True:
            fn, args = self.jobs.get()
            try:
                fn(*args)
            except (OSError, MousesymError) as e:
                self.emit("log", ("err", f"Kapcsolati hiba: {e}"))
                self._drop()
            except Exception as e:  # programhiba: ne álljon le a szál
                self.emit("log", ("err", f"Belső hiba: {e!r}"))

    def _drop(self):
        if self.client:
            try:
                self.client.sock.close()
            except Exception:
                pass
        self.client = None
        self.emit("state", False)

    def _connect(self, host, port, key):
        self._disconnect(quiet=True)
        self.params = (host, port, key)
        self.emit("log", ("info", f"Kapcsolódás: {host}:{port} ..."))
        c = MousesymClient(host, port, key, timeout=4.0, verbose=False)
        c.connect(authenticate=False)
        try:
            c.auth()
        except MousesymError as e:
            c.sock.close()
            self.emit("log", ("err", f"{e} – ellenőrizd a kulcsot"))
            self.emit("state", False)
            return
        self.client = c
        self.emit("log", ("ok", "Kapcsolódva, hitelesítve"))
        self.emit("state", True)
        self._cmd("STATUS")

    def _disconnect(self, quiet=False):
        if self.client:
            try:
                self.client.command("QUIT")
            except Exception:
                pass
            self._drop()
            if not quiet:
                self.emit("log", ("info", "Kapcsolat bontva"))

    def _cmd(self, cmd, log=True):
        if not self.client:
            self.emit("log", ("err", f"Nincs kapcsolat – nem küldhető: {cmd}"))
            return None
        t0 = time.perf_counter()
        resp = self.client.command(cmd)
        ms = (time.perf_counter() - t0) * 1000
        if resp.startswith("OK USB="):
            self.emit("status", resp)
        if log:
            self.emit("log", ("ok" if resp.startswith("OK") else "err", f"{cmd}  →  {resp}   ({ms:.0f} ms)"))
        return resp

    def _flush_drag(self):
        with self.drag_lock:
            pos = self.drag_pos
            self.drag_pending = False
        if pos and self.client:
            self._cmd(f"MOVE {pos[0]} {pos[1]}", log=False)

    # ---- tesztsorozatok ----------------------------------------------
    def _sleep(self, s):
        return self.stop_test.wait(s)   # True, ha megszakították

    def _test(self, name, pause):
        self.stop_test.clear()
        self.emit("log", ("info", f"=== Teszt indul: {name}"))
        self.emit("testing", True)
        ok = True
        try:
            ok = getattr(self, "_t_" + name)(pause)
        finally:
            self.emit("testing", False)
        if self.stop_test.is_set():
            self.emit("log", ("err", f"=== Teszt megszakítva: {name}"))
            if self.client:
                self._cmd("STATUS")
        else:
            self.emit("log", ("ok" if ok else "err", f"=== Teszt {'SIKERES' if ok else 'HIBÁS'}: {name}"))

    def _expect(self, cmd, prefix="OK"):
        r = self._cmd(cmd)
        return r is not None and r.startswith(prefix)

    def _t_corners(self, pause):
        ok = True
        for x, y in [(5000, 5000), (0, 0), (10000, 0), (10000, 10000), (0, 10000), (5000, 5000)]:
            ok &= self._expect(f"MOVE {x} {y}")
            if self._sleep(pause):
                break
        return ok

    def _t_clicks(self, pause):
        ok = True
        for cmd in ["CLICK 5000 5000", "RCLICK 5000 5000", "CLICK 5000 5000", "DBLCLICK 5000 5000",
                    "CLICK 5000 5000 300", "DOWN LEFT 4000 4000", "MOVE 6000 6000", "UP LEFT"]:
            ok &= self._expect(cmd)
            if self._sleep(pause):
                self._cmd("UP LEFT")
                break
        return ok and self._expect("STATUS", "OK USB=CONNECTED BUTTONS=NONE")

    def _t_stuck(self, pause):
        if not self._expect("DOWN LEFT 5000 5000"):
            return False
        self._expect("STATUS", "OK USB=CONNECTED BUTTONS=L")
        self.emit("log", ("info", "Kapcsolat megszakítása RST-vel, a bal gomb lenyomva..."))
        self.client.abort()
        self.client = None
        self.emit("state", False)
        time.sleep(1.0)
        self._connect(*self.params)
        ok = self._expect("STATUS", "OK USB=CONNECTED BUTTONS=NONE")
        self.emit("log", ("ok" if ok else "err",
                          "A firmware felengedte a gombot" if ok else "A gomb NEM engedett fel!"))
        return ok

    def _t_errors(self, pause):
        cases = [("FOO", "ERROR INVALID_COMMAND"), ("CLICK", "ERROR INVALID_COMMAND"),
                 ("CLICK 10001 5000", "ERROR INVALID_COORDINATE"), ("CLICK -1 0", "ERROR INVALID_COORDINATE"),
                 ("MOVE abc def", "ERROR INVALID_COORDINATE"), ("DOWN SIDEWAYS", "ERROR INVALID_COMMAND"),
                 ("CLICK 1 2 3 4 5", "ERROR INVALID_COMMAND")]
        ok = True
        for cmd, want in cases:
            r = self._cmd(cmd)
            if r != want:
                self.emit("log", ("err", f"   várt: {want}"))
                ok = False
        return ok and self._expect("PING")


# =========================================================================
# GUI
# =========================================================================
class App:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.worker = Worker(self.events)
        self.worker.start()
        self.connected = False
        self.last_pos = None
        self.drag_active = False
        self.settings = self._load_settings()

        root.title("Mousesym tesztprogram")
        root.minsize(1000, 700)
        root.geometry("1200x800")
        self._build()
        self._set_connected(False)
        root.after(50, self._poll_events)
        root.after(2000, self._auto_status)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---- beállítások ---------------------------------------------------
    def _load_settings(self):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save_settings(self):
        data = {"host": self.v_host.get(), "port": self.v_port.get(), "aspect": self.v_aspect.get(),
                "pause": self.v_pause.get()}
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except OSError:
            pass

    # ---- felépítés -----------------------------------------------------
    def _build(self):
        s = self.settings
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Big.TButton", padding=(10, 4))

        # --- kapcsolat sáv ---
        top = ttk.Frame(self.root, padding=(10, 8))
        top.pack(fill="x")
        self.v_host = tk.StringVar(value=s.get("host", "192.168.1.200"))
        self.v_port = tk.StringVar(value=str(s.get("port", "5000")))
        self.v_key = tk.StringVar(value=os.environ.get("MOUSESYM_KEY", ""))
        ttk.Label(top, text="IP-cím:").pack(side="left")
        ttk.Entry(top, textvariable=self.v_host, width=16).pack(side="left", padx=(4, 12))
        ttk.Label(top, text="Port:").pack(side="left")
        ttk.Entry(top, textvariable=self.v_port, width=6).pack(side="left", padx=(4, 12))
        ttk.Label(top, text="Kulcs:").pack(side="left")
        e_key = ttk.Entry(top, textvariable=self.v_key, width=18, show="•")
        e_key.pack(side="left", padx=(4, 12))
        e_key.bind("<Return>", lambda e: self._toggle_connect())
        self.b_conn = ttk.Button(top, text="Kapcsolódás", style="Big.TButton", command=self._toggle_connect)
        self.b_conn.pack(side="left")
        self.l_state = tk.Label(top, text="●  Nincs kapcsolat", fg="#b42318", font=("Segoe UI", 10, "bold"))
        self.l_state.pack(side="left", padx=14)

        # --- állapot sáv ---
        st = ttk.Frame(self.root, padding=(10, 0))
        st.pack(fill="x")
        self.v_status = tk.StringVar(value="USB: –   Gombok: –   Pozíció: –   IP: –")
        ttk.Label(st, textvariable=self.v_status, foreground="#475467").pack(side="left")
        self.v_auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(st, text="Állapot automatikus frissítése", variable=self.v_auto).pack(side="right")

        # --- napló ---
        lf = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        lf.pack(side="bottom", fill="x")
        self.log = tk.Text(lf, height=8, font=("Consolas", 9), bg="#0f1720", fg="#d0d5dd",
                           insertbackground="white", state="disabled", wrap="none")
        sb = ttk.Scrollbar(lf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.log.tag_configure("ok", foreground="#6ce9a6")
        self.log.tag_configure("err", foreground="#fda29b")
        self.log.tag_configure("info", foreground="#84caff")

        c = ttk.Frame(self.root, padding=(10, 0, 10, 4))
        c.pack(side="bottom", fill="x")
        ttk.Label(c, text="Szabad parancs:").pack(side="left")
        self.v_free = tk.StringVar()
        e = ttk.Entry(c, textvariable=self.v_free, width=40)
        e.pack(side="left", padx=4)
        e.bind("<Return>", lambda ev: self._send_free())
        ttk.Button(c, text="Küldés", command=self._send_free).pack(side="left")
        ttk.Button(c, text="STATUS lekérdezés", command=lambda: self._send("STATUS")).pack(side="left", padx=8)
        ttk.Button(c, text="Napló törlése", command=self._clear_log).pack(side="right")

        body = ttk.Frame(self.root, padding=10)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        # --- bal: képernyő-mező ---
        left = ttk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        bar = ttk.Frame(left)
        bar.pack(fill="x")
        self.v_mode = tk.StringVar(value="move")
        for val, txt in MODES:
            ttk.Radiobutton(bar, text=txt, value=val, variable=self.v_mode).pack(side="left", padx=(0, 8))
        self.v_aspect = tk.StringVar(value=s.get("aspect", "16:9"))
        cb = ttk.Combobox(bar, textvariable=self.v_aspect, values=list(ASPECTS), width=6, state="readonly")
        cb.pack(side="right")
        cb.bind("<<ComboboxSelected>>", lambda e: self._redraw())
        ttk.Label(bar, text="Képarány:").pack(side="right", padx=4)

        self.canvas = tk.Canvas(left, bg="#1e2a38", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True, pady=(6, 4))
        self.canvas.bind("<Configure>", lambda e: self._redraw())
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", lambda e: self.v_hover.set(""))
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_wheel)                       # Windows
        self.canvas.bind("<Button-4>", lambda e: self._wheel(1))               # Linux
        self.canvas.bind("<Button-5>", lambda e: self._wheel(-1))
        self.v_hover = tk.StringVar()
        info = ttk.Frame(left)
        info.pack(fill="x")
        ttk.Label(info, text="A mező a vezérelt gép képernyőjét jelképezi. Kattints a kiválasztott művelethez; "
                             "görgő = SCROLL.", foreground="#667085").pack(side="left")
        ttk.Label(info, textvariable=self.v_hover, font=("Consolas", 10)).pack(side="right")

        # --- jobb: vezérlők ---
        right = ttk.Frame(body, width=300)
        right.grid(row=0, column=1, sticky="ns")

        g = ttk.LabelFrame(right, text="Koordináta (0–10000)", padding=8)
        g.pack(fill="x")
        self.v_x = tk.IntVar(value=5000)
        self.v_y = tk.IntVar(value=5000)
        ttk.Label(g, text="X").grid(row=0, column=0)
        ttk.Spinbox(g, from_=0, to=10000, increment=100, textvariable=self.v_x, width=7).grid(row=0, column=1, padx=4)
        ttk.Label(g, text="Y").grid(row=0, column=2)
        ttk.Spinbox(g, from_=0, to=10000, increment=100, textvariable=self.v_y, width=7).grid(row=0, column=3, padx=4)
        bf = ttk.Frame(g)
        bf.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        for i, cmd in enumerate(["MOVE", "CLICK", "RCLICK", "DBLCLICK", "MCLICK"]):
            ttk.Button(bf, text=cmd, width=9, command=lambda c=cmd: self._xy_cmd(c)).grid(
                row=i // 3, column=i % 3, sticky="ew", padx=1, pady=1)
        self.v_hold_on = tk.BooleanVar(value=False)
        self.v_hold = tk.IntVar(value=100)
        hf = ttk.Frame(g)
        hf.grid(row=3, column=0, columnspan=4, sticky="w", pady=(4, 0))
        ttk.Checkbutton(hf, text="Egyedi kattintási idő (ms):", variable=self.v_hold_on).pack(side="left")
        ttk.Spinbox(hf, from_=10, to=2000, increment=10, textvariable=self.v_hold, width=6).pack(side="left", padx=4)

        q = ttk.LabelFrame(right, text="Gyorsgombok (mozgatás)", padding=8)
        q.pack(fill="x", pady=(8, 0))
        for (txt, x, y, r, c) in [("↖ Bal felső", 0, 0, 0, 0), ("↗ Jobb felső", 10000, 0, 0, 2),
                                  ("● Közép", 5000, 5000, 1, 1),
                                  ("↙ Bal alsó", 0, 10000, 2, 0), ("↘ Jobb alsó", 10000, 10000, 2, 2)]:
            ttk.Button(q, text=txt, command=lambda x=x, y=y: self._send_pos("MOVE", x, y)).grid(
                row=r, column=c, sticky="ew", padx=1, pady=1)

        b = ttk.LabelFrame(right, text="Gombok", padding=8)
        b.pack(fill="x", pady=(8, 0))
        for i, btn in enumerate(["LEFT", "RIGHT", "MIDDLE"]):
            ttk.Label(b, text={"LEFT": "Bal", "RIGHT": "Jobb", "MIDDLE": "Középső"}[btn]).grid(row=i, column=0, sticky="w")
            ttk.Button(b, text="Lenyom", command=lambda bt=btn: self._send(f"DOWN {bt}")).grid(row=i, column=1, padx=2)
            ttk.Button(b, text="Felenged", command=lambda bt=btn: self._send(f"UP {bt}")).grid(row=i, column=2, padx=2)
        ttk.Button(b, text="Görgő ▲", command=lambda: self._wheel(3)).grid(row=3, column=1, pady=(4, 0))
        ttk.Button(b, text="Görgő ▼", command=lambda: self._wheel(-3)).grid(row=3, column=2, pady=(4, 0))

        t = ttk.LabelFrame(right, text="Tesztsorozatok", padding=8)
        t.pack(fill="x", pady=(8, 0))
        self.test_buttons = []
        for i, (name, txt) in enumerate([("corners", "Sarkok"), ("clicks", "Kattintások"),
                                         ("stuck", "Beragadt gomb"), ("errors", "Hibás parancsok")]):
            bt = ttk.Button(t, text=txt, command=lambda n=name: self._run_test(n))
            bt.grid(row=i // 2, column=i % 2, sticky="ew", padx=1, pady=1)
            self.test_buttons.append(bt)
        pf = ttk.Frame(t)
        pf.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Label(pf, text="Szünet (s):").pack(side="left")
        self.v_pause = tk.DoubleVar(value=float(s.get("pause", 1.0)))
        ttk.Spinbox(pf, from_=0.1, to=10, increment=0.5, textvariable=self.v_pause, width=5).pack(side="left", padx=4)
        self.b_stop = ttk.Button(pf, text="Leállítás", command=self.worker.stop_test.set, state="disabled")
        self.b_stop.pack(side="left", padx=6)



    # ---- képernyő-mező -------------------------------------------------
    def _pad_rect(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        ar = ASPECTS.get(self.v_aspect.get(), 16 / 9)
        pw, ph = w - 20, (w - 20) / ar
        if ph > h - 20:
            ph, pw = h - 20, (h - 20) * ar
        x0, y0 = (w - pw) / 2, (h - ph) / 2
        return x0, y0, pw, ph

    def _redraw(self):
        cv = self.canvas
        cv.delete("all")
        x0, y0, pw, ph = self._pad_rect()
        if pw < 10 or ph < 10:
            return
        cv.create_rectangle(x0, y0, x0 + pw, y0 + ph, fill="#f8fafc", outline="#2f6fed", width=2)
        for i in range(1, 10):
            col = "#cbd5e1" if i == 5 else "#e2e8f0"
            cv.create_line(x0 + pw * i / 10, y0, x0 + pw * i / 10, y0 + ph, fill=col)
            cv.create_line(x0, y0 + ph * i / 10, x0 + pw, y0 + ph * i / 10, fill=col)
        cv.create_text(x0 + 4, y0 + 2, text="0,0", anchor="nw", fill="#94a3b8", font=("Segoe UI", 8))
        cv.create_text(x0 + pw - 4, y0 + ph - 2, text="10000,10000", anchor="se", fill="#94a3b8", font=("Segoe UI", 8))
        if self.last_pos:
            self._draw_marker(*self.last_pos)

    def _draw_marker(self, x, y):
        self.canvas.delete("marker")
        x0, y0, pw, ph = self._pad_rect()
        px, py = x0 + pw * x / 10000, y0 + ph * y / 10000
        self.canvas.create_oval(px - 6, py - 6, px + 6, py + 6, outline="#dc2626", width=2, tags="marker")
        self.canvas.create_line(px - 10, py, px + 10, py, fill="#dc2626", tags="marker")
        self.canvas.create_line(px, py - 10, px, py + 10, fill="#dc2626", tags="marker")

    def _to_pct(self, ev):
        x0, y0, pw, ph = self._pad_rect()
        x = round((ev.x - x0) / pw * 10000)
        y = round((ev.y - y0) / ph * 10000)
        return max(0, min(10000, x)), max(0, min(10000, y)), (0 <= ev.x - x0 <= pw and 0 <= ev.y - y0 <= ph)

    def _on_motion(self, ev):
        x, y, inside = self._to_pct(ev)
        self.v_hover.set(f"x={x:5d}  y={y:5d}" if inside else "")

    def _on_press(self, ev):
        x, y, inside = self._to_pct(ev)
        if not inside:
            return
        self.v_x.set(x)
        self.v_y.set(y)
        mode = self.v_mode.get()
        if mode == "drag":
            self.drag_active = True
            self._send_pos("DOWN LEFT", x, y)
        else:
            self._send_pos({"move": "MOVE", "click": "CLICK", "rclick": "RCLICK",
                            "dbl": "DBLCLICK", "mclick": "MCLICK"}[mode], x, y)

    def _on_drag(self, ev):
        self._on_motion(ev)
        if self.drag_active and self.connected:
            x, y, _ = self._to_pct(ev)
            self.last_pos = (x, y)
            self._draw_marker(x, y)
            self.worker.drag_move(x, y)

    def _on_release(self, ev):
        if self.drag_active:
            self.drag_active = False
            x, y, _ = self._to_pct(ev)
            self._send_pos("UP LEFT", x, y)

    def _on_wheel(self, ev):
        self._wheel(1 if ev.delta > 0 else -1)

    def _wheel(self, n):
        self._send(f"SCROLL {n}")

    # ---- parancsküldés -------------------------------------------------
    def _send(self, cmd):
        if not self.connected:
            self._log("err", "Előbb kapcsolódj a panelhez.")
            return
        self.worker.send(cmd)

    def _send_pos(self, cmd, x, y):
        self.last_pos = (x, y)
        self._draw_marker(x, y)
        hold = ""
        if cmd in ("CLICK", "RCLICK", "DBLCLICK", "MCLICK") and self.v_hold_on.get():
            hold = f" {self._int(self.v_hold, 100)}"
        self._send(f"{cmd} {x} {y}{hold}")

    @staticmethod
    def _int(var, default):
        try:
            return int(var.get())
        except (tk.TclError, ValueError):
            return default

    def _xy_cmd(self, cmd):
        x, y = self._int(self.v_x, -1), self._int(self.v_y, -1)
        if not (0 <= x <= 10000 and 0 <= y <= 10000):
            messagebox.showwarning("Koordináta", "X és Y értéke 0 és 10000 közötti egész szám legyen.")
            return
        self._send_pos(cmd, x, y)

    def _send_free(self):
        cmd = self.v_free.get().strip()
        if cmd:
            self._send(cmd)
            self.v_free.set("")

    def _run_test(self, name):
        if not self.connected:
            self._log("err", "Előbb kapcsolódj a panelhez.")
            return
        if name == "clicks" and not messagebox.askokcancel(
                "Kattintásteszt", "A teszt a képernyő KÖZEPÉN kattint (jobb, bal, dupla, húzás).\n"
                                  "Nyiss meg középen egy üres Jegyzettömböt vagy Paintet.\n\nIndulhat?"):
            return
        try:
            pause = max(0.05, float(self.v_pause.get()))
        except (tk.TclError, ValueError):
            pause = 1.0
        self.worker.submit(self.worker._test, name, pause)

    def _toggle_connect(self):
        if self.connected:
            self.worker.submit(self.worker._disconnect)
            return
        host = self.v_host.get().strip()
        try:
            port = int(self.v_port.get())
        except ValueError:
            messagebox.showerror("Port", "Érvénytelen port.")
            return
        key = self.v_key.get()
        if not host or not key:
            messagebox.showerror("Kapcsolódás", "Add meg az IP-címet és a parancskulcsot.")
            return
        self._save_settings()
        self.b_conn.configure(state="disabled")
        self.worker.submit(self.worker._connect, host, port, key)

    def _auto_status(self):
        if self.connected and self.v_auto.get() and self.worker.jobs.empty() and not self.drag_active:
            self.worker.submit(self.worker._cmd, "STATUS", False)
        self.root.after(2000, self._auto_status)

    # ---- események a munkaszáltól ---------------------------------------
    def _poll_events(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "log":
                    self._log(*data)
                elif kind == "state":
                    self._set_connected(data)
                elif kind == "status":
                    self._show_status(data)
                elif kind == "testing":
                    for b in self.test_buttons:
                        b.configure(state="disabled" if data else "normal")
                    self.b_stop.configure(state="normal" if data else "disabled")
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    def _set_connected(self, on):
        self.connected = on
        self.b_conn.configure(state="normal", text="Bontás" if on else "Kapcsolódás")
        self.l_state.configure(text="●  Kapcsolódva" if on else "●  Nincs kapcsolat",
                               fg="#027a48" if on else "#b42318")
        if not on:
            self.v_status.set("USB: –   Gombok: –   Pozíció: –   IP: –")

    def _show_status(self, line):
        f = dict(p.split("=", 1) for p in line.split()[1:] if "=" in p)
        usb = {"CONNECTED": "csatlakoztatva", "NOT_CONNECTED": "NINCS", "SUSPENDED": "felfüggesztve"}.get(
            f.get("USB", ""), f.get("USB", "?"))
        btn = f.get("BUTTONS", "?")
        btn = "nincs" if btn == "NONE" else btn
        self.v_status.set(f"USB: {usb}    Gombok: {btn}    Pozíció: {f.get('POS', '?')}    "
                          f"Kattintás: {f.get('CLICK_MS', '?')} ms    IP: {f.get('IP', '?')} ({f.get('MODE', '?')})    "
                          f"FW: {f.get('FW', '?')}")
        pos = f.get("POS", "")
        if "," in pos and not self.drag_active:
            try:
                x, y = (int(v) for v in pos.split(","))
                self.last_pos = (x, y)
                self._draw_marker(x, y)
            except ValueError:
                pass

    def _log(self, tag, text):
        self.log.configure(state="normal")
        self.log.insert("end", time.strftime("%H:%M:%S  ") + text + "\n", tag)
        lines = int(self.log.index("end-1c").split(".")[0])
        if lines > 2000:
            self.log.delete("1.0", f"{lines - 2000}.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _on_close(self):
        self._save_settings()
        if self.connected:
            self.worker.submit(self.worker._disconnect)
            self.root.after(300, self.root.destroy)
        else:
            self.root.destroy()


def main():
    try:  # éles megjelenítés nagy DPI-n (Windows); a Tk létrehozása előtt kell
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()

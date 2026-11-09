#!/usr/bin/env python3
"""
win_verify.py – automatikus pozíció- és kattintás-ellenőrzés a VEZÉRELT
Windows 10/11 gépen futtatva (az USB-n a Mousesym panel csatlakozik, a gép
hálózaton eléri a panelt).

Csak standard könyvtár (ctypes, tkinter). Python 3.8+ Windows-on.

  python win_verify.py --host 192.168.1.50 --key <kulcs> position
  python win_verify.py --host 192.168.1.50 --key <kulcs> clicks --count 50

position:
  MOVE parancsokat küld (közép, 4 sarok, 11x11-es rács), minden után
  GetCursorPos()-szal kiolvassa a kurzor valós helyét FIZIKAI pixelben
  (per-monitor DPI-tudatos folyamat), és összeveti a várt értékkel.
  Kiírja, hogy a leképezés az elsődleges monitorra vagy a teljes
  virtuális asztalra illeszkedik-e.

clicks:
  Teljes képernyős (elsődleges monitor) célablakot nyit, véletlen helyekre
  CLICK / RCLICK / DBLCLICK parancsokat küld, és megszámolja, hogy az
  ablak pontosan ugyanannyi és ugyanolyan eseményt kapott-e, a várt helyen.

Ismételd meg a "position" tesztet 100%, 125% és 150% kijelző-skálázással,
valamint felbontásváltás után (docs/TESTING_WINDOWS.md).
"""
import argparse
import ctypes
import os
import random
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mousesym_client import MousesymClient  # noqa: E402

if sys.platform != "win32":
    sys.exit("Ezt a szkriptet a vezérelt Windows gépen kell futtatni.")

user32 = ctypes.windll.user32

# Per-monitor DPI-tudatosság: minden koordináta fizikai pixelben
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def cursor():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return p.x, p.y


def screens():
    prim = (0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))          # SM_CX/CYSCREEN
    virt = (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77),               # SM_X/YVIRTUALSCREEN
            user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))               # SM_CX/CYVIRTUALSCREEN
    return prim, virt


def expected(pct, origin, size):
    """A firmware + Windows leképezés modellje (src/coord_map.h)."""
    hid = (pct * 32767 + 5000) // 10000
    norm = hid * 65535 // 32767
    return origin + (norm * size >> 16)


def test_position(c, tol, settle):
    prim, virt = screens()
    print(f"Elsődleges monitor: {prim[2]}x{prim[3]} px, virtuális asztal: {virt}")
    dpi = user32.GetDpiForSystem() if hasattr(user32, "GetDpiForSystem") else 96
    print(f"Rendszer DPI: {dpi} ({dpi * 100 // 96}% skálázás)")

    pts = [(5000, 5000), (0, 0), (10000, 0), (0, 10000), (10000, 10000)]
    pts += [(x * 1000, y * 1000) for x in range(11) for y in range(11)]
    worst = {"primary": 0, "virtual": 0}
    fails = 0
    for x, y in pts:
        resp = c.command(f"MOVE {x} {y}")
        if resp != "OK":
            print(f"  MOVE {x} {y}: {resp}")
            fails += 1
            continue
        time.sleep(settle)
        cx, cy = cursor()
        for name, (ox, oy, w, h) in (("primary", prim), ("virtual", virt)):
            ex, ey = expected(x, ox, w), expected(y, oy, h)
            worst[name] = max(worst[name], abs(cx - ex), abs(cy - ey))
        ex, ey = expected(x, prim[0], prim[2]), expected(y, prim[1], prim[3])
        flag = "" if abs(cx - ex) <= tol and abs(cy - ey) <= tol else "  <-- ELTÉRÉS"
        if (x, y) in pts[:5] or flag:
            print(f"  {x:5d},{y:5d} -> kurzor {cx:5d},{cy:5d}  várt (elsődleges) {ex:5d},{ey:5d}{flag}")
        if flag:
            fails += 1

    mapping = "elsődleges monitor" if worst["primary"] <= worst["virtual"] else "teljes virtuális asztal"
    print(f"Legnagyobb eltérés: elsődleges={worst['primary']} px, virtuális={worst['virtual']} px")
    print(f"A leképezés erre illeszkedik: {mapping}")
    ok = fails == 0
    print("EREDMÉNY:", "MEGFELELT" if ok else f"HIBA ({fails} pont tolerancián kívül, tol={tol} px)")
    return ok


def test_clicks(c, count, tol):
    import tkinter as tk

    prim, _ = screens()
    W, H = prim[2], prim[3]
    events = []
    plan = []
    done = threading.Event()

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg="#203040", cursor="crosshair")
    lbl = tk.Label(root, text="Mousesym kattintásteszt – ne nyúlj az egérhez", fg="white", bg="#203040",
                   font=("Segoe UI", 20))
    lbl.place(relx=0.5, rely=0.05, anchor="n")

    def rec(kind):
        return lambda e: events.append((kind, e.x_root, e.y_root))

    root.bind("<ButtonPress-1>", rec("L"))
    root.bind("<ButtonPress-3>", rec("R"))
    # Tk-ban egy dupla kattintás második lenyomása a <Double-Button-1>
    # kötést váltja ki (a specifikusabbat), így: dupla = "L" + "D".
    root.bind("<Double-Button-1>", rec("D"))

    rnd = random.Random(42)

    def worker():
        time.sleep(1.5)     # ablak megjelenése
        for i in range(count):
            kind = rnd.choice(["CLICK", "CLICK", "RCLICK", "DBLCLICK"])
            x, y = rnd.randint(500, 9500), rnd.randint(1500, 9500)
            plan.append((kind, x, y))
            if c.command(f"{kind} {x} {y}") != "OK":
                plan[-1] = ("FAIL", x, y)
            if kind == "RCLICK":
                time.sleep(0.15)
            time.sleep(0.6)  # > Windows dupla-kattintási idő, hogy ne olvadjanak össze
        time.sleep(0.5)
        done.set()

    def poll():
        if done.is_set():
            root.destroy()
        else:
            root.after(100, poll)

    threading.Thread(target=worker, daemon=True).start()
    root.after(100, poll)
    root.mainloop()

    want = {"L": 0, "R": 0, "D": 0}
    for kind, _, _ in plan:
        if kind == "CLICK":
            want["L"] += 1
        elif kind == "RCLICK":
            want["R"] += 1
        elif kind == "DBLCLICK":
            want["L"] += 1      # első lenyomás
            want["D"] += 1      # második lenyomás dupla kattintásként
    got = {"L": 0, "R": 0, "D": 0}
    for kind, _, _ in events:
        got[kind] += 1
    print(f"Várt események: {want}")
    print(f"Kapott események: {got}")

    # Pozíció ellenőrzés az első lenyomás alapján parancsonként
    pos_bad = 0
    it = iter(events)   # minden rögzített esemény egy-egy gomblenyomás
    for kind, x, y in plan:
        n = 2 if kind == "DBLCLICK" else 1
        for _ in range(n):
            ev = next(it, None)
            if ev is None:
                break
            ex, ey = expected(x, 0, W), expected(y, 0, H)
            if abs(ev[1] - ex) > tol or abs(ev[2] - ey) > tol:
                pos_bad += 1
    ok = want == got and pos_bad == 0 and all(k != "FAIL" for k, _, _ in plan)
    print(f"Pozícióhibák: {pos_bad}")
    print("EREDMÉNY:", "MEGFELELT" if ok else "HIBA")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Mousesym Windows-ellenőrző")
    ap.add_argument("--host", required=True)
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--key", default=os.environ.get("MOUSESYM_KEY"))
    ap.add_argument("--tol", type=int, default=2, help="pixeltűrés")
    ap.add_argument("--settle", type=float, default=0.08, help="várakozás MOVE után (s)")
    ap.add_argument("--count", type=int, default=30, help="kattintások száma")
    ap.add_argument("test", choices=["position", "clicks"])
    a = ap.parse_args()
    if not a.key:
        import getpass
        a.key = getpass.getpass("Parancskulcs: ")

    with MousesymClient(a.host, a.port, a.key, verbose=False).connect() as c:
        ok = test_position(c, a.tol, a.settle) if a.test == "position" else test_clicks(c, a.count, a.tol)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

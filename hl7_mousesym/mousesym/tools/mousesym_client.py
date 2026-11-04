#!/usr/bin/env python3
"""
mousesym_client.py – egyszerű TCP tesztkliens a Mousesym firmware-hez.

Csak a Python standard könyvtárát használja (Python 3.8+).

Használat:
  # egy vagy több parancs
  python mousesym_client.py --host 192.168.1.50 "CLICK 5000 5000" "STATUS"

  # interaktív mód (parancsok soronként, kilépés: QUIT vagy Ctrl+C)
  python mousesym_client.py --host 192.168.1.50

  # beépített tesztsorozatok (lásd docs/TESTING_WINDOWS.md)
  python mousesym_client.py --host 192.168.1.50 --test corners
  python mousesym_client.py --host 192.168.1.50 --test clicks
  python mousesym_client.py --host 192.168.1.50 --test stuck
  python mousesym_client.py --host 192.168.1.50 --test errors
  python mousesym_client.py --host 192.168.1.50 --test stress

A parancskulcs forrása (ebben a sorrendben): --key, MOUSESYM_KEY környezeti
változó, majd interaktív bekérés.

Hitelesítés: a szerver kapcsolódáskor "HELLO MOUSESYM 1 <nonce>" sort küld,
a kliens "AUTH <hex(HMAC-SHA256(kulcs, nonce))>" sorral válaszol. A kulcs
így nem utazik a hálózaton.
"""
import argparse
import getpass
import hashlib
import hmac
import os
import socket
import sys
import time


class MousesymError(Exception):
    pass


class MousesymClient:
    def __init__(self, host, port=5000, key=None, timeout=5.0, verbose=True):
        self.host, self.port, self.key = host, port, key
        self.timeout, self.verbose = timeout, verbose
        self.sock = None
        self._buf = b""

    # ---- kapcsolat ----------------------------------------------------
    def connect(self, authenticate=True):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        hello = self._readline()
        parts = hello.split()
        if len(parts) != 4 or parts[0] != "HELLO" or parts[1] != "MOUSESYM":
            raise MousesymError(f"Váratlan üdvözlés: {hello!r}")
        self.nonce = parts[3]
        if self.verbose:
            print(f"<< {hello}")
        if authenticate:
            self.auth()
        return self

    def auth(self, key=None):
        key = key if key is not None else self.key
        mac = hmac.new(key.encode("utf-8"), self.nonce.encode("ascii"), hashlib.sha256).hexdigest()
        resp = self.command(f"AUTH {mac}", echo=">> AUTH <hmac>")
        if resp != "OK":
            raise MousesymError(f"Hitelesítés sikertelen: {resp}")
        return resp

    def close(self, graceful=True):
        if not self.sock:
            return
        try:
            if graceful:
                self.command("QUIT")
        except (OSError, MousesymError):
            pass
        finally:
            self.sock.close()
            self.sock = None

    def abort(self):
        """Kapcsolat megszakítása RST-vel (kábelhúzás / programösszeomlás szimulációja)."""
        import struct
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        self.sock.close()
        self.sock = None

    # ---- I/O ----------------------------------------------------------
    def _readline(self):
        while b"\n" not in self._buf:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise MousesymError("A szerver bontotta a kapcsolatot")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return line.decode("ascii", "replace").rstrip("\r")

    def command(self, cmd, echo=None):
        if self.verbose:
            print(echo or f">> {cmd}")
        self.sock.sendall(cmd.encode("ascii") + b"\n")
        resp = self._readline()
        if self.verbose:
            print(f"<< {resp}")
        return resp

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# =========================================================================
# Tesztsorozatok
# =========================================================================
def expect(resp, prefix="OK"):
    if not resp.startswith(prefix):
        raise MousesymError(f"Várt: {prefix}..., kapott: {resp}")


def test_corners(c, pause):
    """Kurzor a középre és a négy sarokba (kattintás NÉLKÜL)."""
    points = [("közép", 5000, 5000), ("bal felső", 0, 0), ("jobb felső", 10000, 0),
              ("jobb alsó", 10000, 10000), ("bal alsó", 0, 10000), ("közép", 5000, 5000)]
    for name, x, y in points:
        print(f"--- {name} ({x},{y})")
        expect(c.command(f"MOVE {x} {y}"))
        time.sleep(pause)


def test_clicks(c, pause):
    """Kattintások a képernyő közepén – nyiss előtte egy üres Jegyzettömböt / Paintet."""
    for cmd in ["CLICK 5000 5000", "RCLICK 5000 5000", "CLICK 5000 5000",
                "DBLCLICK 5000 5000", "CLICK 5000 5000 300",
                "DOWN LEFT 4000 4000", "MOVE 6000 6000", "UP LEFT"]:
        expect(c.command(cmd))
        time.sleep(pause)
    expect(c.command("STATUS"), "OK USB=CONNECTED BUTTONS=NONE")


def test_stuck(c_factory, pause):
    """Beragadt gomb teszt: DOWN LEFT, majd a kapcsolat durva megszakítása."""
    c = c_factory()
    expect(c.command("DOWN LEFT 5000 5000"))
    st = c.command("STATUS")
    expect(st, "OK USB=CONNECTED BUTTONS=L")
    print("--- kapcsolat megszakítása RST-vel, gomb lenyomva")
    c.abort()
    time.sleep(max(pause, 1.0))
    c2 = c_factory()
    st = c2.command("STATUS")
    c2.close()
    expect(st, "OK USB=CONNECTED BUTTONS=NONE")
    print("OK: a firmware felengedte a gombot a kapcsolat megszakadásakor")


def test_errors(c, pause):
    """Hibás parancsok: a firmware-nek hibával kell válaszolnia és működnie kell tovább."""
    cases = [
        ("FOO", "ERROR INVALID_COMMAND"),
        ("CLICK", "ERROR INVALID_COMMAND"),
        ("CLICK 10001 5000", "ERROR INVALID_COORDINATE"),
        ("CLICK -1 0", "ERROR INVALID_COORDINATE"),
        ("MOVE abc def", "ERROR INVALID_COORDINATE"),
        ("DOWN SIDEWAYS", "ERROR INVALID_COMMAND"),
        ("CLICK 1 2 3 4 5", "ERROR INVALID_COMMAND"),
        ("X" * 500, "ERROR INVALID_COMMAND"),
    ]
    for cmd, want in cases:
        resp = c.command(cmd, echo=f">> {cmd[:40]}{'...' if len(cmd) > 40 else ''}")
        if resp != want:
            raise MousesymError(f"{cmd[:30]!r}: várt {want}, kapott {resp}")
    expect(c.command("PING"))
    print("OK: minden hibás parancs helyes hibakódot kapott, a kapcsolat él")


def test_stress(c, pause, n=200):
    """Sok MOVE parancs gyors egymásutánban (USB/Ethernet párhuzamosság)."""
    t0 = time.time()
    for i in range(n):
        x = (i * 397) % 10001
        y = (i * 211) % 10001
        expect(c.command(f"MOVE {x} {y}"))
    dt = time.time() - t0
    expect(c.command("MOVE 5000 5000"))
    print(f"OK: {n} parancs {dt:.2f} s alatt ({n / dt:.0f} parancs/s)")


def test_unauth(host, port):
    """Hitelesítés nélkül minden parancs elutasítva."""
    c = MousesymClient(host, port, key="")
    c.connect(authenticate=False)
    resp = c.command("CLICK 5000 5000")
    c.close()
    if resp != "ERROR UNAUTHORIZED":
        raise MousesymError(f"Hitelesítés nélküli parancsra várt ERROR UNAUTHORIZED, kapott: {resp}")
    print("OK: hitelesítés nélkül elutasítva")


# =========================================================================
def main():
    ap = argparse.ArgumentParser(description="Mousesym TCP tesztkliens")
    ap.add_argument("--host", required=True, help="a panel IP-címe")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--key", help="parancskulcs (alapból MOUSESYM_KEY vagy bekérés)")
    ap.add_argument("--test", choices=["corners", "clicks", "stuck", "errors", "stress", "unauth", "all"])
    ap.add_argument("--pause", type=float, default=1.0, help="szünet a tesztlépések között (s)")
    ap.add_argument("-q", "--quiet", action="store_true")
    ap.add_argument("commands", nargs="*", help='parancsok, pl. "CLICK 5000 5000"')
    a = ap.parse_args()

    key = a.key or os.environ.get("MOUSESYM_KEY")
    if key is None and a.test != "unauth":
        key = getpass.getpass("Parancskulcs: ")

    def factory():
        return MousesymClient(a.host, a.port, key, verbose=not a.quiet).connect()

    try:
        if a.test:
            tests = ["unauth", "errors", "corners", "clicks", "stuck"] if a.test == "all" else [a.test]
            for t in tests:
                print(f"=== teszt: {t}")
                if t == "unauth":
                    test_unauth(a.host, a.port)
                elif t == "stuck":
                    test_stuck(factory, a.pause)
                else:
                    with factory() as c:
                        {"corners": test_corners, "clicks": test_clicks,
                         "errors": test_errors, "stress": test_stress}[t](c, a.pause)
            print("=== minden teszt sikeres")
            return 0

        with factory() as c:
            if a.commands:
                rc = 0
                for cmd in a.commands:
                    if not c.command(cmd).startswith("OK"):
                        rc = 1
                return rc
            print("Interaktív mód. Példák: CLICK 5000 5000 | MOVE 0 0 | STATUS | QUIT")
            while True:
                try:
                    line = input("mousesym> ").strip()
                except EOFError:
                    break
                if not line:
                    continue
                c.command(line)
                if line.upper() == "QUIT":
                    c.sock.close()
                    c.sock = None
                    break
        return 0
    except KeyboardInterrupt:
        return 130
    except (OSError, MousesymError) as e:
        print(f"HIBA: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
mock_server.py – a Mousesym TCP protokoll szoftveres utánzata hardver nélküli
kliensfejlesztéshez és a mousesym_client.py kipróbálásához.

  python mock_server.py --port 5000 --key mousesym
  python mousesym_client.py --host 127.0.0.1 --key mousesym --test all

A szerver nem mozgat egeret, csak a protokollt (HELLO/AUTH, parancsok,
válaszkódok, gombállapot, bontáskori felengedés) valósítja meg ugyanazokkal
a szabályokkal, mint a firmware (src/cmd_parser.c, src/cmd_server.c).
"""
import argparse
import hashlib
import hmac
import re
import secrets
import socketserver

STATE = {"buttons": 0, "pos": None}
BTN = {"LEFT": 1, "RIGHT": 2, "MIDDLE": 4}
NUM = re.compile(r"^[0-9]{1,5}$")


def coord(tok):
    if not NUM.match(tok) or int(tok) > 10000:
        raise ValueError("coord")
    return int(tok)


def handle(line, st):
    """Visszatér: válaszsor. Ugyanaz a szabályrendszer, mint cmd_parser.c."""
    if len(line) > 128 or any(ord(ch) < 0x20 and ch != "\t" or ord(ch) >= 0x7F for ch in line):
        return "ERROR INVALID_COMMAND"
    t = line.split()
    if not t:
        return None
    kw = t[0].upper()
    if kw == "QUIT" and len(t) == 1:
        st["quit"] = True
        return "OK"
    if kw == "AUTH":
        if len(t) != 2 or not re.match(r"^[0-9a-fA-F]{64}$", t[1]):
            return "ERROR INVALID_COMMAND"
        want = hmac.new(st["key"], st["nonce"].encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(want, t[1].lower()):
            st["authed"] = True
            return "OK"
        st["fails"] += 1
        if st["fails"] >= 3:
            st["quit"] = True
        return "ERROR UNAUTHORIZED"
    known = {"STATUS", "PING", "CLICK", "RCLICK", "MCLICK", "DBLCLICK", "MOVE", "DOWN", "UP", "SCROLL"}
    if kw not in known:
        return "ERROR INVALID_COMMAND"
    if kw in ("STATUS", "PING"):
        if len(t) != 1:
            return "ERROR INVALID_COMMAND"
    if not st["authed"]:
        return "ERROR UNAUTHORIZED"
    try:
        if kw == "PING":
            return "OK"
        if kw == "STATUS":
            b = "".join(n for n, m in (("L", 1), ("R", 2), ("M", 4)) if STATE["buttons"] & m) or "NONE"
            pos = "UNKNOWN" if STATE["pos"] is None else "%d,%d" % STATE["pos"]
            return f"OK USB=CONNECTED BUTTONS={b} POS={pos} CLICK_MS=50 DBL_GAP_MS=80 IP=127.0.0.1 MODE=mock FW=mock"
        if kw in ("CLICK", "RCLICK", "MCLICK", "DBLCLICK"):
            if len(t) not in (3, 4):
                return "ERROR INVALID_COMMAND"
            STATE["pos"] = (coord(t[1]), coord(t[2]))
            if len(t) == 4 and (not NUM.match(t[3]) or not 10 <= int(t[3]) <= 2000):
                return "ERROR INVALID_COMMAND"
            return "OK"
        if kw == "MOVE":
            if len(t) != 3:
                return "ERROR INVALID_COMMAND"
            STATE["pos"] = (coord(t[1]), coord(t[2]))
            return "OK"
        if kw in ("DOWN", "UP"):
            if len(t) not in (2, 4) or t[1].upper() not in BTN:
                return "ERROR INVALID_COMMAND"
            if len(t) == 4:
                STATE["pos"] = (coord(t[2]), coord(t[3]))
            if kw == "DOWN":
                STATE["buttons"] |= BTN[t[1].upper()]
            else:
                STATE["buttons"] &= ~BTN[t[1].upper()]
            return "OK"
        if kw == "SCROLL":
            if len(t) != 2 or not re.match(r"^-?[0-9]{1,3}$", t[1]) or not (-127 <= int(t[1]) <= 127) or int(t[1]) == 0:
                return "ERROR INVALID_COMMAND"
            return "OK"
    except ValueError:
        return "ERROR INVALID_COORDINATE"
    return "ERROR INVALID_COMMAND"


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        st = {"key": self.server.key, "nonce": secrets.token_hex(16), "authed": False, "fails": 0, "quit": False}
        print(f"[mock] client {self.client_address[0]} connected")
        try:
            self.wfile.write(f"HELLO MOUSESYM 1 {st['nonce']}\r\n".encode())
            while not st["quit"]:
                raw = self.rfile.readline(4096)
                if not raw:
                    break
                if not raw.endswith(b"\n"):
                    # túl hosszú sor: a maradékot eldobjuk
                    self.wfile.write(b"ERROR INVALID_COMMAND\r\n")
                    while raw and not raw.endswith(b"\n"):
                        raw = self.rfile.readline(4096)
                    continue
                line = raw.decode("latin-1").rstrip("\r\n")
                resp = handle(line, st)
                if resp:
                    self.wfile.write(resp.encode() + b"\r\n")
        except ConnectionError:
            pass
        finally:
            if STATE["buttons"]:
                print("[mock] disconnect -> release all buttons")
            STATE["buttons"] = 0
            print("[mock] client disconnected")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--key", default="mousesym")
    a = ap.parse_args()
    srv = Server(("0.0.0.0", a.port), Handler)
    srv.key = a.key.encode()
    print(f"[mock] listening on {a.port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()

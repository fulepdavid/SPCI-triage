import csv
import io
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        state = self.server.state
        device = query.get('device_id', [None])[0]
        path = parsed.path
        try:
            limit = int(query.get('limit', [state.config['history_size']])[0])
            if not 1 <= limit <= state.config['history_size']:
                raise ValueError()
        except ValueError:
            return self.send_json({'error': 'Invalid limit'}, 400)
        if path == '/api/health':
            return self.send_json({'status': 'ok', 'hl7_listening': not self.server.hl7.stopping.is_set(),
                                   'devices': len(state.devices())})
        if path == '/api/devices':
            return self.send_json(state.devices())
        if path == '/api/latest':
            rows = [r for r in state.devices() if not device or r['device_id'] == device]
            return self.send_json(max(rows, key=lambda r: r['received_at']) if rows else
                                  {'connected': False, 'fresh': False, 'vitals': {}})
        if path == '/api/history':
            return self.send_json(state.histories(device, limit))
        if path == '/api/raw':
            with state.lock:
                return self.send_json(list(state.raw))
        if path == '/api/settings':
            return self.send_json(state.config)
        if path == '/api/history.csv':
            output = io.StringIO(newline='')
            writer = csv.writer(output)
            keys = ['spo2', 'pulse_rate', 'nibp_sys', 'nibp_dia', 'nibp_mean']
            writer.writerow(['received_at', 'device_id'] + [x for k in keys for x in (k, k + '_unit')])
            def safe(value):
                text = '' if value is None else str(value)
                return "'" + text if text.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else text
            for row in state.histories(device, limit):
                values = [row['received_at'], row['device_id']]
                for key in keys:
                    vital = row['vitals'].get(key, {})
                    values.extend([vital.get('value'), vital.get('unit')])
                writer.writerow([safe(v) for v in values])
            return self.send_bytes(output.getvalue().encode('utf-8-sig'), 'text/csv; charset=utf-8', download=True)
        assets = {'/': ('templates/index.html', 'text/html; charset=utf-8'),
                  '/static/style.css': ('static/style.css', 'text/css'),
                  '/static/app.js': ('static/app.js', 'application/javascript')}
        if path in assets:
            file, mime = assets[path]
            return self.send_bytes((state.root / 'web' / file).read_bytes(), mime)
        self.send_json({'error': 'Not found'}, 404)

    def send_json(self, value, status=200):
        self.send_bytes(json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8'),
                        'application/json; charset=utf-8', status)

    def send_bytes(self, body, mime, status=200, download=False):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; object-src 'none'; frame-ancestors 'none'")
        if download:
            self.send_header('Content-Disposition', 'attachment; filename="measurements.csv"')
        self.end_headers()
        self.wfile.write(body)


def make_server(address, state, hl7):
    server = ThreadingHTTPServer(address, Handler)
    server.state, server.hl7 = state, hl7
    return server

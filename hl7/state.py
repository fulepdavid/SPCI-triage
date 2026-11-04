import copy
import json
import logging
import threading
from collections import deque
from datetime import datetime
from hl7.parser import now


class State:
    def __init__(self, root, config):
        self.root, self.config = root, config
        self.lock = threading.RLock()
        self.history = deque(maxlen=config['history_size'])
        self.raw = deque(maxlen=200)
        self.latest = {}
        self.sessions = {}
        path = root / 'data/measurements.jsonl'
        if path.exists():
            with path.open(encoding='utf-8') as stream:
                for line in stream:
                    try:
                        row = json.loads(line)
                        if not isinstance(row, dict) or not all(k in row for k in ('device_id', 'received_at', 'vitals')):
                            raise ValueError('Invalid history row')
                        self.history.append(row)
                    except (ValueError, TypeError):
                        logging.warning('history_row_skipped')

    def connect(self, token, ip):
        with self.lock:
            self.sessions[token] = dict(ip=ip, devices=set())

    def disconnect(self, token):
        with self.lock:
            self.sessions.pop(token, None)

    def record_raw(self, text, ip):
        with self.lock:
            row = dict(received_at=now(), device_ip=ip, message=text)
            if self.config['save_raw_hl7']:
                self.append('hl7_raw.log', row)
            self.raw.append(row)

    def append(self, name, row):
        with (self.root / 'data' / name).open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')

    def accept(self, row, token):
        with self.lock:
            self.append('measurements.jsonl', row)
            self.history.append(row)
            snapshot = copy.deepcopy(row)
            previous = copy.deepcopy(self.latest.get(row['device_id'], {}).get('vitals', {}))
            for key, value in snapshot['vitals'].items():
                value['received_at'] = row['received_at']
                previous[key] = value
            snapshot['vitals'] = previous
            self.latest[row['device_id']] = snapshot
            self.sessions[token]['devices'].add(row['device_id'])

    def devices(self):
        with self.lock:
            rows = copy.deepcopy(list(self.latest.values()))
            for row in rows:
                row['connected'] = any(row['device_id'] in s['devices'] for s in self.sessions.values())
                age = (datetime.now().astimezone() - datetime.fromisoformat(row['received_at'])).total_seconds()
                row['fresh'] = row['connected'] and age <= self.config['stale_seconds']
                row['age_seconds'] = max(0, round(age, 1))
                for vital in row['vitals'].values():
                    age = (datetime.now().astimezone() - datetime.fromisoformat(vital['received_at'])).total_seconds()
                    vital['fresh'] = row['connected'] and age <= self.config['stale_seconds']
                    vital['age_seconds'] = max(0, round(age, 1))
            return rows

    def histories(self, device=None, limit=None):
        with self.lock:
            rows = [r for r in self.history if not device or r['device_id'] == device]
            return copy.deepcopy(rows[-limit:] if limit else rows)

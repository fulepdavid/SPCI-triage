"""Run both listeners with one command. No third-party packages required."""
import argparse
import codecs
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import threading
from hl7.server import HL7Server
from hl7.parser import now
from state import State
from web.server import make_server


class JsonFormatter(logging.Formatter):
    def format(self, record):
        row = dict(timestamp=now(), level=record.levelname, message=record.getMessage())
        if record.exc_info:
            row['exception'] = self.formatException(record.exc_info)
        return json.dumps(row, ensure_ascii=False)


def load_config(path):
    config = json.loads(path.read_text(encoding='utf-8-sig'))
    for key in ('hl7_port', 'web_port'):
        if type(config[key]) is not int or not 1 <= config[key] <= 65535:
            raise ValueError('Invalid ' + key)
    if type(config['history_size']) is not int or config['history_size'] < 1:
        raise ValueError('history_size must be positive')
    for key in ('send_ack', 'save_raw_hl7'):
        if type(config[key]) is not bool:
            raise ValueError(key + ' must be boolean')
    config.setdefault('stale_seconds', 15)
    config.setdefault('encoding', 'utf-8')
    if not isinstance(config['stale_seconds'], (int, float)) or config['stale_seconds'] <= 0:
        raise ValueError('stale_seconds must be positive')
    codecs.lookup(config['encoding'])
    return config


def main():
    root = Path(__file__).resolve().parent
    cli = argparse.ArgumentParser()
    cli.add_argument('--config', type=Path, default=root / 'config.json')
    args = cli.parse_args()
    config = load_config(args.config)
    for directory in ('data', 'logs'):
        (root / directory).mkdir(exist_ok=True)
    handler = RotatingFileHandler(str(root / 'logs/app.log'), maxBytes=5_000_000, backupCount=3, encoding='utf-8')
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    state = State(root, config)
    hl7 = HL7Server((config['hl7_host'], config['hl7_port']), state)
    try:
        web = make_server((config['web_host'], config['web_port']), state, hl7)
    except Exception:
        hl7.server_close()
        raise
    thread = threading.Thread(target=hl7.serve_forever, name='hl7-listener')
    thread.start()
    print('HL7 listening: {}:{}'.format(config['hl7_host'], config['hl7_port']), flush=True)
    print('Web interface: http://127.0.0.1:{}'.format(config['web_port']), flush=True)
    logging.info('application_started')
    try:
        web.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        hl7.stopping.set()
        hl7.shutdown()
        hl7.server_close()
        web.server_close()
        thread.join()
        logging.info('application_stopped')


if __name__ == '__main__':
    main()

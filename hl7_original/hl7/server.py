import logging
import socket
import socketserver
import uuid
from .mllp import Decoder, frame
from .parser import parse, ack


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        state = self.server.state
        ip, token = self.client_address[0], uuid.uuid4().hex
        state.connect(token, ip)
        logging.info('device_connected ip=%s', ip)
        decoder = Decoder()
        self.request.settimeout(1)
        self.request.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        try:
            while not self.server.stopping.is_set():
                try:
                    chunk = self.request.recv(65536)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                for payload in decoder.feed(chunk):
                    text = payload.decode(state.config['encoding'], errors='replace')
                    code = 'AA'
                    try:
                        state.record_raw(text, ip)
                        row = parse(text, ip, state.config)
                        state.accept(row, token)
                        logging.info('message_accepted device=%s id=%s', row['device_id'], row['message_id'])
                    except ValueError as exc:
                        code = 'AE'
                        logging.warning('message_rejected ip=%s reason=%s', ip, exc)
                    except Exception:
                        code = 'AE'
                        logging.exception('message_processing_failed ip=%s', ip)
                    if state.config['send_ack']:
                        try:
                            reply = ack(text, code)
                        except ValueError:
                            logging.warning('ack_unavailable invalid_header ip=%s', ip)
                        else:
                            self.request.sendall(frame(reply))
        except (OSError, ValueError):
            logging.info('connection_closed ip=%s', ip, exc_info=True)
        finally:
            state.disconnect(token)
            logging.info('device_disconnected ip=%s', ip)


class HL7Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = False

    def __init__(self, address, state):
        import threading
        self.state = state
        self.stopping = threading.Event()
        super().__init__(address, Handler)

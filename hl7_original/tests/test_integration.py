import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from urllib.request import urlopen
from hl7.server import HL7Server
from hl7.mllp import frame, Decoder
from state import State
from simulator import sample
from web.server import make_server


class IntegrationTests(unittest.TestCase):
    def test_waveform_does_not_refresh_vital(self):
        from hl7.parser import parse
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'data').mkdir()
            state=State(root,dict(history_size=10,stale_seconds=.01))
            state.connect('s','ip')
            state.accept(parse(sample(),'ip'),'s')
            stamp=state.devices()[0]['vitals']['spo2']['received_at']
            time.sleep(.02)
            wave=sample().split('OBX')[0]+'OBX|1|NA|150452^Wave^MDC||128^128||||||F\r'
            state.accept(parse(wave,'ip'),'s')
            d=state.devices()[0]
            self.assertEqual(d['vitals']['spo2']['received_at'],stamp)
            self.assertFalse(d['vitals']['spo2']['fresh'])
            self.assertEqual(state.histories()[-1]['vitals'],{})

    def test_tcp_ack_api_reconnect_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'data').mkdir()
            config=dict(history_size=3,save_raw_hl7=True,send_ack=True,encoding='utf-8',stale_seconds=.01)
            state=State(root,config)
            server=HL7Server(('127.0.0.1',0),state)
            web=make_server(('127.0.0.1',0),state,server)
            threads=[threading.Thread(target=s.serve_forever) for s in (server,web)]
            for thread in threads: thread.start()
            try:
                def fetch(path):
                    with urlopen('http://127.0.0.1:'+str(web.server_port)+path,timeout=3) as response:
                        return response.read()
                def receive(sock,count):
                    d=Decoder(); rows=[]
                    while len(rows)<count:
                        data=sock.recv(65536)
                        self.assertTrue(data)
                        rows.extend(d.feed(data))
                    return rows
                with socket.create_connection(server.server_address,timeout=3) as sock:
                    good=sample(); bad=sample().replace('|97|','|NaN|')
                    wire=frame(bad)+frame(good)+frame(sample('SECOND'))
                    for i in range(0,len(wire),11): sock.sendall(wire[i:i+11])
                    replies=receive(sock,3)
                    self.assertIn(b'MSA|AE|',replies[0]);self.assertIn(b'MSA|AA|',replies[1])
                    self.assertEqual(len(json.loads(fetch('/api/devices'))),2)
                    self.assertTrue(json.loads(fetch('/api/latest'))['connected'])
                    time.sleep(.03)
                    self.assertFalse(json.loads(fetch('/api/latest'))['fresh'])
                    self.assertEqual(len(json.loads(fetch('/api/history'))),2)
                    self.assertIn(b'nibp_sys_unit',fetch('/api/history.csv'))
                deadline=time.monotonic()+2
                while any(r['connected'] for r in state.devices()) and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertFalse(any(r['connected'] for r in state.devices()))
                with socket.create_connection(server.server_address,timeout=3) as sock:
                    sock.sendall(frame(sample())); self.assertIn(b'MSA|AA|',receive(sock,1)[0])
                self.assertEqual(len(State(root,config).history),3)
                self.assertTrue(json.loads(fetch('/api/health'))['hl7_listening'])
            finally:
                server.stopping.set()
                for s in (server,web): s.shutdown(); s.server_close()
                for thread in threads: thread.join()

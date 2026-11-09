"""Synthetic monitor client; never connects to a real monitor."""
import argparse
import socket
import time
import uuid
from datetime import datetime
from hl7.mllp import frame, Decoder


def sample(device='KC574337852G'):
    stamp = datetime.now().astimezone().strftime('%Y%m%d%H%M%S%z')
    lines = ['MSH|^~\\&|{}|COMEN|RECEIVER|LOCAL|{}||ORU^R01^ORU_R01|{}|P|2.6'.format(device, stamp, uuid.uuid4().hex),
             'PID|1||SIMULATED', 'OBR|1|||VITALS^Vital signs']
    for i, (code, name, value, unit) in enumerate([
        ('150456','SpO2',97,'%'),('149522','Pulse',72,'bpm'),
        ('150301','SYS',126,'mmHg'),('150302','DIA',78,'mmHg'),
        ('150303','MAP',94,'mmHg'),('149546','NIBP Pulse',71,'bpm'),
        ('147842','ECG Heart Rate',73,'bpm'),
        ('SIM_TEMP','Temperature',36.7,'Cel'),('SIM_RESP','Respiration',16,'/min')], 1):
        lines.append('OBX|{}|NM|{}^{}^MDC||{}|{}|||||F|||{}'.format(i,code,name,value,unit,stamp))
    return '\r'.join(lines) + '\r'


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--host', default='127.0.0.1')
    cli.add_argument('--port', type=int, default=5000)
    cli.add_argument('--count', type=int, default=30)
    cli.add_argument('--interval', type=float, default=1)
    cli.add_argument('--device', default='KC574337852G')
    cli.add_argument('--fragment', action='store_true')
    cli.add_argument('--batch', type=int, default=1)
    args = cli.parse_args()
    if args.batch < 1 or args.count < 1 or args.interval < 0:
        cli.error('count and batch must be positive; interval must be nonnegative')
    with socket.create_connection((args.host,args.port), timeout=5) as sock:
        decoder = Decoder()
        for _ in range(args.count):
            messages=[sample(args.device) for _ in range(args.batch)]
            wire=b''.join(frame(m) for m in messages)
            if args.fragment:
                for offset in range(0,len(wire),7):
                    sock.sendall(wire[offset:offset+7])
            else:
                sock.sendall(wire)
            replies=[]
            while len(replies)<args.batch:
                chunk=sock.recv(65536)
                if not chunk: raise ConnectionError('Server disconnected before ACK')
                replies.extend(decoder.feed(chunk))
            for message, reply in zip(messages,replies):
                control=message.split('|')[9]
                if ('MSA|AA|'+control+'\r').encode() not in reply:
                    raise RuntimeError('Unexpected ACK: '+repr(reply))
                print('ACK AA:', control)
            time.sleep(args.interval)


if __name__ == '__main__':
    main()

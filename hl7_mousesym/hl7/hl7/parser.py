"""Small ORU observation parser, not a general HL7 validation engine."""
import math
import uuid
from datetime import datetime
from .codes import CODES, MDC_UNITS


def now():
    return datetime.now().astimezone().isoformat()


def header(text):
    first = text.replace('\r\n', '\r').replace('\n', '\r').split('\r')[0]
    if not first.startswith('MSH') or len(first) < 8:
        raise ValueError('Missing MSH header')
    sep = first[3]
    fields = first.split(sep)
    if len(fields) < 12 or len(fields[1]) < 4 or not fields[9]:
        raise ValueError('Incomplete MSH or missing message control ID')
    return sep, fields[1][0], fields


def parse(text, ip, config=None):
    config = config or {}
    sep, comp, msh = header(text)
    if msh[8].split(comp)[:2] != ['ORU', 'R01']:
        raise ValueError('Expected ORU^R01')
    codes = dict(CODES)
    codes.update({k: (v['key'], v.get('unit', '')) for k, v in config.get('extra_codes', {}).items()})
    def unescape(value):
        esc = msh[1][2]
        for code, char in [('F', sep), ('S', comp), ('R', msh[1][1]), ('T', msh[1][3]), ('E', esc)]:
            value = value.replace(esc + code + esc, char)
        return value
    observations, vitals, equipment = [], {}, ''
    for line in text.replace('\r\n', '\r').replace('\n', '\r').split('\r'):
        f = line.split(sep)
        if f[0] != 'OBX':
            continue
        if len(f) < 6:
            raise ValueError('Truncated OBX')
        get = lambda i: f[i] if len(f) > i else ''
        identifier = get(3).split(comp)
        code = identifier[0]
        # Only interpret numeric identifiers as MDC when namespace is MDC or omitted.
        namespace = identifier[2].upper() if len(identifier) > 2 else ''
        mapping = codes.get(code) if namespace in ('', 'MDC', 'ISO/IEEE 11073-10101') else None
        unit_parts = get(6).split(comp)
        unit = unescape(unit_parts[0])
        if len(unit_parts) > 2 and unit_parts[2].upper() == 'MDC':
            unit = MDC_UNITS.get(unit, unit)
        raw = get(5)
        value = unescape(raw)
        if get(2) == 'NM' and raw not in ('', '""'):
            try:
                value = float(raw)
                if not math.isfinite(value):
                    raise ValueError()
                if value.is_integer():
                    value = int(value)
            except ValueError:
                raise ValueError('Invalid numeric OBX value')
        elif raw in ('', '""'):
            value = None
        item = dict(code=code, name=unescape(identifier[1]) if len(identifier) > 1 else code,
                    value=value, unit=unit, status=get(11), observed_at=get(14),
                    sub_id=get(4), data_type=get(2), raw_value=raw)
        observations.append(item)
        if get(18) and not equipment:
            equipment = get(18).split(comp)[0]
        if mapping:
            item = dict(item)
            item['unit'] = unit or mapping[1]
            vitals[mapping[0]] = item
    if not observations:
        raise ValueError('ORU contains no OBX observations')
    # Explicit IP mapping is safest until the vendor identification profile is known.
    nc_serial = msh[3].split(comp)[0] if msh[2] == 'NC_Monitor' else ''
    device_id = config.get('device_ids', {}).get(ip) or equipment or nc_serial or msh[2].split(comp)[0] or ip
    return dict(device_id=device_id, device_ip=ip, hl7_version=msh[11],
                message_id=msh[9], received_at=now(), vitals=vitals, observations=observations)


def ack(text, code='AA'):
    sep, comp, f = header(text)
    fields = ['MSH', f[1], f[4], f[5], f[2], f[3],
              datetime.now().astimezone().strftime('%Y%m%d%H%M%S%z'), '',
              comp.join(['ACK', (f[8].split(comp) + [''])[1], 'ACK']), uuid.uuid4().hex, f[10] or 'P', f[11]]
    return sep.join(fields) + '\r' + sep.join(['MSA', code, f[9]]) + '\r'

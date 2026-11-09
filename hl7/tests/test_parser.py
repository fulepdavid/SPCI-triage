import unittest
from hl7.parser import parse, ack
from simulator import sample


class ParserTests(unittest.TestCase):
    def test_observed_nc_identity_and_ack_trigger(self):
        message=sample().replace('KC574337852G|COMEN','NC_Monitor|KC574337852G')
        self.assertEqual(parse(message,'ip')['device_id'],'KC574337852G')
        self.assertIn('ACK^R40^ACK',ack(message.replace('ORU^R01','ORU^R40'),'AE'))

    def test_vitals_and_unknown(self):
        d=parse(sample(),'192.168.0.118')
        self.assertEqual(d['device_id'],'KC574337852G')
        self.assertEqual(d['vitals']['spo2']['value'],97)
        self.assertEqual(d['vitals']['nibp_mean']['unit'],'mmHg')
        self.assertEqual(len(d['observations']),9)
        self.assertNotIn('temperature', d['vitals'])

    def test_configured_codes_and_identity(self):
        config={'device_ids':{'ip':'serial'},'extra_codes':{'SIM_TEMP':{'key':'temperature','unit':'Cel'}}}
        d=parse(sample(),'ip',config)
        self.assertEqual(d['device_id'],'serial')
        self.assertEqual(d['vitals']['temperature']['value'],36.7)

    def test_ack_correlation_and_routing(self):
        message=sample(); f=message.split('\r')[0].split('|')
        reply=ack(message); a=reply.split('\r')[0].split('|')
        self.assertIn('MSA|AA|'+f[9]+'\r',reply)
        self.assertEqual(a[2:6],[f[4],f[5],f[2],f[3]])
        self.assertNotEqual(a[9],f[9])

    def test_malformed_numeric_and_message(self):
        for message in ['garbage',sample().replace('|97|','|NaN|'),sample().replace('ORU^R01','ADT^A01')]:
            with self.assertRaises(ValueError): parse(message,'ip')

    def test_custom_separator_null_and_namespace(self):
        d=parse(sample().replace('|','!'),'ip')
        self.assertEqual(d['vitals']['spo2']['value'],97)
        self.assertIsNone(parse(sample().replace('|97|','|""|'),'ip')['vitals']['spo2']['value'])
        self.assertNotIn('spo2',parse(sample().replace('150456^SpO2^MDC','150456^SpO2^LOCAL'),'ip')['vitals'])

import unittest
from hl7.mllp import Decoder, frame


class MLLPTests(unittest.TestCase):
    def test_every_split(self):
        wire=frame(b'MSH|one\r')+frame(b'MSH|two\r')
        for i in range(len(wire)+1):
            d=Decoder()
            self.assertEqual(d.feed(wire[:i])+d.feed(wire[i:]),[b'MSH|one\r',b'MSH|two\r'])

    def test_bytewise_and_noise(self):
        d=Decoder(); result=[]
        for byte in b'noise'+frame(b'hello'):
            result.extend(d.feed(bytes([byte])))
        self.assertEqual(result,[b'hello'])

    def test_resync_and_limit(self):
        self.assertEqual(Decoder().feed(b'\x0bbroken'+frame(b'good')),[b'good'])
        with self.assertRaises(ValueError):
            Decoder(4).feed(b'\x0b12345')

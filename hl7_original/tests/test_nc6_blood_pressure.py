import unittest
from hl7.parser import parse


class NC6BloodPressureTests(unittest.TestCase):
    def message(self, observations):
        return ('MSH|^~\\&|NC_Monitor|TEST_DEVICE|RECEIVER|LOCAL|20260910120000||'
                'ORU^R01^ORU_R01|test-bp|P|2.6\r' + '\r'.join(observations) + '\r')

    def test_device_blood_pressure_codes_and_units(self):
        # Device field structure, with synthetic values and no patient information.
        rows = [
            'OBX||NM|150021^MDC_PRESS_BLD_NONINV_SYS^MDC|1.1.9.150021|126|266016^MDC_DIM_MMHG^MDC',
            'OBX||NM|150022^MDC_PRESS_BLD_NONINV_DIA^MDC|1.1.9.150022|78|266016^MDC_DIM_MMHG^MDC',
            'OBX||NM|150023^MDC_PRESS_BLD_NONINV_MEAN^MDC|1.1.9.150023|94|266016^MDC_DIM_MMHG^MDC',
            'OBX||NM|149546^MDC_PULS_RATE_NON_INV^MDC|1.1.9.149546|72|264864^MDC_DIM_BEAT_PER_MIN^MDC',
            'OBX||NM|150456^MDC_PULS_OXIM_SAT_O2^MDC|1.3.1.150456|97|262688^MDC_DIM_PERCENT^MDC',
        ]
        vitals = parse(self.message(rows), 'test-ip')['vitals']
        for key, value in [('nibp_sys',126),('nibp_dia',78),('nibp_mean',94)]:
            self.assertEqual(vitals[key]['value'], value)
            self.assertEqual(vitals[key]['unit'], 'mmHg')
        self.assertEqual(vitals['nibp_pulse']['unit'], 'bpm')
        self.assertEqual(vitals['spo2']['unit'], '%')

    def test_other_namespace_is_not_reinterpreted(self):
        row = 'OBX||NM|150021^SYS^MDC||126|266016^custom^LOCAL'
        self.assertEqual(parse(self.message([row]),'test-ip')['vitals']['nibp_sys']['unit'], '266016')

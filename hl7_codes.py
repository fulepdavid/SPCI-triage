"""User-provided MDC mappings. Additional verified codes belong in config.json."""
CODES = {
    '150456': ('spo2', '%'), '149522': ('pulse_rate', 'bpm'),
    '150301': ('nibp_sys', 'mmHg'), '150302': ('nibp_dia', 'mmHg'),
    '150303': ('nibp_mean', 'mmHg'), '149546': ('nibp_pulse', 'bpm'),
    '147842': ('ecg_heart_rate', 'bpm'),
    # Confirmed in NC6 raw HL7: MDC_PRESS_BLD_NONINV_{SYS,DIA,MEAN}.
    '150021': ('nibp_sys', 'mmHg'), '150022': ('nibp_dia', 'mmHg'),
    '150023': ('nibp_mean', 'mmHg'),
}

# Coded OBX-6 units observed in the device log; no numeric conversion.
MDC_UNITS = {'262688': '%', '264864': 'bpm', '266016': 'mmHg'}

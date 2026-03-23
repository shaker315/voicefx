import numpy as np

from .base import BaseEffect


class EchoEffect(BaseEffect):
    def __init__(self, samplerate=48000):
        self.samplerate = max(1, int(samplerate))
        self.max_delay_ms = 420.0
        self.buffer_len = max(2, int(self.samplerate * self.max_delay_ms / 1000.0) + 2)
        self.buffer = np.zeros(self.buffer_len, dtype=np.float32)
        self.write_pos = 0

    def process(self, signal, state):
        if not state.echo_on or not state.fx_master_on:
            return signal

        amount = max(1.0, min(4.0, float(state.echo)))
        blend = (amount - 1.0) / 3.0
        delay_ms = 70.0 + blend * 210.0
        feedback = 0.10 + blend * 0.28
        wet = 0.08 + blend * 0.22

        delay_samples = max(1, int(delay_ms * self.samplerate / 1000.0))
        out = np.empty_like(signal)

        for i, sample in enumerate(signal):
            read_pos = (self.write_pos - delay_samples) % self.buffer_len
            delayed = self.buffer[read_pos]

            out[i] = sample * (1.0 - wet) + delayed * wet
            self.buffer[self.write_pos] = np.clip(sample + delayed * feedback, -1.0, 1.0)
            self.write_pos = (self.write_pos + 1) % self.buffer_len

        return out

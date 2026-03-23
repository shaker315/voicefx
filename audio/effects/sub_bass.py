import numpy as np

from .base import BaseEffect


class SubBassEffect(BaseEffect):
    def __init__(self, samplerate=48000, cutoff=90.0):
        self.samplerate = samplerate
        self.cutoff = cutoff
        self.low1 = 0.0
        self.low2 = 0.0
        self.alpha = (2 * np.pi * cutoff) / (2 * np.pi * cutoff + samplerate)

    def process(self, signal, state):
        if not state.sub_bass_on or not state.fx_master_on:
            return signal

        amount = max(1.0, min(10.0, float(state.sub_bass)))
        gain = 0.16 + ((amount - 1.0) / 9.0) * 0.54

        sub = np.zeros_like(signal)
        for i in range(len(signal)):
            self.low1 += self.alpha * (signal[i] - self.low1)
            self.low2 += self.alpha * (self.low1 - self.low2)
            sub[i] = np.tanh(self.low2 * 2.4)

        return signal + sub * gain
